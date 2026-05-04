---
name: judge
description: Cross-model second opinion via OpenRouter — catches hallucinations Claude's self-review misses
---

# Judge Command (V0)

> Get a second opinion from a non-Claude model on code or content Claude just produced.

## Usage

```bash
/judge <file>                              # Judge a file with default model
/judge <file> --context "building DLT CDC" # Add context about the task
/judge <file> --model anthropic/claude-3.5-sonnet  # Override model (still via OpenRouter)
/judge --ledger                             # Show today's budget usage
```

---

## What This Command Does

Sends the target file + optional task context to a non-Claude model via OpenRouter. That model returns a structured verdict:

| Field | Meaning |
|-------|---------|
| **Verdict** | `PASS` (no high-severity issues, confidence ≥ 0.70) or `FAIL` |
| **Confidence** | 0.0 – 1.0, judge's own self-assessment |
| **Summary** | One-sentence gist |
| **Concerns** | Table of issues (severity + evidence citing line numbers or quoted strings) |
| **Suggested fixes** | Concrete repairs |

The verdict renders as markdown in the chat. A ledger entry goes to `.claude/storage/judge-ledger.jsonl`.

---

## When to Use

**Good fits:**
- Schema migrations or DDL you're about to run
- IAM / RLS policies — security-sensitive
- Complex SQL that touches production data
- Terraform / CloudFormation before apply
- Any output where "confidently wrong" would be expensive

**Skip it for:**
- Trivial edits, renames, formatting
- Documentation prose (judge is tuned for code/config correctness)
- Anything under ~20 lines (not enough signal)

The judge is **advisory**. Claude is the author; you make the final call.

---

## Setup

```bash
# One-time: get an OpenRouter key at https://openrouter.ai/keys
export OPENROUTER_API_KEY=sk-or-v1-...

# Optional: change default model (default is openai/gpt-4o-mini — cheap + capable)
export JUDGE_MODEL=openai/gpt-4o

# Optional: change daily budget ceiling (default 10 calls/day)
export JUDGE_BUDGET=25
```

Full setup guide: `docs/getting-started/judge-setup.md`

---

## Examples

### Example 1: Judge a schema migration

```bash
/judge migrations/2026_04_20_add_user_roles.sql --context "Postgres migration adding role column with backfill"
```

Returns a PASS/FAIL on whether the migration handles concurrency, nullability, and indexing properly.

### Example 2: Judge a Terraform module

```bash
/judge infra/iam/s3_writer_role.tf --context "Least-privilege role for Lambda writing to S3 bucket"
```

### Example 3: See what you've used today

```bash
/judge --ledger
```

Output:
```
Judge Ledger — .claude/storage/judge-ledger.jsonl
  Today (2026-04-20):  3 / 10 calls
  All-time:            17 calls

  Today's calls:
    [PASS] openai/gpt-4o-mini  migrations/2026_04_20_add_user_roles.sql
    [FAIL] openai/gpt-4o-mini  infra/iam/s3_writer_role.tf
    [PASS] openai/gpt-4o-mini  models/staging/stg_orders.sql
```

---

## Execution

The command delegates to `scripts/judge.py`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/judge.py "$ARGUMENTS"
```

(In source repo use `./scripts/judge.py` directly.)

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Verdict = PASS |
| 1 | Verdict = FAIL |
| 2 | Config error (missing key, bad args) |
| 3 | Daily budget exhausted |
| 4 | Network / OpenRouter API error |

Non-zero exit codes let this command compose into shell pipelines and CI later.

---

## Roadmap

This is **V0** — opt-in, per-file, single model. Future versions:

- **V1** — graduates to a `--judge[=model]` flag on `/design`, `/build`, `/ship` once the Flag System ships
- **V2** — multi-model ensembles (`--judge=ensemble` queries GPT + Gemini, requires consensus)
- **V3** — opt-in PostToolUse hook for specific file patterns
- **V4** — MCP server wrapper + high-stakes classifier using agent tier signal

See `tasks/backlog.md` → Judge Layer via OpenRouter for the full roadmap.
