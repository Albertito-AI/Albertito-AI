#!/usr/bin/env python3
"""Gate Registry publication on the public service version and MCP behaviour."""
import argparse
import asyncio
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from check_registry import reviewed_metadata

TOOLS = {"search_resources", "get_resource", "get_ibol_lesson"}
MODERN = "2026-07-28"
LEGACY = "2025-11-25"
SERVER_NAME = "albert-research-resource-agent"
INFO_KEY = "io.modelcontextprotocol/serverInfo"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_info(info, expected_version):
    require(isinstance(info, dict), "Missing server identity")
    require(info.get("name") == SERVER_NAME, "Unexpected live MCP server name")
    require(info.get("version") == expected_version, "Live service version differs from reviewed Registry version")


def verify_tools(tools):
    require(isinstance(tools, list), "Tool discovery is not a list")
    require({x.get("name") for x in tools} == TOOLS and len(tools) == len(TOOLS),
            "Live tool set differs from the documented three tools")
    require(all(x.get("annotations", {}).get("readOnlyHint") is True for x in tools),
            "Every published tool must be declared read-only")


def verify_book(result):
    require(result.get("isError") is False, "Book lookup returned a tool error")
    record = result.get("structuredContent", {}).get("resource", {})
    require(record.get("id") == "ibol-book", "Book lookup returned a different resource")
    require("Albert Tan Sin Hon" in record.get("attribution", ""), "Book author credit missing")
    require(record.get("citation_url") == "https://doi.org/10.21827/6ac3948159a9e", "Book DOI differs")
    require("CC BY-NC-ND 4.0" in record.get("rights", ""), "Book rights missing")


def verify_legacy_notification(status, content):
    require(status == 202 and content == b"",
            "Legacy notification must return HTTP 202 with an empty body")


async def legacy_probe(http, endpoint, version):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    init = {"jsonrpc": "2.0", "id": "legacy-initialize", "method": "initialize",
            "params": {"protocolVersion": LEGACY, "capabilities": {},
                       "clientInfo": {"name": "albert-registry-preflight", "version": "1.1.0"}}}
    response = await http.post(endpoint, json=init, headers=headers)
    response.raise_for_status()
    body = response.json()
    require(body.get("id") == init["id"] and "error" not in body, "Legacy initialize was rejected")
    result = body.get("result", {})
    require(result.get("protocolVersion") == LEGACY, "Legacy protocol was not negotiated")
    verify_info(result.get("serverInfo"), version)
    require("tools" in result.get("capabilities", {}), "Legacy tools capability absent")
    require("mcp-session-id" not in response.headers, "Expected stateless legacy endpoint")
    headers["MCP-Protocol-Version"] = LEGACY
    notification = await http.post(endpoint, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=headers)
    verify_legacy_notification(notification.status_code, notification.content)
    listing = await http.post(endpoint, json={"jsonrpc": "2.0", "id": "legacy-tools", "method": "tools/list", "params": {}}, headers=headers)
    listing.raise_for_status()
    result = listing.json()
    require(result.get("id") == "legacy-tools" and "error" not in result, "Legacy tool discovery failed")
    verify_tools(result.get("result", {}).get("tools"))
    return {"protocol_version": LEGACY, "initialize": "passed", "tools_list": "passed"}


async def inspect(expected, report):
    require(importlib.metadata.version("mcp") == "2.3.0", "Use the frozen MCP 2.3.0 verification environment")
    endpoint = expected["remotes"][0]["url"]
    origin = endpoint.removesuffix("/api/mcp")

    async def record_response(response):
        require("authorization" not in response.request.headers, "Public check must not send credentials")
        report["requests"].append({"path": response.request.url.path,
                                   "method": response.request.headers.get("mcp-method"),
                                   "http_status": response.status_code,
                                   "content_type": response.headers.get("content-type")})

    # Use the configured HTTPS network route as-is. No identity spoofing,
    # access-control workaround, automatic retry, API key or sign-in credential.
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    async with httpx2.AsyncClient(proxy=proxy, timeout=30, follow_redirects=False,
                                 event_hooks={"response": [record_response]}) as http:
        health = await http.get(origin + "/healthz")
        health.raise_for_status()
        data = health.json()
        require(data.get("status") == "ok" and data.get("version") == expected["version"],
                "Health check did not confirm the reviewed service version")
        require(data.get("catalogue_records", 0) > 0 and data.get("ibol_lessons", 0) > 0,
                "Public resource snapshot is empty")
        report["health"] = data
        transport = streamable_http_client(endpoint, http_client=http)
        async with Client(transport, mode=MODERN, read_timeout_seconds=30) as client:
            discover = await client.session.send_discover(MODERN)
            require(MODERN in discover.get("supportedVersions", []), "Modern protocol is not supported")
            verify_info(discover.get("_meta", {}).get(INFO_KEY), expected["version"])
            tools = (await client.list_tools()).model_dump(by_alias=True)["tools"]
            verify_tools(tools)
            book = (await client.call_tool("get_resource", {"id": "ibol-book"})).model_dump(by_alias=True)
            verify_book(book)
            search = (await client.call_tool("search_resources", {"query": "insurance trust governance", "limit": 3})).model_dump(by_alias=True)
            require(search.get("isError") is False and search.get("structuredContent", {}).get("results"),
                    "Public search returned no usable result")
            lesson = (await client.call_tool("get_ibol_lesson", {"chapter": 3, "include_facilitator": False})).model_dump(by_alias=True)
            require(lesson.get("isError") is False and lesson.get("structuredContent", {}).get("lesson", {}).get("title"),
                    "Public lesson lookup failed")
            report["modern_mcp"] = {"protocol_version": client.protocol_version,
                                    "tool_names": sorted(TOOLS), "book_citation": "passed",
                                    "search": "passed", "lesson": "passed"}
        report["legacy_mcp"] = await legacy_probe(http, endpoint, expected["version"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    expected = reviewed_metadata()
    report = {"started_at_unix": time.time(), "endpoint": expected["remotes"][0]["url"],
              "expected_version": expected["version"], "sdk": "mcp 2.3.0", "requests": []}
    try:
        asyncio.run(inspect(expected, report))
        report["passed"] = True
    except Exception as error:
        report.update({"passed": False, "error_type": type(error).__name__, "error": str(error)})
    finally:
        report["finished_at_unix"] = time.time()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
