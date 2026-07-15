---
name: sdd-ship
description: |
  Archive a completed feature and close the SDD cycle (Phase 4): verify the build is truly complete, archive every phase artifact, capture lessons learned, update all phase documents to Shipped, and clean the working folders.
  Carries the full ship methodology — verification order, ship readiness matrix, the concrete archive procedure, status transitions, lessons-learned categories, quality gate, and the end-of-cycle handoff. Executed by ship-agent and the /ship command; loadable directly when closing a feature by hand.
  Use when completed work needs closing: "ship the feature", "archive the completed feature", "Phase 4", "lessons learned", "finalize the feature".
  Not for implementation work — writing code, completing tasks, or fixing failing tests is Phase 3; use sdd-build. Shipping starts only after the build report shows 100% completion.
---

# SDD Ship — feature archival and lessons learned (Phase 4)

Ship closes the 5-phase SDD workflow: it turns a completed feature's working documents into a permanent archive with lessons learned, marks every phase document Shipped, and leaves the working folders clean for the next feature. Nothing ships unless the build is verifiably complete.

## Contract

| Aspect | Value |
|--------|-------|
| **Input (required)** | `.claude/sdd/features/DEFINE_{FEATURE}.md` · `.claude/sdd/features/DESIGN_{FEATURE}.md` · `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md` |
| **Input (optional)** | `.claude/sdd/features/BRAINSTORM_{FEATURE}.md` (if Phase 0 was used) |
| **Output** | `.claude/sdd/archive/{FEATURE}/` containing all artifacts + `SHIPPED_{DATE}.md` |
| **Template** | `.claude/sdd/templates/SHIPPED_TEMPLATE.md` — the SHIPPED document's required shape; follow it, never improvise the format |
| **Contract source** | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` (`ship:`, `status_transitions:`, `folder_structure:`, `naming:`) |

Naming rules (from the contracts): feature names are `SCREAMING_SNAKE_CASE` (e.g., `USER_NOTIFICATIONS`); the archive folder is `.claude/sdd/archive/{FEATURE_NAME}/`; the shipped file is `SHIPPED_{YYYY-MM-DD}.md`, dated with the ship date.

---

## Verification order

Resolve completeness in this order before anything is archived:

```text
┌─────────────────────────────────────────────────────────────────────┐
│  1. ARTIFACT VERIFICATION (confirm completeness)                     │
│     └─ Read: .claude/sdd/features/DEFINE_{FEATURE}.md                │
│     └─ Read: .claude/sdd/features/DESIGN_{FEATURE}.md                │
│     └─ Read: .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md           │
│     └─ Optional: .claude/sdd/features/BRAINSTORM_{FEATURE}.md        │
│                                                                      │
│  2. BUILD REPORT VALIDATION                                          │
│     └─ All tasks completed?                                          │
│     └─ All tests passing?                                            │
│     └─ No blocking issues?                                           │
│                                                                      │
│  3. CONFIDENCE ASSIGNMENT                                            │
│     ├─ All artifacts present + tests pass  → 0.95 → Ship             │
│     ├─ Artifacts present + minor issues    → 0.80 → Ask user         │
│     └─ Missing artifacts or failures       → 0.50 → Cannot ship      │
└─────────────────────────────────────────────────────────────────────┘
```

### Ship Readiness Matrix

| Artifacts | Tests | Issues | Confidence | Action |
|-----------|-------|--------|------------|--------|
| All present | Pass | None | 0.95 | Ship immediately |
| All present | Pass | Minor | 0.85 | Ship with notes |
| All present | Fail | Any | 0.50 | Cannot ship |
| Missing | Any | Any | 0.30 | Cannot ship |

### When NOT to ship

Any of these blocks the ship — stop and route back to `/build`:

- BUILD_REPORT shows incomplete tasks
- Tests are failing
- Blocking issues documented in the build report
- Missing required artifacts (DEFINE, DESIGN, BUILD_REPORT)

Ship only when all acceptance tests from DEFINE pass, the build report shows 100% completion, and no blocking issues remain.

---

## Process

### Step 1 — Verify completion

```markdown
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)
Read(.claude/sdd/features/DESIGN_{FEATURE}.md)
Read(.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md)

