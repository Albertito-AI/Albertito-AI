"""Observe a fixed public portfolio and maintain evidence-linked navigation."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
SGT = ZoneInfo("Asia/Singapore")
WATCHLIST = tuple("Albertito-AI/" + name for name in ("policykit", "regnav-source-watch", "symbolon", "piepowder", "tallystick"))
# Legacy paths and the stored agent identifier preserve existing evidence.
# The public utility operates independently of the retired companion state.
CATALOG_PATH = "data/sparks-catalog.json"
MEMORY_PATH = "data/sparks-knowledge.json"
WORKBENCH_PATH = "docs/SPARKS_WORKBENCH.md"
MAX_CHANGES = 20
MAX_JSON_BYTES = 512_000
MAX_API_BYTES = 16_000_000
MAX_TREE_ENTRIES = 20_000
PROBLEMS = {
    "not_public": "Public visibility could not be established.",
    "repository_unavailable": "Repository metadata was unavailable.",
    "commit_unavailable": "The default-branch commit was unavailable.",
    "tree_unavailable": "The exact source tree was unavailable.",
    "release_unavailable": "Release metadata was unavailable.",
    "invalid_response": "The source response did not satisfy the expected contract.",
    "incomplete_tree": "The source tree was truncated or exceeded the observation limit.",
    "rate_limited": "GitHub requested a pause; this source needs another observation.",
}
MEMORY_KEYS = {"schema_version", "agent", "created_at", "updated_at", "last_observed_date", "last_workflow_run_id", "catalog_sha256", "repositories", "changes"}
RECORD_KEYS = {"status", "attempted_at", "problem", "has_compared", "last_good"}
SNAPSHOT_KEYS = {"observed_at", "commit_sha", "tree_sha", "files", "release"}
EVIDENCE_KEYS = {"commit_sha", "readme_sha", "release"}
CHANGE_KEYS = {"repo", "observed_at", "previous_observed_at", "before", "after"}


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(UTC)
    except (AttributeError, ValueError, OverflowError):
        raise ValueError("a valid timezone-aware ISO 8601 timestamp is required") from None


def timestamp(now: datetime) -> str:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("the observation clock must include a timezone")
    return now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha(value, length=40) -> bool:
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is not None


def _path(value) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 180 and re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", value) is not None and all(part not in {".", ".."} for part in value.split("/"))


def _ref(value) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 120 and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value) is not None and ".." not in value and "//" not in value and not value.endswith(("/", ".", ".lock"))


def _decode_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate public-source JSON field")
            result[key] = value
        return result

    def finite_only(value):
        raise ValueError("non-finite public-source JSON value")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=finite_only)


def validate_catalog(catalog: dict) -> None:
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "projects"} or type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        raise ValueError("invalid public portfolio catalog schema")
    projects = catalog["projects"]
    if not isinstance(projects, list) or len(projects) != len(WATCHLIST):
        raise ValueError("the catalog must contain exactly the five public watchlist projects")
    seen = set()
    for project in projects:
        required = {"repo", "title", "purpose", "start_path"}
        if not isinstance(project, dict) or not required <= set(project) <= required | {"contribute_path"}:
            raise ValueError("invalid public catalog project fields")
        repo = project["repo"]
        if not isinstance(repo, str) or repo not in WATCHLIST or repo in seen:
            raise ValueError("catalog repository is outside the fixed watchlist or duplicated")
        seen.add(repo)
        for key, limit in (("title", 80), ("purpose", 300)):
            value = project[key]
            if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 for c in value):
                raise ValueError("invalid public catalog description")
        for key in ("start_path", "contribute_path"):
            if key in project and not _path(project[key]):
                raise ValueError("catalog entrypoints must be safe relative repository file paths")


def catalog_digest(catalog: dict) -> str:
    validate_catalog(catalog)
    ordered = sorted(catalog["projects"], key=lambda item: item["repo"])
    return hashlib.sha256(json.dumps(ordered, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def initial_memory(now: datetime) -> dict:
    stamp = timestamp(now)
    return {
        "schema_version": 1, "agent": "Sparks", "created_at": stamp, "updated_at": stamp,
        "last_observed_date": None, "last_workflow_run_id": 0, "catalog_sha256": None,
        "repositories": {repo: {"status": "unobserved", "attempted_at": None, "problem": None, "has_compared": False, "last_good": None} for repo in WATCHLIST},
        "changes": [],
    }


def _validate_release(release) -> None:
    if release is None:
        return
    if not isinstance(release, dict) or set(release) != {"id", "tag", "published_at"}:
        raise ValueError("invalid saved release evidence")
    if type(release["id"]) is not int or release["id"] <= 0 or not _ref(release["tag"]):
        raise ValueError("invalid saved release identifier")
    parse_time(release["published_at"])


def _validate_evidence(evidence: dict) -> None:
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_KEYS or not _sha(evidence["commit_sha"]):
        raise ValueError("invalid change evidence")
    if evidence["readme_sha"] is not None and not _sha(evidence["readme_sha"]):
        raise ValueError("invalid README evidence")
    _validate_release(evidence["release"])


def _release_identity(release):
    return None if release is None else (release["id"], release["tag"])


def validate_memory(memory: dict) -> None:
    if not isinstance(memory, dict) or set(memory) != MEMORY_KEYS or type(memory["schema_version"]) is not int or memory["schema_version"] != 1 or memory["agent"] != "Sparks":
        raise ValueError("invalid public-source memory schema")
    created, updated = parse_time(memory["created_at"]), parse_time(memory["updated_at"])
    if created > updated:
        raise ValueError("public-source memory timestamps are inconsistent")
    if type(memory["last_workflow_run_id"]) is not int or not 0 <= memory["last_workflow_run_id"] < 10**30:
        raise ValueError("invalid observation replay watermark")
    if memory["catalog_sha256"] is not None and not _sha(memory["catalog_sha256"], 64):
        raise ValueError("invalid catalog fingerprint")
    day = memory["last_observed_date"]
    if day is not None:
        try:
            if not isinstance(day, str) or datetime.strptime(day, "%Y-%m-%d").date().isoformat() != day or day != updated.astimezone(SGT).date().isoformat():
                raise ValueError
        except ValueError:
            raise ValueError("invalid Singapore observation date") from None
    repos = memory["repositories"]
    if not isinstance(repos, dict) or set(repos) != set(WATCHLIST):
        raise ValueError("memory must contain exactly the public watchlist")
    for record in repos.values():
        if not isinstance(record, dict) or set(record) != RECORD_KEYS or type(record["has_compared"]) is not bool:
            raise ValueError("invalid repository observation record")
        if not isinstance(record["status"], str) or record["status"] not in {"unobserved", "current", "unavailable"}:
            raise ValueError("invalid repository observation status")
        if record["status"] == "unobserved":
            if record["attempted_at"] is not None or record["last_good"] is not None or record["problem"] is not None or record["has_compared"]:
                raise ValueError("unobserved repository has inconsistent evidence")
            continue
        attempted = parse_time(record["attempted_at"])
        if not created <= attempted <= updated:
            raise ValueError("repository attempt timestamp is inconsistent")
        if record["status"] == "unavailable" and (not isinstance(record["problem"], str) or record["problem"] not in PROBLEMS):
            raise ValueError("unavailable repository needs a known failure reason")
        if record["status"] == "current" and (record["problem"] is not None or record["last_good"] is None):
            raise ValueError("current repository needs successful source evidence")
        snapshot = record["last_good"]
        if snapshot is None:
            if record["has_compared"]:
                raise ValueError("comparison cannot exist without a successful observation")
            continue
        if not isinstance(snapshot, dict) or set(snapshot) != SNAPSHOT_KEYS or not _sha(snapshot["commit_sha"]) or not _sha(snapshot["tree_sha"]):
            raise ValueError("invalid last-good source snapshot")
        observed = parse_time(snapshot["observed_at"])
        if not created <= observed <= attempted or (record["status"] == "current" and observed != attempted):
            raise ValueError("source observation timestamp is inconsistent")
        files = snapshot["files"]
        if not isinstance(files, dict) or not 1 <= len(files) <= 3 or "README.md" not in files:
            raise ValueError("invalid selected-file evidence")
        for path, evidence in files.items():
            if not _path(path) or not isinstance(evidence, dict) or set(evidence) != {"status", "blob_sha"} or not isinstance(evidence["status"], str) or evidence["status"] not in {"present", "missing", "not_file"}:
                raise ValueError("invalid selected-file record")
            if (evidence["status"] == "present" and not _sha(evidence["blob_sha"])) or (evidence["status"] != "present" and evidence["blob_sha"] is not None):
                raise ValueError("selected-file status disagrees with its blob evidence")
        _validate_release(snapshot["release"])
        if snapshot["release"] is not None and parse_time(snapshot["release"]["published_at"]) > observed:
            raise ValueError("release publication is later than its observation")
    changes = memory["changes"]
    if not isinstance(changes, list) or len(changes) > MAX_CHANGES:
        raise ValueError("public change-receipt limit exceeded")
    if day is None and (memory["last_workflow_run_id"] != 0 or memory["catalog_sha256"] is not None or changes or any(record["status"] != "unobserved" for record in repos.values())):
        raise ValueError("uninitialized observation history is inconsistent")
    if day is not None and (memory["last_workflow_run_id"] == 0 or memory["catalog_sha256"] is None):
        raise ValueError("observation history needs its workflow and catalog evidence")
    seen = set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != CHANGE_KEYS or change["repo"] not in WATCHLIST:
            raise ValueError("invalid public change receipt")
        if not created <= parse_time(change["previous_observed_at"]) <= parse_time(change["observed_at"]) <= updated:
            raise ValueError("change-receipt timestamps are inconsistent")
        for side in ("before", "after"):
            _validate_evidence(change[side])
        before, after = change["before"], change["after"]
        if before["readme_sha"] == after["readme_sha"] and _release_identity(before["release"]) == _release_identity(after["release"]):
            raise ValueError("a change receipt must record a README or release identity change")
        identity = json.dumps(change, sort_keys=True)
        if identity in seen:
            raise ValueError("duplicate public change receipt")
        seen.add(identity)


class APIError(RuntimeError):
    def __init__(self, status=0, rate_limited=False):
        self.status, self.rate_limited = status, rate_limited
        super().__init__("GitHub public-source request was unavailable")


class SourceError(RuntimeError):
    def __init__(self, problem: str):
        self.problem = problem
        super().__init__(PROBLEMS[problem])


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


class GitHubClient:
    def __init__(self, token: str | None = None):
        self._token = token
        self._opener = build_opener(_NoRedirects())

    def get(self, repo: str, resource: str):
        if repo not in WATCHLIST or not isinstance(resource, str) or resource.startswith(("/", "http")) or ".." in resource or "\\" in resource or "#" in resource:
            raise ValueError("refusing a source outside the fixed public API scope")
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "Albert-Tan-Public-Source-Observations"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = Request(f"https://api.github.com/repos/{repo}" + ("/" + resource if resource else ""), headers=headers, method="GET")
        try:
            with self._opener.open(request, timeout=15) as response:
                raw = response.read(MAX_API_BYTES + 1)
            if len(raw) > MAX_API_BYTES:
                raise APIError()
            return _decode_json(raw)
        except HTTPError as exc:
            limited = exc.code == 429 or (exc.code == 403 and (exc.headers.get("Retry-After") or exc.headers.get("X-RateLimit-Remaining") == "0"))
            raise APIError(exc.code, bool(limited)) from None
        except (URLError, OSError, ValueError, UnicodeDecodeError):
            raise APIError() from None


def _fetch(client, repo, resource, problem):
    try:
        return client.get(repo, resource)
    except APIError as exc:
        raise SourceError("rate_limited" if exc.rate_limited else problem) from None


def observe_repository(project: dict, client, now: datetime) -> dict:
    repo = project["repo"]
    metadata = _fetch(client, repo, "", "repository_unavailable")
    if not isinstance(metadata, dict) or metadata.get("full_name") != repo or metadata.get("private") is not False or metadata.get("visibility") != "public":
        raise SourceError("not_public")
    branch = metadata.get("default_branch")
    if not _ref(branch):
        raise SourceError("invalid_response")
    head = _fetch(client, repo, "commits/" + quote(branch, safe=""), "commit_unavailable")
    if not isinstance(head, dict) or not _sha(head.get("sha")):
        raise SourceError("invalid_response")
    commit = head.get("commit")
    tree_ref = commit.get("tree") if isinstance(commit, dict) else None
    if not isinstance(tree_ref, dict) or not _sha(tree_ref.get("sha")):
        raise SourceError("invalid_response")
    tree = _fetch(client, repo, f"git/trees/{tree_ref['sha']}?recursive=1", "tree_unavailable")
    if not isinstance(tree, dict) or tree.get("sha") != tree_ref["sha"] or not isinstance(tree.get("tree"), list):
        raise SourceError("invalid_response")
    if tree.get("truncated") is not False or len(tree["tree"]) > MAX_TREE_ENTRIES:
        raise SourceError("incomplete_tree")
    paths = {"README.md", project["start_path"]}
    if "contribute_path" in project:
        paths.add(project["contribute_path"])
    files = {path: {"status": "missing", "blob_sha": None} for path in sorted(paths)}
    found = set()
    for item in tree["tree"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or item.get("path") not in paths:
            continue
        path = item["path"]
        if path in found:
            raise SourceError("invalid_response")
        found.add(path)
        kind, mode = item.get("type"), item.get("mode")
        if not isinstance(kind, str) or not isinstance(mode, str):
            raise SourceError("invalid_response")
        if (kind, mode) in (("tree", "040000"), ("commit", "160000"), ("blob", "120000")):
            files[path]["status"] = "not_file"
        elif kind != "blob" or mode not in ("100644", "100755"):
            raise SourceError("invalid_response")
        elif not _sha(item.get("sha")):
            raise SourceError("invalid_response")
        else:
            files[path] = {"status": "present", "blob_sha": item["sha"]}
    try:
        raw_release = client.get(repo, "releases/latest")
    except APIError as exc:
        if exc.status == 404:
            raw_release = None
        else:
            raise SourceError("rate_limited" if exc.rate_limited else "release_unavailable") from None
    release = None
    if raw_release is not None:
        if not isinstance(raw_release, dict) or raw_release.get("draft") is not False or raw_release.get("prerelease") is not False:
            raise SourceError("invalid_response")
        release = {"id": raw_release.get("id"), "tag": raw_release.get("tag_name"), "published_at": raw_release.get("published_at")}
        try:
            _validate_release(release)
            if parse_time(release["published_at"]) > now:
                raise ValueError
        except ValueError:
            raise SourceError("invalid_response") from None
    return {"observed_at": timestamp(now), "commit_sha": head["sha"], "tree_sha": tree_ref["sha"], "files": files, "release": release}


def _evidence(snapshot: dict) -> dict:
    return {"commit_sha": snapshot["commit_sha"], "readme_sha": snapshot["files"]["README.md"]["blob_sha"], "release": deepcopy(snapshot["release"])}


@dataclass(frozen=True)
class Observation:
    memory: dict
    is_noop: bool
    message: str


def observe(memory: dict, catalog: dict, client, now: datetime, event_id: str, force=False) -> Observation:
    validate_memory(memory)
    digest = catalog_digest(catalog)
    now = parse_time(timestamp(now))
    if now < parse_time(memory["updated_at"]):
        raise ValueError("observation clock moved backwards")
    if not isinstance(event_id, str) or not re.fullmatch(r"actions:[1-9][0-9]{0,28}", event_id):
        raise ValueError("event ID must be actions:<positive workflow run ID>")
    run_id = int(event_id.split(":")[1])
    if run_id <= memory["last_workflow_run_id"]:
        return Observation(deepcopy(memory), True, "Repeated or stale observation run; no change.")
    day = now.astimezone(SGT).date().isoformat()
    full = bool(force or day != memory["last_observed_date"] or digest != memory["catalog_sha256"])
    targets = list(WATCHLIST) if full else [repo for repo in WATCHLIST if memory["repositories"][repo]["status"] != "current"]
    if not targets:
        return Observation(deepcopy(memory), True, "Today's public sources are already observed; no change.")
    updated = deepcopy(memory)
    updated.update(updated_at=timestamp(now), last_observed_date=day, last_workflow_run_id=run_id, catalog_sha256=digest)
    projects = {project["repo"]: project for project in catalog["projects"]}
    paused = False
    good = 0
    for repo in targets:
        record = updated["repositories"][repo]
        previous = record["last_good"]
        record["attempted_at"] = timestamp(now)
        try:
            if paused:
                raise SourceError("rate_limited")
            snapshot = observe_repository(projects[repo], client, now)
        except SourceError as exc:
            record.update(status="unavailable", problem=exc.problem)
            paused = paused or exc.problem == "rate_limited"
            continue
        good += 1
        if previous is not None:
            before, after = _evidence(previous), _evidence(snapshot)
            if before["readme_sha"] != after["readme_sha"] or _release_identity(before["release"]) != _release_identity(after["release"]):
                updated["changes"].append({"repo": repo, "observed_at": timestamp(now), "previous_observed_at": previous["observed_at"], "before": before, "after": after})
            record["has_compared"] = True
        record.update(status="current", problem=None, last_good=snapshot)
    updated["changes"] = updated["changes"][-MAX_CHANGES:]
    validate_memory(updated)
    return Observation(updated, False, f"Observed {good} of {len(targets)} requested public sources; unavailable sources retain their previous evidence.")


def _text(value: str) -> str:
    result = escape(value, quote=False).replace("\\", "\\\\")
    for character in "`*_[]|":
        result = result.replace(character, "\\" + character)
    return result


def _when(value: str) -> str:
    local = parse_time(value).astimezone(SGT)
    month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[local.month - 1]
    return f"{local.day:02d} {month} {local.year}, {local:%H:%M} SGT"


def _file_url(repo, commit, path) -> str:
    return f"https://github.com/{repo}/blob/{commit}/{quote(path, safe='/')}"


def _release_text(repo, release) -> str:
    if release is None:
        return "No published stable release was returned"
    return f"[{_text(release['tag'])}](https://github.com/{repo}/releases/tag/{quote(release['tag'], safe='')}) ([record {release['id']}](https://api.github.com/repos/{repo}/releases/{release['id']}))"


def _entry(repo, path, snapshot) -> str:
    if snapshot is None or path not in snapshot["files"]:
        return "Awaiting observation"
    evidence = snapshot["files"][path]
    if evidence["status"] != "present":
        return f"{_text(path)}: {'missing' if evidence['status'] == 'missing' else 'not a regular file'}"
    return f"[{_text(path)}]({_file_url(repo, snapshot['commit_sha'], path)})"


def render_workbench(memory: dict, catalog: dict) -> str:
    validate_memory(memory)
    digest = catalog_digest(catalog)
    config_current = digest == memory["catalog_sha256"]
    projects = {project["repo"]: project for project in catalog["projects"]}
    lines = ["# Public project source observations", "", "This workbench checks selected entrypoints in five public projects and compares source observations over time. Each result comes from a bounded GitHub source read and retains its recorded evidence.", "", "Project purposes come from the maintained public portfolio catalog. File checks establish presence at a recorded commit; they do not establish correctness, legal reliability, adoption or successful execution.", "", "[Maintenance and scope](PUBLIC_SOURCE_OBSERVATIONS.md).", ""]
    if memory["last_observed_date"] is None:
        lines.append("**Observation status:** awaiting the first public-source observation.")
    else:
        lines.append(f"**Latest observation:** {_when(memory['updated_at'])}. Each project below retains its own source-check time.")
    if not config_current and memory["last_observed_date"] is not None:
        lines.append("**Catalog changed:** the selected paths need a fresh observation before they can be treated as current.")
    current = [repo for repo in WATCHLIST if memory["repositories"][repo]["status"] == "current" and config_current]
    verified_starts = sum(memory["repositories"][repo]["last_good"]["files"].get(projects[repo]["start_path"], {}).get("status") == "present" for repo in current)
    compared = sum(memory["repositories"][repo]["has_compared"] for repo in current)
    lines.extend(["", "## Recorded checks", "", f"- **Project navigation:** {verified_starts} of 5 selected starting paths are present in current public snapshots.", f"- **Entrypoint audit:** {len(current)} of 5 projects have current complete source observations; absent or non-file paths are reported below.", f"- **Change briefing:** {compared} of 5 current projects have been compared with an earlier successful observation. First observations establish baselines.", "", "## Find a project", "", "| Project and purpose | Start here | Contribution path | Source status |", "| --- | --- | --- | --- |"])
    for repo in WATCHLIST:
        project, record = projects[repo], memory["repositories"][repo]
        snapshot = record["last_good"]
        if record["status"] == "unobserved":
            status = "Not observed yet"
        elif record["status"] == "unavailable":
            status = "Unavailable: " + PROBLEMS[record["problem"]]
        else:
            status = "Current observation" if config_current else "Catalog changed; recheck needed"
        if snapshot is not None:
            qualifier = "Last good evidence (stale)" if record["status"] != "current" or not config_current else "Checked"
            status += f" {qualifier} {_when(snapshot['observed_at'])} at [{snapshot['commit_sha'][:10]}](https://github.com/{repo}/tree/{snapshot['commit_sha']})."
        contribute = _entry(repo, project["contribute_path"], snapshot) if "contribute_path" in project else "No separate path configured"
        lines.append(f"| **{_text(project['title'])}**. {_text(project['purpose'])} | {_entry(repo, project['start_path'], snapshot)} | {contribute} | {status} |")
    lines.extend(["", "## Published-release observations", ""])
    for repo in WATCHLIST:
        record, project = memory["repositories"][repo], projects[repo]
        snapshot = record["last_good"]
        label = "Not observed" if snapshot is None else _release_text(repo, snapshot["release"])
        if snapshot is not None:
            label += f"; observed {_when(snapshot['observed_at'])}"
        if record["status"] == "unavailable":
            label += "; current source unavailable, retained evidence is stale"
        lines.append(f"- **{_text(project['title'])}:** {label}.")
    lines.extend(["", "## Recorded source changes", "", "Only differences between successful observations enter this list. An unavailable source is never reported as unchanged. At most the latest 20 change receipts are retained.", ""])
    if not memory["changes"]:
        lines.append("No README or release-identity change has been recorded. This alone does not establish that every source is current or has a comparison baseline.")
    for change in reversed(memory["changes"]):
        repo, before, after = change["repo"], change["before"], change["after"]
        parts = []
        if before["readme_sha"] != after["readme_sha"]:
            def readme_link(evidence, label):
                return f"[{label}]({_file_url(repo, evidence['commit_sha'], 'README.md')})" if evidence["readme_sha"] else f"README absent or non-file in [{label}](https://github.com/{repo}/tree/{evidence['commit_sha']})"
            parts.append("README changed: " + readme_link(before, "previous snapshot") + " to " + readme_link(after, "new snapshot"))
        if _release_identity(before["release"]) != _release_identity(after["release"]):
            parts.append("Release observation changed: " + _release_text(repo, before["release"]) + " to " + _release_text(repo, after["release"]))
        lines.append(f"- **{_text(projects[repo]['title'])}, {_when(change['observed_at'])}:** " + "; ".join(parts) + ".")
    next_task = "Compare the next daily public-source snapshots with the saved evidence."
    for repo in WATCHLIST:
        project, record = projects[repo], memory["repositories"][repo]
        if record["status"] != "current" or not config_current:
            next_task = f"Obtain a current public-source observation for {_text(project['title'])}; existing gaps must not be treated as verified facts."
            break
        missing = [path for path in (project["start_path"], project.get("contribute_path")) if path and record["last_good"]["files"].get(path, {}).get("status") != "present"]
        if missing:
            next_task = f"Review the configured entrypoint {_text(missing[0])} for {_text(project['title'])}; the latest source tree does not establish it as a regular file."
            break
    lines.extend(["", "## Next useful task", "", next_task, "", "The observer reads only the fixed public watchlist. It does not execute source code or edit the watched projects. Observations and change receipts persist in the [public-source record](../data/sparks-knowledge.json).", ""])
    return "\n".join(lines)


def _read_json(path: Path):
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("public-source JSON exceeds its size limit")
    try:
        return _decode_json(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("invalid public-source JSON") from None


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None, root: Path = ROOT, client=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("initialize", "observe"))
    parser.add_argument("--event-id")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--now")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check and (args.command or args.event_id or args.force or args.now):
        parser.error("--check is an offline, read-only command")
    if not args.check and not args.command:
        parser.error("choose initialize, observe or --check")
    if args.command == "observe" and not args.event_id:
        parser.error("observe requires --event-id")
    if args.command == "initialize" and (args.event_id or args.force):
        parser.error("initialize does not accept a workflow event or force option")
    try:
        catalog = _read_json(root / CATALOG_PATH)
        validate_catalog(catalog)
        memory_path = root / MEMORY_PATH
        if args.command == "initialize":
            if memory_path.exists():
                raise ValueError("public-source memory already exists; initialization will not reset it")
            memory = initial_memory(parse_time(args.now) if args.now else datetime.now(UTC))
            message = "Initialized public-source memory without API calls."
        else:
            memory = _read_json(memory_path)
            validate_memory(memory)
            message = "Public-source memory and workbench are consistent."
        if args.command == "observe":
            now = parse_time(args.now) if args.now else datetime.now(UTC)
            api = client if client is not None else GitHubClient(os.environ.get("GITHUB_TOKEN"))
            result = observe(memory, catalog, api, now, args.event_id, args.force)
            if result.is_noop:
                print(result.message)
                return 0
            memory, message = result.memory, result.message
        workbench = render_workbench(memory, catalog)
        if args.check:
            if (root / WORKBENCH_PATH).read_text(encoding="utf-8") != workbench:
                raise ValueError("the public workbench differs from its saved evidence and catalog")
        else:
            _write(root / MEMORY_PATH, json.dumps(memory, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
            _write(root / WORKBENCH_PATH, workbench)
        print(message)
        return 0
    except (ValueError, OSError) as exc:
        print(f"Public portfolio observation stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
