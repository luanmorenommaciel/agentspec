"""Unit tests for the AgentSpec MCP server.

We exercise the dispatch surface directly (no stdio loop) so tests run fast.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_PKG = REPO_ROOT / "packages" / "agentspec-mcp"


@pytest.fixture(scope="module")
def server():
    """Import the MCP server, pointing it at the local .claude/ tree."""
    sys.path.insert(0, str(MCP_PKG))
    # Reset module cache so AGENTSPEC_ROOT env vars take effect.
    if "agentspec_mcp" in sys.modules:
        del sys.modules["agentspec_mcp"]
    if "agentspec_mcp.server" in sys.modules:
        del sys.modules["agentspec_mcp.server"]
    if "agentspec_mcp.routing" in sys.modules:
        del sys.modules["agentspec_mcp.routing"]
    os.environ.setdefault("AGENTSPEC_RESOURCES", str(REPO_ROOT / ".claude"))
    module = importlib.import_module("agentspec_mcp.server")
    return module


class TestHandshake:
    def test_initialize(self, server):
        response = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert response["result"]["serverInfo"]["name"] == "agentspec-mcp"

    def test_tools_list_includes_core_tools(self, server):
        response = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        names = {tool["name"] for tool in response["result"]["tools"]}
        assert {"kb_search", "kb_read", "route_agent", "sdd_status", "judge"} <= names


class TestKbSearch:
    def test_finds_known_keyword(self, server):
        response = server.handle_request({
            "jsonrpc": "2.0", "id": 10,
            "method": "tools/call",
            "params": {"name": "kb_search", "arguments": {"query": "incremental", "limit": 2}},
        })
        result = json.loads(response["result"]["content"][0]["text"])
        assert "hits" in result
        assert len(result["hits"]) >= 1


class TestRouteAgent:
    def test_top_result_is_relevant_for_schema(self, server):
        response = server.handle_request({
            "jsonrpc": "2.0", "id": 11,
            "method": "tools/call",
            "params": {"name": "route_agent", "arguments": {"task": "design star schema for analytics", "top_k": 3}},
        })
        result = json.loads(response["result"]["content"][0]["text"])
        assert result["results"]
        top_names = {r["name"] for r in result["results"]}
        assert "schema-designer" in top_names


class TestSddStatus:
    def test_unknown_feature_reports_phases(self, server, tmp_path):
        response = server.handle_request({
            "jsonrpc": "2.0", "id": 12,
            "method": "tools/call",
            "params": {"name": "sdd_status", "arguments": {"feature": "demo", "workspace": str(tmp_path)}},
        })
        result = json.loads(response["result"]["content"][0]["text"])
        assert result["feature"] == "DEMO"
        assert all(not phase["exists"] for phase in result["phases"].values())


class TestErrors:
    def test_unknown_tool(self, server):
        response = server.handle_request({
            "jsonrpc": "2.0", "id": 13,
            "method": "tools/call",
            "params": {"name": "not_a_tool", "arguments": {}},
        })
        assert "error" in response
        assert "unknown tool" in response["error"]["message"]

    def test_unknown_method(self, server):
        response = server.handle_request({
            "jsonrpc": "2.0", "id": 14,
            "method": "nope",
            "params": {},
        })
        assert "error" in response
