# PDF resource-isolation validation | 22 November 2026

This change moves the optional PDF parser into a separate Linux process. It is
an internal AI-assisted engineering check, not independent human security review,
legal evaluation or approval to process real case files. All inputs were original
fictional or synthetic fixtures. Earlier dated validation records remain unchanged.

## Scope and compatibility

The parent preserves the document schema, original-byte SHA-256, input byte count,
parser name/version, physical-page origins, block identifiers, extraction notes
and `UNVERIFIED_TRANSCRIPTION` status. TXT/Markdown, DOCX and the report engine
retain their existing paths. Empty or whitespace-only PDF pages retain their
explicit unextractable-page notes and do not become text blocks.

PDF intake now requires Linux and an optional `pypdf` installation visible to
the same interpreter or virtual environment in isolated mode. Windows, macOS
and other unsupported platforms reject PDF input. This intentionally changes
their former best-effort PDF availability; there is no unbounded inline fallback.
`PYTHONPATH`, user-site packages and ambient credential variables are not passed
through as a substitute for an installed parser. No dependency is installed by
the program.

## Resource and failure boundaries

Before importing `pypdf` or reading the input, the worker must install and read
back hard limits of 1 GiB address space, 35 CPU seconds, 16 MiB per output file
and zero core-dump bytes. Stricter inherited soft and hard limits are preserved. The
parent imposes a 45-second deadline, terminates the private process group on every outcome before accepting output,
reaps its direct child and accepts only a complete bounded JSON result.
Child stderr is discarded and stdout goes to a temporary regular file, avoiding
unbounded output accumulation in parent memory. The parent also checks output
length and the exact pages/version result shape before constructing segments.

The worker disables `jbig2dec_binary` and reads the configuration back before
constructing `PdfReader`. The installed pypdf 7.1.1
[decoder source](https://github.com/py-pdf/pypdf/blob/7.1.1/pypdf/filters.py) and
[configuration source](https://github.com/py-pdf/pypdf/blob/7.1.1/pypdf/_configuration.py)
were byte-checked against the official 7.1.1 tag. The source shows that the
optional helper can be reached by a filtered text stream, so disabling it is part
of this supported text profile. Parser configuration changes occur only in the
child process.

These are resource controls, not filesystem, network or arbitrary-code-execution
containment. The worker runs with the local user's OS authority. The existing
real untrusted-case-file gate remains. Process creation and OS termination
scheduling are outside a hard real-time deadline guarantee.

## Checks actually run

Environment: CPython 3.12.14, Linux x86_64/glibc 2.41, in a dedicated virtual
environment with `pypdf` 7.1.1. The unchanged baseline passed 87 tests.

- The changed mirror source passed **112 unittest cases, no skips**.
- The 25 new tests cover production-limit installation/readback; a tighter
  inherited soft cap; failures to set or read back limits; real child CPU
  termination, memory-allocation failure and file-size enforcement; wall-time
  kill/reap; descendant cleanup after a successful leader exit; malformed,
  oversized and partial IPC; platform refusal, parser availability and isolated
  imports/environment.
- Synthetic PDF tests verify exact text, metadata, original-byte hash and
  physical-page origins; empty-page notes; compressed oversized text; page and
  aggregate-text limits; and malformed input without an output report. The
  existing encrypted-PDF and empty-page tests also passed.
- A small original PDF whose text stream uses `/JBIG2Decode` first invokes a
  harmless marker helper in a controlled positive test. The guarded worker then
  refuses the same stream without invoking that helper. A separate test proves
  that failure to establish decoder suppression prevents `PdfReader` from being
  called. No real external decoder or real case document was executed.
- Real resource-failure tests use smaller child-only test limits for speed:
  one CPU second, 128 MiB address space or a 4 KiB output file. A separate test
  installs and reads back the production limits. The parent output rejection
  test uses a reduced read bound; production remains 16 MiB.
- All four documented CLI workflows and one complete synthetic PDF intake
  completed successfully.
  All reports retained `HUMAN_REVIEW_REQUIRED`, filing decision `NONE` and no truth
  certification. The PDF workflow preserved its input digest and physical page
  numbers, including a gap for an empty page.
- A second agent independently reviewed the code and re-tested the inherited
  limit, descendant-cleanup and decoder-suppression findings. These checks are
  not independent human security review or a judicial approval.

No native Windows/macOS run or multi-version local run is claimed.
This older mirror has no project-specific hosted workflow. Its local results
do not certify the unrelated research-hub website checks. The dedicated
repository has a separate Ubuntu regression workflow.

## Reproduce

Use a Linux virtual environment, install the declared PDF extra, then run:

```sh
python -m unittest discover -s tests -v
```

Run the four CLI examples in the README with new output directories. Tests that
need Linux or the optional parser are explicitly skipped when those prerequisites
are absent; the unsupported-platform refusal test is unconditional. A skip is not
a passing parser test.

Python's documented [resource limits](https://docs.python.org/3/library/resource.html),
[subprocess behaviour](https://docs.python.org/3/library/subprocess.html) and
[isolated interpreter mode](https://docs.python.org/3/using/cmdline.html#cmdoption-I)
inform the implementation. Platform-dependent resource facilities are not claimed
to exist or work identically on every POSIX system.
