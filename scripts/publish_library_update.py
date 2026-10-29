"""Commit only generated library records, rejecting a concurrently changed main."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = (
    "site/lab/data/library.json",
    "site/lab/data/library-review-queue.json",
    "site/lab/data/library-history.json",
)


def git(*args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        # Do not echo subprocess diagnostics from an authenticated operation.
        raise RuntimeError("Git operation failed; no force push was attempted: " + args[0])
    return result.stdout.strip()


def output(name: str, value: str) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")
    print(f"{name}={value}")


def main() -> None:
    if os.environ.get("GITHUB_REPOSITORY") != "Albertito-AI/Albertito-AI":
        raise SystemExit("Publishing is restricted to the original public repository.")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise SystemExit("Generated library records may be published only from main.")
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        raise SystemExit("The workflow's repository token is required.")
    remote_url = git("config", "--get", "remote.origin.url").rstrip("/")
    if remote_url not in (
        "https://github.com/Albertito-AI/Albertito-AI",
        "https://github.com/Albertito-AI/Albertito-AI.git",
    ):
        raise SystemExit("Unexpected repository remote; refusing authenticated publishing.")
    env = dict(os.environ)
    env.pop("GH_TOKEN", None)
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    encoded = base64.b64encode(("x-access-token:" + token).encode()).decode()
    env["GIT_CONFIG_VALUE_0"] = "AUTHORIZATION: basic " + encoded
    baseline = git("rev-parse", "HEAD")
    remote = git("ls-remote", "origin", "refs/heads/main", env=env).split()[0]
    if remote != baseline:
        raise SystemExit("Main advanced during refresh. Preserve the current publication and rerun from its new head.")
    for name in ALLOWED:
        if not (ROOT / name).is_file():
            raise SystemExit("Expected generated record missing: " + name)
    git("add", "--", *ALLOWED)
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    if not staged.issubset(set(ALLOWED)):
        raise SystemExit("Unexpected staged path; refusing to commit unrelated work.")
    record = json.loads((ROOT / ALLOWED[0]).read_text(encoding="utf-8"))
    output("health", str(record["status"]))
    if not staged:
        output("changed", "false")
        output("commit_sha", baseline)
        return
    git("-c", "user.name=github-actions[bot]", "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", "Refresh source-linked research library records")
    git("push", "origin", "HEAD:refs/heads/main", env=env)
    output("changed", "true")
    output("commit_sha", git("rev-parse", "HEAD"))


if __name__ == "__main__":
    main()
