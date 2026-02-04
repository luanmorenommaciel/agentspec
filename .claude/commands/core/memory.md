---
name: memory
description: Save valuable insights from the current session to storage
---

# Memory Command

Save session insights to `.claude/storage/` for future reference.

## Usage

```bash
/memory                           # Save current session insights
/memory "specific note to save"   # Save with specific context
```

---

## What It Does

1. **Analyzes** current conversation for valuable insights
2. **Compresses** to high-signal format (decisions, patterns, gotchas)
3. **Saves** to `.claude/storage/memory-{YYYY-MM-DD}.md`

---

## When to Use

Use `/memory` when you've discovered something worth remembering:

- ✅ Non-obvious decisions with rationale
- ✅ Patterns that worked well
- ✅ Gotchas discovered
- ✅ Architecture decisions
- ✅ Terminology clarifications

**Don't save:**

- ❌ Step-by-step implementation details (obvious from code)
- ❌ Temporary debugging info
- ❌ Every session (only valuable ones)

---

## Output Format

Creates: `.claude/storage/memory-{YYYY-MM-DD}.md`

```markdown
# Memory: {date}

> {One-line summary of session}

## Decisions Made

| Decision | Rationale | Impact |
| -------- | --------- | ------ |
| {what} | {why} | {files affected} |

## Patterns Discovered

- {pattern}: {where applied}

## Gotchas

- {gotcha}: {how to avoid}

## Open Items

- [ ] {item for next session}

---
*Saved: {timestamp}*
```

---

## Process

When invoked:

```text
1. Scan conversation for:
   - Decisions (look for "decided", "chose", "will use")
   - Patterns (look for reusable solutions)
   - Gotchas (look for "gotcha", "watch out", "careful")
   - Open items (look for "TODO", "later", "next time")

2. Compress ruthlessly:
   - Max 5 decisions
   - Max 3 patterns
   - Max 3 gotchas
   - Max 3 open items

3. Write to storage:
   - Create .claude/storage/ if not exists
   - Append to existing file if same date
   - Use consistent format
```

---

## Example

```text
User: /memory "Completed authentication refactoring"

→ Scanning conversation...
→ Found: 2 decisions, 1 pattern, 1 gotcha

Saved to: .claude/storage/memory-2026-01-23.md

## Preview:
> Completed authentication refactoring with JWT + refresh tokens

| Decision | Rationale |
| -------- | --------- |
| Use JWT + refresh | Stateless, scales better |
| 15min access token | Balance security/UX |

Pattern: Token rotation on refresh

Gotcha: Must invalidate refresh tokens on password change
```

---

## Best Practices

| Do | Don't |
| -- | ----- |
| Save only valuable insights | Save every session |
| Compress ruthlessly | Write long summaries |
| Reference file paths | Duplicate code comments |
| Store decisions + rationale | Store implementation details |
