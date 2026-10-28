# Sparks' Dance Floor

[Meet Sparks](SPARKS.md) · [Profile](https://github.com/Albertito-AI)

**[Open the interactive stage](https://albertito-ai.github.io/Albertito-AI/)** · [Full silent video](../assets/sparks-dance.mp4)

The [GitHub profile](https://github.com/Albertito-AI) includes an animated
18-second sampler covering all six routines. It plays as a GIF directly in the
README. A matching still is selected for reduced-motion preferences.

The interactive stage is published from this repository on
[GitHub Pages](https://albertito-ai.github.io/Albertito-AI/). The complete [HTML source](../site/index.html)
is self-contained and can also be downloaded and opened in a browser.

The Dance Floor integrates the supplied Spark's Dance Floor HTML demonstration
with the retro Sparks research companion. It preserves the supplied robot
sprites, six routines, choreography, stage and synthesized beat, and adds links
back to the GitHub profile and care diary.

## Using the interactive stage

Choose a routine to loop it, or choose **Play whole set** to cycle through all six.
**Pause** stops the dance; **Beat off / Beat on** toggles a synthesized drum loop.
Sound starts off. The named songs are inspirations and are not included as audio.

| Routine | Robot interpretation |
| --- | --- |
| Runway hip pop | A hip pop, turn and pose |
| Be OK | A cheerful bounce with robot captions |
| Pumpkinhead illusion | A pumpkin-headed dance |
| Pray For Me slow-mo | A dramatic slow-motion entrance |
| Two Fishes | Deadpan gestures and animated expressions |
| Ramalama costume walk | An approaching walk and costume reveal |

The stage starts paused when the browser requests reduced motion. Visitors can
choose to play it. Turning on reduced motion while the page is open pauses the
dance. The layout adapts to narrow screens, controls work with a keyboard, and
audio pauses when the dance is paused or the tab is hidden.

Dancing is a browser demonstration. GitHub care requests and saved companion
state continue through the profile's Feed, Study, Play and Rest links.

## Inspiration and attribution

The supplied demonstration interprets written descriptions from
[NewEngen's TikTok trend roundup](https://newengen.com/insights/tiktok-trends/),
read on 28 October 2026 and then dated 26 October 2026. The runway routine also
references [NYLON's reporting on JADE's song and the runway appearance](https://www.nylon.com/entertainment/jade-angel-of-my-dreams-victorias-secret-fashion-show-2026).
This is a dated collection, not a continuously updated trend ranking.
The choreography is an original robot interpretation of those descriptions.

The HTML and accompanying notes were supplied by the profile owner. Integration
and verification were AI-assisted. The original sources remain linked from the
page. Google Fonts supplies optional display fonts; system fallbacks remain
available if the fonts cannot load.

## Source and deployment

The complete app is [site/index.html](../site/index.html), with its original PNG
body-part sprites embedded. It runs as a static page with no build step or backend.
The profile GIF and the full silent MP4 are rendered from that same canvas
choreography using [the export script](../scripts/export_sparks_dance.py).
The GIF uses three seconds from each routine; the MP4 contains the full set.
Dimensions, duration, source checksum and output details are recorded in
[the media manifest](../assets/sparks-dance-manifest.json).

The export workflow writes only to a `feat/sparks-dance-profile-*` feature branch.
Review and merge the generated assets through a pull request. If the HTML source
changes, render fresh GIF and MP4 files so the media continues to match the app.

The [Pages workflow](../.github/workflows/sparks-pages.yml) automatically publishes
only `site/` when that directory or the deployment workflow changes on `main`.
It can also be run manually from `main`. After deployment, the workflow checks
that the public HTML matches the committed source.

Browser checks verify actual GIF animation, the still fallback and the public
profile after publication. They also exercise all six routines, setlist cycling, pause, sound controls,
reduced motion, desktop and mobile layouts. Existing profile integrity checks
continue to cover the companion's generated artwork and saved state.
