#!/usr/bin/env python3
"""Judge Layer V0 — cross-model second opinion via OpenRouter.

Reads a target file (or stdin), sends it to a non-Claude model via OpenRouter,
and returns a PASS/FAIL verdict with reasoning. Designed to be invoked by the
`/judge` slash command — user-initiated, one call per invocation, budget-capped.

V0 is intentionally minimal:
- No MCP server, no PostToolUse hook, no classifier
- Single model per call (default openai/gpt-4o-mini — cheap, capable)
- Hard budget ceiling per session, enforced via append-only ledger

Usage:
  python3 scripts/judge.py <file> [--model MODEL] [--context CONTEXT]
  python3 scripts/judge.py --stdin [--model MODEL] [--context CONTEXT]
  python3 scripts/judge.py --ledger       # show today's usage
  python3 scripts/judge.py --reset-ledger # zero the budget (confirm prompt)

Environment:
  OPENROUTER_API_KEY   Required. Get one at https://openrouter.ai/keys
  JUDGE_MODEL          Optional. Default: openai/gpt-4o-mini
  JUDGE_BUDGET         Optional. Max calls per UTC day. Default: 10

Exit codes:
  0  verdict = PASS
  1  verdict = FAIL
  2  config error (missing key, bad args)
  3  budget exceeded
  4  network / API error
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / ".claude" / "storage" / "judge-ledger.jsonl"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_BUDGET = 10


# ── Verdict schema ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior reviewer providing a SECOND OPINION on output produced by another AI (Claude). Your job is to catch mistakes Claude's self-review would miss: hallucinated APIs, wrong invariants, silently broken invariants, insecure patterns, logic errors.

You MUST respond with a JSON object matching this schema EXACTLY:

{
  "verdict": "PASS" | "FAIL",
  "confidence": 0.0-1.0,
  "summary": "One sentence — what's right or what's wrong.",
  "concerns": [
    {"severity": "high" | "medium" | "low", "issue": "...", "evidence": "..."}
  ],
  "suggested_fixes": ["..."]
}

Rules:
- PASS means: no high-severity issues AND confidence >= 0.70.
- FAIL means: any high-severity issue OR confidence < 0.70.
- Be specific. Cite line numbers, function names, or exact quoted strings as evidence.
- If the content is fine, return an empty concerns array and empty suggested_fixes.
- Do NOT wrap the JSON in markdown fences. Return raw JSON only."""


# ── Budget ledger ────────────────────────────────────────────────────────────

def today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def load_today_count() -> int:
    if not LEDGER.exists():
        return 0
    today = today_utc()
    count = 0
    with LEDGER.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("date") == today:
                count += 1
    return count


def append_ledger(model: str, target: str, verdict: str, cost_usd: float | None = None) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "date": today_utc(),
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": model,
        "target": target,
        "verdict": verdict,
    }
    if cost_usd is not None:
        entry["cost_usd"] = cost_usd
    with LEDGER.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def show_ledger() -> int:
    if not LEDGER.exists():
        print("No judge calls recorded yet.")
        return 0
    today = today_utc()
    today_calls = []
    total_calls = 0
    with LEDGER.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            total_calls += 1
            if entry.get("date") == today:
                today_calls.append(entry)
    budget = int(os.environ.get("JUDGE_BUDGET", DEFAULT_BUDGET))
    print(f"Judge Ledger — {LEDGER.relative_to(REPO_ROOT)}")
    print(f"  Today ({today}):  {len(today_calls)} / {budget} calls")
    print(f"  All-time:         {total_calls} calls")
    if today_calls:
        print("\n  Today's calls:")
        for e in today_calls:
            verdict = e.get("verdict", "?")
            model = e.get("model", "?")
            target = e.get("target", "?")
            print(f"    [{verdict:4}] {model}  {target}")
    return 0


# ── OpenRouter call ──────────────────────────────────────────────────────────

def call_openrouter(api_key: str, model: str, content: str, context: str) -> dict:
    """POST to OpenRouter, return parsed verdict dict."""
    user_prompt = f"Context: {context}\n\n--- CONTENT TO JUDGE ---\n{content}\n--- END CONTENT ---"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/luanmorenommaciel/agentspec",
            "X-Title": "AgentSpec Judge V0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"[ERROR] OpenRouter HTTP {e.code}: {body[:300]}", file=sys.stderr)
        sys.exit(4)
    except urllib.error.URLError as e:
        print(f"[ERROR] Network error: {e.reason}", file=sys.stderr)
        sys.exit(4)

    api_resp = json.loads(raw)
    try:
        content_str = api_resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print(f"[ERROR] Unexpected OpenRouter response shape: {raw[:400]}", file=sys.stderr)
        sys.exit(4)

    # Strip accidental markdown fences
    content_str = re.sub(r"^```(?:json)?\s*\n?", "", content_str.strip())
    content_str = re.sub(r"\n?```\s*$", "", content_str)

    try:
        verdict = json.loads(content_str)
    except json.JSONDecodeError:
        print(f"[ERROR] Judge returned non-JSON:\n{content_str[:500]}", file=sys.stderr)
        sys.exit(4)

    # Usage/cost best-effort
    usage = api_resp.get("usage", {})
    if usage:
        verdict["_usage"] = usage
    return verdict


