"""Small synthetic fixtures test parser safety, not the real video's content."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ingest_video import parse_captions, read_local_file, validate_cues, rolling_reading_copy, normalise_maxrss_kib, peak_rss_kib, main


class CaptionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_vtt_preserves_source_times_and_decodes_presentation(self):
        path = self.fixture("synthetic.vtt", "WEBVTT\n\n00:00:01.000 --> 00:00:03.500 align:start\n<v Reader>Alpha &amp; beta.<00:00:02.000>\n")
        self.assertEqual(parse_captions(path), [{"start_seconds": 1.0, "end_seconds": 3.5, "text": "Alpha & beta."}])

    def test_srt_decimal_comma(self):
        path = self.fixture("synthetic.srt", "1\n00:00:02,250 --> 00:00:04,000\nSynthetic fixture.\n")
        self.assertEqual(parse_captions(path)[0]["start_seconds"], 2.25)

    def test_youtube_space_only_payload_line_does_not_drop_first_cue(self):
        path = self.fixture("synthetic.vtt", "WEBVTT\n\n00:00:00.400 --> 00:00:02.950\n \nFirst<00:00:00.880><c> words.</c>\n\n00:00:02.950 --> 00:00:02.960\nFirst words.\n \n")
        cues = parse_captions(path)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0]["start_seconds"], 0.4)
        self.assertEqual(cues[0]["text"], "First words.")

    def test_json3_uses_real_event_timing(self):
        path = self.fixture("synthetic.json", json.dumps({"events": [{"tStartMs": 1500, "dDurationMs": 1250, "segs": [{"utf8": "Test "}, {"utf8": "fixture."}]}]}))
        self.assertEqual(parse_captions(path)[0], {"start_seconds": 1.5, "end_seconds": 2.75, "text": "Test fixture."})

    def test_empty_response_is_never_treated_as_transcript(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            parse_captions(self.fixture("empty.json", ""))

    def test_invalid_and_out_of_bounds_timestamps_rejected(self):
        for cues in [[{"start_seconds": -1, "end_seconds": 2}], [{"start_seconds": 3, "end_seconds": 2}], [{"start_seconds": 0, "end_seconds": 20}]]:
            with self.subTest(cues=cues), self.assertRaises(ValueError):
                validate_cues(cues, 10)

    def test_json3_does_not_invent_missing_duration(self):
        path = self.fixture("missing.json", json.dumps({"events": [{"tStartMs": 0, "segs": [{"utf8": "Fixture"}]}]}))
        with self.assertRaisesRegex(ValueError, "source start and duration"):
            parse_captions(path)

    def test_remote_inputs_are_not_downloaded(self):
        with self.assertRaisesRegex(ValueError, "Only local"):
            read_local_file("https://example.invalid/private.vtt")

    def test_rolling_copy_removes_only_exact_suffix_prefix_overlap(self):
        cues = [{"start_seconds": 0, "end_seconds": 2, "text": "The first three words"},
                {"start_seconds": 2, "end_seconds": 4, "text": "first three words continue here"}]
        original = json.loads(json.dumps(cues))
        text, mapping = rolling_reading_copy(cues)
        self.assertIn("The first three words continue here", text)
        self.assertEqual(mapping[1]["removed_exact_prefix_tokens"], 3)
        self.assertEqual(mapping[1]["source_cue_index_zero_based"], 1)
        self.assertEqual(cues, original)

    def test_rolling_copy_preserves_non_overlapping_repeats_and_short_repeats(self):
        cues = [{"start_seconds": 0, "end_seconds": 2, "text": "This is repeated"},
                {"start_seconds": 3, "end_seconds": 4, "text": "This is repeated"},
                {"start_seconds": 4, "end_seconds": 5, "text": "repeated again"}]
        text, mapping = rolling_reading_copy(cues)
        self.assertEqual([m["removed_exact_prefix_tokens"] for m in mapping], [0, 0, 0])
        self.assertEqual(text.count("This is repeated"), 2)

    def test_rolling_copy_preserves_different_case_and_punctuation(self):
        cues = [{"start_seconds": 0, "end_seconds": 2, "text": "One two three"},
                {"start_seconds": 2, "end_seconds": 4, "text": "one two three."}]
        _, mapping = rolling_reading_copy(cues)
        self.assertEqual(mapping[1]["removed_exact_prefix_tokens"], 0)

    def test_rolling_copy_preserves_repeat_after_ten_millisecond_gap(self):
        cues = [{"start_seconds": 0, "end_seconds": 2, "text": "This is repeated"},
                {"start_seconds": 2.01, "end_seconds": 4, "text": "This is repeated"}]
        _, mapping = rolling_reading_copy(cues)
        self.assertEqual(mapping[1]["removed_exact_prefix_tokens"], 0)

    def test_memory_measurement_is_optional_and_units_are_explicit(self):
        self.assertEqual(normalise_maxrss_kib(2048, "darwin"), 2)
        self.assertEqual(normalise_maxrss_kib(2048, "linux"), 2048)
        with patch("ingest_video.resource", None):
            self.assertIsNone(peak_rss_kib())

    def test_metadata_only_run_has_no_fabricated_transcript_or_clips(self):
        path = self.fixture("synthetic-metadata.json", json.dumps({"video_id": "TEST_ONLY", "title": "Synthetic test fixture", "channel_id": "TEST_CHANNEL", "source_url": "https://example.invalid/test", "duration_seconds": 10}))
        output = self.root / "out"
        self.assertEqual(main(["--metadata", str(path), "--output-dir", str(output)]), 0)
        record = json.loads((output / "catalogue-record.json").read_text())
        self.assertEqual(record["review"]["status"], "blocked_no_transcript_or_media")
        self.assertEqual(record["excerpt_candidates"], [])
        self.assertFalse((output / "transcript.txt").exists())
        self.assertFalse(record["review"]["audio_listening_performed"])

    def test_end_to_end_caption_ingestion_remains_unreviewed(self):
        metadata = self.fixture("synthetic-metadata.json", json.dumps({"video_id": "TEST_ONLY", "title": "Synthetic test fixture", "channel_id": "TEST_CHANNEL", "source_url": "https://example.invalid/test", "duration_seconds": 10}))
        captions = self.fixture("synthetic.vtt", "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nTest fixture only.\n")
        output = self.root / "captions-out"
        self.assertEqual(main(["--metadata", str(metadata), "--captions", str(captions), "--caption-origin", "youtube_auto", "--output-dir", str(output)]), 0)
        record = json.loads((output / "catalogue-record.json").read_text())
        self.assertEqual(record["review"]["caption_origin"], "youtube_auto")
        self.assertFalse(record["review"]["manual_transcript_correction_performed"])
        self.assertEqual(parse_captions(output / "captions.vtt"), parse_captions(captions))

    def test_stale_caption_outputs_are_not_relabelled_as_new_run(self):
        metadata = self.fixture("synthetic-metadata.json", json.dumps({"video_id": "TEST_ONLY", "title": "Synthetic test fixture", "channel_id": "TEST_CHANNEL", "source_url": "https://example.invalid/test", "duration_seconds": 10}))
        output = self.root / "stale-out"
        output.mkdir()
        (output / "transcript.txt").write_text("Old synthetic fixture")
        with self.assertRaisesRegex(ValueError, "stale"):
            main(["--metadata", str(metadata), "--output-dir", str(output)])

    def test_metadata_only_previous_run_is_not_silently_overwritten(self):
        metadata = self.fixture("synthetic-metadata.json", json.dumps({"video_id": "TEST_ONLY", "title": "Synthetic test fixture", "channel_id": "TEST_CHANNEL", "source_url": "https://example.invalid/test", "duration_seconds": 10}))
        output = self.root / "metadata-only-out"
        main(["--metadata", str(metadata), "--output-dir", str(output)])
        before = (output / "catalogue-record.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "new empty"):
            main(["--metadata", str(metadata), "--output-dir", str(output)])
        self.assertEqual((output / "catalogue-record.json").read_bytes(), before)

    def test_non_ascii_source_title_survives_utf8_roundtrip(self):
        title = "Synthetic fixture 陳信宏"
        metadata = self.fixture("unicode-metadata.json", json.dumps({"video_id": "TEST_ONLY", "title": title, "channel_id": "TEST_CHANNEL", "source_url": "https://example.invalid/test", "duration_seconds": 10}, ensure_ascii=False))
        output = self.root / "unicode-out"
        main(["--metadata", str(metadata), "--output-dir", str(output)])
        self.assertEqual(json.loads((output / "catalogue-record.json").read_text(encoding="utf-8"))["title"], title)

    def test_nan_media_duration_is_rejected(self):
        metadata = self.fixture("synthetic-metadata.json", json.dumps({"video_id": "TEST_ONLY", "title": "Synthetic test fixture", "channel_id": "TEST_CHANNEL", "source_url": "https://example.invalid/test", "duration_seconds": 10}))
        media = self.fixture("synthetic-media.txt", "Not real media; ffprobe is mocked for this validation test.")
        with patch("ingest_video.media_probe", return_value={"format": {"duration": "NaN"}}):
            with self.assertRaisesRegex(ValueError, "valid duration"):
                main(["--metadata", str(metadata), "--media", str(media), "--output-dir", str(self.root / "nan-out")])


if __name__ == "__main__":
    unittest.main()
