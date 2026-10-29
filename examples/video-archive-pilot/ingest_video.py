#!/usr/bin/env python3
"""Local-only one-video caption/media ingestion. Never downloads or publishes.

The default run records metadata with no invented transcript. Caption text and
timestamps come only from a supplied VTT, SRT, or YouTube JSON3 file. Optional
local media inspection uses an already-installed ffprobe. ASR is not run.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

try:
    import resource
except ImportError:
    resource = None


def normalise_maxrss_kib(value: int | float, platform_name: str) -> int | float:
    return value / 1024 if platform_name == "darwin" else value


def peak_rss_kib(children: bool = False) -> int | float | None:
    if resource is None:
        return None
    who = resource.RUSAGE_CHILDREN if children else resource.RUSAGE_SELF
    return normalise_maxrss_kib(resource.getrusage(who).ru_maxrss, sys.platform)


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_local_file(value: str | Path) -> Path:
    if "://" in str(value):
        raise ValueError("Only local files are accepted; no network retrieval occurs.")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"Local input file does not exist: {path.name}")
    return path


def parse_time(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"Invalid caption timestamp: {value}")
    numbers = [float(part) for part in parts]
    if any(not math.isfinite(n) or n < 0 for n in numbers):
        raise ValueError("Caption times must be finite and non-negative.")
    if numbers[-1] >= 60 or (len(numbers) == 3 and numbers[-2] >= 60):
        raise ValueError("Caption timestamp has an invalid minute/second field.")
    return sum(number * factor for number, factor in zip(numbers[::-1], (1, 60, 3600)))


def clean_caption(text: str) -> str:
    # Remove VTT presentation/voice tags and inline timestamps, not spoken words.
    text = re.sub(r"<[^>]*>", "", text)
    return " ".join(html.unescape(text).split())


def parse_captions(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8-sig")
    cues = []
    if not raw.strip():
        raise ValueError("Caption input is empty; an empty HTTP response is not a transcript.")
    if path.suffix.lower() == ".json":
        document = json.loads(raw)
        if not isinstance(document, dict) or "events" not in document:
            raise ValueError("JSON caption input must be a YouTube JSON3 event document.")
        for event in document["events"]:
            text = clean_caption("".join(seg.get("utf8", "") for seg in event.get("segs", [])))
            if not text:
                continue
            if "tStartMs" not in event or "dDurationMs" not in event:
                raise ValueError("Spoken JSON3 events must include source start and duration.")
            start = float(event["tStartMs"]) / 1000
            end = start + float(event["dDurationMs"]) / 1000
            cues.append({"start_seconds": start, "end_seconds": end, "text": text})
    elif path.suffix.lower() in (".vtt", ".srt"):
        lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith(("NOTE", "STYLE", "REGION")):
                i += 1
                while i < len(lines) and lines[i].strip():
                    i += 1
                continue
            if "-->" not in line:
                i += 1
                continue
            start_text, end_text = line.split("-->", 1)
            start, end = parse_time(start_text.strip()), parse_time(end_text.strip().split()[0])
            i += 1
            content = []
            while i < len(lines) and lines[i] != "":
                content.append(lines[i])
                i += 1
            text = clean_caption(" ".join(content))
            if text:
                cues.append({"start_seconds": start, "end_seconds": end, "text": text})
    else:
        raise ValueError("Supported caption files: .vtt, .srt and YouTube JSON3 .json.")
    if not cues:
        raise ValueError("No non-empty timed caption cues were found.")
    validate_cues(cues)
    return cues


def validate_cues(cues: list[dict], video_duration: float | None = None) -> None:
    previous_start = -1.0
    for cue in cues:
        start, end = cue["start_seconds"], cue["end_seconds"]
        if not all(math.isfinite(n) for n in (start, end)) or start < 0 or end <= start:
            raise ValueError("Caption end must be greater than a finite, non-negative start.")
        if start < previous_start:
            raise ValueError("Source caption cues are not in chronological order.")
        if video_duration is not None and end > video_duration + 2:
            raise ValueError("Caption timestamps exceed the source video duration.")
        previous_start = start


def vtt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


def readable_transcript(cues: list[dict]) -> str:
    # Preserve every cue. Rolling-caption duplicates are deliberately not guessed
    # away because that can silently delete genuine repeated speech.
    return "\n".join(f"[{vtt_time(c['start_seconds'])}] {c['text']}" for c in cues) + "\n"


def rolling_reading_copy(cues: list[dict]) -> tuple[str, list[dict]]:
    """A separate display copy; exact overlap only, with an auditable cue map.

    Remove at least three matching suffix/prefix tokens only when consecutive
    display cues touch or overlap. Gaps and shorter repeats are preserved. This
    is not speech correction and the original cue list is never modified.
    """
    mapping = []
    previous = None
    for index, cue in enumerate(cues):
        words = cue["text"].split()
        overlap = 0
        if previous and cue["start_seconds"] <= previous["end_seconds"]:
            before = previous["text"].split()
            for size in range(min(len(before), len(words)), 2, -1):
                if before[-size:] == words[:size]:
                    overlap = size
                    break
        mapping.append({"source_cue_index_zero_based": index,
                        "source_start_seconds": cue["start_seconds"],
                        "source_end_seconds": cue["end_seconds"],
                        "removed_exact_prefix_tokens": overlap,
                        "kept_text": " ".join(words[overlap:])})
        previous = cue
    paragraphs = []
    paragraph = []
    start = None
    for entry in mapping:
        if not entry["kept_text"]:
            continue
        if start is None:
            start = entry["source_start_seconds"]
        if paragraph and entry["source_start_seconds"] - start >= 25:
            paragraphs.append(f"[{vtt_time(start)}] " + " ".join(paragraph))
            paragraph = []
            start = entry["source_start_seconds"]
        paragraph.append(entry["kept_text"])
    if paragraph:
        paragraphs.append(f"[{vtt_time(start)}] " + " ".join(paragraph))
    return ("DERIVED READING COPY: unreviewed source captions.\n"
            "Exact adjacent rolling overlap removed; source cues and mapping are retained.\n"
            "Not audio-corrected. Paragraph timestamps identify source display cues.\n\n"
            + "\n\n".join(paragraphs) + "\n"), mapping


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def media_probe(path: Path) -> dict:
    binary = shutil.which("ffprobe")
    if not binary:
        raise ValueError("ffprobe is not installed. No installation will be attempted.")
    result = subprocess.run(
        [binary, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    return json.loads(result.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--captions")
    parser.add_argument("--caption-origin", choices=("creator_supplied", "youtube_auto", "unknown"), default="unknown")
    parser.add_argument("--media")
    args = parser.parse_args(argv)
    started = time.monotonic()
    metadata_path = read_local_file(args.metadata)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    for field in ("video_id", "title", "channel_id", "source_url", "duration_seconds"):
        if not metadata.get(field):
            raise ValueError(f"Missing required source metadata field: {field}")
    duration = float(metadata["duration_seconds"])
    if not math.isfinite(duration) or not 0 < duration <= 600:
        raise ValueError("This bounded pilot accepts one source of no more than 600 seconds.")
    output = Path(args.output_dir).resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Use a new empty output directory; stale outputs will not be overwritten or relabelled.")
    output.mkdir(parents=True, exist_ok=True)
    evidence = [{"role": "source_metadata", "path": metadata_path.name, "sha256": sha256(metadata_path)}]
    media = None
    if args.media:
        media = read_local_file(args.media)
        probe = media_probe(media)
        actual_duration = float(probe.get("format", {}).get("duration", 0))
        if not math.isfinite(actual_duration) or actual_duration <= 0 or actual_duration > 602:
            raise ValueError("Local media must have a valid duration within the ten-minute pilot bound.")
        if abs(actual_duration - duration) > 3:
            raise ValueError("Local media duration does not match the selected source. Verify identity before processing.")
        write_json(output / "media-probe.json", probe)
        evidence.append({"role": "local_media", "path": media.name, "sha256": sha256(media),
                         "identity_status": "user_supplied_identity_not_content_verified"})
    cues, origin = [], None
    if args.captions:
        captions = read_local_file(args.captions)
        cues = parse_captions(captions)
        origin = args.caption_origin
        evidence.append({"role": "source_captions", "path": captions.name, "sha256": sha256(captions),
                         "identity_status": "user_supplied_identity_not_content_verified"})
    if cues:
        validate_cues(cues, duration)
        write_json(output / "cues.json", cues)
        (output / "transcript.txt").write_text(readable_transcript(cues), encoding="utf-8")
        reading, cue_map = rolling_reading_copy(cues)
        (output / "reading-transcript.txt").write_text(reading, encoding="utf-8")
        write_json(output / "reading-cue-map.json", cue_map)
        blocks = [f"{vtt_time(c['start_seconds'])} --> {vtt_time(c['end_seconds'])}\n{c['text']}" for c in cues]
        (output / "captions.vtt").write_text("WEBVTT\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")
    status = "unreviewed_captions_available" if cues else "blocked_no_transcript_or_media"
    review = {"status": status, "caption_origin": origin, "audio_listening_performed": False,
              "manual_transcript_correction_performed": False, "claim_verification_performed": False,
              "asr_run": None, "source_caption_cue_count": len(cues),
              "source_last_cue_end_seconds": cues[-1]["end_seconds"] if cues else None,
              "completeness_verified": False,
              "note": "Source text and timing are preserved; formatting conversion is not factual or listening review.",
              "reading_copy_transformation": "Separate file removes exact suffix/prefix overlap of at least three tokens between touching/overlapping adjacent display cues. Original cues and every transformation map are retained."}
    record = {**metadata, "review": review,
              "chapters": [], "excerpt_candidates": [],
              "chapters_and_excerpts_status": "pending_review_of_real_transcript_and_audio",
              "publication_status": "local_only_not_published"}
    write_json(output / "catalogue-record.json", record)
    write_json(output / "chapter-excerpt-review.json", {
        "video_id": metadata["video_id"], "status": record["chapters_and_excerpts_status"],
        "chapters": [], "excerpt_candidates": [],
        "reason": "No chapter title, quotation or clip boundary is inferred from the video title alone.",
        "required_review": ["Check spoken words against source audio", "Verify surrounding context",
                            "Check excerpt start/end against real playback", "Keep NotebookLM/source disclosures"],
    })
    run = {"started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - (time.monotonic() - started))),
           "elapsed_seconds": round(time.monotonic() - started, 6),
           "process_peak_rss_kib": peak_rss_kib(),
           "peak_child_rss_kib": peak_rss_kib(children=True),
           "memory_measurement_available": resource is not None,
           "measurement_scope": "This local ingestion process only, excluding research and earlier retrieval attempts.",
           "paid_api_calls": 0, "downloads_performed_by_ingestion": 0,
           "publication_actions": 0, "input_evidence": evidence,
           "output_files": [{"name": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)}
                            for p in sorted(output.iterdir()) if p.is_file()]}
    write_json(output / "run-receipt.json", run)
    print(json.dumps({"status": status, "cue_count": len(cues),
                      "elapsed_seconds": run["elapsed_seconds"],
                      "process_peak_rss_kib": run["process_peak_rss_kib"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"Ingestion stopped: {exc}")
