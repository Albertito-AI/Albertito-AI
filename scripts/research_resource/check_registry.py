#!/usr/bin/env python3
"""Verify reviewed metadata and Registry readback. Only an HTTP 404 exits 2."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, build_opener

NAME = "io.github.Albertito-AI/research-resource-agent"
ENDPOINT = "https://albert-agent-network.travelingbert.chatgpt.site/api/mcp"
SCHEMA = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
REGISTRY = "https://registry.modelcontextprotocol.io"
DEFAULT_SERVER = Path("mcp/research-resource-agent/server.json")
DEFAULT_REQUEST = Path("mcp/research-resource-agent/release-request.json")


class NoRedirect(HTTPRedirectHandler):
    """An exact Registry version lookup must not follow another location."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def reviewed_metadata(server_path=DEFAULT_SERVER, request_path=DEFAULT_REQUEST):
    raw = server_path.read_bytes()
    server = json.loads(raw)
    request = json.loads(request_path.read_text())
    if set(request) != {"name", "version", "server_sha256", "required_protocols"}:
        raise ValueError("Release request must contain the reviewed fields only")
    if request["server_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("server.json differs from the reviewed release-request hash")
    if server.get("name") != NAME or request["name"] != NAME:
        raise ValueError("Unexpected Registry namespace or server name")
    if request["version"] != server.get("version"):
        raise ValueError("Release request and server version differ")
    if request["required_protocols"] != ["2026-07-28", "2025-11-25"]:
        raise ValueError("Both reviewed MCP protocol gates must remain enabled")
    if set(server) != {"$schema", "name", "title", "description", "version", "websiteUrl", "remotes"}:
        raise ValueError("Unexpected fields in this remote-only metadata record")
    if server["$schema"] != SCHEMA:
        raise ValueError("Unexpected Registry schema")
    if server["websiteUrl"] != "https://alberttansinhon.com/for-agents/":
        raise ValueError("Unexpected public guide URL")
    if server["remotes"] != [{"type": "streamable-http", "url": ENDPOINT}]:
        raise ValueError("Remote must be the reviewed public Streamable HTTP endpoint")
    return server


def registry_url(expected):
    return (REGISTRY + "/v0.1/servers/" + quote(expected["name"], safe="")
            + "/versions/" + quote(expected["version"], safe=""))


def compare_record(expected, actual):
    if not isinstance(actual, dict) or not isinstance(actual.get("server"), dict):
        raise ValueError("Registry response lacks the server object")
    server = actual["server"]
    for field in ("name", "version", "title", "description", "websiteUrl"):
        if server.get(field) != expected[field]:
            raise ValueError("Existing Registry " + field + " differs from the reviewed record")
    if server.get("repository") not in (None, {}):
        raise ValueError("Unexpected source-repository claim in Registry record")
    if server.get("packages") not in (None, []):
        raise ValueError("Unexpected package distribution in remote-only Registry record")
    remotes = server.get("remotes")
    if not isinstance(remotes, list) or len(remotes) != 1:
        raise ValueError("Registry record does not contain exactly one remote")
    remote = remotes[0]
    if not isinstance(remote, dict) or set(remote) - {"type", "url", "headers", "variables"}:
        raise ValueError("Unexpected remote configuration")
    if {k: remote.get(k) for k in ("type", "url")} != expected["remotes"][0]:
        raise ValueError("Existing Registry remote differs from the reviewed endpoint")
    if remote.get("headers") not in (None, []) or remote.get("variables") not in (None, {}):
        raise ValueError("Registry remote unexpectedly requires extra connection inputs")
    meta = actual.get("_meta", {})
    official = meta.get("io.modelcontextprotocol.registry/official", meta)
    if official.get("status") != "active":
        raise ValueError("Registry version is not confirmed active")
    return {"state": "matching_active_version", "registry_url": registry_url(expected),
            "server": {key: server[key] for key in expected if key != "$schema"},
            "registry_status": official["status"]}


def check(expected, opener=None):
    url = registry_url(expected)
    open_exact = opener or build_opener(NoRedirect()).open
    try:
        with open_exact(url, timeout=30) as response:
            if response.geturl() != url or response.status != 200:
                raise ValueError("Registry lookup did not return HTTP 200 at the exact version URL")
            actual = json.load(response)
    except HTTPError as error:
        if error.code == 404 and error.geturl() == url:
            return 2, {"state": "absent", "registry_url": url, "http_status": 404}
        raise
    return 0, compare_record(expected, actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", type=Path, default=DEFAULT_SERVER)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    expected = reviewed_metadata(args.server, args.request)
    if args.metadata_only:
        code, receipt = 0, {"state": "reviewed_metadata_valid", "name": expected["name"],
                            "version": expected["version"], "remote": expected["remotes"][0]}
    else:
        code, receipt = check(expected)
    print(json.dumps(receipt, indent=2))
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"state": "failed", "error_type": type(error).__name__,
                          "error": str(error)}), file=sys.stderr)
        raise SystemExit(1)
