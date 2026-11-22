# Threat and justice-safeguard boundary

## Current operating boundary

Local, single trusted operator, fictional material, bounded JSON and document input,
standard-library core/TXT/DOCX intake, optional pypdf PDF parser, no network calls
and no model provider. PDF parsing uses a separate Linux worker with mandatory,
verified address-space, CPU and output-file limits plus a parent wall deadline.
Unsupported platforms and unavailable limits fail closed; parsing never falls
back into the parent. The worker uses the same interpreter in isolated mode, so
the optional parser must be installed in that interpreter or its virtual
environment, not supplied through `PYTHONPATH` or user-site packages.

The PDF limits are 1 GiB address space, 35 CPU seconds, 45 wall seconds and a
16 MiB result file, with stricter inherited soft and hard limits preserved. Input remains
limited to 5 MiB, 200 pages, 100,000 characters per nonblank block and 2,000,000
extracted characters. The parent validates the complete bounded result, retains
the original-byte hash and physical-page locations, and rejects worker failure
or timeout without producing a partial report. The private process group is
terminated before output is accepted, including descendants left after a worker
leader exits. The direct child is reaped. The deadline covers the running
worker; OS process creation and termination scheduling are not hard real-time
guarantees. Core dumps are disabled in the child. The optional external `jbig2dec`
helper is disabled and that setting is verified before parsing. A text stream
requiring that decoder, or failure to establish its suppression, stops intake.

This is resource isolation, not a filesystem, network or native-code-execution
sandbox. The worker still runs as the local user. DOCX parsing remains in the
parent under its existing archive/XML limits. A compressed-file size limit alone
does not establish parser safety. Do not process untrusted real-case files before
a suitable hostile-input isolation design and independent security review. The HTML report
has escaped content, no scripts or active source URLs, and a restrictive content
security policy. JSON does not name files to read, invoke commands or define code.
This is not a secure multi-tenant or production judicial processing environment.

## Important residual risks

- Sources, origins, completeness and annotations are user-supplied. Hashes do not
  authenticate authorship, creation time, chain of custody or source truth.
- Selective quotation, fabricated exhibits, misleading but accurate excerpts and
  omitted claims can evade these bounded checks. A coverage count is not recall.
- Whitespace-only comparison can produce false alerts for legitimate quotation
  conventions, translation, transcription errors and alternative citation forms.
- Arithmetic, chronology and assertion mappings can themselves be wrong. They
  must be reviewed against the original before a finding is relied upon.
- This local CLI is not a defence against an attacker concurrently modifying
  its filesystem. Symlink inputs and overwrites are rejected, but hostile races,
  process kills, storage failures and operating-system compromise remain outside
  the trusted-operator boundary. Cleanup is best-effort.
- Generated reports reproduce supplied text. They are not anonymised, redacted,
  encrypted or safe to publish. `.gitignore` is not a confidentiality control.
- No independent security audit, legal evaluation, multilingual benchmark or
  accessibility certification has been performed.

## Required before any real court pilot

Court-approved data purpose and legal basis; rights and confidentiality review;
role-based access; separation of party-accessible evidence from restricted and
privileged records; appropriate hosting and data residency; authenticated users;
retention/deletion rules; encryption and key management; tamper-evident audit
history; incident handling; security testing; input quarantine and safe document
parsing; and a reviewed rule/source supply chain.

A future model-assisted layer must treat documents as untrusted data, not
instructions, enforce tool and network restrictions, minimise sensitive input,
show source evidence, abstain explicitly and record the model and prompt version.
A second model's agreement is not independent verification or human review.
No such layer or paid provider is active in this alpha.

## Access to justice

No automatic refusal, sanction, credibility score or merits recommendation.
Preserve the original submission, receipt time, urgent/manual filing route and
ability to challenge a flag. An outage or unavailable source must not remove a
litigant's access to the court or silently prejudice a limitation deadline.

Do not equate polished prose with truth, poor grammar with poor merits, unfamiliar
language with incoherence, lack of a source link with falsity, or legal novelty
with error. Allegations, admissions, contested facts and alternative arguments
must remain distinct. Evaluate error rates separately across document types,
represented/self-represented users, languages and extraction quality.

These are design requirements, not implemented production controls or a statement
that every jurisdiction imposes identical legal requirements.
