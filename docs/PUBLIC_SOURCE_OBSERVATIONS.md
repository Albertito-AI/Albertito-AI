# Public project source observations

The [source workbench](SPARKS_WORKBENCH.md) checks the selected starting and
contribution files for RegNav, RegNav Source Watch, Symbolon, Piepowder and
Tallystick. It records repository revisions, README fingerprints and published
release identities so that maintenance work can begin from specific evidence.

## Schedule and scope

The [Public project source observations workflow](../.github/workflows/persona.yml)
runs once daily at 07:17 Asia/Singapore. GitHub may delay scheduled runs. Changes
to the observer, its catalogue or the workflow trigger a fresh check. A maintainer
can also run the workflow manually and choose whether to repeat that day's checks.

The worker reads only the fixed public watchlist. It does not execute a watched
project's code or edit that project. A failed lookup is reported as unavailable;
the last successful evidence remains dated. At most 20 source-change receipts
are retained. A changed fingerprint records different bytes, while an entrypoint
check establishes file presence. Neither establishes successful installation,
legal accuracy or outside adoption.

## Preserved records

The observer remains separate from the retired Sparks companion. The historical
filenames, stored agent identifier and workflow concurrency key remain compatible
with existing evidence. Current observations write only
[the source record](../data/sparks-knowledge.json) and its generated workbench.
Companion state, care receipts and artwork remain preserved records.

Routine observation no longer advances mascot state, processes public care
issues, acknowledges care requests or exports dance media. Historical dance
checks are available through a separate manual workflow; they have no scheduled
or push-triggered execution.

## Verify locally

```sh
python -m unittest discover -s tests -p 'test_sparks_agent.py' -v
python scripts/sparks_agent.py --check
```

The offline check compares the generated workbench with saved source evidence.
It makes no API calls and does not update timestamps or rewrite records.
