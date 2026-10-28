# Portfolio visibility policy

**Adopted:** 27 October 2026  
**Owner:** Albert Tan Sin Hon (`Albertito-AI`)

## Purpose

Repository visibility is selected according to the function of the material, not by a general preference that everything be public or private. Public scrutiny can improve reproducibility, reputation and collaboration. Confidentiality, security, assessment integrity and contractual duties require separate controls.

## Three-layer rule

### 1. Public intellectual and reference layer

Suitable public material includes original source code intended for public inspection, protocol specifications, synthetic fixtures, openly licensed or public-source research, documentation, reproducible demonstrations and non-confidential issue discussions.

### 2. Restricted operational layer

Private repositories or workspaces are used when actual material exists that requires restricted access, including customer-specific configurations, production deployment details, unpublished commercial methods, controlled examinations, internal evaluation procedures and non-public partner integrations.

### 3. Confidential records layer

Credentials, personal data, client documents, participant or student records, protected health information, private correspondence, real transactions and restricted third-party material must not enter a public repository. Their storage, access, retention and deletion require purpose-specific controls outside the public reference layer.

## Current public portfolio

The public portfolio comprises:

- the `Albertito-AI` profile and public navigation repository;
- `policykit`, the RegNav evidence-ledger research prototype;
- `regnav-source-watch`, the separately released Apache-2.0 Source Watch GitHub Action;
- `symbolon`, the machine-work contract and verification reference implementation;
- `piepowder`, the fictional agent-commerce acceptance and review prototype;
- `tallystick`, the sports-fact provenance and settlement research workbench;
- `AlberTito-MasterMind`, the RIF computational research prototype;
- `evtalbert`, the EVT software prototype, with real user records excluded.

Each public repository retains its own licence or rights statement. The
Apache-2.0 licence of `regnav-source-watch` applies to that package only and
does not change `policykit`'s reserved rights. Public visibility alone grants
no permission beyond each repository's terms.

## Private institutional systems

Institutional systems involving admissions, learner or participant identities, hidden assessment materials, answer keys, security architecture or protected records remain private. A public prospectus, selected module or research report may later be released through a separate, deliberate publication decision.

## When to create a private repository

Create a private repository when at least one concrete restricted artifact or operational requirement exists and its owner, access group and purpose can be identified. Do not create an empty private clone merely to signal that a commercial version might exist someday.

## Pre-publication test

Before committing or changing visibility, confirm:

1. The owner has the right to publish every included artifact.
2. No credentials, personal data, confidential records or restricted third-party material are present.
3. Public examples are synthetic, lawfully public or properly cleared.
4. Claims match implemented behaviour and observed evidence.
5. The repository states its licence or reserved-rights position accurately.
6. Production, client, student, participant and assessment boundaries are documented.
7. A visibility change will not unintentionally expose Actions logs, historical artifacts or prior commits.

## Review and exception

Review visibility when a project acquires real users, regulated data, payment or identity integrations, human-subject research, controlled examinations or contractual confidentiality. A justified exception records the affected material, decision-maker, reason, safeguards and review date.

Changing a repository from public to private is not a substitute for removing or rotating exposed secrets. Changing it from private to public is a publication event requiring a fresh history, Actions and data review.
