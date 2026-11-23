"""Tests for immutable-publication and source-attribution failure cases."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.response import addinfourl

import check_registry as registry
from check_remote import verify_book, verify_health, verify_info, verify_legacy_notification, verify_tools


class PublicationGuardTests(unittest.TestCase):
    def setUp(self):
        self.expected, self.release_request = registry.reviewed_release()
        self.actual = {"server": copy.deepcopy(self.expected), "_meta": {
            "io.modelcontextprotocol.registry/official": {"status": "active"}}}

    def test_matching_active_record_is_idempotent(self):
        receipt = registry.compare_record(self.expected, self.actual)
        self.assertEqual(receipt["state"], "matching_active_version")

    def test_conflicting_or_inactive_record_stops_publication(self):
        for change in ("endpoint", "version", "icon", "repository", "auth", "deprecated"):
            with self.subTest(change=change):
                record = copy.deepcopy(self.actual)
                server = record["server"]
                if change == "endpoint": server["remotes"][0]["url"] += "/wrong"
                elif change == "version": server["version"] = "0.0.0"
                elif change == "icon": server["icons"][0]["src"] = "https://example.com/unreviewed.png"
                elif change == "repository": server["repository"] = {"url": "https://github.com/example/source"}
                elif change == "auth": server["remotes"][0]["headers"] = [{"name": "Authorization", "isRequired": True}]
                else: record["_meta"]["io.modelcontextprotocol.registry/official"]["status"] = "deprecated"
                with self.assertRaises(ValueError): registry.compare_record(self.expected, record)

    def test_only_404_means_absent(self):
        for status in (401, 403, 404, 410, 429, 500):
            def opener(url, timeout, status=status):
                raise HTTPError(url, status, "fixture", {}, io.BytesIO())
            with self.subTest(status=status):
                if status == 404:
                    code, receipt = registry.check(self.expected, opener)
                    self.assertEqual((code, receipt["state"]), (2, "absent"))
                else:
                    with self.assertRaises(HTTPError): registry.check(self.expected, opener)

    def test_redirected_404_is_not_absence_of_the_requested_version(self):
        def opener(url, timeout):
            raise HTTPError(url + "/different-location", 404, "fixture", {}, io.BytesIO())
        with self.assertRaises(HTTPError): registry.check(self.expected, opener)

    def test_matching_metadata_at_a_different_url_is_rejected(self):
        def opener(url, timeout):
            return addinfourl(io.BytesIO(json.dumps(self.actual).encode()), {},
                             url + "/different-location", code=200)
        with self.assertRaises(ValueError): registry.check(self.expected, opener)

    def test_legacy_notification_requires_202_and_no_body(self):
        verify_legacy_notification(202, b"")
        for status, content in [(200, b""), (204, b""), (202, b"{}"), (202, b" ")]:
            with self.subTest(status=status, content=content), self.assertRaises(ValueError):
                verify_legacy_notification(status, content)

    def test_modified_metadata_fails_review_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            server = Path(temp) / "server.json"
            request = Path(temp) / "release-request.json"
            raw = json.dumps(self.expected).encode()
            server.write_bytes(raw + b"\n")
            reviewed = copy.deepcopy(self.release_request)
            reviewed["server_sha256"] = hashlib.sha256(raw).hexdigest()
            request.write_text(json.dumps(reviewed))
            with self.assertRaisesRegex(ValueError, "reviewed release-request hash"):
                registry.reviewed_metadata(server, request)

    def test_reviewed_snapshot_counts_must_be_explicit_positive_integers(self):
        invalid_snapshots = [None, {}, {"catalogue_records": 32},
                             {"catalogue_records": 32, "ibol_lessons": 8, "extra": 1}]
        for field in ("catalogue_records", "ibol_lessons"):
            for value in (0, -1, True, 32.0, "32", None):
                snapshot = copy.deepcopy(self.release_request["expected_snapshot"])
                snapshot[field] = value
                invalid_snapshots.append(snapshot)
        with tempfile.TemporaryDirectory() as temp:
            server = Path(temp) / "server.json"
            request = Path(temp) / "release-request.json"
            server.write_bytes(registry.DEFAULT_SERVER.read_bytes())
            for snapshot in invalid_snapshots:
                reviewed = copy.deepcopy(self.release_request)
                reviewed["expected_snapshot"] = snapshot
                request.write_text(json.dumps(reviewed))
                with self.subTest(snapshot=snapshot), self.assertRaisesRegex(ValueError, "Reviewed snapshot"):
                    registry.reviewed_release(server, request)
            reviewed = copy.deepcopy(self.release_request)
            del reviewed["expected_snapshot"]
            request.write_text(json.dumps(reviewed))
            with self.assertRaisesRegex(ValueError, "reviewed fields"):
                registry.reviewed_release(server, request)

    def test_live_snapshot_must_match_both_reviewed_counts(self):
        snapshot = self.release_request["expected_snapshot"]
        health = {"status": "ok", "version": self.expected["version"], **snapshot}
        verify_health(health, self.expected["version"], snapshot)
        for field in snapshot:
            for value in (snapshot[field] - 1, snapshot[field] + 1, None, str(snapshot[field]), True):
                bad = {**health, field: value}
                with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, field):
                    verify_health(bad, self.expected["version"], snapshot)
        with self.assertRaisesRegex(ValueError, "reviewed service version"):
            verify_health({**health, "version": "1.1.0"}, self.expected["version"], snapshot)

    def test_wrong_live_version_or_write_capability_fails(self):
        with self.assertRaises(ValueError):
            verify_info({"name": "albert-research-resource-agent", "version": "1.0.0"}, self.expected["version"])
        with self.assertRaises(ValueError):
            verify_tools([{"name": name, "annotations": {"readOnlyHint": False}}
                          for name in ("search_resources", "get_resource", "get_ibol_lesson")])

    def test_citation_rights_and_author_must_survive_retrieval(self):
        result = {"isError": False, "structuredContent": {"resource": {
            "id": "ibol-book", "attribution": "Written by Albert Tan Sin Hon.",
            "citation_url": "https://doi.org/10.21827/6ac3948159a9e", "rights": "CC BY-NC-ND 4.0"}}}
        verify_book(result)
        for field in ("attribution", "citation_url", "rights"):
            bad = copy.deepcopy(result)
            bad["structuredContent"]["resource"][field] = ""
            with self.subTest(field=field), self.assertRaises(ValueError): verify_book(bad)


if __name__ == "__main__":
    unittest.main()
