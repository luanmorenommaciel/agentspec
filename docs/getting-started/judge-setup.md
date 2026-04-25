# Judge Layer — Setup Guide (V0)

> Get a second opinion from GPT, Gemini, or any OpenRouter-supported model on code Claude just produced.

---

## Why Use the Judge

Single-model LLMs fail in predictable ways — hallucinated APIs, silently wrong invariants, insecure defaults. A second model from a different family catches different errors than Claude's own self-review.

The Judge is **advisory and opt-in**. You invoke it explicitly with `/judge <file>`. No automatic hooks in V0.

**Good fits:** schema migrations, IAM/RLS policies, Terraform before apply, complex SQL on production data.
**Skip it for:** trivial edits, prose docs, anything under ~20 lines.

---

## One-Time Setup

### 1. Get an OpenRouter API key

1. Go to https://openrouter.ai/keys
2. Sign in (GitHub OAuth or email)
3. Create a key — name it `agentspec-judge` so it's easy to spot in the dashboard
4. Add credit — $5 is plenty for weeks of judge calls at default settings

### 2. Export the key

Add to your shell rc file (`~/.zshrc`, `~/.bashrc`, or `~/.profile`):

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

Reload your shell: `source ~/.zshrc`

### 3. (Optional) Tune defaults

```bash
# Change the default model (default: openai/gpt-4o-mini — cheap + capable)
export JUDGE_MODEL=openai/gpt-4o          # More capable, ~10x the cost
export JUDGE_MODEL=google/gemini-2.5-pro  # Different model family — good for cross-bias

# Change the daily budget ceiling (default: 10 calls/day)
export JUDGE_BUDGET=25
```

---

## First Run

Test against a small file:

```bash
/judge scripts/judge.py --context "Python script for OpenRouter verdict calls"
```

You should see a markdown verdict block in the chat. Confirm the ledger recorded it:

```bash
/judge --ledger
```

---

## Cost Reference

Rough per-call cost at default settings (openai/gpt-4o-mini, ~2000-token target):

| Target size | Approx cost per call |
|-------------|---------------------|
| Small file (<100 lines) | $0.001 – $0.003 |
| Medium file (100-500 lines) | $0.003 – $0.010 |
| Large file (500-2000 lines) | $0.010 – $0.030 |

At 10 calls/day (default budget) on mostly medium files → roughly **$0.50-$1.00/month**.

Switch to `openai/gpt-4o` for higher-quality verdicts at ~10x the cost — still under $10/month at default budget.

---

## Understanding Verdicts

The judge returns a markdown block like:

```markdown
## Judge Verdict — FAIL

**Target:** `migrations/2026_04_20_add_user_roles.sql`  |  **Model:** `openai/gpt-4o-mini`  |  **Confidence:** 0.82

**Summary:** Migration adds NOT NULL column without a backfill default — will fail on any existing rows.

### Concerns

| Severity | Issue | Evidence |
|----------|-------|----------|
| high | NOT NULL without default | line 3: `ALTER TABLE users ADD COLUMN role text NOT NULL;` |
| medium | No index on new column | line 3: no CREATE INDEX follows the ALTER |

### Suggested Fixes

- Add `DEFAULT 'member'` to the column definition, or run a backfill before adding NOT NULL
- Add `CREATE INDEX CONCURRENTLY idx_users_role ON users(role);` after the column is populated
```

### What the fields mean

| Field | Interpretation |
|-------|----------------|
| **Verdict** | `PASS` = no high-severity issues AND confidence ≥ 0.70. `FAIL` = anything else |
| **Confidence** | 0.0 – 1.0. Below 0.5 means the judge itself isn't sure — read carefully |
| **Concerns** | Ordered by severity. `high` items are the ones that would make Claude's output actually break |
| **Evidence** | Line numbers or quoted strings. If evidence is vague, the judge may be hallucinating — trust Claude more |

### When the judge disagrees with Claude

The judge is wrong sometimes too. The tie-breaker:

1. **Read the evidence.** If the judge cites a specific line or function, verify it's real.
2. **Run the code.** Empirical truth beats either LLM.
3. **Ask a human.** Especially for security or production DDL.

Treat the judge as a diligent reviewer whose comments are sometimes off-base — not as an oracle.

---

## Budget Controls

The judge enforces a hard per-day ceiling to prevent runaway spend:

| Mechanism | Behavior |
|-----------|----------|
| Daily ceiling | Default 10 calls/day (UTC). Override with `JUDGE_BUDGET=25` |
| Ledger | Every call appends a line to `.claude/storage/judge-ledger.jsonl` |
| Over-budget | Script exits with code 3 and a message — no OpenRouter call made |
| Reset | Automatic at UTC midnight. No manual reset needed |

Inspect usage any time:

```bash
/judge --ledger
```

---

## Privacy Note

Content you judge is sent to **OpenRouter**, which routes to the model provider you selected (OpenAI, Google, etc.). Standard API privacy terms apply — see [OpenRouter privacy](https://openrouter.ai/privacy).

**Do not judge:**
- Files containing API keys, passwords, or secrets
- Customer data (PII, payment info, health records)
- Code marked confidential by your organization

Check `.gitignore` entries before judging — if a file is gitignored, it's probably sensitive.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `OPENROUTER_API_KEY not set` | Export the key in your shell rc and `source` it |
| `HTTP 401` | Key is invalid or expired — regenerate at https://openrouter.ai/keys |
| `HTTP 402` | Out of credit — add more at https://openrouter.ai/account |
| `HTTP 429` | Rate-limited — wait 60s, or lower `JUDGE_BUDGET` |
| `Judge returned non-JSON` | Model ignored the JSON schema — try a more capable model like `openai/gpt-4o` |
| `File exceeds 200KB` | V0 doesn't chunk — split the file or judge a smaller region |

---

## Roadmap

V0 is intentionally minimal. Upcoming:

- **V1** — `--judge` flag on `/design`, `/build`, `/ship` (once Flag System ships)
- **V2** — multi-model ensembles (`--judge=ensemble`)
- **V3** — opt-in PostToolUse hook for file patterns like `migrations/**/*.sql`
- **V4** — MCP server + high-stakes classifier

See `tasks/backlog.md` → Judge Layer via OpenRouter.
