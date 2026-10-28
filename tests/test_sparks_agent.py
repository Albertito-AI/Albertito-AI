from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import timedelta
from email.message import Message
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sparks_agent as agent


def sha(label):
    return hashlib.sha1(label.encode("utf-8")).hexdigest()


def catalog():
    return {"schema_version": 1, "projects": [
        {"repo": repo, "title": repo.split("/")[1], "purpose": "A public project described by its owner.", "start_path": "docs/start.md", "contribute_path": "CONTRIBUTING.md"}
        for repo in agent.WATCHLIST
    ]}


class FakeClient:
    def __init__(self):
        self.calls = []
        self.commit_versions = dict.fromkeys(agent.WATCHLIST, 1)
        self.readme_versions = dict.fromkeys(agent.WATCHLIST, 1)
        self.releases = dict.fromkeys(agent.WATCHLIST, None)
        self.overrides = {}
        self.errors = {}
        self.missing = set()
        self.nonfiles = set()

    def get(self, repo, resource):
        self.calls.append((repo, resource))
        key = (repo, resource)
        if key in self.errors:
            raise self.errors[key]
        if key in self.overrides:
            return self.overrides[key]
        version = self.commit_versions[repo]
        tree_sha = sha(f"{repo}:tree:{version}")
        if resource == "":
            return {"full_name": repo, "private": False, "visibility": "public", "default_branch": "main", "description": "NEVER_COPY_PRIVATE_OR_ARBITRARY_DESCRIPTION"}
        if resource == "commits/main":
            return {"sha": sha(f"{repo}:commit:{version}"), "commit": {"tree": {"sha": tree_sha}, "message": "NEVER_COPY_COMMIT_MESSAGE"}}
        if resource == f"git/trees/{tree_sha}?recursive=1":
            entries = []
            for path in ("README.md", "docs/start.md", "CONTRIBUTING.md"):
                if (repo, path) in self.missing:
                    continue
                entries.append({"path": path, "type": "tree" if (repo, path) in self.nonfiles else "blob", "mode": "040000" if (repo, path) in self.nonfiles else "100644", "sha": sha(f"{repo}:{path}:{self.readme_versions[repo] if path == 'README.md' else 1}")})
            return {"sha": tree_sha, "truncated": False, "tree": entries}
        if resource == "releases/latest":
            if self.releases[repo] is None:
                raise agent.APIError(404)
            return self.releases[repo]
        raise AssertionError(f"unexpected fixture resource: {resource}")


