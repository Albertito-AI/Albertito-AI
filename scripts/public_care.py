"""Process bounded public care requests for Sparks without reading issue bodies."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

import update_persona as pet


ROOT = Path(__file__).resolve().parents[1]
REPO = "Albertito-AI/Albertito-AI"
API = "https://api.github.com"
REPO_API = f"{API}/repos/{REPO}"
LEDGER_PATH = "data/public-care.json"
DIARY_PATH = "docs/SPARKS_CARE_LOG.md"
MAX_RECEIPTS = 2000
MAX_REQUESTS = 20
MAX_ACKS = 20
PAGE_SIZE = 100
MAX_JSON_BYTES = 3_000_000
MAX_API_BYTES = 32_000_000
ELIGIBILITY = timedelta(hours=24)
RETENTION = timedelta(hours=72)
ACTOR_COOLDOWN = timedelta(hours=1)
TITLES = {f"[Sparks] {action}": action for action in pet.EFFECTS}
LEDGER_KEYS = {"schema_version", "enabled_at", "scan_page", "receipts"}
RECEIPT_KEYS = {"action", "reason", "message", "accepted", "processed_at", "created_at", "actor_key", "pending_ack"}
REASONS = {"accepted", "cooldown", "actor_cooldown", "satisfied", "too_tired", "expired"}
FIXED_MESSAGES = {
    "cooldown": "Thanks, I need a short pause. Please wait until the 15-minute shared care interval has passed.",
    "actor_cooldown": "Thanks for caring for me. Please allow one hour between your accepted care actions.",
    "too_tired": "Thanks, I am too tired to study. A little rest would help.",
    "expired": "Thanks for thinking of me. This request is more than 24 hours old; please open a new one.",
}
SATISFIED_MESSAGES = {
    "feed": "Thanks, I have enough ideas for now.",
    "play": "Thanks, I have had enough play for now.",
    "rest": "Thanks, I am already well rested.",
    "study": "Thanks, I have enough to study for now.",
}
LABELS = {
    "accepted": ("sparks: accepted", "2DA44E", "Sparks accepted this care request."),
    "satisfied": ("sparks: enough for now", "A371F7", "Sparks already had enough of this care."),
    "too_tired": ("sparks: needs rest", "D4A72C", "Sparks was too tired to study."),
    "cooldown": ("sparks: cooldown", "BF8700", "A shared or visitor care interval was still active."),
    "actor_cooldown": ("sparks: cooldown", "BF8700", "A shared or visitor care interval was still active."),
    "expired": ("sparks: expired", "6E7781", "This care request was older than 24 hours."),
}
CARE_NAMES = {"feed": "Feed an idea", "study": "Study", "play": "Play", "rest": "Rest"}


class PublicCareError(RuntimeError):
    pass


class GitHubAPIError(PublicCareError):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"GitHub API request failed with HTTP {status}; no new decisions were saved.")


class RateLimitError(PublicCareError):
    pass


class ResponseTooLarge(PublicCareError):
    pass


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def _positive_integer(value) -> bool:
    return type(value) is int and value > 0


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON contains duplicate fields")
        result[key] = value
    return result


def _decode_json(raw: bytes | str, limit: int = MAX_JSON_BYTES):
    if len(raw.encode("utf-8") if isinstance(raw, str) else raw) > limit:
        raise ValueError("JSON exceeds the public-care size limit")
    try:
        return json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid JSON in public-care data") from exc


class GitHubClient:
    """Fixed-host client; never follows redirects or includes HTTP bodies in errors."""

    def __init__(self, token: str):
        if not token:
            raise PublicCareError("GITHUB_TOKEN is required for public-care API operations")
        self._token = token
        self._opener = build_opener(_NoRedirects())
        self._labels = set()

    def _request(self, method: str, path: str, payload=None):
        if method not in {"GET", "POST", "PATCH"} or not path.startswith(f"/repos/{REPO}/"):
            raise PublicCareError("refusing an unexpected GitHub endpoint")
        if ".." in path or "#" in path or "\\" in path:
            raise PublicCareError("refusing an unsafe GitHub endpoint")
        data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
        request = Request(API + path, data=data, method=method, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Sparks-Public-Care",
            "Content-Type": "application/json",
        })
        try:
            with self._opener.open(request, timeout=20) as response:
                raw = response.read(MAX_API_BYTES + 1)
        except HTTPError as exc:
            if exc.code in {403, 429} and (exc.code == 429 or exc.headers.get("Retry-After") or exc.headers.get("X-RateLimit-Remaining") == "0"):
                retry = exc.headers.get("Retry-After", "")
                hint = f" Retry after {int(retry)} seconds." if re.fullmatch(r"[0-9]{1,7}", retry) else " Retry later according to GitHub's rate-limit guidance."
                raise RateLimitError("GitHub rate limit reached; stopping immediately." + hint) from None
            raise GitHubAPIError(exc.code) from None
        except (URLError, OSError):
            raise PublicCareError("GitHub API connection failed; no credentials or response content were logged") from None
        if len(raw) > MAX_API_BYTES:
            raise ResponseTooLarge("GitHub API response exceeded its bounded size limit")
        return _decode_json(raw, limit=MAX_API_BYTES) if raw else None

    def list_open_issues(self, page: int) -> list:
        if not _positive_integer(page):
            raise ValueError("invalid issue scan page")
        def fetch(subpage: int, size: int) -> list:
            query = urlencode({"state": "open", "sort": "created", "direction": "asc", "per_page": size, "page": subpage})
            result = self._request("GET", f"/repos/{REPO}/issues?{query}")
            if not isinstance(result, list) or len(result) > size:
                raise PublicCareError("GitHub returned an unexpected issue page")
            return result

        try:
            return fetch(page, PAGE_SIZE)
        except ResponseTooLarge:
            # Full REST objects contain bodies. Split only an oversized page,
            # keeping the same 100-issue window and a finite ten-call fallback.
            results = []
            for subpage in range((page - 1) * 10 + 1, page * 10 + 1):
                batch = fetch(subpage, 10)
                results.extend(batch)
                if len(batch) < 10:
                    break
            return results

    def get_issue(self, number: int) -> dict:
        if not _positive_integer(number):
            raise ValueError("invalid issue number")
        return self._request("GET", f"/repos/{REPO}/issues/{number}")

    def ensure_label(self, label: tuple[str, str, str]) -> None:
        if label not in LABELS.values():
            raise ValueError("refusing an unknown outcome label")
        name, color, description = label
        if name in self._labels:
            return
        path = f"/repos/{REPO}/labels/{quote(name, safe='')}"
        try:
            existing = self._request("GET", path)
        except GitHubAPIError as exc:
            if exc.status != 404:
                raise
            try:
                existing = self._request("POST", f"/repos/{REPO}/labels", {"name": name, "color": color, "description": description})
            except GitHubAPIError as create_error:
                if create_error.status != 422:
                    raise
                existing = self._request("GET", path)
        if not isinstance(existing, dict) or existing.get("name") != name:
            raise PublicCareError("GitHub returned an unexpected outcome label")
        self._labels.add(name)

    def add_label(self, number: int, name: str) -> None:
        if not _positive_integer(number) or name not in {item[0] for item in LABELS.values()}:
            raise ValueError("invalid public-care label request")
        self._request("POST", f"/repos/{REPO}/issues/{number}/labels", {"labels": [name]})

    def close_issue(self, number: int, accepted: bool) -> None:
        if not _positive_integer(number) or type(accepted) is not bool:
            raise ValueError("invalid public-care closure request")
        self._request("PATCH", f"/repos/{REPO}/issues/{number}", {
            "state": "closed", "state_reason": "completed" if accepted else "not_planned",
        })


def initial_ledger(enabled_at: datetime) -> dict:
    return {"schema_version": 1, "enabled_at": pet.timestamp(enabled_at), "scan_page": 1, "receipts": {}}


def feedback(action: str, reason: str) -> str:
    if action not in pet.EFFECTS or reason not in REASONS or (reason == "too_tired" and action != "study"):
        raise ValueError("invalid public-care outcome")
    if reason == "accepted":
        return pet.ACCEPTED_MESSAGES[action]
    if reason == "satisfied":
        return SATISFIED_MESSAGES[action]
    return FIXED_MESSAGES[reason]


def _ledger_time(value) -> datetime:
    try:
        return pet.parse_time(value)
    except (ValueError, OverflowError):
        raise ValueError("public-care timestamps must be valid timezone-aware ISO 8601 values") from None


def validate_ledger(ledger: dict, now: datetime | None = None) -> None:
    if not isinstance(ledger, dict) or set(ledger) != LEDGER_KEYS:
        raise ValueError("public-care ledger fields do not match schema version 1")
    if type(ledger["schema_version"]) is not int or ledger["schema_version"] != 1:
        raise ValueError("unsupported public-care ledger schema")
    if not _positive_integer(ledger["scan_page"]):
        raise ValueError("public-care scan_page must be a positive integer")
    enabled = _ledger_time(ledger["enabled_at"])
    receipts = ledger["receipts"]
    if not isinstance(receipts, dict) or len(receipts) > MAX_RECEIPTS:
        raise ValueError("public-care receipt capacity exceeded or receipts are malformed")
    for number, receipt in receipts.items():
        if not isinstance(number, str) or not re.fullmatch(r"[1-9][0-9]*", number):
            raise ValueError("public-care receipt keys must be canonical positive issue numbers")
        if not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS:
            raise ValueError("public-care receipt fields are malformed")
        if type(receipt["accepted"]) is not bool or type(receipt["pending_ack"]) is not bool:
            raise ValueError("public-care outcome flags must be boolean")
        if not isinstance(receipt["action"], str) or not isinstance(receipt["reason"], str):
            raise ValueError("public-care action and reason must be known strings")
        if receipt["message"] != feedback(receipt["action"], receipt["reason"]):
            raise ValueError("public-care receipt contains a noncanonical response")
        if receipt["accepted"] != (receipt["reason"] == "accepted"):
            raise ValueError("public-care accepted flag disagrees with its reason")
        actor = receipt["actor_key"]
        if not isinstance(actor, str) or not re.fullmatch(r"[0-9a-f]{64}", actor):
            raise ValueError("public-care actor key is malformed")
        created, processed = _ledger_time(receipt["created_at"]), _ledger_time(receipt["processed_at"])
        if not enabled <= created <= processed or (now is not None and processed > now):
            raise ValueError("public-care receipt timestamps are inconsistent")
        if receipt["accepted"] and processed - created > ELIGIBILITY:
            raise ValueError("an expired public-care request cannot be accepted")
        if receipt["reason"] == "expired" and processed - created <= ELIGIBILITY:
            raise ValueError("public-care expiry is inconsistent with its timestamps")


def actor_key(user_id: int) -> str:
    if not _positive_integer(user_id):
        raise ValueError("invalid public-care actor identifier")
    return hashlib.sha256(f"sparks:{user_id}".encode("ascii")).hexdigest()


def event_issue_number(event) -> int | None:
    if not isinstance(event, dict) or event.get("action") != "opened":
        return None
    repository, issue = event.get("repository"), event.get("issue")
    if not isinstance(repository, dict) or repository.get("full_name") != REPO:
        return None
    if not isinstance(issue, dict) or "pull_request" in issue or not _positive_integer(issue.get("number")):
        return None
    return issue["number"]


def _request_metadata(issue, enabled: datetime, now: datetime, expected_number: int | None = None):
    if not isinstance(issue, dict) or "pull_request" in issue or issue.get("state") != "open":
        return None
    number, title, user = issue.get("number"), issue.get("title"), issue.get("user")
    if not _positive_integer(number) or (expected_number is not None and number != expected_number):
        return None
    if issue.get("repository_url") != REPO_API or not isinstance(title, str) or title not in TITLES:
        return None
    if not isinstance(user, dict) or user.get("type") != "User" or not _positive_integer(user.get("id")):
        return None
    try:
        created = _ledger_time(issue.get("created_at"))
    except ValueError:
        return None
    if not enabled <= created <= now:
        return None
    return {"number": number, "action": TITLES[title], "created_at": pet.timestamp(created), "actor_key": actor_key(user["id"])}


def _immutable_part(receipt: dict) -> dict:
    return {key: value for key, value in receipt.items() if key != "pending_ack"}


def _check_baseline(working: dict, committed: dict, now: datetime) -> None:
    if working["enabled_at"] != committed["enabled_at"]:
        raise ValueError("public-care activation timestamp cannot change during processing")
    for number, original in committed["receipts"].items():
        current = working["receipts"].get(number)
        if current is not None and _immutable_part(current) != _immutable_part(original):
            raise ValueError("a committed public-care decision was modified")
        if current is None and (original["pending_ack"] or now - _ledger_time(original["processed_at"]) <= RETENTION):
            raise ValueError("a pending or recent committed public-care decision was removed")


def _ack_one(client, number: str, receipt: dict) -> None:
    terminal_statuses = {301, 302, 303, 307, 308, 404, 410}
    try:
        latest = client.get_issue(int(number))
    except GitHubAPIError as exc:
        if exc.status in terminal_statuses:
            return
        raise
    if not isinstance(latest, dict):
        raise PublicCareError("GitHub returned an unexpected decided issue")
    if latest.get("repository_url") != REPO_API or latest.get("number") != int(number) or "pull_request" in latest:
        return
    if latest.get("title") != f"[Sparks] {receipt['action']}" or latest.get("state") == "closed":
        return
    if latest.get("state") != "open":
        raise PublicCareError("GitHub returned an unexpected decided-issue state")
    label = LABELS[receipt["reason"]]
    client.ensure_label(label)
    try:
        client.add_label(int(number), label[0])
        client.close_issue(int(number), receipt["accepted"])
    except GitHubAPIError as exc:
        if exc.status not in terminal_statuses:
            raise


def acknowledge_ledger(ledger: dict, client, limit: int = MAX_ACKS) -> int:
    """Acknowledge a committed snapshot without mutating the snapshot or local files."""
    validate_ledger(ledger)
    pending = sorted((number for number, receipt in ledger["receipts"].items() if receipt["pending_ack"]), key=int)
    for number in pending[:limit]:
        _ack_one(client, number, ledger["receipts"][number])
    return min(len(pending), limit)


@dataclass(frozen=True)
class Prepared:
    state: dict
    ledger: dict
    processed: int
    acknowledged: int
    capacity_reached: bool = False
    backlog_remaining: bool = False


def prepare(state: dict, ledger: dict, committed: dict, client, now: datetime, event=None) -> Prepared:
    """Make decisions in memory; only receipts in the committed baseline may be acknowledged."""
    now = pet.parse_time(pet.timestamp(now))
    pet.validate_state(state)
    if _ledger_time(state["updated_at"]) > now:
        raise ValueError("public-care clock precedes the saved persona state")
    validate_ledger(ledger, now)
    validate_ledger(committed, now)
    _check_baseline(ledger, committed, now)
    working, current_state = deepcopy(ledger), deepcopy(state)
    prior_pending = sorted((number for number, receipt in committed["receipts"].items() if receipt["pending_ack"] and working["receipts"][number]["pending_ack"]), key=int)
    acknowledged = 0
    for number in prior_pending[:MAX_ACKS]:
        _ack_one(client, number, committed["receipts"][number])
        working["receipts"][number]["pending_ack"] = False
        acknowledged += 1
    for number, receipt in list(working["receipts"].items()):
        if not receipt["pending_ack"] and now - _ledger_time(receipt["processed_at"]) > RETENTION:
            del working["receipts"][number]
    if len(prior_pending) > MAX_ACKS:
        return Prepared(current_state, working, 0, acknowledged, backlog_remaining=True)
    if len(working["receipts"]) >= MAX_RECEIPTS:
        return Prepared(current_state, working, 0, acknowledged, capacity_reached=True)

    page = client.list_open_issues(working["scan_page"])
    if not isinstance(page, list) or len(page) > PAGE_SIZE:
        raise PublicCareError("unexpected public-care discovery page")
    working["scan_page"] = working["scan_page"] + 1 if len(page) == PAGE_SIZE else 1
    enabled = _ledger_time(working["enabled_at"])
    numbers = []
    event_number = event_issue_number(event)
    if event_number is not None:
        numbers.append(event_number)
    for issue in page:
        metadata = _request_metadata(issue, enabled, now)
        if metadata is not None:
            numbers.append(metadata["number"])
    candidates = list(dict.fromkeys(number for number in numbers if str(number) not in working["receipts"]))[:MAX_REQUESTS]
    processed = 0
    for number in candidates:
        if len(working["receipts"]) >= MAX_RECEIPTS:
            break
        try:
            latest = client.get_issue(number)
        except GitHubAPIError as exc:
            if exc.status == 404:
                continue
            raise
        metadata = _request_metadata(latest, enabled, now, expected_number=number)
        if metadata is None:
            continue
        action, actor = metadata["action"], metadata["actor_key"]
        if now - _ledger_time(metadata["created_at"]) > ELIGIBILITY:
            candidate = pet.advance(current_state, now, "tick", event_id=None)
            reason, accepted = "expired", False
        else:
            candidate = pet.advance(current_state, now, action, event_id=None)
            reason, accepted = candidate.reason, candidate.accepted
            recent_actor_care = any(receipt["accepted"] and receipt["actor_key"] == actor and now - _ledger_time(receipt["processed_at"]) < ACTOR_COOLDOWN for receipt in working["receipts"].values())
            if reason not in {"satisfied", "too_tired"} and recent_actor_care:
                candidate = pet.advance(current_state, now, "tick", event_id=None)
                reason, accepted = "actor_cooldown", False
        current_state = candidate.state
        working["receipts"][str(number)] = {
            "action": action, "reason": reason, "message": feedback(action, reason),
            "accepted": accepted, "processed_at": pet.timestamp(now),
            "created_at": metadata["created_at"], "actor_key": actor, "pending_ack": True,
        }
        processed += 1
    validate_ledger(working, now)
    pet.validate_state(current_state)
    return Prepared(current_state, working, processed, acknowledged, capacity_reached=len(working["receipts"]) >= MAX_RECEIPTS)


def render_diary(ledger: dict) -> str:
    validate_ledger(ledger)
    lines = [
        "# Caring for Sparks", "",
        "Sparks is a fictional digital companion. This diary shows the latest 20 handled care requests and Sparks' responses.",
        "", "A request can be accepted, declined when Sparks has enough or needs rest, paused by a care interval, or declined because it is more than 24 hours old.", "",
    ]
    recent = sorted(ledger["receipts"].items(), key=lambda item: (_ledger_time(item[1]["processed_at"]), int(item[0])), reverse=True)[:20]
    if not recent:
        return "\n".join(lines + ["No care requests have been handled yet.", ""])
    lines.extend(["| Singapore time | Request | Care | Sparks' response |", "| --- | --- | --- | --- |"])
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    for number, receipt in recent:
        local = _ledger_time(receipt["processed_at"]).astimezone(pet.SINGAPORE)
        stamp = f"{local.day:02d} {months[local.month - 1]} {local.year}, {local:%H:%M} SGT"
        outcome = "Accepted." if receipt["accepted"] else "Declined."
        lines.append(f"| {stamp} | [#{number}](https://github.com/{REPO}/issues/{number}) | {CARE_NAMES[receipt['action']]} | {outcome} {receipt['message']} |")
    return "\n".join(lines) + "\n"


def load_committed_ledger(root: Path) -> dict:
    result = subprocess.run(["git", "show", f"HEAD:{LEDGER_PATH}"], cwd=root, capture_output=True, timeout=15, check=False)
    if result.returncode != 0:
        raise PublicCareError("cannot read the committed public-care ledger from HEAD")
    ledger = _decode_json(result.stdout)
    validate_ledger(ledger)
    return ledger


def _read_event():
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        return None
    return _decode_json(Path(path).read_bytes())


def main(argv: list[str] | None = None, root: Path = ROOT, client=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", nargs="?", choices=("prepare", "acknowledge"))
    parser.add_argument("--check", action="store_true", help="Validate the working ledger and exact diary without API calls or writes.")
    parser.add_argument("--now", help="Timezone-aware ISO 8601 clock for reproducible local processing.")
    args = parser.parse_args(argv)
    if args.check and (args.phase or args.now):
        parser.error("--check cannot be combined with a phase or clock override")
    if not args.check and not args.phase:
        parser.error("choose prepare, acknowledge or --check")
    try:
        if args.check:
            ledger = _decode_json((root / LEDGER_PATH).read_bytes())
            validate_ledger(ledger)
            if (root / DIARY_PATH).read_text(encoding="utf-8") != render_diary(ledger):
                raise ValueError("Sparks' care diary differs from the saved public-care ledger")
            print("Public-care ledger and diary are consistent.")
            return 0
        committed = load_committed_ledger(root)
        api = client if client is not None else GitHubClient(os.environ.get("GITHUB_TOKEN", ""))
        if args.phase == "acknowledge":
            count = acknowledge_ledger(committed, api)
            print(f"Acknowledged {count} committed care request(s); local files were unchanged.")
            return 0
        now = pet.parse_time(args.now) if args.now else datetime.now(pet.UTC)
        ledger = _decode_json((root / LEDGER_PATH).read_bytes())
        state = _decode_json((root / "data/persona.json").read_bytes())
        template = (root / "assets/persona-template.svg").read_text(encoding="utf-8")
        result = prepare(state, ledger, committed, api, now, _read_event())
        outputs = pet.render_outputs(result.state, template)
        outputs[LEDGER_PATH] = json.dumps(result.ledger, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        outputs[DIARY_PATH] = render_diary(result.ledger)
        outputs["data/persona.json"] = json.dumps(result.state, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        for relative, content in outputs.items():
            pet._atomic_write(root / relative, content)
        print(f"Prepared {result.processed} care decision(s); acknowledged {result.acknowledged} older committed request(s).")
        if result.capacity_reached:
            print("Receipt capacity reached; further care was deferred without applying effects.")
        if result.backlog_remaining:
            print("Committed acknowledgements remain; new care was deferred.")
        return 0
    except (PublicCareError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"Public care stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
