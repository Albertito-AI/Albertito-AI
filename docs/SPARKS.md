# Sparks: a little life of inquiry

Sparks is a fictional scholarly companion in Albert Tan's profile header.
His approved retro robot design combines charcoal armour, aged bronze and warm
amber lights against the navy sky and gold constellation. Gentle movement and
mode indicators accompany his saved state. His energy, curiosity, joy and growth
are game values. They do not describe Albert's actual mood, availability, health,
research output or academic standing. Renaming him from Albertito preserves his
birth time and care history.

## Anyone can care for Sparks

Anyone signed into GitHub can submit a public care request. Use **Feed an idea**,
**Study**, **Play** or **Rest** beneath the [profile header](../README.md).
Each link opens a prefilled GitHub issue. Keep its title unchanged and click
**Create** to submit the request. Opening the form alone does not act on
Sparks.

A request joins a shared queue. Sparks checks whether he needs that kind of care
and may politely decline. The workflow labels the outcome and closes recognised
care issues; the [care diary](SPARKS_CARE_LOG.md) records the exact response and
decision time. Responses are recorded there, without posting bot comments.
If a request is declined or expires, wait until appropriate and submit a new
request. Reopening or replaying an old request does not earn another reward.

The controls are asynchronous. A workflow run and GitHub's image cache can delay
what you see, so refresh the profile after the outcome is recorded. The image's
update time identifies its saved snapshot. This is one shared companion, so
someone else's accepted care can affect your request.

## A companion with his own needs

Sparks uses explicit game rules. He is a rule-based simulation, without a
language model or an understanding of the text entered into an issue body.
**Feed an idea** is a care action, not a way to teach him the contents of a
message.

| Action | What accepted care does | When Sparks declines for his current needs |
| --- | --- | --- |
| Feed an idea | Adds 22 curiosity, 8 energy and 5 joy. | Curiosity is already at least 85. |
| Study | Adds 12 curiosity and 4 joy, using 12 energy. | Energy is below 30, or curiosity is already at least 90. Tiredness takes priority. |
| Play | Adds 24 joy and 5 curiosity, using 8 energy. | Joy is already at least 85. |
| Rest | Adds 25 energy and 8 joy, using 3 curiosity. | Energy is already at least 90. |

Values stay within 0–100. Elapsed time is applied before Sparks checks his needs,
and those needs are checked before the shared cooldown. The image rounds the
values it displays; decisions use the saved numerical values. For example, when
he already has enough ideas, he responds: “Thanks, I have enough ideas for now.”
A refusal adds no care effect or experience point and does not restart the
cooldown. Ordinary time passage can still change his values.

Accepted care shares a **15-minute cooldown** across visitors and owner controls.
A GitHub account can provide at most **one accepted public care action per hour**.
Owner controls are exempt from that account limit, but the same needs and shared
cooldown still apply. These limits give other visitors a chance to participate.

Each accepted care action earns one game experience point. Growth stages are
**Spark** (0–3 points), **Reader** (4–11), **Scholar** (12–29) and **Sage** (30 or
more). These are playful titles for the character. Scheduled refreshes and
refused or replayed requests earn no points.

## Useful work and persistent knowledge

Sparks also maintains a [public workbench](SPARKS_WORKBENCH.md) for the five
featured software projects. It provides a guide to their documented purposes,
checks their selected starting and contribution files, and records observed
README and published-release changes. Each successful observation identifies
the repository revision and links to its evidence.

This work has a persistent memory separate from his care values. The first
observation establishes a baseline. Later observations compare the saved source
fingerprints and release records. A failed lookup is reported as unavailable;
the last good observation stays dated and visibly stale. A changed README
fingerprint establishes that its bytes changed, not what that change means or
whether the project improved.

The workbench checks only the approved public catalogue. It never runs code
from those projects. Project descriptions are maintained text, not conclusions
generated from arbitrary repository instructions. A check that a starting file
exists is not a test that its installation instructions succeed.