class SparksObservationTests(unittest.TestCase):
    def setUp(self):
        self.now = agent.parse_time("2026-10-28T06:00:00Z")
        self.catalog = catalog()
        self.memory = agent.initial_memory(self.now)
        self.client = FakeClient()

    def observe(self, memory=None, client=None, now=None, event=1, force=False, config=None):
        return agent.observe(self.memory if memory is None else memory, self.catalog if config is None else config, self.client if client is None else client, now or self.now, f"actions:{event}", force)

    def test_first_observation_establishes_baselines_and_commit_pinned_navigation(self):
        result = self.observe()
        self.assertEqual(result.memory["changes"], [])
        self.assertEqual(len(self.client.calls), 20)
        for repo, record in result.memory["repositories"].items():
            self.assertEqual(record["status"], "current")
            self.assertFalse(record["has_compared"])
            self.assertEqual(record["last_good"]["commit_sha"], sha(f"{repo}:commit:1"))
        report = agent.render_workbench(result.memory, self.catalog)
        self.assertIn("5 of 5 selected starting paths", report)
        self.assertIn("0 of 5 current projects have been compared", report)
        self.assertNotIn("/blob/main/", report)
        self.assertNotIn("NEVER_COPY", report)
        self.assertEqual(self.memory, agent.initial_memory(self.now))

    def test_commit_only_changes_do_not_invent_readme_or_release_changes(self):
        baseline = self.observe().memory
        client = FakeClient()
        client.commit_versions = dict.fromkeys(agent.WATCHLIST, 2)
        second = self.observe(memory=baseline, client=client, now=self.now + timedelta(days=1), event=2).memory
        self.assertEqual(second["changes"], [])
        self.assertTrue(all(record["has_compared"] for record in second["repositories"].values()))

    def test_later_readme_and_release_identity_changes_have_previous_and_new_evidence(self):
        baseline = self.observe().memory
        client = FakeClient()
        first, second = agent.WATCHLIST[:2]
        client.commit_versions[first] = client.readme_versions[first] = 2
        client.releases[second] = {"id": 77, "tag_name": "v1.0.0", "published_at": agent.timestamp(self.now), "draft": False, "prerelease": False, "name": "NEVER_COPY_RELEASE_TITLE", "body": "NEVER_COPY_RELEASE_BODY"}
        result = self.observe(memory=baseline, client=client, now=self.now + timedelta(days=1), event=2).memory
        self.assertEqual(len(result["changes"]), 2)
        readme_change = next(change for change in result["changes"] if change["repo"] == first)
        self.assertEqual(readme_change["before"]["commit_sha"], baseline["repositories"][first]["last_good"]["commit_sha"])
        self.assertNotEqual(readme_change["before"]["readme_sha"], readme_change["after"]["readme_sha"])
        report = agent.render_workbench(result, self.catalog)
        self.assertIn("README changed", report)
        self.assertIn("Release observation changed", report)
        self.assertNotIn("NEVER_COPY", report)

    def test_privacy_gate_precedes_every_further_read(self):
        private_repo = agent.WATCHLIST[0]
        self.client.overrides[(private_repo, "")] = {"full_name": private_repo, "private": True, "visibility": "private", "default_branch": "main", "description": "SECRET_CONTENT"}
        result = self.observe().memory
        self.assertEqual([resource for repo, resource in self.client.calls if repo == private_repo], [""])
        self.assertEqual(result["repositories"][private_repo]["problem"], "not_public")
        self.assertIsNone(result["repositories"][private_repo]["last_good"])
        self.assertNotIn("SECRET_CONTENT", agent.render_workbench(result, self.catalog))

    def test_failure_retains_last_good_evidence_and_cannot_become_unchanged_or_no_release(self):
        repo = agent.WATCHLIST[0]
        self.client.releases[repo] = {"id": 77, "tag_name": "v1", "published_at": agent.timestamp(self.now), "draft": False, "prerelease": False}
        baseline = self.observe().memory
        failing = FakeClient()
        failing.errors[(repo, "releases/latest")] = agent.APIError(503)
        result = self.observe(memory=baseline, client=failing, now=self.now + timedelta(days=1), event=2).memory
        record = result["repositories"][repo]
        self.assertEqual(record["status"], "unavailable")
        self.assertEqual(record["last_good"], baseline["repositories"][repo]["last_good"])
        self.assertEqual(result["changes"], [])
        report = agent.render_workbench(result, self.catalog)
        self.assertIn("Last good evidence (stale)", report)
        self.assertIn("v1", report)
        self.assertIn("current source unavailable, retained evidence is stale", report)

    def test_incomplete_tree_is_unavailable_and_missing_or_nonfile_entrypoints_are_explicit(self):
        repo = agent.WATCHLIST[0]
        tree_resource = f"git/trees/{sha(f'{repo}:tree:1')}?recursive=1"
        self.client.overrides[(repo, tree_resource)] = {"sha": sha(f"{repo}:tree:1"), "truncated": True, "tree": []}
        incomplete = self.observe().memory
        self.assertEqual(incomplete["repositories"][repo]["problem"], "incomplete_tree")
        self.assertIsNone(incomplete["repositories"][repo]["last_good"])
        baseline = self.observe(client=FakeClient()).memory
        stale = self.observe(memory=baseline, now=self.now + timedelta(days=1), event=2).memory
        self.assertEqual(stale["repositories"][repo]["last_good"], baseline["repositories"][repo]["last_good"])
        self.assertIn("Last good evidence (stale)", agent.render_workbench(stale, self.catalog))
        client = FakeClient()
        client.missing.add((repo, "docs/start.md"))
        client.nonfiles.add((repo, "CONTRIBUTING.md"))
        result = self.observe(client=client).memory
        self.assertEqual(result["repositories"][repo]["status"], "current")
        report = agent.render_workbench(result, self.catalog)
        self.assertIn("docs/start.md: missing", report)
        self.assertIn("CONTRIBUTING.md: not a regular file", report)
        self.assertIn("Review the configured entrypoint", report)
        self.assertIn("4 of 5 selected starting paths", report)

    def test_successful_daily_gate_and_singapore_midnight_boundary(self):
        before_midnight = agent.parse_time("2026-10-28T15:59:00Z")
        baseline = self.observe(now=before_midnight).memory
        unused = FakeClient()
        skipped = self.observe(memory=baseline, client=unused, now=before_midnight + timedelta(seconds=30), event=2)
        self.assertTrue(skipped.is_noop)
        self.assertEqual(unused.calls, [])
        new_day = self.observe(memory=baseline, client=unused, now=before_midnight + timedelta(minutes=2), event=3)
        self.assertFalse(new_day.is_noop)
        self.assertEqual(new_day.memory["last_observed_date"], "2026-10-29")
        self.assertEqual(len(unused.calls), 20)

    def test_same_day_retries_only_unavailable_sources_then_stops(self):
        repo = agent.WATCHLIST[0]
        self.client.errors[(repo, "releases/latest")] = agent.APIError(500)
        partial = self.observe().memory
        client = FakeClient()
        recovered = self.observe(memory=partial, client=client, now=self.now + timedelta(hours=1), event=2)
        self.assertFalse(recovered.is_noop)
        self.assertEqual(len(client.calls), 4)
        self.assertEqual({repo for repo, _ in client.calls}, {repo})
        for other in agent.WATCHLIST[1:]:
            self.assertEqual(recovered.memory["repositories"][other], partial["repositories"][other])
        idle = FakeClient()
        self.assertTrue(self.observe(memory=recovered.memory, client=idle, now=self.now + timedelta(hours=2), event=3).is_noop)
        self.assertEqual(idle.calls, [])

    def test_replay_is_noop_even_forced_and_changed_catalog_requires_new_observation(self):
        baseline = self.observe(event=100).memory
        unused = FakeClient()
        self.assertTrue(self.observe(memory=baseline, client=unused, event=100, force=True).is_noop)
        self.assertTrue(self.observe(memory=baseline, client=unused, event=99, force=True).is_noop)
        self.assertEqual(unused.calls, [])
        changed = deepcopy(self.catalog)
        changed["projects"][0]["start_path"] = "README.md"
        refreshed = self.observe(memory=baseline, client=unused, config=changed, event=101)
        self.assertFalse(refreshed.is_noop)
        self.assertEqual(len(unused.calls), 20)
        self.assertNotEqual(refreshed.memory["catalog_sha256"], baseline["catalog_sha256"])
        with self.assertRaisesRegex(ValueError, "backwards"):
            self.observe(memory=baseline, now=self.now - timedelta(seconds=1), event=102)

    def test_rate_limit_stops_network_reads_and_marks_remaining_sources_unavailable(self):
        for status in (403, 429):
            client = FakeClient()
            client.errors[(agent.WATCHLIST[0], "")] = agent.APIError(status, rate_limited=True)
            result = self.observe(client=client).memory
            self.assertEqual(client.calls, [(agent.WATCHLIST[0], "")])
            self.assertTrue(all(record["problem"] == "rate_limited" for record in result["repositories"].values()))

    def test_malformed_selected_tree_entry_becomes_unavailable_without_discarding_evidence(self):
        baseline = self.observe().memory
        repo = agent.WATCHLIST[0]
        resource = f"git/trees/{sha(f'{repo}:tree:1')}?recursive=1"
        malformed = {"sha": sha(f"{repo}:tree:1"), "truncated": False, "tree": [{"path": "README.md", "type": "blob", "mode": [], "sha": sha("blob")}]}
        self.client.overrides[(repo, resource)] = malformed
        result = self.observe(memory=baseline, now=self.now + timedelta(days=1), event=2).memory
        self.assertEqual(result["repositories"][repo]["problem"], "invalid_response")
        self.assertEqual(result["repositories"][repo]["last_good"], baseline["repositories"][repo]["last_good"])

    def test_change_history_is_bounded_without_losing_latest_source_memory(self):
        memory = self.observe().memory
        repo = agent.WATCHLIST[0]
        for version in range(2, 24):
            client = FakeClient()
            client.commit_versions[repo] = client.readme_versions[repo] = version
            memory = self.observe(memory=memory, client=client, now=self.now + timedelta(minutes=version), event=version, force=True).memory
        self.assertEqual(len(memory["changes"]), 20)
        self.assertEqual(memory["repositories"][repo]["last_good"]["commit_sha"], sha(f"{repo}:commit:23"))
        too_many = deepcopy(memory)
        too_many["changes"].append(deepcopy(too_many["changes"][-1]))
        with self.assertRaisesRegex(ValueError, "limit"):
            agent.validate_memory(too_many)

    def test_strict_schemas_and_safe_paths_reject_unexpected_scope_and_data(self):
        for field, value in (("start_path", "../private.md"), ("start_path", "https://elsewhere.invalid/x"), ("repo", "Albertito-AI/private-project")):
            invalid = deepcopy(self.catalog)
            invalid["projects"][0][field] = value
            with self.assertRaises(ValueError):
                agent.validate_catalog(invalid)
        invalid_memory = deepcopy(self.memory)
        invalid_memory["unrelated_records"] = []
        with self.assertRaises(ValueError):
            agent.validate_memory(invalid_memory)
        malformed = self.observe().memory
        malformed["repositories"][agent.WATCHLIST[0]]["last_good"]["commit_sha"] = "main"
        with self.assertRaises(ValueError):
            agent.validate_memory(malformed)

    def test_catalog_text_is_escaped_and_fetched_prose_never_enters_outputs(self):
        self.catalog["projects"][0]["title"] = "A [link](https://untrusted.invalid) <script>"
        self.catalog["projects"][0]["purpose"] = "A | table `escape` & safe text."
        result = self.observe().memory
        report = agent.render_workbench(result, self.catalog)
        self.assertNotIn("<script>", report)
        self.assertIn("&lt;script&gt;", report)
        self.assertIn("A \\| table", report)
        self.assertNotIn("NEVER_COPY", report)


