# Study activity accessibility record

Review date: 7 November 2026. This is a source inspection and implementation plan, not a WCAG conformance certification or a completed assistive-technology test.

## Existing companion: inspected features

The existing landing page uses a language declaration, a skip link, a main landmark, labelled navigation and native buttons, selects and disclosure elements. Its CSS provides a visible focus outline and narrow-screen layouts. Feedback regions use `role="status"` or `aria-live="polite"`. Quiz and sorter transitions move focus to the new question heading. The practice interface makes no network requests and retains answers only in memory. Static seminar pages and a no-script notice provide reading alternatives.

## Items to verify in interactive review

- Selecting a practice answer disables all answer buttons, including the focused button. Confirm that keyboard focus remains intelligible and the enabled Next control can be reached in each supported browser.
- Restarting a quiz or case replaces content without an explicit focus move to the question. Confirm that the change is understandable with a screen reader; a deliberate announcement or focus policy would make the new activity clearer.
- The source includes small text in labels and metadata. Test zoom and text enlargement with real browsers; source inspection alone cannot establish readability or successful reflow.
- Responsive rules are present, but a full 320 CSS-pixel reflow and 400% zoom check remains a rendered-interface task.
- The inspected CSS contains no animation and includes a reduced-motion preference rule. No motion control is needed for the planned static card transitions.

## Implemented study lab

A self-contained HTML page holds eight original retrieval-practice cards about records, dates, component effectiveness, connecting propositions, missing evidence, evidence labels, decision authority and qualified conclusions. Each card links to the relevant printed source pages. Native controls support previous, reveal, next and restart. Revealing an answer updates an explicit status region. The page has no timer, automatic advance, score, drag interaction, account, tracking, remote script or remote font.

The readable cards remain available as ordinary HTML. A separate printable fictional evidence-mapping worksheet lets students write a legal question, supporting document, missing fact and qualified conclusion. A facilitator guide explains the materials and their limits. A portable JSON export distinguishes original companion text from the book and preserves source references. A factual FAQ provides fourteen ordinary HTML answers about access, reuse, citation and discovery.

Acceptance checks: keyboard operation through native controls; visible focus; semantic headings and labels; source links for every card; understandable state changes; no network calls or persistence; local-file use; narrow-screen wrapping; legible print layout; distinct book and companion licences. Browser and assistive-technology observations must be labelled separately from code-level checks.

## Primary guidance consulted

- [W3C: Keyboard, criterion 2.1.1](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html): functionality needs a keyboard-operable route without timing-dependent keystrokes.
- [W3C: Focus Visible, criterion 2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html): keyboard users need a visible indication of the focused element.
- [W3C: Status Messages, criterion 4.1.3](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html): relevant status changes should be programmatically available without requiring focus.
- [W3C: Reflow, criterion 1.4.10](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html): ordinary vertical content should remain usable at a width equivalent to 320 CSS pixels.

These W3C Understanding documents explain the criteria; they do not by themselves establish that this companion conforms.

## Study lab control checks

The study lab uses native buttons and leaves keyboard events to the browser. Its on-page instructions describe Tab, Shift+Tab, Enter and Space. Previous, next and restart move focus to the new card heading; that heading is associated with the visible card count. Reveal and hide preserve the button and expose the expanded state. A polite, atomic status region announces the result. Initial page load does not move focus.

On 7 November 2026, a unit-level JavaScript harness executed the actual inline script with a minimal DOM. All eight reveal/hide transitions, source correspondence, first/last boundaries, backwards navigation, restart state, focus policy and status attributes passed. This does not exercise browser-native key handling or screen-reader speech.

Browser test checklist (central browser observations are recorded separately): Tab from the skip link into the lab; activate Reveal with Enter and Space; reveal then Next; Previous at an interior card; advance to the eighth card; restart while commentary is visible; verify visible focus and spoken card/count/state; disable JavaScript and use all eight native disclosures. Check local-file operation, 320 CSS-pixel layout, 400% zoom and printing separately.

## Structure, contrast and motion audit

On 7 November 2026, source inspection confirmed one H1 per activity page, sequential H2 sections, language declarations, named controls, unique IDs, resolvable ARIA references and no positive tabindex. Focus follows the document order except for the explicit move to a new card heading. The keyboard instructions are initially hidden and shown with the interactive controls, so a no-script reader is not directed towards unavailable buttons.

Relative-luminance calculations used the actual stylesheet colours. The weakest normal-text pair checked was muted text `#4c605b` against the answer background `#f0e9db`, at approximately 5.55:1. The focus colour `#963b22` against the paper background `#f6f3eb` is approximately 6.43:1. The primary button’s light text against `#183b35` is approximately 12.03:1. Ratios were evaluated without rounding against the relevant thresholds. The worksheet’s writing boundary was darkened from `#84968d` to `#63736a`, increasing contrast against the page background from approximately 2.81:1 to 4.52:1. These calculations cover declared colours, not every possible browser override or rendering condition.

There are no animated transitions, automatic scrolling calls or timers. The study lab also includes a reduced-motion media rule. Neither activity requires movement or timing to complete.

Additional primary guidance: [W3C text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) and [focus order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html). Browser rendering, native keyboard behaviour and assistive-technology speech remain separate checks.

## Export, link and print-source checks

The round-nine source check resolved 33 local HTML links and fragments, checked local Markdown link targets and confirmed that the portable JSON contains exactly the eight inline cards. All three standalone HTML pages retain their source licence notices. The worksheet has seven writing areas, a declared A4 print stylesheet, a deliberate page break before the concluding tasks and source/attribution text outside hidden navigation. These are source-level observations. No printed page count, printer output or PDF pagination is certified here.

The classroom archive must be regenerated after source changes. Its final publication check should compare every activity member byte-for-byte with the corresponding source file, including this record and the FAQ.