# ── Markdown renderer ────────────────────────────────────────────────────────

def render_markdown(verdict: dict, target: str, model: str) -> str:
    v = verdict.get("verdict", "?").upper()
    conf = verdict.get("confidence", 0)
    summary = verdict.get("summary", "")
    concerns = verdict.get("concerns", [])
    fixes = verdict.get("suggested_fixes", [])

    badge = "PASS" if v == "PASS" else "FAIL"
    out = [
        f"## Judge Verdict — {badge}",
        "",
        f"**Target:** `{target}`  |  **Model:** `{model}`  |  **Confidence:** {conf:.2f}",
        "",
        f"**Summary:** {summary}",
        "",
    ]

    if concerns:
        out.append("### Concerns")
        out.append("")
        out.append("| Severity | Issue | Evidence |")
        out.append("|----------|-------|----------|")
        for c in concerns:
            sev = c.get("severity", "?")
            issue = (c.get("issue") or "").replace("|", "\\|")
            ev = (c.get("evidence") or "").replace("|", "\\|")
            out.append(f"| {sev} | {issue} | {ev} |")
        out.append("")

    if fixes:
        out.append("### Suggested Fixes")
        out.append("")
        for fix in fixes:
            out.append(f"- {fix}")
        out.append("")

    usage = verdict.get("_usage", {})
    if usage:
        prompt_t = usage.get("prompt_tokens", "?")
        comp_t = usage.get("completion_tokens", "?")
        out.append(f"*Tokens — prompt: {prompt_t}  completion: {comp_t}*")

    out.append("")
    out.append(f"_Judge is advisory. Claude is the author; final call is yours._")
    return "\n".join(out) + "\n"


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Judge Layer V0 — OpenRouter second opinion")
    ap.add_argument("target", nargs="?", help="Path to file to judge (or use --stdin)")
    ap.add_argument("--stdin", action="store_true", help="Read content from stdin instead of a file")
    ap.add_argument("--model", default=os.environ.get("JUDGE_MODEL", DEFAULT_MODEL),
                    help=f"OpenRouter model slug (default: {DEFAULT_MODEL})")
    ap.add_argument("--context", default="General code/content review — flag anything Claude may have gotten wrong.",
                    help="Short description of what Claude was trying to accomplish")
    ap.add_argument("--ledger", action="store_true", help="Show today's budget usage and exit")
    ap.add_argument("--json", action="store_true", help="Emit raw JSON verdict instead of markdown")
    args = ap.parse_args()

    if args.ledger:
        return show_ledger()

    # Config checks
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("[ERROR] OPENROUTER_API_KEY not set.", file=sys.stderr)
        print("  Get a key at https://openrouter.ai/keys and export it:", file=sys.stderr)
        print("  export OPENROUTER_API_KEY=sk-or-v1-...", file=sys.stderr)
        return 2

    # Resolve content
    if args.stdin:
        content = sys.stdin.read()
        target_label = "<stdin>"
    elif args.target:
        target_path = Path(args.target).expanduser().resolve()
        if not target_path.exists():
            print(f"[ERROR] File not found: {target_path}", file=sys.stderr)
            return 2
        if target_path.stat().st_size > 200_000:
            print(f"[ERROR] File exceeds 200KB — judge V0 does not chunk large files.", file=sys.stderr)
            return 2
        content = target_path.read_text(encoding="utf-8", errors="replace")
        try:
            target_label = str(target_path.relative_to(REPO_ROOT))
        except ValueError:
            target_label = str(target_path)
    else:
        ap.error("Provide a file path or --stdin")
        return 2

    if not content.strip():
        print("[ERROR] Target content is empty.", file=sys.stderr)
        return 2

    # Budget check
    budget = int(os.environ.get("JUDGE_BUDGET", DEFAULT_BUDGET))
    used = load_today_count()
    if used >= budget:
        print(f"[ERROR] Daily budget exhausted: {used}/{budget} calls today.", file=sys.stderr)
        print(f"  Raise via: export JUDGE_BUDGET={budget * 2}", file=sys.stderr)
        print(f"  Inspect via: python3 scripts/judge.py --ledger", file=sys.stderr)
        return 3

    # Judge call
    verdict = call_openrouter(api_key, args.model, content, args.context)
    v = verdict.get("verdict", "FAIL").upper()

    append_ledger(model=args.model, target=target_label, verdict=v)

    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print(render_markdown(verdict, target_label, args.model))

    return 0 if v == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