The first eligible companion run each Singapore day refreshes the workbench.
Later scheduled runs retry unavailable sources while leaving successfully
checked sources alone until the next day, unless a fresh check is requested.
Ordinary public care requests do not run a project scan. Owners can select
**Check Sparks public project sources again today** in the manual workflow to
request a fresh observation. Changes to the worker or catalogue also trigger a
fresh check. GitHub may delay scheduled runs.

Useful abilities are described through their actual outputs: source navigation,
selected-file checks and comparison with prior observations. Care experience,
age and the fictional growth titles are not educational marks or measures of
general intelligence. Adding a new capability requires an implemented procedure,
appropriate tests and review. The current worker uses explicit procedures and
saved evidence; it does not train model weights or provide free-form chat.

## His persistent daily routine

Self-contained SVG animation supplies the small movements while you view the
header. A Python program maintains saved game state in
[persona.json](../data/persona.json) and regenerates the image when the companion
workflow runs. Reloading the profile does not reset his age or growth. The
current state format is schema version 2, with the name `Sparks`; migration from
the original format retains the existing birth time, values and care history.

His fictional daily routine uses **Asia/Singapore** time. The workflow is
scheduled for **07:17, 13:17, 19:17 and 22:17** each day. Opening a recognised care
issue also queues an update, and the scheduled runs sweep pending requests.
A request pending for more than **24 hours** expires and needs a new submission.
Requests created before public care was activated are ignored.

At night, from **22:00 to 06:59 Singapore time**, he rests. By day, a recent study,
play or rest action can determine his visible mode for up to six hours. Otherwise
he is curious, with a resting appearance when his energy is low. Time gradually
changes his game values, and automatic recovery keeps neglect from killing him.
You can return after a break without losing his growth.

GitHub may delay scheduled runs and cache an older image. The workflow must be
on the default branch, and repository Actions must be enabled. Public-repository
schedules can be disabled after 60 days without repository activity. These
constraints are documented in GitHub's [workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
and [image-cache guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-anonymized-urls).