class SparksCLITests(unittest.TestCase):
    def setUp(self):
        self.now = "2026-10-28T06:00:00Z"

    def test_initialization_observation_and_offline_check_only_write_two_owned_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / agent.CATALOG_PATH).write_text(json.dumps(catalog()), encoding="utf-8")
            protected = [root / "data/persona.json", root / "data/public-care.json"]
            for path in protected:
                path.write_text('"DO_NOT_CHANGE_CARE"', encoding="utf-8")
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in protected}
            with patch.object(agent, "GitHubClient", side_effect=AssertionError("no API during initialization")), redirect_stdout(io.StringIO()):
                self.assertEqual(agent.main(["initialize", "--now", self.now], root=root), 0)
                self.assertEqual(agent.main(["--check"], root=root), 0)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(agent.main(["observe", "--now", self.now, "--event-id", "actions:1"], root=root, client=FakeClient()), 0)
            snapshots = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in (root / agent.MEMORY_PATH, root / agent.WORKBENCH_PATH)}
            with patch.object(agent, "GitHubClient", side_effect=AssertionError("no API during check")), redirect_stdout(io.StringIO()):
                self.assertEqual(agent.main(["--check"], root=root), 0)
            self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in protected})
            self.assertEqual(snapshots, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in snapshots})
            with redirect_stderr(io.StringIO()):
                self.assertEqual(agent.main(["initialize", "--now", self.now], root=root), 1)
            self.assertEqual(snapshots, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in snapshots})

    def test_replay_does_not_rewrite_files_and_check_detects_report_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / agent.CATALOG_PATH).write_text(json.dumps(catalog()), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                agent.main(["initialize", "--now", self.now], root=root)
                agent.main(["observe", "--now", self.now, "--event-id", "actions:1"], root=root, client=FakeClient())
            workbench = root / agent.WORKBENCH_PATH
            workbench.write_text("An uncommitted manual edit", encoding="utf-8")
            paths = [root / agent.MEMORY_PATH, workbench]
            before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
            unused = FakeClient()
            with redirect_stdout(io.StringIO()):
                self.assertEqual(agent.main(["observe", "--now", self.now, "--event-id", "actions:1", "--force"], root=root, client=unused), 0)
            self.assertEqual(unused.calls, [])
            self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths})
            with redirect_stderr(io.StringIO()):
                self.assertEqual(agent.main(["--check"], root=root), 1)
            self.assertEqual(workbench.read_text(), "An uncommitted manual edit")

    def test_api_never_follows_redirects_or_leaks_tokens_and_limits_scope(self):
        client = agent.GitHubClient("SECRET_TOKEN")
        error = HTTPError("https://api.github.com/", 302, "SECRET_BODY", Message(), io.BytesIO(b"SECRET_BODY"))
        with patch.object(client._opener, "open", side_effect=error), self.assertRaises(agent.APIError) as caught:
            client.get(agent.WATCHLIST[0], "")
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertIsNone(agent._NoRedirects().redirect_request(None, None, 302, "", Message(), "https://untrusted.invalid/"))
        with self.assertRaises(ValueError):
            client.get("Albertito-AI/private-project", "")
        with self.assertRaises(ValueError):
            client.get(agent.WATCHLIST[0], "https://untrusted.invalid/")

    def test_ambiguous_duplicate_visibility_fields_fail_before_further_reads(self):
        client = agent.GitHubClient("SECRET_TOKEN")
        repo = agent.WATCHLIST[0]
        payload = ('{"full_name":"' + repo + '","private":true,"private":false,"visibility":"public","default_branch":"main"}').encode()
        with patch.object(client._opener, "open", return_value=io.BytesIO(payload)) as network, self.assertRaises(agent.SourceError) as caught:
            agent.observe_repository(catalog()["projects"][0], client, agent.parse_time(self.now))
        self.assertEqual(caught.exception.problem, "repository_unavailable")
        self.assertEqual(network.call_count, 1)


if __name__ == "__main__":
    unittest.main()
