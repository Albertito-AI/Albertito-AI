# One-video archive pilot

This small local utility turns verified source metadata and an existing caption
file into an auditable catalogue record, preserved cues, VTT captions and a
separate reading copy. It supports an existing creator's video archive. It does
not publish, change a YouTube account, generate engagement, run a background
agent or install software.

The executed pilot used one real video, [Learning with Bert - The Honest
AI](https://www.youtube.com/watch?v=BwHQWbHH-o4). Its English auto-generated
captions were retrieved and processed. The public example retains source
identifiers, hashes and an accurately labelled execution summary. Full captions,
claim-review notes and acquisition evidence belong in the private creator
deliverable, not this repository example.

## Run the self-contained synthetic example

Python 3.11 or newer is sufficient for caption ingestion. No extra Python package
or API credential is required. Run from this example's directory:

```bash
python ingest_video.py --metadata fixtures/synthetic.metadata.json --captions fixtures/synthetic.en.vtt --caption-origin unknown --output-dir build/synthetic-example
python -m unittest discover -s tests -v
```

The fixture is explicitly synthetic. It demonstrates parsing and overlap
handling; it is not the Learning with Bert transcript or a simulated success for
the real video. Use a new output directory for each run so stale captions cannot
be mistaken for fresh results.

The executed pilot ran on Linux. On platforms without Python's optional
`resource` module, memory measurements are recorded as `null`. macOS RSS values
are converted from bytes to KiB. Caption processing itself does not require that
module. Other operating systems have not been exercised in this pilot.

## Use an authorised local caption file

Provide metadata with `video_id`, `title`, `channel_id`, `source_url` and
`duration_seconds`, then pass an existing `.vtt`, `.srt` or YouTube JSON3 `.json`
caption file. This bounded pilot accepts one video of at most ten minutes.
`--caption-origin` records `youtube_auto`, `creator_supplied` or `unknown`; it does
not establish accuracy or ownership. Match the caption file to the source video
before using it.

`capture_public_metadata.py` can extract the selected public fields from an
already retrieved YouTube watch-page HTML file. It checks the expected video and
channel IDs. It does not execute page JavaScript or retain signed media URLs,
visitor identifiers or the full description in the resulting metadata.

Optional `--media LOCAL_FILE` uses an existing `ffprobe` installation to inspect
local media and compare duration with the selected source. Duration matching is
not a content-identity guarantee. The utility does not download a model or run
ASR. The original video already had source captions, so local ASR was unnecessary
in the executed pilot.

## What the outputs mean

| Output | Meaning |
| --- | --- |
| `catalogue-record.json` | Source metadata, caption origin, review status and publication status |
| `cues.json` | All non-empty timed source display cues, in order |
| `captions.vtt` | Formatting conversion of those cues, without factual correction |
| `transcript.txt` | Timed text preserving the source rolling-caption repetitions |
| `reading-transcript.txt` | Separate reading copy with conservative overlap removal |
| `reading-cue-map.json` | Every input cue's timing, overlap count and retained text |
| `chapter-excerpt-review.json` | Empty by default, awaiting evidence-based editorial review |
| `run-receipt.json` | Input hashes and measured local process time/memory |

The reading transformation removes an exact suffix/prefix match of at least
three tokens only when consecutive display cues touch or overlap. Case,
punctuation, short repeats and repeats after a gap are retained. Genuine
immediate repeated speech can still resemble a rolling display. Preserve the
original captions and inspect the mapping when it matters. This transformation
does not correct words against audio, establish factual accuracy or prove
caption completeness. Display-cue timestamps are not guaranteed edit points.

## Executed result and limits

See `pilot_summary.json` for the specific source URL, SHA-256 hashes, 239-cue
result and measured operations. The source captions run from 0.400 to 291.000
seconds. A full audio comparison has not been completed.

The standard source-video retrieval returned small HTML error bodies instead of
media. FFmpeg rejected them. No usable source audio/video or rendered excerpt
was produced. The error bodies were quarantined outside the public package, and
no synthetic substitute was used. A real authorised original/export is needed
before rendering or listening review can continue.

Some narrated research claims require source verification. Candidate chapters
and excerpts remain private drafts with explicit review holds. This example
does not publish those claims as established facts or imply a subscriber-growth
result.

Rendering and durable composition remain the responsibility of the existing
CohortFrame workflow. This utility's handoff consists of the source identity,
caption/provenance hashes, candidate time ranges and review state. No separate
publishing or orchestration layer is introduced.

## Rights, resources and public packaging

Use media and captions you are authorised to process. Software licences do not
grant rights to source media, cited research, voices or other third-party
material. FFmpeg and yt-dlp are optional acquisition/inspection dependencies and
are not redistributed in this example. Their distribution licences differ by
build; the pilot used the installed FFmpeg build and an isolated yt-dlp wheel.

No paid API, paid advertising or new hosted service was used. Measurements come
from this execution environment, not a benchmark of the creator's own computer.
Existing compute, storage, electricity and network resources are still consumed.

Publish only the explicit allowlist in `PUBLIC_ALLOWLIST.txt`. Exclude source
captions, generated transcripts, private review notes, watch-page HTML, yt-dlp
info JSON, error bodies, downloaded dependencies, caches and account analytics.
