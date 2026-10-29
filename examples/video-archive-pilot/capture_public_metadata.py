#!/usr/bin/env python3
"""Extract one video's observed public metadata from an existing watch-page file.

No network calls, page JavaScript execution, account credentials or publication.
The page hash and observed fields are retained. Signed playback/caption URLs and
visitor identifiers are deliberately excluded from the resulting metadata.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re


def extract_page(path: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    match = re.search(r"(?:var\s+)?ytInitialPlayerResponse\s*=\s*", text)
    if not match:
        raise ValueError("No embedded player response was found in this source page.")
    response, _ = json.JSONDecoder().raw_decode(text[match.end():])
    details = response.get("videoDetails", {})
    microformat = response.get("microformat", {}).get("playerMicroformatRenderer", {})
    tracks = response.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    video_id = details.get("videoId")
    if not video_id or not details.get("channelId"):
        raise ValueError("Source page lacks a video identity and channel identity.")
    return {
        "video_id": video_id,
        "title": details.get("title"),
        "source_url": f"https://www.youtube.com/watch?v={video_id}",
        "channel_id": details.get("channelId"),
        "channel_name": details.get("author"),
        "channel_url": microformat.get("ownerProfileUrl", "").replace("http://", "https://"),
        "duration_seconds": int(details.get("lengthSeconds", 0)),
        "published_at_as_reported": microformat.get("publishDate"),
        "category_as_reported": microformat.get("category"),
        "description_sha256": hashlib.sha256(details.get("shortDescription", "").encode("utf-8")).hexdigest(),
        "notebooklm_assistance_disclosed": "Google NotebookLM" in details.get("shortDescription", ""),
        "rights_notice_present": "All rights reserved" in details.get("shortDescription", ""),
        "third_party_materials_notice_present": "third-party frameworks or materials" in details.get("shortDescription", ""),
        "keywords_as_reported": details.get("keywords", []),
        "playability_status_as_reported": response.get("playabilityStatus", {}).get("status"),
        "caption_tracks_advertised": [
            {"language_code": track.get("languageCode"), "kind": track.get("kind"),
             "name": track.get("name", {}).get("simpleText")}
            for track in tracks
        ],
        "source_watch_page_sha256": hashlib.sha256(raw).hexdigest(),
        "metadata_review_status": "public_player_metadata_only_no_audio_review",
        "content_language_verified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch-page", required=True)
    parser.add_argument("--expected-video-id", required=True)
    parser.add_argument("--expected-channel-id", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    metadata = extract_page(Path(args.watch_page))
    if metadata["video_id"] != args.expected_video_id or metadata["channel_id"] != args.expected_channel_id:
        raise SystemExit("Source identity mismatch; refusing to use a different video/channel.")
    metadata["observed_at_utc"] = args.observed_at
    Path(args.output).write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"video_id": metadata["video_id"], "duration_seconds": metadata["duration_seconds"],
                      "caption_tracks_advertised": metadata["caption_tracks_advertised"]}))


if __name__ == "__main__":
    main()
