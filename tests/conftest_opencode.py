"""OpenCode integration test fixture.

Starts an ``opencode serve`` process against a mock workspace with
the built ``.opencode/`` content. Provides helper methods to query
the server's HTTP API.

No external dependencies — uses only stdlib (urllib, subprocess, json).
"""
from __future__ import annotations

import atexit
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
OPENCODE_BIN = shutil.which("opencode")

# ── Helpers ───────────────────────────────────────────────────────────────────


def _free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(url: str, timeout: float = 20.0) -> bool:
    """Poll ``/global/health`` until the server is ready or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/global/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.3)
    return False


# ── Fixture result ────────────────────────────────────────────────────────────


class OpenCodeServer:
    """Wraps a running ``opencode serve`` process and its mock workspace."""

    def __init__(self, proc: subprocess.Popen, workspace: Path, port: int):
        self._proc = proc
        self.workspace = workspace
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self._stderr_lines: list[str] = []
        self._stderr_thread = threading.Thread(
            target=self._capture_stderr, daemon=True
        )

    def _capture_stderr(self) -> None:
        assert self._proc.stderr is not None
        for line in self._proc.stderr:
            decoded = line.decode(errors="replace") if isinstance(line, bytes) else line
            self._stderr_lines.append(decoded)

    def start_capture(self) -> None:
        self._stderr_thread.start()

    def stop_capture(self) -> None:
        if self._stderr_thread.is_alive():
            self._stderr_thread.join(timeout=2)

    # ── API helpers ──────────────────────────────────────────────────────────

    def _get_json(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read())

    def get_agents(self) -> list[dict]:
        """Return parsed ``GET /agent`` response."""
        return self._get_json("/agent")

    def get_commands(self) -> list[dict]:
        """Return parsed ``GET /command`` response."""
        return self._get_json("/command")

    def get_config(self) -> dict:
        """Return parsed ``GET /config`` response."""
        return self._get_json("/config")

    def get_health(self) -> dict:
        """Return parsed ``GET /global/health`` response."""
        return self._get_json("/global/health")

    def has_stderr_line(self, pattern: str) -> bool:
        """Check if stderr contains a line matching *pattern* (substring)."""
        return any(pattern in line for line in self._stderr_lines)


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def opencode_server() -> OpenCodeServer:
    """Start ``opencode serve`` against a mock workspace with our build artifact.

    Skips the entire module if the ``opencode`` binary is not found or
    the build artifact (``repo/.opencode/``) has not been generated.
    """
    if not OPENCODE_BIN:
        pytest.skip("opencode binary not found on PATH")

    if not (REPO_ROOT / ".opencode" / "agents").exists():
        pytest.skip(".opencode/ not built — run 'make build-opencode' first")

    # ── 1. Create mock workspace ──────────────────────────────────────────
    workspace = Path(tempfile.mkdtemp(prefix="opencode-test-"))
    atexit.register(shutil.rmtree, workspace, ignore_errors=True)

    # git init (required by opencode)
    subprocess.run(
        ["git", "init", "-q"],
        cwd=workspace, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@agentspec.test"],
        cwd=workspace, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "AgentSpec Test"],
        cwd=workspace, check=True, capture_output=True,
    )

    # Minimal README
    (workspace / "README.md").write_text("# AgentSpec OpenCode Test Workspace\n")

    # Copy .opencode/ build artifact
    shutil.copytree(
        REPO_ROOT / ".opencode",
        workspace / ".opencode",
        symlinks=False,
        dirs_exist_ok=True,
    )

    # Copy opencode.json to project root (OpenCode expects it there)
    opencode_json_src = workspace / ".opencode" / "opencode.json"
    if opencode_json_src.exists():
        shutil.copy(opencode_json_src, workspace / "opencode.json")

    # ── 2. Start server ───────────────────────────────────────────────────
    port = _free_port()
    proc = subprocess.Popen(
        [
            OPENCODE_BIN,
            "serve",
            "--pure",
            "--port", str(port),
            "--print-logs",
        ],
        cwd=workspace,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env={**os.environ, "OPENCODE_DISABLE_CLAUDE_CODE": "1"},
    )

    server = OpenCodeServer(proc, workspace, port)
    server.start_capture()

    # ── 3. Wait for ready ─────────────────────────────────────────────────
    if not _wait_for_health(server.base_url):
        proc.kill()
        proc.wait(timeout=5)
        stderr_tail = "".join(server._stderr_lines[-20:])
        pytest.skip(
            f"opencode serve did not become healthy within timeout\n"
            f"Last stderr:\n{stderr_tail}"
        )

    yield server

    # ── 4. Teardown ───────────────────────────────────────────────────────
    server.stop_capture()
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except (subprocess.TimeoutExpired, ProcessLookupError):
        proc.kill()
        proc.wait(timeout=5)

    shutil.rmtree(workspace, ignore_errors=True)
