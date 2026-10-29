"""Offline boundary tests for ingestion, preservation and honest review levels."""
import copy
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("library_refresh", ROOT / "scripts/library/refresh.py")
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)
NOW = "2026-10-29T01:00:00Z"


def work(n=1, title="Sustainability reporting and corporate accountability", **patch):
    value = {"DOI": f"10.5555/example-{n}", "title": [title], "author": [{"given": "Ada", "family": "Researcher"}], "publisher": "Example Academic Publisher", "container-title": ["Example Research Journal"], "published": {"date-parts": [[2026, 10, 1]]}, "type": "journal-article", "subject": []}
    value.update(patch)
    return value


def reference(**patch):
    value = {"id": "reference-official", "title": "Official research framework", "type": "reference", "description": "A source-inspected official framework.", "use_for": "Compare the documented concepts in a source review.", "topics": ["Research methods"], "links": [{"label": "Official source", "url": "https://example.org/framework"}], "verification": {"checked_at": "2026-10-28T01:00:00Z", "source_url": "https://example.org/framework", "scope": "Official source inspected for its stated scope."}, "citation": {"url": "https://example.org/framework", "text": "Example official source.", "available": True}}
    value.update(patch)
    return value


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config/library_sources.json").read_text())
        self.source = self.config["sources"][0]
        self.responses = {s["id"]: {"items": []} for s in self.config["sources"]}
        self.base = {"items": []}
        self.previous = {"items": [], "source_runs": []}

    def build(self, refs=None, previous=None, now=NOW, responses=None, rechecks=None, curated_only=False):
        return pipeline.build_library(self.config, [] if refs is None else refs, self.base, self.previous if previous is None else previous, self.responses if responses is None else responses, now, rechecks, curated_only=curated_only)

    def test_realistic_metadata_admission_retains_attribution(self):
        self.responses[self.source["id"]]["items"] = [work()]
        result = self.build()
        self.assertEqual(result["status"], "ok")
        item = result["items"][0]
        self.assertEqual(item["review_status"], "metadata_only")
        self.assertEqual(item["authors"], ["Ada Researcher"])
        self.assertEqual(item["publisher"], "Example Academic Publisher")
        self.assertIn("10.5555/example-1", item["citation"]["text"])
        self.assertEqual(item["last_metadata_check"], NOW)
        self.assertNotIn("abstract", item)
        self.assertIn("full text were not fetched", item["verification"]["scope"])

    def test_two_relevance_groups_are_required(self):
        for title in ("Corporate governance in regional markets", "The history of sustainability", "Climate measurements and marine physics"):
            item, reason = pipeline.normalise_work(work(title=title), self.source, NOW, 2015)
            self.assertIsNone(item)
            self.assertEqual(reason, "outside_topic")

    def test_partial_word_does_not_match_ai(self):
        source = self.config["sources"][1]
        item, reason = pipeline.normalise_work(work(title="Chair evaluation for better governance"), source, NOW, 2015)
        self.assertIsNone(item)
        self.assertEqual(reason, "outside_topic")

    def test_incomplete_or_future_records_rejected(self):
        for patch in ({"author": []}, {"DOI": "not-a-doi"}, {"publisher": ""}, {"title": []}, {"published": {"date-parts": [[2030, 1, 1]]}}, {"published": {"date-parts": [[2026, 13, 32]]}}):
            item, reason = pipeline.normalise_work(work(**patch), self.source, NOW, 2015)
            self.assertIsNone(item, patch)
            self.assertEqual(reason, "missing_or_invalid_metadata")

    def test_online_date_precedes_future_print_date(self):
        item, reason = pipeline.normalise_work(work(**{"published-print": {"date-parts": [[2027, 1, 1]]}, "published-online": {"date-parts": [[2026, 9, 12]]}}), self.source, NOW, 2015)
        self.assertFalse(reason)
        self.assertEqual(item["publication_date"], "2026-09-12")

    def test_date_precision_is_not_invented(self):
        item, reason = pipeline.normalise_work(work(published={"date-parts": [[2026]]}), self.source, NOW, 2015)
        self.assertFalse(reason)
        self.assertEqual(item["publication_date"], "2026")
        self.assertEqual(item["publication_date_precision"], "year")

    def test_duplicates_in_source_and_base_catalogue_are_suppressed(self):
        existing = work()
        self.base["items"] = [{"id": "already-curated", "citation": {"doi": "HTTPS://DOI.ORG/10.5555/EXAMPLE-1"}}]
        self.responses[self.source["id"]]["items"] = [existing, work(2), work(2)]
        result = self.build()
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["doi"], "10.5555/example-2")
        self.assertEqual(result["changes"]["rejected"]["duplicate"], 2)

    def test_repeated_refresh_preserves_identity_and_added_date(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        second = self.build(previous=first, now="2026-10-30T01:00:00Z")
        self.assertEqual(len(second["items"]), 1)
        self.assertEqual(second["items"][0]["added_at"], NOW)
        self.assertEqual(second["items"][0]["last_metadata_check"], "2026-10-30T01:00:00Z")
        self.assertEqual(second["changes"]["added"], [])
        self.assertEqual(second["changes"]["updated"], [])

    def test_incidental_other_query_does_not_create_false_review_flag(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        self.responses[self.config["sources"][1]["id"]]["items"] = [work()]
        second = self.build(previous=first)
        self.assertEqual(second["items"][0]["review_status"], "metadata_only")
        self.assertEqual(second["changes"]["flagged"], [])

    def test_per_topic_and_global_budgets_across_same_day_reruns(self):
        titles = ["Sustainability reporting accountability", "Artificial intelligence governance and evaluation", "Legal evidence provenance in courts"]
        for number, source in enumerate(self.config["sources"]):
            self.responses[source["id"]]["items"] = [work(number * 20 + i, title=titles[number]) for i in range(10)]
        first = self.build()
        self.assertEqual(len(first["items"]), 9)
        second = self.build(previous=first, now="2026-10-29T03:00:00Z")
        self.assertEqual(len(second["items"]), 9)
        self.assertEqual(second["changes"]["added"], [])
        third = self.build(previous=second, now="2026-10-30T03:00:00Z")
        self.assertEqual(len(third["items"]), 18)

    def test_singapore_day_boundary_is_used(self):
        self.assertEqual(pipeline.service_day("2026-10-28T23:00:00Z"), "2026-10-29")

    def test_full_failure_keeps_last_good_data_and_success_time(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build(refs=[reference()])
        failures = {s["id"]: {"error": "HTTP 503"} for s in self.config["sources"]}
        second = self.build(refs=[reference()], previous=first, responses=failures, now="2026-10-30T01:00:00Z")
        self.assertEqual(second["status"], "failed")
        self.assertEqual(second["last_successful_refresh"], NOW)
        self.assertEqual(second["items"], first["items"])
        self.assertEqual(second["source_runs"][0]["last_successful_check"], NOW)

    def test_partial_failure_reports_degraded(self):
        self.responses[self.source["id"]] = {"error": "timeout"}
        result = self.build()
        self.assertEqual(result["status"], "degraded")
        self.assertIsNone(result["last_successful_refresh"])

    def test_retraction_notice_is_not_new_research(self):
        item, reason = pipeline.normalise_work(work(title="Retraction: Sustainability reporting and accountability"), self.source, NOW, 2015)
        self.assertIsNone(item)
        self.assertEqual(reason, "update_notice")

    def test_retracted_existing_record_is_retained_and_flagged(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        update = work(relation={"is-retracted-by": [{"id": "10.5555/notice"}]})
        second = self.build(previous=first, rechecks={"10.5555/example-1": {"item": update}})
        self.assertEqual(len(second["items"]), 1)
        self.assertEqual(second["items"][0]["review_status"], "needs_review")
        self.assertEqual(second["changes"]["flagged"], [first["items"][0]["id"]])

    def test_retraction_flag_is_not_cleared_by_later_clean_metadata(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        flagged = self.build(previous=first, rechecks={"10.5555/example-1": {"item": work(relation={"is-retracted-by": [{"id": "10.5555/notice"}]})}})
        later = self.build(previous=flagged, now="2026-10-30T01:00:00Z")
        self.assertEqual(later["items"][0]["review_status"], "needs_review")

    def test_metadata_updates_record_change_without_new_count(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        self.responses[self.source["id"]]["items"] = [work(publisher="Corrected Publisher Name")]
        later = self.build(previous=first, now="2026-10-30T01:00:00Z")
        self.assertEqual(later["items"][0]["publisher"], "Corrected Publisher Name")
        self.assertEqual(len(later["changes"]["updated"]), 1)
        self.assertEqual(later["changes"]["added"], [])

    def test_html_is_not_retained_and_unsafe_urls_are_rejected(self):
        item, reason = pipeline.normalise_work(work(title="<script>alert(1)</script><i>Sustainability reporting</i> and accountability"), self.source, NOW, 2015)
        self.assertFalse(reason)
        self.assertNotIn("<", item["title"])
        self.assertNotIn("alert", item["title"])
        for url in ("javascript:alert(1)", "http://example.org", "https://localhost/a", "https://127.0.0.1/a", "https://user:password@example.org/a", "https://example.org:8888/a"):
            self.assertFalse(pipeline.safe_url(url), url)
        bad = reference(links=[{"label": "Bad", "url": "javascript:alert(1)"}])
        with self.assertRaises(pipeline.ValidationError):
            self.build(refs=[bad])

    def test_network_host_and_redirect_are_restricted(self):
        self.assertTrue(pipeline.approved_api_url("https://api.crossref.org/works?rows=3"))
        self.assertFalse(pipeline.approved_api_url("https://evil.example/works"))
        self.assertFalse(pipeline.approved_api_url("https://api.crossref.org/members"))
        with self.assertRaises(pipeline.ValidationError):
            pipeline.fetch_json("https://127.0.0.1/")
        request = urllib.request.Request("https://api.crossref.org/works")
        with self.assertRaises(pipeline.ValidationError):
            pipeline.SafeRedirect().redirect_request(request, None, 302, "Found", {}, "https://evil.example/works")

    def test_curated_inspection_date_never_advances_from_pipeline_execution(self):
        first = self.build(refs=[reference()])
        second = self.build(refs=[reference()], previous=first, now="2026-11-01T01:00:00Z")
        self.assertEqual(second["items"][0]["verification"]["checked_at"], "2026-10-28T01:00:00Z")
        self.assertEqual(second["items"][0]["added_at"], NOW)

    def test_curated_staleness_and_removal_are_visible(self):
        first = self.build(refs=[reference()])
        stale = self.build(refs=[reference()], previous=first, now="2027-03-01T01:00:00Z")
        self.assertEqual(stale["items"][0]["review_status"], "needs_review")
        removed = self.build(previous=first)
        self.assertEqual(len(removed["items"]), 1)
        self.assertEqual(removed["items"][0]["review_status"], "needs_review")

    def test_machine_cannot_promote_its_review_level(self):
        self.responses[self.source["id"]]["items"] = [work()]
        result = self.build()
        result["items"][0]["review_status"] = "source_inspected"
        with self.assertRaises(pipeline.ValidationError):
            pipeline.validate_library(result)

    def test_abstracts_and_full_text_are_not_imported(self):
        self.responses[self.source["id"]]["items"] = [work(abstract="A copyrighted complete abstract.", full_text="Private input")]
        result = self.build()
        encoded = json.dumps(result)
        self.assertNotIn("copyrighted complete", encoded)
        self.assertNotIn("Private input", encoded)

    def test_queue_is_actionable_and_does_not_assert_review(self):
        self.responses[self.source["id"]]["items"] = [work()]
        queue = pipeline.review_queue(self.build(refs=[reference()]))
        self.assertEqual(len(queue["items"]), 1)
        self.assertIn("exact supporting location", queue["items"][0]["next_action"])
        self.assertEqual(queue["items"][0]["review_status"], "metadata_only")

    def test_offline_transform_is_deterministic(self):
        self.responses[self.source["id"]]["items"] = [work()]
        self.assertEqual(self.build(refs=[reference()]), self.build(refs=[reference()]))

    def test_historical_second_page_makes_bounded_forward_progress(self):
        self.config["sources"] = [self.source]
        self.source["rows"] = 2
        self.config["recheck_limit"] = 0

        def fetch(url):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            offset = int(query["offset"][0]) if "offset" in query else None
            return {"items": [] if offset is None else [work(offset + 1), work(offset + 2)], "total-results": 100}, "fixture-digest"

        with mock.patch.object(pipeline, "fetch_json", side_effect=fetch) as retrieve:
            responses, rechecks = pipeline.get_responses(self.config, self.previous, NOW)
            first = self.build(responses=responses, rechecks=rechecks)
            self.assertEqual(first["coverage"]["sources"][self.source["id"]]["offset"], 2)
            responses, rechecks = pipeline.get_responses(self.config, first, "2026-10-30T01:00:00Z")
            second = self.build(previous=first, responses=responses, rechecks=rechecks, now="2026-10-30T01:00:00Z")
        self.assertEqual(len(second["items"]), 4)
        self.assertEqual(second["coverage"]["sources"][self.source["id"]]["offset"], 4)
        self.assertEqual(retrieve.call_count, 4)
        urls = [call.args[0] for call in retrieve.call_args_list]
        self.assertTrue(any("offset=2" in url for url in urls))
        self.assertIn("from-index-date", urllib.parse.unquote(urls[0]))
        self.assertIn("not an exhaustive", second["coverage"]["notice"])

    def test_historical_failure_does_not_advance_position(self):
        self.config["sources"] = [self.source]
        self.config["recheck_limit"] = 0
        previous = self.build()
        previous["coverage"]["sources"][self.source["id"]] = {"year": 2024, "offset": 160, "last_advanced_at": NOW}

        def fetch(url):
            if "offset=" in url:
                raise OSError("historical source unavailable")
            return {"items": []}, "recent-digest"

        with mock.patch.object(pipeline, "fetch_json", side_effect=fetch):
            responses, rechecks = pipeline.get_responses(self.config, previous, "2026-10-30T01:00:00Z")
        result = self.build(previous=previous, responses=responses, rechecks=rechecks, now="2026-10-30T01:00:00Z")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["coverage"]["sources"], previous["coverage"]["sources"])
        self.assertEqual(result["last_successful_refresh"], NOW)
        self.assertEqual(result["source_runs"][0]["queries"][0]["status"], "ok")
        self.assertEqual(result["source_runs"][0]["queries"][1]["status"], "failed")

    def test_historical_offset_and_year_cycle_are_finite(self):
        next_position = pipeline.next_backfill_position(self.source, self.config, {"year": 2025, "offset": 400}, self.source["rows"], NOW)
        self.assertEqual(next_position, {"year": 2024, "offset": 0})
        wrapped = pipeline.next_backfill_position(self.source, self.config, {"year": 2015, "offset": 0}, 0, NOW)
        self.assertEqual(wrapped, {"year": 2026, "offset": 0})
        short_page = pipeline.next_backfill_position(self.source, self.config, {"year": 2023, "offset": 0}, 1, NOW)
        self.assertEqual(short_page, {"year": 2022, "offset": 0})

    def test_pending_survives_quota_and_source_failure_without_fake_freshness(self):
        self.responses[self.source["id"]]["items"] = [work(i) for i in range(7)]
        first = self.build()
        self.assertEqual(len(first["items"]), 3)
        self.assertEqual(len(first["pending"]), 4)
        repeated = self.build(previous=first)
        self.assertEqual(len(repeated["pending"]), 4)
        self.assertEqual(len({i["doi"] for i in repeated["pending"]}), 4)
        failures = {s["id"]: {"error": "source unavailable"} for s in self.config["sources"]}
        next_day = self.build(previous=repeated, responses=failures, now="2026-10-30T01:00:00Z")
        self.assertEqual(next_day["status"], "failed")
        self.assertEqual(len(next_day["items"]), 6)
        self.assertEqual(len(next_day["pending"]), 1)
        new_records = [i for i in next_day["items"] if i["id"] in next_day["changes"]["added"]]
        self.assertEqual(len(new_records), 3)
        self.assertTrue(all(i["added_at"] == "2026-10-30T01:00:00Z" for i in new_records))
        self.assertTrue(all(i["last_metadata_check"] == NOW for i in new_records))
        self.assertEqual(next_day["last_successful_refresh"], NOW)

    def test_pending_overflow_is_bounded_and_reported(self):
        self.config["pending_limit_per_topic"] = 2
        self.responses[self.source["id"]]["items"] = [work(i) for i in range(8)]
        result = self.build()
        self.assertEqual(len(result["pending"]), 2)
        receipt = result["source_runs"][0]
        self.assertEqual(receipt["pending_count"], 2)
        self.assertEqual(receipt["pending_limit"], 2)
        self.assertEqual(receipt["pending_overflow"], 3)

    def test_same_book_chapters_are_limited_across_daily_reruns(self):
        self.responses[self.source["id"]]["items"] = [work(i, type="book-chapter", **{"container-title": ["One Book"]}) for i in range(4)]
        first = self.build()
        self.assertEqual(len(first["items"]), 1)
        self.assertEqual(len(first["pending"]), 3)
        self.assertEqual(first["source_runs"][0]["queued_for_container_diversity"], 3)
        self.responses[self.source["id"]]["items"].append(work(10, type="book-chapter", **{"container-title": ["A Different Book"]}))
        self.responses[self.source["id"]]["items"].append(work(11))
        repeated = self.build(previous=first, now="2026-10-29T02:00:00Z")
        self.assertEqual(len(repeated["items"]), 3)
        self.assertEqual(sum(i.get("venue") == "One Book" for i in repeated["items"]), 1)
        next_day = self.build(previous=repeated, now="2026-10-30T01:00:00Z")
        self.assertEqual(sum(i.get("venue") == "One Book" for i in next_day["items"]), 2)

    def test_journal_container_does_not_trigger_chapter_limit(self):
        self.responses[self.source["id"]]["items"] = [work(i) for i in range(4)]
        result = self.build()
        self.assertEqual(len(result["items"]), 3)
        self.assertNotIn("queued_for_container_diversity", result["source_runs"][0])

    def test_curated_only_preserves_real_retrieval_receipts_and_pending(self):
        self.responses[self.source["id"]]["items"] = [work(i) for i in range(5)]
        first = self.build(refs=[reference()])
        new_reference = reference(id="another-reference", links=[{"url": "https://example.org/another"}], citation={"url": "https://example.org/another"})
        second = self.build(refs=[reference(), new_reference], previous=first, now="2026-10-30T01:00:00Z", curated_only=True)
        self.assertEqual(second["refresh_mode"], "curated_only")
        self.assertEqual(second["source_runs"], first["source_runs"])
        self.assertEqual(second["last_successful_refresh"], NOW)
        self.assertEqual(second["pending"], first["pending"])
        self.assertEqual(second["coverage"], first["coverage"])
        self.assertEqual(len(second["items"]), len(first["items"]) + 1)
        self.assertEqual(second["changes"]["added"], ["another-reference"])
        self.assertTrue(all(i["last_metadata_check"] == NOW for i in second["items"] if i["origin"] == "crossref"))

    def test_updated_by_retraction_excludes_new_and_flags_existing_record(self):
        update = work(**{"updated-by": [{"DOI": "10.5555/notice", "type": "retraction", "source": "publisher"}]})
        item, reason = pipeline.normalise_work(update, self.source, NOW, 2015)
        self.assertIsNone(item)
        self.assertEqual(reason, "update_notice")
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        second = self.build(previous=first, rechecks={"10.5555/example-1": {"item": update}})
        self.assertEqual(second["items"][0]["review_status"], "needs_review")
        self.assertIn("updated-by", pipeline.SELECT_FIELDS.split(","))

    def test_separate_retraction_notice_flags_original_and_pending_record(self):
        self.responses[self.source["id"]]["items"] = [work(i) for i in range(4)]
        first = self.build()
        published = first["items"][0]
        pending = first["pending"][0]
        notice = work(10, title="Retraction: Sustainability reporting and accountability", **{"update-to": [{"DOI": published["doi"], "type": "retraction"}, {"DOI": pending["doi"], "type": "retraction"}]})
        self.responses[self.source["id"]]["items"] = [notice]
        second = self.build(previous=first, now="2026-10-30T01:00:00Z")
        updated = next(i for i in second["items"] if i["id"] == published["id"])
        self.assertEqual(updated["review_status"], "needs_review")
        self.assertEqual(updated["last_metadata_check"], NOW)
        self.assertEqual(updated["last_update_notice_check"], "2026-10-30T01:00:00Z")
        self.assertEqual(second["pending"][0]["review_status"], "needs_review")
        self.assertEqual(second["changes"]["added"], [])

    def test_failed_rechecks_rotate_without_falsifying_success_dates(self):
        self.config["recheck_limit"] = 1
        self.responses[self.source["id"]]["items"] = [work(1), work(2)]
        first = self.build()

        def fetch(url):
            if urllib.parse.urlsplit(url).path != "/works":
                raise OSError("permanent failed record")
            return {"items": []}, "fixture-digest"

        with mock.patch.object(pipeline, "fetch_json", side_effect=fetch):
            responses, rechecks = pipeline.get_responses(self.config, first, "2026-10-30T01:00:00Z")
            second = self.build(previous=first, responses=responses, rechecks=rechecks, now="2026-10-30T01:00:00Z")
            _, later_rechecks = pipeline.get_responses(self.config, second, "2026-10-31T01:00:00Z")
        self.assertNotEqual(set(rechecks), set(later_rechecks))
        self.assertTrue(all(i["last_metadata_check"] == NOW for i in second["items"]))
        attempted = next(i for i in second["items"] if i["doi"] in rechecks)
        self.assertEqual(attempted["last_metadata_attempt"], "2026-10-30T01:00:00Z")

    def test_promotion_into_base_retains_provenance_and_quota(self):
        self.responses[self.source["id"]]["items"] = [work(i) for i in range(5)]
        first = self.build()
        promoted = first["items"][0]
        self.base["items"] = [{"id": "curator-reviewed-record", "citation": {"doi": promoted["doi"]}}]
        second = self.build(previous=first)
        self.assertEqual(len(second["items"]), 2)
        self.assertEqual(len(second["pending"]), 2)
        self.assertEqual(second["stats"]["new_metadata_today"], 3)
        self.assertEqual(second["superseded_records"][0]["record"], promoted)
        self.assertEqual(second["superseded_records"][0]["superseded_by"], "curator-reviewed-record")
        pipeline.validate_library(second, self.base)
        repeated = self.build(previous=second)
        self.assertEqual(len(repeated["superseded_records"]), 1)

    def test_malformed_optional_subjects_and_extra_title_values_are_inert(self):
        payload = work(subject=None)
        payload["title"].append(None)
        item, reason = pipeline.normalise_work(payload, self.source, NOW, 2015)
        self.assertFalse(reason)
        self.assertEqual(item["review_status"], "metadata_only")

    def test_notice_in_later_source_prevents_new_original_admission(self):
        self.responses[self.source["id"]]["items"] = [work()]
        self.responses[self.config["sources"][2]["id"]]["items"] = [work(10, title="Retraction: Sustainability reporting and accountability", **{"update-to": [{"DOI": "10.5555/example-1", "type": "retraction"}]})]
        result = self.build()
        self.assertEqual(result["items"], [])
        self.assertEqual(result["pending"], [])

    def test_curated_reference_promotion_archives_automatic_record(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        curated = reference(doi=first["items"][0]["doi"])
        second = self.build(previous=first, refs=[curated], now="2026-10-30T01:00:00Z", curated_only=True)
        self.assertEqual(len(second["items"]), 1)
        self.assertEqual(second["items"][0]["origin"], "curated_reference")
        self.assertEqual(second["items"][0]["added_at"], NOW)
        self.assertEqual(second["changes"]["added"], [])
        self.assertEqual(second["changes"]["updated"], [curated["id"]])
        self.assertEqual(second["superseded_records"][0]["record"], first["items"][0])
        self.assertEqual(second["stats"]["new_metadata_today"], 0)

    def test_same_id_curated_promotion_preserves_addition_date_on_later_day(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build()
        original = first["items"][0]
        curated = reference(id=original["id"], doi=original["doi"])
        second = self.build(previous=first, refs=[curated], now="2026-10-30T01:00:00Z", curated_only=True)
        self.assertEqual(second["items"][0]["added_at"], NOW)
        self.assertEqual(second["changes"]["added"], [])
        self.assertEqual(second["changes"]["updated"], [original["id"]])
        self.assertEqual(second["stats"]["added_this_run"], 0)
        self.assertEqual(second["superseded_records"][0]["record"], original)

    def test_cli_publishes_degraded_health_and_keeps_successful_data(self):
        self.responses[self.source["id"]]["items"] = [work()]
        first = self.build(refs=[reference()])
        failures = {s["id"]: {"error": "source unavailable"} for s in self.config["sources"]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, data in (("config.json", self.config), ("catalog.json", self.base), ("refs.json", [reference()]), ("library.json", first)):
                (root / name).write_text(json.dumps(data))
            args = ["--refresh", "--config", str(root / "config.json"), "--references", str(root / "refs.json"), "--catalog", str(root / "catalog.json"), "--output", str(root / "library.json"), "--now", "2026-10-30T01:00:00Z"]
            with mock.patch.object(pipeline, "get_responses", return_value=(failures, {})), mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch("sys.stderr", new_callable=io.StringIO):
                exit_code = pipeline.main(args)
            result = json.loads((root / "library.json").read_text())
            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["items"], first["items"])
            self.assertTrue((root / "library-review-queue.json").exists())
            self.assertTrue((root / "library-history.json").exists())

    def test_cli_curated_only_does_not_call_network_and_invalid_input_keeps_snapshot(self):
        first = self.build(refs=[reference()])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, data in (("config.json", self.config), ("catalog.json", self.base), ("refs.json", [reference()]), ("library.json", first)):
                (root / name).write_text(json.dumps(data))
            args = ["--curated-only", "--config", str(root / "config.json"), "--references", str(root / "refs.json"), "--catalog", str(root / "catalog.json"), "--output", str(root / "library.json"), "--now", "2026-10-30T01:00:00Z"]
            with mock.patch.object(pipeline, "get_responses") as network, mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(pipeline.main(args), 0)
                network.assert_not_called()
                expected_bytes = (root / "library.json").read_bytes()
                (root / "refs.json").write_text(json.dumps([{"id": "invalid-reference"}]))
                self.assertEqual(pipeline.main(args), 1)
                self.assertEqual((root / "library.json").read_bytes(), expected_bytes)


if __name__ == "__main__":
    unittest.main()
