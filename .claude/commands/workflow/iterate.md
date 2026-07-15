---
name: iterate
description: Update any phase document when requirements or design change (Cross-Phase)
---

# Iterate Command

> Update any phase document when requirements or design changes (Cross-Phase)

## Usage

```bash
/iterate <file> "<change-description>"
```

## Examples

```bash
/iterate BRAINSTORM_SEARCH_API.md "Consider ElasticSearch instead of PostgreSQL full-text search"
/iterate DEFINE_SEARCH_API.md "Add support for fuzzy matching, not just exact search"
/iterate DESIGN_SEARCH_API.md "Services need to be self-contained, no shared common/"
/iterate .claude/sdd/features/DEFINE_AUTH.md "Change from JWT to session-based auth"
```

---

## What This Command Works On

`/iterate` updates the document phases of the SDD workflow:

```text
Phase 0: /brainstorm → BRAINSTORM_{FEATURE}.md ← /iterate can update
Phase 1: /define     → DEFINE_{FEATURE}.md     ← /iterate can update
Phase 2: /design     → DESIGN_{FEATURE}.md     ← /iterate can update
Phase 3: /build      → (code)                  ← update DESIGN, then /build
Phase 4: /ship       → (archive)               ← N/A
```

**Important:** to change code during Phase 3, update the DESIGN document first — the cascade to
code triggers a rebuild via `/build`. This ensures traceability.

**Scope check:** more than ~50% change, a different problem, or different target users is a new
`/define`, not an iterate — the skill carries the thresholds.

---

## What Happens

1. **Load the skill** — read `.claude/skills/sdd-iterate/SKILL.md`; it owns the full
   methodology.
2. **Classify the change** — additive, modifying, removing, or architectural, with impact level.
3. **Analyze cascades** — walk the downstream documents (BRAINSTORM → DEFINE → DESIGN → CODE)
   for required updates.
4. **Confirm with the user** — present the cascade options; never apply cascading edits
   silently.
5. **Apply** — update the target (and confirmed downstream documents) with version bumps and
   change notes.

---

## Output

| Artifact | Location |
|----------|----------|
| **Updated document** | Same location as input |
| **Cascade updates** | Downstream documents (if confirmed) |

---

## References

- Skill (methodology): `.claude/skills/sdd-iterate/SKILL.md`
- Agent (executor): `.claude/agents/workflow/iterate-agent.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
