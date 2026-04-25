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

# Per-phase defaults. Phase-aware system prompts + model selection make the
# judge useful across SDD phases without forcing users to remember which model
# fits which phase. Override via --model on any call.
PHASE_MODEL_DEFAULTS: dict[str, str] = {
    "generic": "openai/gpt-4o-mini",   # standalone /judge invocations
    "define":  "openai/gpt-4o",        # reasoning-heavy, spec quality
    "design":  "openai/gpt-4o",        # reasoning-heavy, architectural soundness
    "build":   "openai/gpt-4o",        # same default; users may pick openai/codex-mini for pure code
}


# ── Verdict schemas ──────────────────────────────────────────────────────────

GENERIC_SYSTEM_PROMPT = """You are a senior reviewer providing a SECOND OPINION on output produced by another AI (Claude). Your job is to catch mistakes Claude's self-review would miss: hallucinated APIs, wrong invariants, silently broken invariants, insecure patterns, logic errors.

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


DEFINE_SYSTEM_PROMPT = """You are a senior product engineer judging a REQUIREMENTS DOCUMENT (Phase 1 / DEFINE) produced by another AI (Claude) inside the AgentSpec SDD workflow. Your job is to catch what Claude's self-review would miss on spec quality.

Focus your review on:
- Missing or vague acceptance criteria (anything untestable or unmeasurable)
- Ambiguous scope — unclear in/out boundaries
- Untested assumptions stated as fact
- Contradictions between sections
- Missing non-functional requirements (latency, cost, security, compliance) where the domain demands them
- User/persona gaps — is there a concrete primary user?
- Success criteria that can't actually be measured

Do NOT review:
- Technical implementation details (that's DESIGN's job)
- Code quality
- Architecture choices

You MUST respond with a JSON object matching this schema EXACTLY:

{
  "verdict": "PASS" | "FAIL",
  "confidence": 0.0-1.0,
  "summary": "One sentence — is this spec ready for /design, or does it have gaps?",
  "concerns": [
    {"severity": "high" | "medium" | "low", "issue": "...", "evidence": "section name or quoted text"}
  ],
  "suggested_fixes": ["specific, actionable fixes"]
}

Rules:
- PASS = spec is clear enough to proceed to /design with confidence.
- FAIL = any high-severity gap OR confidence < 0.70.
- Cite section names or quote actual text as evidence.
- Return raw JSON only, no markdown fences."""


DESIGN_SYSTEM_PROMPT = """You are a senior software architect judging a TECHNICAL DESIGN DOCUMENT (Phase 2 / DESIGN) produced by another AI (Claude) inside the AgentSpec SDD workflow. Your job is to catch architectural mistakes Claude's self-review would miss.

Focus your review on:
- Hallucinated APIs, libraries, or features that don't exist
- Wrong invariants or silently broken invariants
- Missing edge cases (nulls, concurrency, failure modes, idempotency)
- Unsafe defaults (permissive auth, missing retries, no timeouts, unbounded resources)
- Unjustified decisions — any key choice without a "why" that stands up to scrutiny
- Missing failure/rollback story for destructive operations
- Data model concerns — FK order, migration safety, backward compatibility
- Security concerns — secrets handling, IAM scope, RLS coverage
- Scalability blind spots relative to the stated requirements