GitHub sanitizes README HTML and SVG images run without ordinary JavaScript
interaction; see [GitHub Markup](https://github.com/github/markup),
[SVG image restrictions](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image)
and the [SVG processing modes](https://www.w3.org/TR/SVG/conform.html).
The ordinary links beneath the header provide care controls. An immediately
interactive game inside a web page would require a separate web application.

## Motion and access

Sparks gently floats in his curious mode. Studying adds amber indicators; playing
adds a small bob and sparks; resting dims the robot, slows his movement and shows
sleep marks. The original PNG supplies the robot's face and body throughout.

The image includes alternative text, an SVG title and a description. It respects
the browser's `prefers-reduced-motion` setting. A separate
[still image](../assets/research-header-static.svg?version=sparks-retro-20261028) disables animation regardless
of that preference. All controls and explanatory text also appear as ordinary
links outside the image.

## Owner controls

Open [Sparks companion in Actions](https://github.com/Albertito-AI/Albertito-AI/actions/workflows/persona.yml),
choose **Run workflow**, keep the branch set to **main**, and choose `feed`,
`study`, `play`, `rest` or `tick`. `tick` refreshes the saved state and daily
routine without awarding experience. GitHub requires repository write access
for these manual runs, as explained in its
[manual workflow instructions](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

Rerunning a previously processed manual workflow does not repeat its reward. If
a manual care request is refused, start a **new** run when it is appropriate to
try again. To pause saved-state updates, disable **Sparks companion** in Actions.
The last saved image remains visible and its local animation continues; use the
still image as the README image source if you also want to stop motion. To
resume, enable the workflow and run `tick`.

## Maintaining the companion

| File | Purpose |
| --- | --- |
| [persona-template.svg](../assets/persona-template.svg) | Editable header layout, embedded robot artwork and motion. |
| [sparks-retro.png](../assets/sparks-retro.png) | Approved original retro robot artwork. |
| [persona.json](../data/persona.json) | Saved game values, birth time, care history and update time. |
| [update_persona.py](../scripts/update_persona.py) | State transitions and escaped SVG rendering. |
| [public_care.py](../scripts/public_care.py) | Public request processing, receipts and GitHub acknowledgements. |
| [public-care.json](../data/public-care.json) | Public care activation time and processed-request ledger. |
| [sparks_agent.py](../scripts/sparks_agent.py) | Bounded public-project observation, comparison and workbench rendering. |
| [sparks-catalog.json](../data/sparks-catalog.json) | Reviewed public project descriptions and selected starting files. |
| [sparks-knowledge.json](../data/sparks-knowledge.json) | Dated public-source observations and change memory. |
| [SPARKS_WORKBENCH.md](SPARKS_WORKBENCH.md) | Generated project guide, source checks and change notes. |
| [persona.yml](../.github/workflows/persona.yml) | Scheduled, issue-triggered and manual updates. |
| [SPARKS_CARE_LOG.md](SPARKS_CARE_LOG.md) | Generated public care responses and decision times. |
| [test_persona.py](../tests/test_persona.py) | Tests for the clock, state, replay and rendering rules. |
| [test_public_care.py](../tests/test_public_care.py) | Tests for public requests, limits, receipts and acknowledgements. |
| [test_sparks_agent.py](../tests/test_sparks_agent.py) | Tests for source evidence, failure handling, memory and workbench output. |

The source template embeds the PNG so each generated header is self-contained.
The profile validator requires its decoded image bytes to match
`assets/sparks-retro.png`. An appearance change must update the source template
and regenerate both header outputs from the saved state.

Run the repository checks with Python 3.12 or later:

```bash
python -m unittest discover -s tests -v
python scripts/update_persona.py --check
python scripts/public_care.py --check
python scripts/sparks_agent.py --check
python scripts/validate_profile.py
```

To regenerate a local working copy after editing the template:

```bash
python scripts/update_persona.py --action tick
```

The program uses the operating system's time-zone database. Windows installations
without IANA time-zone data may need the Python `tzdata` package. The configured
GitHub runner already supplies the database.

The worker recognises only the exact titles `[Sparks] feed`, `[Sparks] study`,
`[Sparks] play` and `[Sparks] rest`. It uses public issue and account identifiers
to prevent repeat rewards and apply the account limit. Processed-request
receipts are retained for at least **72 hours**, and records still awaiting
GitHub acknowledgement are retained. The receipt store is capped at **2,000**
entries. If it fills and cannot safely remove old entries, the worker stops
applying additional public care rather than risk rewarding a request twice.
Only committed decisions are acknowledged on GitHub. A backlog of pending
acknowledgements can defer new requests.

The workflow uses GitHub's built-in short-lived token. It needs no separately
configured API key, external service, model call or paid hosting. Its generated
outputs are the care state, public care receipts and diary, the two header images,
and the public-source knowledge file and workbench.
Existing scholarly text and the substantive profile-update date are outside its
write list. A normal push rejects a competing change to `main`; no force push
or branch-protection bypass is used. A missing state file is an error: restore
it from Git history to preserve age and growth before running the companion
again.

AI assistance: the original character, implementation and checks were prepared
with ChatGPT. Public care requests and responses are game events, not research
findings or academic judgements.

## Dance Floor

[Sparks' Dance Floor](SPARKS_DANCE_FLOOR.md) includes an animated profile preview,
a full silent video and an interactive stage with all six routines. The stage uses
the supplied robot sprites and offers setlist, pause and optional synthesized-beat
controls. [Open the interactive stage](https://albertito-ai.github.io/Albertito-AI/).

The profile selects the still header image when reduced motion is requested.
The Dance Floor starts paused for the same preference.
