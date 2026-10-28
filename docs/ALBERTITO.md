# Albertito: a little life of inquiry

Albertito is a fictional scholarly companion in Albert Tan's profile header.
He keeps the original navy sky and gold constellation, carries a book, blinks,
breathes and changes his expression. His energy, curiosity, joy and growth are
game values. They do not describe Albert's actual mood, availability, health,
research output or academic standing.

## What makes him persistent

The image has two kinds of change. Self-contained SVG animation supplies the
small movements while you view it. A Python program maintains saved game state
in [persona.json](../data/persona.json) and regenerates the image when the
companion workflow runs. Reloading the page does not reset his age or growth.

His fictional daily routine uses **Asia/Singapore** time. The workflow is
scheduled for **07:17, 13:17, 19:17 and 22:17** each day. Scheduled runs update
the saved snapshot; they do not create a continuously connected game session.
The displayed update time identifies the snapshot you are seeing.

GitHub may delay scheduled runs and cache an older image. The workflow must be
on the default branch, and repository Actions must be enabled. Public-repository
schedules can be disabled after 60 days without repository activity. These
constraints are documented in GitHub's [workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
and [image-cache guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-anonymized-urls).

## Care controls

Open [Albertito companion in Actions](https://github.com/Albertito-AI/Albertito-AI/actions/workflows/persona.yml),
choose **Run workflow**, keep the branch set to **main**, and choose an action.
The controls become available after the workflow is merged into the default
branch. GitHub requires repository write access to run them, as explained in
its [manual workflow instructions](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

| Action | Meaning |
| --- | --- |
| `tick` | Refresh the saved state and Singapore routine without awarding experience. |
| `feed` | Feed an idea: replenish curiosity and a little energy and joy. |
| `study` | Spend some energy exploring an idea and earn a care experience point. |
| `play` | Add joy and curiosity while spending a little energy. |
| `rest` | Replenish energy and settle into a resting appearance. |

Accepted care actions share a **15-minute cooldown** and each earns one game
experience point. Rerunning an old workflow does not repeat its reward. If a
care request arrives during the cooldown, wait for it to expire and start a
**new** workflow run; replaying the rejected run will not apply it later. The
growth stages are **Spark** (0–3 points), **Reader** (4–11), **Scholar** (12–29)
and **Sage** (30 or more). These are playful titles for the character.

At night, from **22:00 to 06:59 Singapore time**, he rests. By day, a recent
study, play or rest action can determine his expression for up to six hours.
Otherwise he is curious, with a resting appearance when his energy is low.
Time gradually changes his game values, and automatic recovery keeps neglect
from killing him. You can return after a break without losing his growth.

Visitors see the saved character and can read this guide. The banner itself
does not contain clickable game controls. GitHub sanitizes README HTML and SVG
images run without ordinary JavaScript interaction; see [GitHub Markup](https://github.com/github/markup),
[SVG image restrictions](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image)
and the [SVG processing modes](https://www.w3.org/TR/SVG/conform.html).
An immediately interactive visitor game would require a linked web application.

## Motion and access

The image includes alternative text, an SVG title and a description. It respects
the browser's `prefers-reduced-motion` setting. A separate [still image](../assets/research-header-static.svg)
disables animation regardless of that preference. All controls and explanatory
text also appear as ordinary links outside the image.

## Maintaining the companion

| File | Purpose |
| --- | --- |
| [persona-template.svg](../assets/persona-template.svg) | Editable original vector design and motion. |
| [persona.json](../data/persona.json) | Saved game values, birth time, care history and update time. |
| [update_persona.py](../scripts/update_persona.py) | Standard-library state transitions and escaped SVG rendering. |
| [persona.yml](../.github/workflows/persona.yml) | Scheduled and manual updates. |
| [test_persona.py](../tests/test_persona.py) | Tests for the clock, state, replay and rendering rules. |

Run the repository checks with Python 3.12 or later:

```bash
python -m unittest discover -s tests -v
python scripts/update_persona.py --check
python scripts/validate_profile.py
```

To regenerate a local working copy after editing the template:

```bash
python scripts/update_persona.py --action tick
```

The program uses the operating system's time-zone database. Windows installations
without IANA time-zone data may need the Python `tzdata` package. The configured
GitHub runner already supplies the database.

Only the workflow update job receives `contents: write`. It uses GitHub's
built-in short-lived workflow token, and needs no separately configured API key,
external service, model call, visitor tracking or paid hosting. It commits only
the state file and the two generated images. Existing profile text and the
substantive profile-update date are outside its write list. A normal push rejects
a competing change to main. If that happens, a rerun uses the new head. If a
newer companion run has already saved state, the older run is treated as stale;
start a **new** care run to request the action again. No force push or
branch-protection bypass is used. A missing state file is an error: restore it
from Git history to preserve age and growth before running the companion again.

To pause saved-state updates, disable **Albertito companion** in Actions. The
last saved SVG remains visible and its local animation continues; use the still
image as the README image source if you also want to stop motion. To resume,
enable the workflow and run `tick`.

AI assistance: the original character, implementation and checks were prepared
with ChatGPT. The companion is a rule-based simulation; it does not read the
profile visitor's messages or operate as a conversational AI.
