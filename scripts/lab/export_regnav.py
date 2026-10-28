"""Execute pinned public RegNav examples and export a recorded browser replay.

No model or source-URL requests are made. Supply the two checked-out upstream
repositories; their exact reviewed revisions and tracked bytes are checked.
Temporary fictional inputs are discarded. Only --output is written, and only
after every expected result has actually been observed. --verify writes nothing.

Rights: policykit retains its existing RIGHTS.md terms. Source Watch has a
separate Apache-2.0 licence and NOTICE. This exporter grants no additional rights
in either project's code, fictional materials, or third-party sources.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = Path(__file__).with_name("regnav_fixtures.json")
POLICY_REPO = "Albertito-AI/policykit"
WATCH_REPO = "Albertito-AI/regnav-source-watch"
POLICY_PIN = "130cf41b0d59e1f72a238b0cf3c145c6ca337265"
WATCH_PIN = "2a6501fbbf535c58b11aeef16a8e8d0cc48148c0"
DISCLAIMER = (
    "Recorded executions of fictional training examples, not browser-side legal "
    "verification. Structural validity, unchanged bytes and recorded review "
    "declarations do not establish source authenticity, legal correctness, "
    "factual truth, completeness or an actual human review. Visitor notes are "
    "practice annotations and never alter the source review declarations."
)
MAX_COMMAND_OUTPUT = 1_048_576


def digest(data):
    return hashlib.sha256(data).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def encode_json(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def execute(argv, cwd, env, timeout=45):
    result = subprocess.run(
        list(map(str, argv)), cwd=cwd, env=env, text=True, encoding="utf-8",
        capture_output=True, timeout=timeout, check=False,
    )
    if len(result.stdout.encode()) + len(result.stderr.encode()) > MAX_COMMAND_OUTPUT:
        raise ValueError("A command exceeded the bounded receipt size.")
    return result


def git(root, args, env):
    result = execute(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.autocrlf=false",
         "-c", "commit.gpgsign=false",
         "-C", str(root), *args], root, env,
    )
    if result.returncode:
        raise ValueError("Git operation failed: " + result.stderr[:2000])
    return result.stdout.strip()


def source_record(root, repository, pin, prefixes, rights_file, env):
    if git(root, ["rev-parse", "HEAD"], env) != pin:
        raise ValueError(f"{repository} must be checked out at the reviewed revision {pin}.")
    changed = execute(
        ["git", "-C", str(root), "diff", "--exit-code", "HEAD", "--", *prefixes], root, env
    )
    if changed.returncode:
        raise ValueError(f"{repository}: tracked source or fixture bytes differ from the pinned commit.")
    names = git(root, ["ls-tree", "-r", "--name-only", pin, "--", *prefixes], env).splitlines()
    records = []
    for name in sorted(set(names)):
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Expected a regular source file: {repository}/{name}")
        records.append({
            "path": name, "sha256": digest(path.read_bytes()),
            "url": f"https://github.com/{repository}/blob/{pin}/{name}",
        })
    if not records:
        raise ValueError(f"No pinned source files found for {repository}.")
    return {
        "repository": repository, "revision": pin,
        "url": f"https://github.com/{repository}/tree/{pin}",
        "rights_url": f"https://github.com/{repository}/blob/{pin}/{rights_file}",
        "rights": ("Rights reserved; consult policykit RIGHTS.md."
                   if repository == POLICY_REPO else
                   "Apache-2.0 for this separate project; consult its LICENSE and NOTICE."),
        "files": records,
    }


class Run:
    def __init__(self, policy, watch, directory, env, node):
        self.policy, self.watch, self.directory = policy, watch, directory
        self.env, self.node, self.receipts = env, node, []
        self.input_files = {}

    def normalise(self, value):
        text = str(value)
        for prefix, label in (
            (str(self.policy), "$POLICYKIT"), (str(self.watch), "$SOURCE_WATCH"),
            (str(self.directory), "$FIXTURES"),
        ):
            if text == prefix or text.startswith(prefix + os.sep):
                return label + text[len(prefix):]
        if text == sys.executable:
            return "python"
        if text == self.node:
            return "node"
        return text

    def call(self, identifier, argv, cwd, expected_exit, json_output=False):
        started = utc_now()
        result = execute(argv, cwd, self.env)
        receipt = {
            "id": identifier,
            "command": [self.normalise(value) for value in argv],
            "cwd": self.normalise(cwd),
            "exit_code": result.returncode,
            "expected_exit_code": expected_exit,
            "stdout": result.stdout, "stderr": result.stderr,
            "assertions": [],
            "execution": {
                "started_at": started, "finished_at": utc_now(),
                "actual_command": list(map(str, argv)), "actual_cwd": str(cwd),
            },
        }
        self.receipts.append(receipt)
        check(receipt, "exit code", result.returncode, expected_exit)
        return receipt, json.loads(result.stdout) if json_output else result.stdout

    def ledger_file(self, identifier, value):
        path = self.directory / "ledgers" / (identifier + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        contents = value if isinstance(value, bytes) else encode_json(value)
        path.write_bytes(contents)
        self.input_files[identifier] = {
            "path": self.normalise(path), "sha256": digest(contents),
            "bytes": len(contents), "kind": "fictional training fixture",
        }
        return path

    def validate(self, identifier, path, expected, strict=False):
        args = [sys.executable, "-m", "regnav_evidence", "validate", str(path), "--json"]
        if strict:
            args.append("--strict")
        receipt, report = self.call(identifier, args, self.policy, expected["exit_code"], True)
        for key in ("error_count", "warning_count"):
            if key in expected:
                check(receipt, key, report[key], expected[key])
        for key, severity in (("warning_codes", "warning"), ("error_codes", "error")):
            if key in expected:
                codes = sorted(item["code"] for item in report["findings"] if item["severity"] == severity)
                check(receipt, key, codes, sorted(expected[key]))
        check(receipt, "structural-validity flag", report["structurally_valid"], expected.get("error_count", 0) == 0)
        return receipt, report


def check(receipt, name, observed, expected):
    passed = observed == expected
    receipt["assertions"].append({
        "name": name, "passed": passed, "expected": expected, "observed": observed,
    })
    if not passed:
        raise ValueError(f"{receipt['id']}: {name}: expected {expected!r}, observed {observed!r}")


def source_packet(policy, ledger):
    text = (policy / "examples/training_sources.md").read_text(encoding="utf-8")
    paragraphs = [{"id": match.group(1), "text": match.group(2)}
                  for match in re.finditer(r"^\*\*([AB]\.\d+)\*\*\s+(.+)$", text, re.M)]
    if len(paragraphs) != 5:
        raise ValueError("The pinned fictional source packet must contain its five known paragraphs.")
    url = f"https://github.com/{POLICY_REPO}/blob/{POLICY_PIN}/examples/training_sources.md"
    return {
        "title": "Complete fictional source packet", "text": text, "url": url,
        "sources": [
            {"id": source["id"], "title": source["title"],
             "url": url + ("#draft-a" if source["id"] == "SRC-draft-a" else "#draft-b"),
             "paragraphs": [item for item in paragraphs if item["id"].startswith("A." if source["id"] == "SRC-draft-a" else "B.")]}
            for source in ledger["sources"]
        ],
    }


def ledger_text(ledger):
    lines = [ledger["title"], "", "Recorded sources:"]
    for source in ledger["sources"]:
        lines.append(f"{source['id']}: {source['version']}; accessed {source.get('accessed', 'not recorded')}.")
    lines.append("\nRecorded propositions:")
    for claim in ledger["claims"]:
        lines.extend([f"{claim['id']} [{claim['review_status']}]", claim["text"]])
        for link in claim["evidence"]:
            lines.append(f"  {link['source_id']}, {link['pinpoint'] or '(no pinpoint)'}, relation: {link['relation']}.")
    return "\n".join(lines)


def ledger_display(before, after, packet, fields, title):
    old = {item["id"]: item for item in before["claims"]}
    new = {item["id"]: item for item in after["claims"]}
    packet_sources = {item["id"]: item for item in packet["sources"]}

    def evidence_for(claim, ledger):
        if claim is None:
            return []
        recorded_ids = {item["id"] for item in ledger["sources"]}
        evidence = []
        for link in claim["evidence"]:
            source = packet_sources.get(link["source_id"]) if link["source_id"] in recorded_ids else None
            quote = next((part["text"] for part in source["paragraphs"] if part["id"] == link["pinpoint"]), "") if source else ""
            url = source["url"] if source else None
            label = ("Original fictional passage at the pinned source revision" if quote else
                     "No pinpoint recorded" if source and not link["pinpoint"] else
                     "No matching passage in the recorded source packet" if source else
                     "Source not recorded in this snapshot")
            evidence.append({
                **link, "quote": quote, "source_url": url,
                "original_source_url": url,
                "quote_origin": "upstream-fixture" if source else "unresolved-source",
                "quote_label": label,
            })
        return evidence

    def note_for(claim):
        if claim is None:
            return "This proposition is absent from this snapshot."
        return (claim.get("review") or {}).get("note", "No completed review declaration is recorded.")

    claims = []
    for identifier in dict.fromkeys([*old, *new]):
        previous, current = old.get(identifier), new.get(identifier)
        item = current or previous
        before_evidence = evidence_for(previous, before)
        after_evidence = evidence_for(current, after)
        before_note, after_note = note_for(previous), note_for(current)
        claims.append({
            "id": identifier, "text": item["text"],
            "before_status": previous["review_status"] if previous else "not present",
            "after_status": current["review_status"] if current else "withdrawn from this fixture",
            "before_evidence": before_evidence, "after_evidence": after_evidence,
            "before_review_note": before_note, "after_review_note": after_note,
            "source_quote": "\n".join(link["quote"] for link in after_evidence if link["quote"]),
            "source_url": next((link["source_url"] for link in after_evidence if link["source_url"]), None),
            "review_note": after_note, "evidence": after_evidence,
        })
    return {
        "before_title": "Original fictional ledger", "after_title": title,
        "before_text": ledger_text(before), "after_text": ledger_text(after),
        "changed_fields": fields, "claims": claims,
    }


def ledger_scenarios(run, fixture, packet, baseline, baseline_path):
    scenarios = []
    expected = fixture["expectations"]
    r0, report0 = run.validate("ledger-baseline", baseline_path, expected["baseline"])
    strict_expected = {**expected["baseline"], "exit_code": 2}
    rs, strict_report = run.validate("ledger-baseline-strict", baseline_path, strict_expected, True)
    check(rs, "strict mode preserves the same findings", strict_report, report0)
    rc, csv_text = run.call("ledger-matrix-csv",
        [sys.executable, "-m", "regnav_evidence", "report", str(baseline_path), "--format", "csv"],
        run.policy, 0)
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    check(rc, "CSV evidence row count", len(rows), 4)
    # This checks the actual CSV contents without relying on a guessed column label.
    ids = [value for row in rows for value in row.values() if value in {"CLAIM-logging", "CLAIM-remedy", "CLAIM-timing"}]
    check(rc, "CSV represents three propositions", sorted(set(ids)), ["CLAIM-logging", "CLAIM-remedy", "CLAIM-timing"])
    check(rc, "two evidence rows preserve the timing disagreement", ids.count("CLAIM-timing"), 2)

    def scenario(identifier, title, prompt, after, report, explanation, receipt_ids, fields):
        return {
            "id": identifier, "title": title, "prompt": prompt,
            "input": {"ledger": after, "base_ledger": baseline,
                      "fixture_sha256": run.input_files[identifier]["sha256"]},
            "observed": {"validation": report},
            "expected": expected[identifier],
            "explanation": explanation, "receipt_ids": receipt_ids,
            "display": ledger_display(baseline, after, packet, fields, title),
        }

    scenarios.append(scenario(
        "baseline", "Inspect the recorded gaps",
        "Select a proposition and read its linked passage. Which findings concern missing structure, and which preserve an unresolved question?",
        baseline, report0,
        "The distributed example has no structural errors but retains three warnings. Ordinary validation exits 0; strict validation exits 2. Neither exit status verifies the propositions or authenticates the fictional reviewer.",
        [r0["id"], rs["id"], rc["id"]], [],
    ))

    irrelevant = deepcopy(baseline)
    next(item for item in irrelevant["claims"] if item["id"] == "CLAIM-remedy")["evidence"][0]["pinpoint"] = fixture["irrelevant_pinpoint"]
    path = run.ledger_file("irrelevant-pinpoint", irrelevant)
    receipt, report = run.validate("ledger-irrelevant-pinpoint", path, expected["irrelevant-pinpoint"])
    check(receipt, "review declarations are unchanged", [item.get("review") for item in irrelevant["claims"]], [item.get("review") for item in baseline["claims"]])
    scenarios.append(scenario(
        "irrelevant-pinpoint", "A populated field is not supporting evidence",
        "The missing pinpoint is replaced with B.2. Read B.2: does its statement about response time establish a further review procedure?",
        irrelevant, report,
        "B.2 discusses response time, not further review. The missing-pinpoint warning disappears because the field is populated. The claim remains unreviewed. This is a deliberate negative example of what structural validation cannot establish.",
        [receipt["id"]], ["CLAIM-remedy.evidence[0].pinpoint"],
    ))

    withdrawn = deepcopy(baseline)
    withdrawn["claims"] = [item for item in withdrawn["claims"] if item["id"] != fixture["withdrawn_claim_id"]]
    path = run.ledger_file("withdraw-unsupported", withdrawn)
    receipt, report = run.validate("ledger-withdraw-unsupported", path, expected["withdraw-unsupported"])
    check(receipt, "remaining propositions and declarations unchanged", withdrawn["claims"], [item for item in baseline["claims"] if item["id"] != fixture["withdrawn_claim_id"]])
    scenarios.append(scenario(
        "withdraw-unsupported", "Withdraw an unsupported proposition",
        "Compare the ledger after withdrawing CLAIM-remedy. Does that resolve the separate five-day versus ten-day disagreement?",
        withdrawn, report,
        "The unsupported proposition is removed in this temporary exercise. The contested timing proposition remains contested, and its warning remains. No human-review declaration has been fabricated or upgraded.",
        [receipt["id"]], ["claims: CLAIM-remedy removed"],
    ))

    invalid = deepcopy(baseline)
    next(item for item in invalid["claims"] if item["id"] == "CLAIM-remedy")["evidence"][0]["source_id"] = fixture["invalid_source_id"]
    path = run.ledger_file("invalid-source", invalid)
    receipt, report = run.validate("ledger-invalid-source", path, expected["invalid-source"])
    scenarios.append(scenario(
        "invalid-source", "Reject a reference to an absent source",
        "Inspect the source identifier on CLAIM-remedy. Is that source recorded anywhere in the ledger?",
        invalid, report,
        "The actual CLI rejects the absent source reference with UNKNOWN_SOURCE and exit 1. A missing source is never converted into a successful or verified result.",
        [receipt["id"]], ["CLAIM-remedy.evidence[0].source_id"],
    ))

    revised = deepcopy(baseline)
    revised["sources"][0]["version"] = fixture["changed_version"]
    revised_path = run.ledger_file("source-version-changed", revised)
    receipt, comparison = run.call("ledger-source-version-comparison",
        [sys.executable, "-m", "regnav_evidence", "compare", str(baseline_path), str(revised_path), "--json"],
        run.policy, 0, True)
    ids = sorted(item["id"] for item in comparison["claims"] if item["recheck_prior_review"])
    check(receipt, "previous declarations requiring reconsideration", ids, expected["source-version-changed"]["recheck_claim_ids"])
    check(receipt, "one material source-record change", [(item["id"], item["change"]) for item in comparison["sources"]], [("SRC-draft-a", "material")])
    check(receipt, "recorded declarations preserved", revised["claims"], baseline["claims"])
    scenarios.append({
        "id": "source-version-changed", "title": "A changed source record prompts reconsideration",
        "prompt": "Which previously checked or contested propositions depend on draft A?",
        "input": {"ledger": revised, "base_ledger": baseline, "fixture_sha256": run.input_files["source-version-changed"]["sha256"]},
        "observed": {"comparison": comparison}, "expected": expected["source-version-changed"],
        "explanation": "Only a fictional version label is changed here. The comparison conservatively identifies potentially stale prior declarations for CLAIM-logging and CLAIM-timing. It neither observes a real legal amendment nor performs a new review.",
        "receipt_ids": [receipt["id"]],
        "display": ledger_display(baseline, revised, packet, ["SRC-draft-a.version"], "Revised fictional source record"),
    })

    metadata = deepcopy(baseline)
    metadata["sources"][0]["accessed"] = fixture["metadata_accessed_date"]
    metadata_path = run.ledger_file("metadata-only", metadata)
    receipt, comparison = run.call("ledger-metadata-only-negative",
        [sys.executable, "-m", "regnav_evidence", "compare", str(baseline_path), str(metadata_path), "--json"],
        run.policy, 0, True)
    check(receipt, "access-date edit does not demand renewed substantive review", [item["id"] for item in comparison["claims"] if item["recheck_prior_review"]], [])
    check(receipt, "access-date category", comparison["sources"][0]["change"], "metadata_only")

    duplicate = baseline_path.read_bytes().decode("utf-8").replace(
        '"schema_version": "1.0"', '"schema_version": "1.0", "schema_version": "1.0"', 1
    ).encode("utf-8")
    duplicate_path = run.ledger_file("duplicate-key", duplicate)
    receipt, _ = run.call("ledger-duplicate-key-negative",
        [sys.executable, "-m", "regnav_evidence", "validate", str(duplicate_path), "--json"],
        run.policy, 1)
    check(receipt, "duplicate JSON key is explicitly rejected", "Duplicate JSON key" in receipt["stderr"], True)
    return scenarios


def watch_display(before, after, original_texts, changed_text, fields, title):
    old = {item["id"]: item for item in before["claims"]}
    new = {item["id"]: item for item in after["claims"]}
    original_sources = {item["id"]: item for item in before["sources"]}
    after_texts = {**original_texts, "source-policy": changed_text}

    def evidence_for(claim, manifest, texts):
        if claim is None:
            return []
        sources = {item["id"]: item for item in manifest["sources"]}
        evidence = []
        for link in claim["evidence"]:
            identifier = link["source_id"]
            source = sources.get(identifier)
            original = original_sources.get(identifier)
            quote = texts.get(identifier, "") if source else ""
            original_url = (f"https://github.com/{WATCH_REPO}/blob/{WATCH_PIN}/examples/basic/{original['path']}"
                            if original else None)
            amended = source is not None and quote != original_texts.get(identifier, "")
            origin = ("unresolved-source" if source is None else
                      "temporary-fixture" if amended else "upstream-fixture")
            label = ("Source not recorded in this snapshot" if source is None else
                     "Fictional source text amended in this recorded temporary scenario" if amended else
                     "Original fictional source at the pinned upstream revision")
            evidence.append({
                **link, "quote": quote,
                "source_url": original_url if origin == "upstream-fixture" else None,
                "original_source_url": original_url,
                "quote_origin": origin, "quote_label": label,
            })
        return evidence

    def note_for(claim):
        if claim is None:
            return "This proposition is absent from this snapshot."
        return (claim.get("review") or {}).get("note", "No review declaration is recorded.")

    claims = []
    for identifier in dict.fromkeys([*old, *new]):
        previous, current = old.get(identifier), new.get(identifier)
        claim = current or previous
        before_evidence = evidence_for(previous, before, original_texts)
        after_evidence = evidence_for(current, after, after_texts)
        before_note, after_note = note_for(previous), note_for(current)
        claims.append({
            "id": identifier, "text": claim["text"],
            "before_status": "fictional declaration recorded" if previous and previous.get("review") else "no declaration",
            "after_status": "fictional declaration recorded" if current and current.get("review") else "no declaration",
            "before_evidence": before_evidence, "after_evidence": after_evidence,
            "before_review_note": before_note, "after_review_note": after_note,
            "source_quote": "\n".join(link["quote"] for link in after_evidence if link["quote"]),
            "source_url": next((link["source_url"] for link in after_evidence if link["source_url"]), None),
            "review_note": after_note, "evidence": after_evidence,
        })
    return {
        "before_title": "Unmodified upstream fictional source",
        "after_title": title,
        "before_text": original_texts["source-policy"],
        "after_text": changed_text,
        "changed_fields": fields, "claims": claims,
    }


def watch_scenarios(run, fixture):
    directory = run.directory / "source-watch"
    shutil.copytree(run.watch / "examples/basic", directory)
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError("The copied fictional example contains an unexpected symlink.")
    env = dict(run.env)
    env.update({
        "GIT_AUTHOR_NAME": "RegNav fictional fixture",
        "GIT_COMMITTER_NAME": "RegNav fictional fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": fixture["synthetic_git_date"],
        "GIT_COMMITTER_DATE": fixture["synthetic_git_date"],
    })
    git(directory, ["init", "--quiet", "--initial-branch=main", "--object-format=sha1"], env)

    def commit(message):
        git(directory, ["add", "--", "."], env)
        git(directory, ["commit", "--quiet", "-m", message], env)
        return git(directory, ["rev-parse", "HEAD"], env)

    manifest_path = directory / ".regnav/manifest.json"
    baseline = json.loads(manifest_path.read_text(encoding="utf-8"))
    texts = {item["id"]: (directory / item["path"]).read_text(encoding="utf-8") for item in baseline["sources"]}
    base = commit("Record fictional baseline")
    scenarios = []
    revision_files = {}

    def observe(identifier, title, prompt, explanation, manifest, text, fields):
        head = git(directory, ["rev-parse", "HEAD"], env)
        expected = fixture["expectations"][identifier]
        receipt, report = run.call(identifier,
            [run.node, str(run.watch / "src/cli.mjs"), "--repo", str(directory),
             "--base", base, "--head", head, "--mode", "strict"],
            run.watch, expected["exit_code"], True)
        check(receipt, "verdict", report["verdict"], expected["verdict"])
        if "affected_claim_ids" in expected:
            check(receipt, "affected claims", sorted(item["id"] for item in report["affected_claims"]), expected["affected_claim_ids"])
            check(receipt, "compared exact fixture commits", [report["base_revision"], report["head_revision"]], [base, head])
        snapshots = {}
        for source in baseline["sources"]:
            path = directory / source["path"]
            snapshots[source["path"]] = digest(path.read_bytes())
        snapshots[".regnav/manifest.json"] = digest(manifest_path.read_bytes())
        revision_files[head] = snapshots
        run.input_files[identifier] = {
            "kind": "temporary fictional Git snapshot",
            "revision": head, "files": snapshots,
            "author_date_is_synthetic": True,
        }
        scenarios.append({
            "id": identifier, "title": title, "prompt": prompt,
            "input": {"manifest": deepcopy(manifest), "base_manifest": baseline,
                      "modified_paths": fields, "fixture_files_sha256": snapshots},
            "observed": {"source_watch": report}, "expected": expected,
            "explanation": explanation,
            "fixture_history": {
                "kind": "temporary fictional Git commits; not upstream GitHub commits",
                "base_revision": base, "head_revision": head,
                "synthetic_author_date": fixture["synthetic_git_date"],
            },
            "receipt_ids": [receipt["id"]],
            "display": watch_display(baseline, manifest, texts, text, fields, title),
        })
        return receipt, report

    observe(
        "watch-unchanged", "Compare the same recorded sources",
        "What can an unchanged result establish about these two exact snapshots?",
        "UNCHANGED describes only the listed source bytes and declared relationships at the compared commits. It is not a claim that the fictional statements are correct or that any real law is current.",
        baseline, texts["source-policy"], [],
    )
    policy_path = directory / "sources/fictional-policy.md"
    changed_text = texts["source-policy"] + fixture["source_watch_amendment"]
    policy_path.write_text(changed_text, encoding="utf-8")
    changed = commit("Change one fictional source")
    receipt, report = observe(
        "watch-source-changed", "Observe a change in a recorded source file",
        "Which claim depends on the amended fictional policy, and which separate claim should remain unaffected?",
        "The example appends the same fictional amendment used by the upstream demonstration. The real Source Watch CLI reports changed source bytes and flags only claim-routine. It does not determine which statement is legally correct.",
        baseline, changed_text, ["sources/fictional-policy.md"],
    )
    check(receipt, "exactly the policy source changed", [item["id"] for item in report["source_changes"]], ["source-policy"])
    check(receipt, "byte-change reason is retained", "SOURCE_BYTES_CHANGED" in report["source_changes"][0]["reasons"], True)

    reviewed = deepcopy(baseline)
    reviewed["claims"][0]["review"]["note"] = fixture["edited_review_note"]
    manifest_path.write_bytes(encode_json(reviewed))
    commit("Edit a fictional review declaration")
    receipt, report = observe(
        "watch-review-edited", "A review declaration cannot erase the observation",
        "The fictional review note changes after the source amendment. Does this make the earlier file change disappear?",
        "The edited note is a deliberately fictional test record. Source Watch still returns RECHECK_REQUIRED and exit 2, retaining the source finding and affected claim. No actual reviewer or completed assessment is represented.",
        reviewed, changed_text, ["sources/fictional-policy.md", ".regnav/manifest.json: claim-routine.review.note"],
    )
    check(receipt, "changed review record recorded separately", [item["id"] for item in report["review_record_changes"]], ["claim-routine"])
    check(receipt, "edited declaration does not clear changed source", [item["id"] for item in report["source_changes"]], ["source-policy"])

    invalid = deepcopy(reviewed)
    invalid["claims"][0]["evidence"][0]["source_id"] = fixture["invalid_source_id"]
    manifest_path.write_bytes(encode_json(invalid))
    commit("Record a deliberately invalid fictional source reference")
    receipt, report = observe(
        "watch-invalid-manifest", "An invalid comparison cannot become unchanged",
        "What should happen when a declared evidence link names an absent source?",
        "The real CLI rejects the invalid manifest with verdict INVALID and exit 1. It supplies no successful unchanged comparison.",
        invalid, changed_text, [".regnav/manifest.json: absent source reference"],
    )
    check(receipt, "invalid input has an explicit error", bool(report.get("errors")), True)
    return scenarios


def workflow_context():
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    valid_run = repository == "Albertito-AI/Albertito-AI" and run_id is not None and run_id.isdigit()
    return {
        "provider": "GitHub Actions" if valid_run else "local execution",
        "repository": repository if valid_run else None,
        "run_id": run_id if valid_run else None,
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT") if valid_run else None,
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}" if valid_run else None,
        "commit": os.environ.get("GITHUB_SHA") if valid_run else None,
    }


def generate(policy, watch):
    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    if (fixture["policykit_revision"], fixture["source_watch_revision"]) != (POLICY_PIN, WATCH_PIN):
        raise ValueError("Fixture revisions do not match the reviewed exporter pins.")
    node = shutil.which("node")
    if node is None:
        raise ValueError("Node.js 24 or later is required for the real Source Watch CLI.")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env.pop("PYTHONPATH", None)
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    node_version = execute([node, "--version"], ROOT, env).stdout.strip()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", node_version) or int(node_version[1:].split(".")[0]) < 24:
        raise ValueError("The pinned Source Watch project requires Node.js 24 or later.")
    git_version = execute(["git", "--version"], ROOT, env).stdout.strip()
    policy_paths = ["regnav_evidence", "examples/synthetic_ledger.json", "examples/training_sources.md", "RIGHTS.md", "AGENTS.md"]
    watch_paths = ["src", "examples/basic", "package.json", "scripts/demo.mjs", "LICENSE", "NOTICE", "AGENTS.md"]
    provenance = [
        source_record(policy, POLICY_REPO, POLICY_PIN, policy_paths, "RIGHTS.md", env),
        source_record(watch, WATCH_REPO, WATCH_PIN, watch_paths, "LICENSE", env),
    ]
    with tempfile.TemporaryDirectory(prefix="regnav-lab-") as temporary:
        directory = Path(temporary)
        run = Run(policy, watch, directory, env, node)
        original_bytes = (policy / "examples/synthetic_ledger.json").read_bytes()
        baseline = json.loads(original_bytes)
        packet = source_packet(policy, baseline)
        baseline_path = run.ledger_file("baseline", original_bytes)
        scenarios = ledger_scenarios(run, fixture, packet, baseline, baseline_path)
        scenarios.extend(watch_scenarios(run, fixture))
        # Validate that the read-only CLI calls did not change any ledger fixture.
        for identifier, record in run.input_files.items():
            if record["kind"] == "fictional training fixture":
                path = directory / "ledgers" / (identifier + ".json")
                if digest(path.read_bytes()) != record["sha256"]:
                    raise ValueError("A recorded ledger input was modified during execution.")
        for original, root, repository, pin, paths, rights in (
            (provenance[0], policy, POLICY_REPO, POLICY_PIN, policy_paths, "RIGHTS.md"),
            (provenance[1], watch, WATCH_REPO, WATCH_PIN, watch_paths, "LICENSE"),
        ):
            if source_record(root, repository, pin, paths, rights, env) != original:
                raise ValueError("An upstream source or fixture changed during execution.")
        return {
            "schema_version": 1, "id": "regnav",
            "title": "RegNav: inspect evidence and replay source changes",
            "status": "passed",
            "generated_at": utc_now(),
            "disclaimer": DISCLAIMER,
            "provenance": {
                "sources": provenance, "workflow": workflow_context(),
                "environment": {"python": sys.version.split()[0], "node": node_version, "git": git_version},
                "exporter": {
                    "path": "scripts/lab/export_regnav.py",
                    "sha256": digest(Path(__file__).read_bytes()),
                    "fixtures_path": "scripts/lab/regnav_fixtures.json",
                    "fixtures_sha256": digest(fixture_bytes),
                },
            },
            "source_packet": packet,
            "scenarios": scenarios, "receipts": run.receipts,
            "fixtures": run.input_files,
            "summary": {
                "scenario_count": len(scenarios),
                "command_count": len(run.receipts),
                "assertion_count": sum(len(item["assertions"]) for item in run.receipts),
                "meaning": "Every asserted result matched the observed CLI behaviour, including intended rejection cases.",
                "independent_human_review": "Not established by this automated run.",
            },
        }


def semantic(value):
    """Compare observable results, not execution dates or runner-specific paths."""
    result = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    result.pop("generated_at", None)
    result["provenance"].pop("workflow", None)
    result["provenance"].pop("environment", None)
    for receipt in result["receipts"]:
        receipt.pop("execution", None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policykit", required=True, type=Path)
    parser.add_argument("--source-watch", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "site/lab/data/regnav.json")
    parser.add_argument("--verify", action="store_true",
                        help="Rerun all examples and compare semantic results to the existing receipt; write nothing.")
    args = parser.parse_args()
    policy, watch, output = args.policykit.resolve(), args.source_watch.resolve(), args.output.resolve()
    if output.is_relative_to(policy) or output.is_relative_to(watch):
        raise ValueError("Output must not be inside either pinned upstream checkout.")
    previous = json.loads(output.read_text(encoding="utf-8")) if args.verify else None
    result = generate(policy, watch)
    if args.verify:
        if semantic(previous) != semantic(result):
            raise ValueError("Recorded RegNav data differs from freshly observed semantic results or source hashes.")
        print(f"RegNav replay verified: {result['summary']['command_count']} real CLI executions and "
              f"{result['summary']['assertion_count']} assertions; saved receipt and timestamps unchanged.")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        temporary.write_bytes(encode_json(result))
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"RegNav replay recorded: {result['summary']['command_count']} real CLI executions, "
          f"{result['summary']['assertion_count']} assertions, {result['summary']['scenario_count']} scenarios.")
    print(f"Output: {output}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"RegNav replay failed: {error}", file=sys.stderr)
        sys.exit(1)
