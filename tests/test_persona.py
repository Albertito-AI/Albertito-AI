from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import timedelta
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_persona as pet


SIMPLE_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" class="mode-{{mode}}">
<style>@keyframes wave { to { opacity: .5; } } .star { animation: wave 2s infinite; }</style>
<title>{{thought}}</title><text>{{updated_at}}</text>
<rect width="{{energy_width}}"/><text>{{stage}} {{age_days}} {{energy}}</text>
</svg>
'''


class PersonaStateTests(unittest.TestCase):
    def setUp(self):
        self.start = pet.parse_time("2026-10-28T05:00:00Z")  # 13:00 Singapore.
        self.state = pet.initial_state(self.start)

    def test_singapore_day_night_boundaries_in_winter_and_summer(self):
        for month in (1, 7):
            for hour, minute, expected in ((6, 59, "resting"), (7, 0, "curious"), (21, 59, "curious"), (22, 0, "resting")):
                now = pet.parse_time(f"2026-{month:02d}-15T{hour:02d}:{minute:02d}:00+08:00")
                state = pet.initial_state(now)
                with self.subTest(month=month, hour=hour, minute=minute):
                    self.assertEqual(pet.mode_for(state), expected)

    def test_care_mode_expiry_night_priority_and_low_energy_rest(self):
        playing = pet.advance(self.state, self.start, "play").state
        self.assertEqual(pet.mode_for(playing), "playful")
        near_expiry = pet.advance(playing, self.start + timedelta(hours=5, minutes=59)).state
        self.assertEqual(pet.mode_for(near_expiry), "playful")
        expired = pet.advance(playing, self.start + timedelta(hours=6)).state
        self.assertEqual(pet.mode_for(expired), "curious")
        evening = pet.parse_time("2026-10-28T21:00:00+08:00")
        studying = pet.advance(playing, evening, "study").state
        self.assertEqual(pet.mode_for(studying), "studying")
        night = pet.advance(studying, evening + timedelta(hours=1)).state
        self.assertEqual(pet.mode_for(night), "resting")
        self.state["stats"]["energy"] = 24
        self.assertEqual(pet.mode_for(self.state), "resting")

    def test_fifteen_minute_shared_cooldown_and_exact_boundary(self):
        first = pet.advance(self.state, self.start, "feed", "actions:100").state
        blocked = pet.advance(first, self.start + timedelta(minutes=14, seconds=59), "play", "actions:101")
        self.assertIn("cooldown", blocked.message)
        self.assertIn("start a new workflow run", blocked.message)
        self.assertEqual(blocked.state["xp"], 1)
        self.assertEqual(blocked.state["last_action"], "feed")
        accepted = pet.advance(blocked.state, self.start + timedelta(minutes=15), "play", "actions:102")
        self.assertIn("accepted", accepted.message)
        self.assertEqual(accepted.state["xp"], 2)
        self.assertEqual(accepted.state["last_action"], "play")

    def test_repeated_and_older_workflow_runs_cannot_reapply_care(self):
        fed = pet.advance(self.state, self.start, "feed", "actions:12345").state
        for event_id in ("actions:12345", "actions:12344"):
            repeated = pet.advance(fed, self.start + timedelta(days=20), "feed", event_id)
            self.assertEqual(repeated.state, fed)
            self.assertTrue(repeated.is_noop)
            self.assertIn("stale", repeated.message)
        next_run = pet.advance(fed, self.start + timedelta(hours=1), "rest", "actions:12346")
        self.assertEqual(next_run.state["xp"], 2)

    def test_elapsed_time_calculation_is_independent_of_tick_cadence(self):
        start = pet.parse_time("2026-10-28T01:23:45Z")
        initial = pet.initial_state(start)
        final_time = start + timedelta(days=12, hours=17, minutes=31)
        single = pet.advance(initial, final_time).state
        stepped = deepcopy(initial)
        cursor = start
        while cursor < final_time:
            cursor = min(final_time, cursor + timedelta(hours=1, minutes=37))
            stepped = pet.advance(stepped, cursor).state
        for key in initial["stats"]:
            self.assertAlmostEqual(single["stats"][key], stepped["stats"][key], places=9)
        self.assertEqual(single["born_at"], initial["born_at"])

    def test_large_gap_is_finite_bounded_and_recoverable(self):
        self.state["stats"] = {"energy": 0, "curiosity": 0, "joy": 0}
        future = pet.parse_time("2526-10-28T05:00:00Z")
        after = pet.advance(self.state, future).state
        pet.validate_state(after)
        self.assertGreater(after["stats"]["energy"], 25)
        self.assertEqual(after["stats"]["curiosity"], 20)
        self.assertEqual(after["stats"]["joy"], 20)
        fed = pet.advance(after, future, "feed").state
        self.assertGreater(fed["stats"]["curiosity"], 20)
        self.assertEqual(fed["born_at"], self.state["born_at"])

    def test_all_care_effects_are_bounded_and_xp_has_a_finite_ceiling(self):
        for action in pet.EFFECTS:
            for value in (0, 100):
                candidate = deepcopy(self.state)
                candidate["stats"] = dict.fromkeys(candidate["stats"], value)
                result = pet.advance(candidate, self.start, action).state
                self.assertTrue(all(0 <= number <= 100 for number in result["stats"].values()))
        capped = pet.advance(self.state, self.start, "study").state
        capped["xp"] = capped["care_count"] = pet.MAX_COUNTER
        again = pet.advance(capped, self.start + timedelta(minutes=15), "study").state
        self.assertEqual(again["xp"], pet.MAX_COUNTER)

    def test_stages_reflect_care_experience_and_age_uses_elapsed_days(self):
        cared = pet.advance(self.state, self.start, "feed").state
        for xp, stage in ((0, "Spark"), (3, "Spark"), (4, "Reader"), (11, "Reader"), (12, "Scholar"), (29, "Scholar"), (30, "Sage")):
            candidate = deepcopy(cared if xp else self.state)
            candidate["xp"] = candidate["care_count"] = xp
            self.assertEqual(pet.view_values(candidate)["stage"], stage)
        aged = pet.advance(cared, self.start + timedelta(days=2, hours=23)).state
        self.assertEqual(pet.view_values(aged)["age_days"], "2")

    def test_backwards_clock_naive_clock_and_bad_event_id_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "backwards"):
            pet.advance(self.state, self.start - timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, "timezone"):
            pet.advance(self.state, self.start.replace(tzinfo=None))
        for event_id in ("actions:0", "$(touch bad)", "actions:123x"):
            with self.subTest(event_id=event_id), self.assertRaisesRegex(ValueError, "event ID"):
                pet.advance(self.state, self.start, "feed", event_id)

    def test_malformed_or_inconsistent_state_is_rejected(self):
        variants = []
        for key, value in (("schema_version", 2), ("xp", True), ("care_count", -1), ("last_workflow_run_id", -1), ("last_action", [])):
            variant = deepcopy(self.state)
            variant[key] = value
            variants.append(variant)
        for value in (float("nan"), float("inf"), -1, 101, "80", True):
            variant = deepcopy(self.state)
            variant["stats"]["energy"] = value
            variants.append(variant)
        extra = deepcopy(self.state)
        extra["unexpected"] = "data"
        variants.append(extra)
        future_birth = deepcopy(self.state)
        future_birth["born_at"] = "2027-01-01T00:00:00Z"
        variants.append(future_birth)
        missing_zone = deepcopy(self.state)
        missing_zone["updated_at"] = "2026-10-28T05:00:00"
        variants.append(missing_zone)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                pet.validate_state(variant)


class PersonaRenderingTests(unittest.TestCase):
    def setUp(self):
        self.state = pet.initial_state(pet.parse_time("2026-10-28T05:00:00Z"))

    def test_untrusted_render_values_are_xml_escaped(self):
        text = '<script>alert("x")</script> & "quoted"'
        rendered = pet.render_template('<svg xmlns="http://www.w3.org/2000/svg"><text>{{thought}}</text></svg>', {"thought": text})
        root = ET.fromstring(rendered)
        self.assertEqual(len(root), 1)
        self.assertEqual(root[0].text, text)
        self.assertNotIn("<script>", rendered)

    def test_unknown_placeholders_invalid_xml_and_non_svg_are_rejected(self):
        for template in (
            '<svg xmlns="http://www.w3.org/2000/svg">{{unknown}}</svg>',
            '<svg xmlns="http://www.w3.org/2000/svg">{{bad-name}}</svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><text></svg>',
            '<html>not an image</html>',
        ):
            with self.subTest(template=template), self.assertRaises(ValueError):
                pet.render_template(template, pet.view_values(self.state))

    def test_static_output_disables_motion_without_losing_accessible_text(self):
        outputs = pet.render_outputs(self.state, SIMPLE_TEMPLATE)
        static = outputs["assets/research-header-static.svg"]
        self.assertIn("animation: none !important", static)
        self.assertIn("transition: none !important", static)
        self.assertIn("What would count as good evidence?", static)
        ET.fromstring(static)

    def test_check_is_read_only_reproducible_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            (root / "data").mkdir()
            (root / "data/persona.json").write_text(json.dumps(self.state), encoding="utf-8")
            (root / "assets/persona-template.svg").write_text(SIMPLE_TEMPLATE, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pet.main(["--now", "2026-10-28T05:00:00Z"], root=root), 0)
            files = [root / "data/persona.json", root / "assets/research-header.svg", root / "assets/research-header-static.svg"]
            before = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in files}
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pet.main(["--check"], root=root), 0)
                self.assertEqual(pet.main(["--check"], root=root), 0)
            self.assertEqual(before, {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in files})
            files[1].write_text("tampered image", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(pet.main(["--check"], root=root), 1)
            self.assertEqual(files[1].read_text(encoding="utf-8"), "tampered image")

    def test_failing_input_does_not_overwrite_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            (root / "data").mkdir()
            (root / "assets/persona-template.svg").write_text(SIMPLE_TEMPLATE, encoding="utf-8")
            state_file = root / "data/persona.json"
            state_file.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")
            before = state_file.read_bytes()
            with redirect_stderr(io.StringIO()):
                self.assertEqual(pet.main([], root=root), 1)
            self.assertEqual(state_file.read_bytes(), before)
            self.assertFalse((root / "assets/research-header.svg").exists())

    def test_cli_replayed_or_stale_event_does_not_render_or_write_changed_template(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            (root / "data").mkdir()
            (root / "data/persona.json").write_text(json.dumps(self.state), encoding="utf-8")
            template = root / "assets/persona-template.svg"
            template.write_text(SIMPLE_TEMPLATE, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(pet.main([
                    "--action", "feed", "--event-id", "actions:100",
                    "--now", "2026-10-28T05:00:00Z",
                ], root=root), 0)
            files = [root / "data/persona.json", root / "assets/research-header.svg", root / "assets/research-header-static.svg"]
            before = {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in files}
            # A replay must not consume even a newer, incomplete template.
            template.write_text("a changed and currently invalid template", encoding="utf-8")
            for event_id in ("actions:100", "actions:99"):
                output = io.StringIO()
                with self.subTest(event_id=event_id), redirect_stdout(output):
                    self.assertEqual(pet.main([
                        "--action", "feed", "--event-id", event_id,
                        "--now", "2026-11-28T05:00:00Z",
                    ], root=root), 0)
                self.assertIn("no change", output.getvalue())
                self.assertEqual(before, {str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in files})
            self.assertEqual(template.read_text(encoding="utf-8"), "a changed and currently invalid template")

    def test_missing_state_fails_without_recreating_pet_or_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            template = root / "assets/persona-template.svg"
            template.write_text(SIMPLE_TEMPLATE, encoding="utf-8")
            before = template.read_bytes(), template.stat().st_mtime_ns
            error = io.StringIO()
            with redirect_stderr(error):
                self.assertEqual(pet.main([
                    "--action", "feed", "--event-id", "actions:100",
                    "--now", "2026-10-28T05:00:00Z",
                ], root=root), 1)
            self.assertIn("restore it from Git history", error.getvalue())
            self.assertFalse((root / "data/persona.json").exists())
            self.assertFalse((root / "assets/research-header.svg").exists())
            self.assertFalse((root / "assets/research-header-static.svg").exists())
            self.assertEqual(before, (template.read_bytes(), template.stat().st_mtime_ns))


if __name__ == "__main__":
    unittest.main()