# Verify build report shows success
```

Run the verification order above. Confidence below 0.85 → do not proceed.

### Step 2 — Create archive folder

```bash
mkdir -p .claude/sdd/archive/{FEATURE_NAME}/
```

### Step 3 — Copy artifacts to archive

```bash
cp .claude/sdd/features/DEFINE_{FEATURE}.md .claude/sdd/archive/{FEATURE}/
cp .claude/sdd/features/DESIGN_{FEATURE}.md .claude/sdd/archive/{FEATURE}/
cp .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md .claude/sdd/archive/{FEATURE}/
```

If Phase 0 was used, also archive the brainstorm:

```bash
cp .claude/sdd/features/BRAINSTORM_{FEATURE}.md .claude/sdd/archive/{FEATURE}/
```

Resulting archive structure:

```text
.claude/sdd/archive/{FEATURE}/
├── BRAINSTORM_{FEATURE}.md  (if exists)
├── DEFINE_{FEATURE}.md
├── DESIGN_{FEATURE}.md
├── BUILD_REPORT_{FEATURE}.md
└── SHIPPED_{DATE}.md
```

### Step 4 — Generate SHIPPED document

Compose the SHIPPED document following `.claude/sdd/templates/SHIPPED_TEMPLATE.md` — the template owns the format; do not improvise sections. It covers the summary, timeline, metrics, what was built, success-criteria verification against DEFINE, lessons learned, recommendations, and the archived-artifact list.

### Step 5 — Update document statuses

Per `WORKFLOW_CONTRACTS.yaml` (`status_transitions`, trigger `/ship completes`), ship MUST update **ALL** phase documents to Shipped — this is the contract obligation that prevents stale "Ready for X" statuses:

| File | Field | Value |
|------|-------|-------|
| `DEFINE_{FEATURE}.md` | Status | `✅ Shipped` |
| `DESIGN_{FEATURE}.md` | Status | `✅ Shipped` |
| `BUILD_REPORT_{FEATURE}.md` | Status | `✅ Shipped` |

Apply the updates to the **archived copies** (the working copies are removed in Step 6) and add a revision-history note to each:

```markdown
Edit: archive/{FEATURE}/DEFINE_{FEATURE}.md
  - Status: → "✅ Shipped"
  - Add revision: "Shipped and archived"

Edit: archive/{FEATURE}/DESIGN_{FEATURE}.md
  - Status: → "✅ Shipped"
  - Add revision: "Shipped and archived"

Edit: archive/{FEATURE}/BUILD_REPORT_{FEATURE}.md
  - Status: → "✅ Shipped"
```

### Step 6 — Clean up working files

```bash
rm .claude/sdd/features/DEFINE_{FEATURE}.md
rm .claude/sdd/features/DESIGN_{FEATURE}.md
rm .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
```

If a BRAINSTORM was archived in Step 3, remove its working copy too:

```bash
rm .claude/sdd/features/BRAINSTORM_{FEATURE}.md
```

### Step 7 — Save SHIPPED document

```markdown
Write(.claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md)
```

---

## Lessons learned

Review all artifacts for insights and capture at least 2 specific lessons in these categories:

| Category | Example |
|----------|---------|
| **Process** | "Breaking into 4 independent functions enabled parallel development" |
| **Technical** | "Using config.yaml instead of env vars improved testability" |
| **Communication** | "Clarifying v1/v2 scope early prevented feature creep" |
| **Tools** | "Using X library simplified Y" |

Rules for good lessons:

1. **Don't skip this** — lessons learned prevent future mistakes.
2. **Be honest** — document what didn't work too.
3. **Be specific and actionable** — "Better planning" → "Create architecture diagram before coding".
4. **Archive everything** — future you will thank present you.

Avoid vague lessons:

```markdown
❌ "Better planning" (too vague)
❌ "More testing" (not specific)
❌ "Improved communication" (not actionable)
```

---

## Quality Gate

Before saving the SHIPPED document:

```text
PRE-FLIGHT CHECK
├─ [ ] All artifacts verified present (DEFINE, DESIGN, BUILD_REPORT)
├─ [ ] BUILD_REPORT shows all tasks complete
├─ [ ] All tests passing
├─ [ ] Acceptance tests from DEFINE verified
├─ [ ] No blocking issues in the build report
├─ [ ] Code deployed (if applicable)
├─ [ ] Archive directory created
├─ [ ] All artifacts copied to archive
├─ [ ] ALL archived documents' status updated to "✅ Shipped"
├─ [ ] At least 2 specific lessons documented
└─ [ ] Working files cleaned up from features/ and reports/
```

---

## Close the cycle — end-of-cycle handoff

When the archive is complete, report closure to the user:

| Handoff item | Content |
|--------------|---------|
| **Archive location** | `.claude/sdd/archive/{FEATURE}/` with the full artifact list |
| **SHIPPED document** | Path to `SHIPPED_{DATE}.md` + one-line summary of what shipped |
| **Lessons headline** | The 2-3 most actionable lessons captured |
| **Statuses** | Confirmation that DEFINE, DESIGN, and BUILD_REPORT now read "✅ Shipped" |
| **Workspace** | `features/` and `reports/` clean of this feature's working files |
| **Next step** | Start the next feature with `/define` (or `/brainstorm` for an unshaped idea) |

---

## Anti-Patterns

| Never Do | Why | Instead |
|----------|-----|---------|
| Ship with failing tests | Broken code archived | Fix tests first — route back to `/build` |
| Ship incomplete builds | Missing functionality | Complete build first |
| Vague lessons learned | Not actionable | Be specific and concrete |
| Skip artifact verification | May be incomplete | Always verify all exist |
| Leave working files | Clutter | Clean up after archive |
| Re-inline the SHIPPED format | Drifts from the template | Follow `SHIPPED_TEMPLATE.md` |

---

## References

- Template: `.claude/sdd/templates/SHIPPED_TEMPLATE.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Executor: `.claude/agents/workflow/ship-agent.md`
- Entrypoint: `.claude/commands/workflow/ship.md`
- Previous phase: `.claude/commands/workflow/build.md`
