from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import timedelta
from email.message import Message
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import public_care as care
import update_persona as pet


TEMPLATE = '<svg xmlns="http://www.w3.org/2000/svg"><title>{{thought}}</title></svg>\n'


class FakeClient:
    def __init__(self, issues=None, page=None):
        self.issues = {item["number"]: dict(item) for item in (issues or [])}
        self.page = list(page) if page is not None else list(self.issues.values())
        self.get_calls = []
        self.pages = []
        self.labels = []
        self.closed = []
        self.get_errors = {}
        self.close_error = None

    def list_open_issues(self, page):
        self.pages.append(page)
        return self.page

    def get_issue(self, number):
        self.get_calls.append(number)
        if number in self.get_errors:
            raise self.get_errors[number]
        if number not in self.issues:
            raise care.GitHubAPIError(404)
        return self.issues[number]

    def ensure_label(self, label):
        if label not in care.LABELS.values():
            raise AssertionError("unexpected label")

    def add_label(self, number, name):
        self.labels.append((number, name))

    def close_issue(self, number, accepted):
        if self.close_error:
            raise self.close_error
        self.closed.append((number, accepted))
        self.issues[number]["state"] = "closed"


class PublicCareTests(unittest.TestCase):
    def setUp(self):
        self.now = pet.parse_time("2026-10-28T08:00:00Z")
        self.ledger = care.initial_ledger(self.now - timedelta(days=7))
        self.state = pet.initial_state(self.now)

    def issue(self, number, action="feed", user=123, created=None, **changes):
        result = {
            "number": number, "title": f"[Sparks] {action}", "state": "open",
            "repository_url": care.REPO_API,
            "user": {"type": "User", "id": user, "login": "never-copy-this-login"},
            "created_at": pet.timestamp(created or self.now - timedelta(minutes=1)),
            "body": "NEVER COPY THIS BODY: $(print-token) <script>bad()</script>",
        }
        result.update(changes)
        return result

    def receipt(self, action="feed", reason="accepted", user=123, processed=None, pending=False):
        when = processed or self.now - timedelta(hours=2)
        return {
            "action": action, "reason": reason, "message": care.feedback(action, reason),
            "accepted": reason == "accepted", "processed_at": pet.timestamp(when),
            "created_at": pet.timestamp(when - timedelta(minutes=1)),
            "actor_key": care.actor_key(user), "pending_ack": pending,
        }

    def run_prepare(self, client, state=None, ledger=None, committed=None, now=None, event=None):
        working = self.ledger if ledger is None else ledger
        return care.prepare(self.state if state is None else state, working, working if committed is None else committed, client, now or self.now, event)

    def test_untrusted_titles_bodies_bots_prs_and_wrong_repositories_are_ignored(self):
        bad = [
            self.issue(1, title="[Sparks] feed; $(print-token)"),
            self.issue(2, title="[Sparks] feed "),
            self.issue(3, user={"type": "Bot", "id": 3}),
            self.issue(4, pull_request={"url": "untrusted"}),
            self.issue(5, repository_url="https://api.github.com/repos/other/repo"),
            self.issue(6, created=self.now + timedelta(seconds=1)),
            self.issue(7, created=self.now - timedelta(days=8)),
            self.issue(8, user={"type": "User", "id": True}),
        ]
        valid = self.issue(99)
        # The handler must not require any particular issue-body type or value.
        valid["body"] = object()
        client = FakeClient(bad + [valid])
        result = self.run_prepare(client)
        self.assertEqual(set(result.ledger["receipts"]), {"99"})
        self.assertEqual(client.get_calls, [99])
        self.assertEqual(client.labels, [])
        self.assertEqual(client.closed, [])
        diary = care.render_diary(result.ledger)
        self.assertNotIn("NEVER COPY", diary)
        self.assertNotIn("never-copy-this-login", diary)
        self.assertNotIn("actor_key", diary)

    def test_current_event_is_first_and_wrong_repository_or_action_is_ignored(self):
        event_issue, listed = self.issue(100), self.issue(1, "play", user=456)
        event = {"action": "opened", "repository": {"full_name": care.REPO}, "issue": {"number": 100}}
        client = FakeClient([event_issue, listed], page=[listed])
        result = self.run_prepare(client, event=event)
        self.assertEqual(client.get_calls, [100, 1])
        self.assertTrue(result.ledger["receipts"]["100"]["accepted"])
        for change in ({"repository": {"full_name": "other/repo"}}, {"action": "edited"}, {"issue": {"number": 100, "pull_request": {}}}):
            invalid = dict(event)
            invalid.update(change)
            isolated = FakeClient([event_issue], page=[])
            self.assertEqual(self.run_prepare(isolated, event=invalid).processed, 0)
            self.assertEqual(isolated.get_calls, [])

    def test_latest_closed_or_repurposed_request_is_rechecked_before_decision(self):
        listed = self.issue(1)
        for changes in ({"state": "closed"}, {"title": "A real research question"}, {"repository_url": "https://api.github.com/repos/other/repo"}):
            latest = dict(listed)
            latest.update(changes)
            client = FakeClient([latest], page=[listed])
            result = self.run_prepare(client)
            self.assertEqual(result.processed, 0)
            self.assertEqual(result.state, self.state)
            self.assertEqual(client.get_calls, [1])

    def test_satisfied_care_declines_without_xp_or_acknowledging_uncommitted_result(self):
        self.state["stats"]["curiosity"] = 100
        self.state["last_workflow_run_id"] = 999999
        client = FakeClient([self.issue(1)])
        result = self.run_prepare(client)
        receipt = result.ledger["receipts"]["1"]
        self.assertFalse(receipt["accepted"])
        self.assertEqual(receipt["reason"], "satisfied")
        self.assertEqual(receipt["message"], "Thanks, I have enough ideas for now.")
        self.assertTrue(receipt["pending_ack"])
        self.assertEqual(result.state["xp"], 0)
        self.assertEqual(result.state["last_workflow_run_id"], 999999)
        self.assertEqual(client.closed, [])

    def test_duplicate_after_newer_owner_workflow_does_not_reapply_care(self):
        issue = self.issue(1)
        first = self.run_prepare(FakeClient([issue]))
        owner_now = self.now + timedelta(minutes=20)
        owner = pet.advance(first.state, owner_now, "play", "actions:999999").state
        client = FakeClient([issue])
        rerun = self.run_prepare(client, state=owner, ledger=first.ledger, now=owner_now)
        self.assertEqual(rerun.state, owner)
        self.assertEqual(rerun.processed, 0)
        self.assertEqual(client.closed, [(1, True)])
        self.assertFalse(rerun.ledger["receipts"]["1"]["pending_ack"])
        self.assertEqual(care._immutable_part(rerun.ledger["receipts"]["1"]), care._immutable_part(first.ledger["receipts"]["1"]))

    def test_actor_limit_counts_only_accepted_care_and_needs_take_priority(self):
        self.ledger["receipts"]["1"] = self.receipt(processed=self.now - timedelta(minutes=45))
        for curiosity, expected in ((75, "actor_cooldown"), (100, "satisfied")):
            state = deepcopy(self.state)
            state["stats"]["curiosity"] = curiosity
            result = self.run_prepare(FakeClient([self.issue(2)]), state=state)
            self.assertEqual(result.ledger["receipts"]["2"]["reason"], expected)
            self.assertEqual(result.state["xp"], 0)
        self.ledger["receipts"]["1"] = self.receipt(processed=self.now - timedelta(hours=1))
        self.assertTrue(self.run_prepare(FakeClient([self.issue(2)])).ledger["receipts"]["2"]["accepted"])
        self.ledger["receipts"]["1"] = self.receipt(reason="satisfied", processed=self.now - timedelta(minutes=1))
        self.assertTrue(self.run_prepare(FakeClient([self.issue(2)])).ledger["receipts"]["2"]["accepted"])

    def test_global_cooldown_has_finite_feedback_and_no_extra_xp(self):
        first = self.run_prepare(FakeClient([self.issue(1)]))
        later = self.now + timedelta(minutes=5)
        ledger = deepcopy(first.ledger)
        ledger["receipts"]["1"]["pending_ack"] = False
        second = self.run_prepare(FakeClient([self.issue(2, "play", user=456)]), state=first.state, ledger=ledger, now=later)
        self.assertEqual(second.ledger["receipts"]["2"]["reason"], "cooldown")
        self.assertEqual(second.ledger["receipts"]["2"]["message"], care.FIXED_MESSAGES["cooldown"])
        self.assertEqual(second.state["xp"], 1)

    def test_expiry_and_pruning_cannot_make_old_requests_award_experience(self):
        issue = self.issue(1, created=self.now - timedelta(hours=25))
        expired = self.run_prepare(FakeClient([issue]))
        self.assertEqual(expired.ledger["receipts"]["1"]["reason"], "expired")
        self.assertEqual(expired.state["xp"], 0)
        acknowledged = deepcopy(expired.ledger)
        acknowledged["receipts"]["1"]["pending_ack"] = False
        later = self.now + timedelta(hours=73)
        replay = self.run_prepare(FakeClient([issue]), state=expired.state, ledger=acknowledged, now=later)
        self.assertEqual(replay.ledger["receipts"]["1"]["reason"], "expired")
        self.assertEqual(replay.state["xp"], 0)
        self.assertEqual(replay.ledger["receipts"]["1"]["processed_at"], pet.timestamp(later))
        boundary = self.run_prepare(FakeClient([self.issue(2, created=self.now - timedelta(hours=24))]))
        self.assertTrue(boundary.ledger["receipts"]["2"]["accepted"])

    def test_capacity_fails_closed_without_evicting_or_discovering_new_care(self):
        receipt = self.receipt()
        self.ledger["receipts"] = {str(i): deepcopy(receipt) for i in range(1, care.MAX_RECEIPTS + 1)}
        client = FakeClient([self.issue(9999)])
        result = self.run_prepare(client)
        self.assertTrue(result.capacity_reached)
        self.assertEqual(result.processed, 0)
        self.assertEqual(result.state, self.state)
        self.assertEqual(result.ledger, self.ledger)
        self.assertEqual(client.pages, [])
        too_many = deepcopy(self.ledger)
        too_many["receipts"]["9999"] = deepcopy(receipt)
        with self.assertRaisesRegex(ValueError, "capacity"):
            care.validate_ledger(too_many)

    def test_pending_ack_failure_is_retried_and_never_pruned(self):
        self.ledger["receipts"]["1"] = self.receipt(processed=self.now - timedelta(hours=100), pending=True)
        original = deepcopy(self.ledger)
        failing = FakeClient([self.issue(1)])
        failing.close_error = care.GitHubAPIError(500)
        with self.assertRaises(care.GitHubAPIError):
            self.run_prepare(failing)
        self.assertEqual(self.ledger, original)
        self.assertTrue(self.ledger["receipts"]["1"]["pending_ack"])
        retry = FakeClient([self.issue(1)], page=[])
        completed = self.run_prepare(retry)
        self.assertEqual(retry.closed, [(1, True)])
        self.assertNotIn("1", completed.ledger["receipts"])
        self.assertEqual(completed.state["xp"], 0)

    def test_missing_or_transferred_decided_issue_does_not_poison_new_care(self):
        self.ledger["receipts"]["1"] = self.receipt(pending=True)
        for terminal_status in (404, 410, 301, 307):
            client = FakeClient([self.issue(2, user=456)])
            client.get_errors[1] = care.GitHubAPIError(terminal_status)
            result = self.run_prepare(client)
            self.assertFalse(result.ledger["receipts"]["1"]["pending_ack"])
            self.assertEqual(care._immutable_part(result.ledger["receipts"]["1"]), care._immutable_part(self.ledger["receipts"]["1"]))
            self.assertTrue(result.ledger["receipts"]["2"]["accepted"])
            self.assertEqual(client.closed, [])
        for failure in (care.GitHubAPIError(401), care.GitHubAPIError(403), care.RateLimitError("rate limited")):
            client = FakeClient([self.issue(2)])
            client.get_errors[1] = failure
            with self.assertRaises(care.PublicCareError):
                self.run_prepare(client)
            self.assertEqual(client.pages, [])

    def test_repurposed_decided_issue_is_not_labelled_or_closed(self):
        self.ledger["receipts"]["1"] = self.receipt(pending=True)
        client = FakeClient([self.issue(1, title="Now a substantive research discussion")])
        result = self.run_prepare(client)
        self.assertFalse(result.ledger["receipts"]["1"]["pending_ack"])
        self.assertEqual(client.labels, [])
        self.assertEqual(client.closed, [])

    def test_only_committed_pending_receipts_may_be_acknowledged(self):
        working = deepcopy(self.ledger)
        working["receipts"]["1"] = self.receipt(pending=True)
        client = FakeClient([self.issue(1)])
        result = self.run_prepare(client, ledger=working, committed=self.ledger)
        self.assertTrue(result.ledger["receipts"]["1"]["pending_ack"])
        self.assertEqual(client.get_calls, [])
        self.assertEqual(client.closed, [])
        committed = deepcopy(working)
        snapshot = deepcopy(committed)
        self.assertEqual(care.acknowledge_ledger(committed, client), 1)
        self.assertEqual(committed, snapshot)
        self.assertEqual(client.closed, [(1, True)])
        self.assertEqual(care.acknowledge_ledger(committed, client), 1)
        self.assertEqual(client.closed, [(1, True)])  # Already closed is terminal.

    def test_committed_decisions_are_immutable_and_pending_cannot_be_removed(self):
        self.ledger["receipts"]["1"] = self.receipt(pending=True)
        changed = deepcopy(self.ledger)
        changed["receipts"]["1"]["actor_key"] = care.actor_key(999)
        with self.assertRaisesRegex(ValueError, "modified"):
            self.run_prepare(FakeClient(), ledger=changed, committed=self.ledger)
        removed = care.initial_ledger(pet.parse_time(self.ledger["enabled_at"]))
        with self.assertRaisesRegex(ValueError, "removed"):
            self.run_prepare(FakeClient(), ledger=removed, committed=self.ledger)

    def test_discovery_and_acknowledgement_work_are_bounded(self):
        issues = [self.issue(i, user=i) for i in range(1, 101)]
        client = FakeClient(issues)
        result = self.run_prepare(client)
        self.assertEqual(client.pages, [1])
        self.assertEqual(len(client.get_calls), 20)
        self.assertEqual(result.processed, 20)
        self.assertEqual(result.ledger["scan_page"], 2)
        backlog = deepcopy(self.ledger)
        backlog["receipts"] = {str(i): self.receipt(user=i, pending=True) for i in range(1, 22)}
        pending_client = FakeClient(issues)
        pending = self.run_prepare(pending_client, ledger=backlog)
        self.assertTrue(pending.backlog_remaining)
        self.assertEqual(len(pending_client.closed), 20)
        self.assertEqual(pending_client.pages, [])

    def test_ledger_and_diary_reject_arbitrary_feedback_and_show_only_latest_twenty(self):
        self.ledger["receipts"] = {str(i): self.receipt(user=i) for i in range(1, 26)}
        diary = care.render_diary(self.ledger)
        self.assertEqual(diary.count("](https://github.com/Albertito-AI/Albertito-AI/issues/"), 20)
        self.assertIn("SGT", diary)
        self.assertNotIn("[#1]", diary)
        altered = deepcopy(self.ledger)
        altered["receipts"]["1"]["message"] = "Arbitrary untrusted content"
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            care.validate_ledger(altered)
        malformed = deepcopy(self.ledger)
        malformed["scan_page"] = True
        with self.assertRaises(ValueError):
            care.validate_ledger(malformed)
        with self.assertRaisesRegex(ValueError, "size limit"):
            care._decode_json(b" " * (care.MAX_JSON_BYTES + 1))

    def test_check_is_read_only_and_needs_neither_token_nor_git_or_api(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "docs").mkdir()
            ledger_path, diary_path = root / care.LEDGER_PATH, root / care.DIARY_PATH
            ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
            diary_path.write_text(care.render_diary(self.ledger), encoding="utf-8")
            before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (ledger_path, diary_path)}
            with patch.object(care, "GitHubClient", side_effect=AssertionError("no API")), patch.object(care, "load_committed_ledger", side_effect=AssertionError("no Git")), redirect_stdout(io.StringIO()):
                self.assertEqual(care.main(["--check"], root=root), 0)
            self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (ledger_path, diary_path)})
            diary_path.write_text("drift", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(care.main(["--check"], root=root), 1)
            self.assertEqual(diary_path.read_text(), "drift")

    def test_acknowledge_cli_ignores_uncommitted_working_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            working = deepcopy(self.ledger)
            working["receipts"]["1"] = self.receipt(pending=True)
            path = root / care.LEDGER_PATH
            path.write_text(json.dumps(working), encoding="utf-8")
            before = path.read_bytes(), path.stat().st_mtime_ns
            client = FakeClient([self.issue(1)])
            with patch.object(care, "load_committed_ledger", return_value=self.ledger) as loader, redirect_stdout(io.StringIO()):
                self.assertEqual(care.main(["acknowledge"], root=root, client=client), 0)
            loader.assert_called_once_with(root)
            self.assertEqual(client.get_calls, [])
            self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))

    def test_rate_limit_after_tentative_decision_leaves_all_working_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {care.LEDGER_PATH: json.dumps(self.ledger), care.DIARY_PATH: care.render_diary(self.ledger), "data/persona.json": json.dumps(self.state), "assets/persona-template.svg": TEMPLATE}
            files.update(pet.render_outputs(self.state, TEMPLATE))
            for relative, content in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            before = {relative: ((root / relative).read_bytes(), (root / relative).stat().st_mtime_ns) for relative in files}
            client = FakeClient([self.issue(1), self.issue(2, user=456)])
            client.get_errors[2] = care.RateLimitError("GitHub rate limit reached; stopping immediately. Retry after 60 seconds.")
            error = io.StringIO()
            with patch.object(care, "load_committed_ledger", return_value=self.ledger), patch.object(care, "_read_event", return_value=None), redirect_stderr(error):
                self.assertEqual(care.main(["prepare", "--now", pet.timestamp(self.now)], root=root, client=client), 1)
            self.assertIn("Retry after 60", error.getvalue())
            self.assertEqual(before, {relative: ((root / relative).read_bytes(), (root / relative).stat().st_mtime_ns) for relative in files})
            self.assertEqual(client.closed, [])