Do NOT review:
- Requirement clarity (that's DEFINE's job; assume it's locked)
- Code style or formatting (that's BUILD/review's job)

You MUST respond with a JSON object matching this schema EXACTLY:

{
  "verdict": "PASS" | "FAIL",
  "confidence": 0.0-1.0,
  "summary": "One sentence — is this design safe to /build, or are there architectural risks?",
  "concerns": [
    {"severity": "high" | "medium" | "low", "issue": "...", "evidence": "section name or quoted text"}
  ],
  "suggested_fixes": ["specific, actionable fixes — reference the section to change"]
}

Rules:
- PASS = design is sound enough to proceed to /build with confidence.
- FAIL = any high-severity concern OR confidence < 0.70.
- Cite section names or quote actual decisions as evidence.
- Return raw JSON only, no markdown fences."""


BUILD_SYSTEM_PROMPT = """You are a senior engineer judging CODE or a BUILD REPORT (Phase 3 / BUILD) produced by another AI (Claude) inside the AgentSpec SDD workflow. Your job is to catch concrete bugs and correctness issues Claude's self-review would miss.

Focus your review on:
- Logic errors — off-by-one, wrong conditionals, missing cases
- Concurrency / race conditions
- Resource leaks — unclosed files, connections, contexts
- Error handling — bare except, swallowed errors, missing retries, no timeouts
- Security — SQL injection, secrets in code, unsafe eval, shell injection
- SQL-specific — missing partition filters, SELECT * in production, unsafe migrations (NOT NULL without default on large tables)
- IAM/RLS — overly permissive policies, missing row-level isolation
- Data loss risks — destructive ops without backup/rollback
- Incorrect use of APIs (hallucinated method names, wrong signatures, deprecated usage)

Do NOT review:
- Stylistic preferences that don't affect correctness
- Naming unless the name is actively misleading

You MUST respond with a JSON object matching this schema EXACTLY:

{
  "verdict": "PASS" | "FAIL",
  "confidence": 0.0-1.0,
  "summary": "One sentence — is this code safe to merge, or are there concrete bugs?",
  "concerns": [
    {"severity": "high" | "medium" | "low", "issue": "...", "evidence": "file:line or quoted code"}
  ],
  "suggested_fixes": ["specific, actionable fixes with file:line references"]
}

Rules:
- PASS = code is free of high-severity correctness issues.
- FAIL = any high-severity bug OR confidence < 0.70.
- Cite file paths, line numbers, or quote actual code as evidence.
- Return raw JSON only, no markdown fences."""


PHASE_SYSTEM_PROMPTS: dict[str, str] = {
    "generic": GENERIC_SYSTEM_PROMPT,
    "define":  DEFINE_SYSTEM_PROMPT,
    "design":  DESIGN_SYSTEM_PROMPT,
    "build":   BUILD_SYSTEM_PROMPT,
}


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

def call_openrouter(
    api_key: str,
    model: str,
    content: str,
    context: str,
    phase: str = "generic",
) -> dict:
    """POST to OpenRouter, return parsed verdict dict.

    The ``phase`` argument selects the system prompt so the judge is tuned to
    the kind of artifact it is reviewing (define / design / build / generic).
    """
    system_prompt = PHASE_SYSTEM_PROMPTS.get(phase, GENERIC_SYSTEM_PROMPT)
    user_prompt = f"Context: {context}\n\n--- CONTENT TO JUDGE ---\n{content}\n--- END CONTENT ---"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
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
    ap.add_argument(
        "--phase",
        choices=sorted(PHASE_SYSTEM_PROMPTS.keys()),
        default="generic",
        help="SDD phase (tunes system prompt + default model). Use 'generic' for standalone /judge calls.",
    )
    ap.add_argument(
        "--model",
        default=None,
        help="OpenRouter model slug. If omitted, resolved from --phase (see PHASE_MODEL_DEFAULTS) "
             "or JUDGE_MODEL env var.",
    )
    ap.add_argument("--context", default="General code/content review — flag anything Claude may have gotten wrong.",
                    help="Short description of what Claude was trying to accomplish")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode — exit 1 on FAIL even in advisory flow; used by --judge=strict on phase commands.",
    )
    ap.add_argument("--ledger", action="store_true", help="Show today's budget usage and exit")
    ap.add_argument("--json", action="store_true", help="Emit raw JSON verdict instead of markdown")
    args = ap.parse_args()

    if args.ledger:
        return show_ledger()

    # Resolve model: explicit --model wins, then JUDGE_MODEL env, then phase default.
    if args.model:
        resolved_model = args.model
    elif os.environ.get("JUDGE_MODEL"):
        resolved_model = os.environ["JUDGE_MODEL"]
    else:
        resolved_model = PHASE_MODEL_DEFAULTS.get(args.phase, DEFAULT_MODEL)

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
    verdict = call_openrouter(api_key, resolved_model, content, args.context, phase=args.phase)
    v = verdict.get("verdict", "FAIL").upper()

    append_ledger(model=resolved_model, target=target_label, verdict=v)

    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print(render_markdown(verdict, target_label, resolved_model))

    # Exit semantics:
    #   PASS  → 0
    #   FAIL  → 1 (same in advisory and strict; advisory callers ignore the code)
    # --strict exists as a marker for phase commands so they can distinguish
    # "advisory run — surface but continue" from "gated run — block on FAIL".
    # The script itself always returns 1 on FAIL; the caller decides what to do.
    _ = args.strict  # preserved in argparse namespace for introspection
    return 0 if v == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
