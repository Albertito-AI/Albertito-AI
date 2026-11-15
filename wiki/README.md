# Wiki publication source

[Read the complete whitepaper](Whitepaper.md). This is the versioned source for the
project's GitHub Wiki. It is an AI-assisted design synthesis, not independent
review or a claim that the ideal roadmap is already implemented. Existing project
rights and visibility remain unchanged.

## Publication state

On **15 November 2026**, a read-only check retrieved the public Wiki at revision
`c73e0bdc07354a2c91d443a344e37322d681121e`. Its `Whitepaper.md` matched the
repository source at `e80498f303a515353dc5678941a727e0e473cbde` byte for byte, and
its managed Home section matched that revision's `wiki/Home.md`. The Wiki is
initialised. Earlier instructions to create its first page describe a superseded
state.

That receipt applies to the source revision named above. It does not certify
publication of later source changes. After a documentation update, check the
publisher's actual outcome and compare the destination bytes again. A committed
file and a successful workflow are each insufficient on their own.

The `Publish project whitepaper to Wiki` workflow runs after relevant source
changes, a Wiki edit or an authorised manual dispatch. It uses the
repository-scoped workflow token. Its summary reports `PUBLISHED`,
`ALREADY_CURRENT` or `BLOCKED_UNINITIALISED`; the last state means no Wiki page
was published. No paid service or third-party publishing action is used.

The publisher writes only its marked Whitepaper page and a marked, additive Home
section. It preserves other pages and Home text, refuses an existing unmarked
Whitepaper, and uses a non-forced push. Concurrent changes require reconciliation.
Each managed source file is limited to 200,000 bytes. Other files placed in
`wiki/`, including this README and the portfolio index, are not automatically
published as additional Wiki pages by this workflow.

Edit the versioned source for future paper updates. The script never executes
Wiki content, changes visibility or grants new reuse rights. It does not
initialise a missing Wiki.

## Recovery if a Wiki is genuinely uninitialised

First distinguish an absent Wiki from an authentication, network or concurrent
edit problem. Do not replace an existing Home page or change repository settings
as a workaround. Only after an authorised owner confirms that the Wiki is
uninitialised, create a minimal first page titled `Home` through GitHub's normal
Wiki interface. A subsequent `gollum` event can retry the publisher. Check the
result and actual destination content before reporting publication.

GitHub's documented initialisation requirement:
https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages

