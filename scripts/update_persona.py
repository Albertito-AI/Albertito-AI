"""Update Sparks' fictional state and render self-contained profile images.

Only the Python standard library is used. No activity, visitor or private data
is collected; the numbers describe a game, not Albert Tan's real life.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import escape
import json
import math
from pathlib import Path
import re
import sys
from typing import Literal
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
SINGAPORE = ZoneInfo("Asia/Singapore")
ACTIONS = ("tick", "feed", "study", "play", "rest")
CARE_COOLDOWN = timedelta(minutes=15)
MOOD_DURATION = timedelta(hours=6)
MAX_COUNTER = 1_000_000_000
SCHEMA_VERSION = 2
PERSONA_NAME = "Sparks"
STATE_KEYS = {
    "schema_version", "name", "born_at", "updated_at", "stats", "xp",
    "care_count", "last_action", "last_action_at", "last_workflow_run_id",
}
THOUGHTS = {
    "curious": "What would count as good evidence?",
    "studying": "One page. One question. A little more light.",
    "playful": "A little play makes room for new ideas.",
    "resting": "Even good questions need a little sleep.",
}
EFFECTS = {
    "feed": {"energy": 8, "curiosity": 22, "joy": 5},
    "study": {"energy": -12, "curiosity": 12, "joy": 4},
    "play": {"energy": -8, "curiosity": 5, "joy": 24},
    "rest": {"energy": 25, "curiosity": -3, "joy": 8},
}
ACCEPTED_MESSAGES = {
    "feed": "Thank you. That gives me something new to think about.",
    "study": "Thank you. Let's work through a question together.",
    "play": "Thank you. A little play sounds lovely.",
    "rest": "Thank you. I'll take a little rest.",
}


def parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamps must be timezone-aware ISO 8601 strings")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid ISO 8601 timestamp: {value!r}") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamps must include an explicit timezone")
    return result.astimezone(UTC)


def timestamp(now: datetime) -> str:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("the clock must include an explicit timezone")
    return now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def initial_state(now: datetime) -> dict:
    stamp = timestamp(now)
    return {
        "schema_version": SCHEMA_VERSION,
        "name": PERSONA_NAME,
        "born_at": stamp,
        "updated_at": stamp,
        "stats": {"energy": 80.0, "curiosity": 75.0, "joy": 80.0},
        "xp": 0,
        "care_count": 0,
        "last_action": None,
        "last_action_at": None,
        "last_workflow_run_id": 0,
    }


def _validate_state(state: dict, version: int, name: str) -> None:
    if not isinstance(state, dict) or set(state) != STATE_KEYS:
        raise ValueError(f"state fields do not match schema version {version}")
    if type(state["schema_version"]) is not int or state["schema_version"] != version:
        raise ValueError(f"unsupported state schema version; expected {version}")
    if state["name"] != name:
        raise ValueError(f"state name must be {name}")
    born, updated = parse_time(state["born_at"]), parse_time(state["updated_at"])
    if born > updated:
        raise ValueError("birth timestamp is later than the last update")
    for key in ("xp", "care_count"):
        if type(state[key]) is not int or not 0 <= state[key] <= MAX_COUNTER:
            raise ValueError(f"{key} must be a bounded non-negative integer")
    if state["xp"] != state["care_count"]:
        raise ValueError("XP must equal the number of accepted care actions")
    run_id = state["last_workflow_run_id"]
    if type(run_id) is not int or not 0 <= run_id < 10**30:
        raise ValueError("invalid workflow run watermark")
    stats = state["stats"]
    if not isinstance(stats, dict) or set(stats) != {"energy", "curiosity", "joy"}:
        raise ValueError("state must contain exactly energy, curiosity and joy")
    for key, value in stats.items():
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError(f"{key} must be a finite number from 0 to 100")
    action, action_at = state["last_action"], state["last_action_at"]
    if action is None:
        if action_at is not None or state["care_count"] != 0:
            raise ValueError("uncared-for state has inconsistent care history")
    elif not isinstance(action, str) or action not in EFFECTS or not isinstance(action_at, str):
        raise ValueError("invalid last care action")
    elif not born <= parse_time(action_at) <= updated or state["care_count"] == 0:
        raise ValueError("last care timestamp is inconsistent with the state")


def validate_state(state: dict) -> None:
    """Require the canonical Sparks state, without implicitly migrating it."""
    _validate_state(state, SCHEMA_VERSION, PERSONA_NAME)


def migrate_state(state: dict) -> dict:
    """Rename a strictly valid legacy pet while preserving its complete history."""
    if isinstance(state, dict) and state.get("schema_version") == 1:
        _validate_state(state, 1, "Albertito")
        migrated = deepcopy(state)
        migrated["schema_version"] = SCHEMA_VERSION
        migrated["name"] = PERSONA_NAME
        validate_state(migrated)
        return migrated
    validate_state(state)
    return deepcopy(state)


def _energy_segment(energy: float, start: datetime, end: datetime) -> float:
    """Integrate at most one Singapore day, splitting at 07:00 and 22:00."""
    cursor = start
    while cursor < end:
        local = cursor.astimezone(SINGAPORE)
        daytime = 7 <= local.hour < 22
        if daytime:
            boundary = local.replace(hour=22, minute=0, second=0, microsecond=0)
        else:
            boundary = local.replace(hour=7, minute=0, second=0, microsecond=0)
            if local.hour >= 22:
                boundary += timedelta(days=1)
        stop = min(end, boundary.astimezone(UTC))
        hours = (stop - cursor).total_seconds() / 3600
        target = 65.0 if daytime else 90.0
        energy = target + (energy - target) * math.exp(-hours / 12)
        cursor = stop
    return energy


def energy_after(energy: float, start: datetime, end: datetime) -> float:
    """Closed-form full days make even years of absence cheap to calculate."""
    if end < start:
        raise ValueError("clock moved backwards")
    local = start.astimezone(SINGAPORE)
    morning = local.replace(hour=7, minute=0, second=0, microsecond=0)
    if local > morning:
        morning += timedelta(days=1)
    aligned = min(end, morning.astimezone(UTC))
    energy = _energy_segment(energy, start, aligned)
    full_days = (end - aligned).days
    if full_days:
        day_decay, night_decay = math.exp(-15 / 12), math.exp(-9 / 12)
        daily_decay = day_decay * night_decay
        daily_offset = 65 * (1 - day_decay) * night_decay + 90 * (1 - night_decay)
        equilibrium = daily_offset / (1 - daily_decay)
        energy = equilibrium + (energy - equilibrium) * daily_decay**full_days
        aligned += timedelta(days=full_days)
    return _energy_segment(energy, aligned, end)


def workflow_id(event_id: str | None) -> int | None:
    if event_id is None:
        return None
    if not re.fullmatch(r"actions:[1-9][0-9]{0,28}", event_id):
        raise ValueError("event ID must have the form actions:<positive workflow run ID>")
    return int(event_id.split(":", 1)[1])


@dataclass(frozen=True)
class UpdateResult:
    state: dict
    message: str
    is_noop: bool = False
    accepted: bool = False
    reason: Literal["accepted", "cooldown", "satisfied", "too_tired", "tick", "replayed"] = "tick"


def _care_refusal(stats: dict, action: str) -> tuple[str, str] | None:
    # Tiredness has priority when study would be both tiring and unnecessary.
    if action == "study" and stats["energy"] < 30:
        return "too_tired", "Thanks, I am too tired to study. A little rest would help."
    if action == "feed" and stats["curiosity"] >= 85:
        return "satisfied", "Thanks, I have enough ideas for now."
    if action == "play" and stats["joy"] >= 85:
        return "satisfied", "Thanks, I have had enough play for now."
    if action == "rest" and stats["energy"] >= 90:
        return "satisfied", "Thanks, I am already well rested."
    if action == "study" and stats["curiosity"] >= 90:
        return "satisfied", "Thanks, I have enough to study for now."
    return None


def advance(state: dict, now: datetime, action: str = "tick", event_id: str | None = None) -> UpdateResult:
    validate_state(state)
    if action not in ACTIONS:
        raise ValueError(f"unsupported action: {action!r}")
    now = parse_time(timestamp(now))
    previous = parse_time(state["updated_at"])
    if now < previous:
        raise ValueError("clock moved backwards; refusing to alter the saved state")
    run_id = workflow_id(event_id)
    if run_id is not None and run_id <= state["last_workflow_run_id"]:
        return UpdateResult(deepcopy(state), "Previously processed or stale workflow run; no change.", is_noop=True, reason="replayed")

    result = deepcopy(state)
    hours = (now - previous).total_seconds() / 3600
    if hours:
        result["stats"]["energy"] = energy_after(state["stats"]["energy"], previous, now)
        result["stats"]["curiosity"] = max(20.0, state["stats"]["curiosity"] - 0.5 * hours)
        result["stats"]["joy"] = max(20.0, state["stats"]["joy"] - 0.4 * hours)
    result["updated_at"] = timestamp(now)
    if run_id is not None:
        result["last_workflow_run_id"] = run_id

    message = "Routine updated."
    accepted = False
    reason = "tick"
    last_care = parse_time(state["last_action_at"]) if state["last_action_at"] else None
    refusal = _care_refusal(result["stats"], action)
    if refusal is not None:
        reason, message = refusal
    elif action != "tick" and last_care and now - last_care < CARE_COOLDOWN:
        remaining = math.ceil((CARE_COOLDOWN - (now - last_care)).total_seconds() / 60)
        reason = "cooldown"
        if run_id is None:
            message = f"Thanks, please give me another {remaining} minute(s) before more care."
        else:
            message = f"Care cooldown: start a new workflow run in {remaining} minute(s). Routine updated."
    elif action != "tick":
        for key, delta in EFFECTS[action].items():
            result["stats"][key] = min(100.0, max(0.0, result["stats"][key] + delta))
        result["xp"] = min(MAX_COUNTER, state["xp"] + 1)
        result["care_count"] = result["xp"]
        result["last_action"] = action
        result["last_action_at"] = timestamp(now)
        message = ACCEPTED_MESSAGES[action]
        accepted = True
        reason = "accepted"
    validate_state(result)
    return UpdateResult(result, message, accepted=accepted, reason=reason)


def mode_for(state: dict) -> str:
    now = parse_time(state["updated_at"])
    if now.astimezone(SINGAPORE).hour >= 22 or now.astimezone(SINGAPORE).hour < 7:
        return "resting"
    if state["stats"]["energy"] < 25:
        return "resting"
    if state["last_action_at"] and now - parse_time(state["last_action_at"]) < MOOD_DURATION:
        return {"study": "studying", "play": "playful", "rest": "resting", "feed": "curious"}[state["last_action"]]
    return "curious"


def view_values(state: dict) -> dict[str, str]:
    validate_state(state)
    now = parse_time(state["updated_at"])
    local = now.astimezone(SINGAPORE)
    mode = mode_for(state)
    xp = state["xp"]
    stage = "Spark" if xp < 4 else "Reader" if xp < 12 else "Scholar" if xp < 30 else "Sage"
    # Explicit month names keep output independent of the runner's locale.
    month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[local.month - 1]
    values = {
        "mode": mode,
        "stage": stage,
        "age_days": str((now - parse_time(state["born_at"])).days),
        "thought": THOUGHTS[mode],
        "updated_at": f"{local.day:02d} {month} {local.year} · {local:%H:%M} SGT",
    }
    for key, number in state["stats"].items():
        values[key] = str(round(number))
        values[f"{key}_width"] = f"{number:.2f}".rstrip("0").rstrip(".")
    return values


def render_template(template: str, values: dict[str, str]) -> str:
    def substitute(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise ValueError(f"unknown SVG placeholder: {key}")
        return escape(str(values[key]), quote=True)

    rendered = re.sub(r"\{\{([a-z_]+)\}\}", substitute, template)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("unresolved SVG template placeholder")
    try:
        root = ET.fromstring(rendered)
    except ET.ParseError as exc:
        raise ValueError(f"rendered SVG is invalid: {exc}") from exc
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("template must be a namespaced SVG image")
    return rendered


def render_outputs(state: dict, template: str) -> dict[str, str]:
    animated = render_template(template, view_values(state))
    if "</svg>" not in animated:
        raise ValueError("template requires an explicit closing SVG tag")
    static_rule = "  <style>*, *::before, *::after { animation: none !important; transition: none !important; }</style>\n"
    head, tail = animated.rsplit("</svg>", 1)
    static = head + static_rule + "</svg>" + tail
    return {"assets/research-header.svg": animated, "assets/research-header-static.svg": static}


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=ACTIONS, default="tick")
    parser.add_argument("--event-id", help="Use actions:<workflow run ID> to ignore repeated or older runs.")
    parser.add_argument("--now", help="Timezone-aware ISO 8601 clock, for reproducible local checks.")
    parser.add_argument("--check", action="store_true", help="Check saved state and image consistency without writing or advancing time.")
    args = parser.parse_args(argv)
    if args.check and (args.action != "tick" or args.event_id or args.now):
        parser.error("--check cannot be combined with an action, event ID or clock override")
    try:
        state_path = root / "data/persona.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if args.check:
                validate_state(state)
            else:
                state = migrate_state(state)
        else:
            raise ValueError("saved state data/persona.json is missing; restore it from Git history before updating")
        message = "Saved state and both images are consistent."
        if not args.check:
            clock = parse_time(args.now) if args.now else datetime.now(UTC)
            result = advance(state, clock, args.action, args.event_id)
            if result.is_noop:
                print(result.message)
                return 0
            state, message = result.state, result.message
        template = (root / "assets/persona-template.svg").read_text(encoding="utf-8")
        outputs = render_outputs(state, template)
        if args.check:
            for relative, expected in outputs.items():
                path = root / relative
                if not path.exists() or path.read_text(encoding="utf-8") != expected:
                    raise ValueError(f"generated image is missing or differs from saved state: {relative}")
        else:
            for relative, content in outputs.items():
                _atomic_write(root / relative, content)
            _atomic_write(state_path, json.dumps(state, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        print(message)
        return 0
    except (ValueError, OSError) as exc:
        print(f"Persona update failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