class GitHubClientTests(unittest.TestCase):
    def test_redirects_and_error_bodies_cannot_leak_credentials(self):
        client = care.GitHubClient("SECRET_TOKEN")
        headers = Message()
        headers["Retry-After"] = "60"
        for status in (302, 401, 429):
            error = HTTPError(care.REPO_API + "/issues", status, "SECRET_BODY", headers, io.BytesIO(b"SECRET_BODY"))
            with patch.object(client._opener, "open", side_effect=error), self.assertRaises(care.PublicCareError) as caught:
                client.get_issue(1)
            self.assertNotIn("SECRET", str(caught.exception))
            if status == 429:
                self.assertIn("Retry after 60", str(caught.exception))
        self.assertIsNone(care._NoRedirects().redirect_request(None, None, 302, "", headers, "https://elsewhere.invalid/"))
        with patch.object(client._opener, "open", side_effect=AssertionError("unexpected network")), self.assertRaises(care.PublicCareError):
            client._request("GET", "https://elsewhere.invalid/")

    def test_oversized_page_has_a_bounded_fallback_for_the_same_hundred_issues(self):
        client = care.GitHubClient("TEST_TOKEN")
        queries = []

        def response(method, path, payload=None):
            query = parse_qs(urlsplit(path).query)
            queries.append(query)
            if query["per_page"] == ["100"]:
                raise care.ResponseTooLarge("bounded response")
            start = (int(query["page"][0]) - 1) * 10
            return [{"number": number} for number in range(start + 1, start + 11)]

        with patch.object(client, "_request", side_effect=response):
            page = client.list_open_issues(7)
        self.assertEqual([item["number"] for item in page], list(range(601, 701)))
        self.assertEqual(len(queries), 11)
        self.assertEqual([int(q["page"][0]) for q in queries[1:]], list(range(61, 71)))
        self.assertTrue(all(q["sort"] == ["created"] and q["direction"] == ["asc"] for q in queries))


if __name__ == "__main__":
    unittest.main()
