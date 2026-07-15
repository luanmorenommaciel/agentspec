---
name: sdd-iterate
description: |
  Update an existing SDD phase document (BRAINSTORM/DEFINE/DESIGN) mid-stream with full cascade awareness: classify the change (additive, modifying, removing, architectural), apply it with a version bump and change note, walk the cascade rules for downstream impact, and confirm with the user before applying any cascading edits. Owns the SDD change-management methodology: cascade rules, version-tracking and status-field obligations, and the iterate-vs-restart thresholds. Use when the user wants to update the requirements or design mid-stream — "requirements changed", "the design needs to change", "cascade the change" — or any existing phase document must change after downstream work has started. Do not use for a brand-new feature or a fundamentally different problem: a different problem, different users, or a change beyond roughly half the document calls for sdd-brainstorm/sdd-define instead of an iterate.
---

# SDD Iterate — Mid-Stream Change Management

Requirements change mid-stream; that is normal. This skill owns the methodology for updating any
SDD phase document without breaking the chain: classify the change, apply it with version
tracking, analyze downstream cascades, and propagate updates only after user confirmation.

Executor: `iterate-agent`. Entrypoint: `/iterate <file> "<change-description>"`. Contract: the
`iterate` block in `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` owns the command surface,
the `works_with` chain, and the thresholds; per that block's `skill` entry, this skill owns the
rules below.

## Document Relationships

`/iterate` works on the document phases of the SDD workflow:

```text
Phase 0: /brainstorm → BRAINSTORM_{FEATURE}.md ← /iterate can update
Phase 1: /define     → DEFINE_{FEATURE}.md     ← /iterate can update
Phase 2: /design     → DESIGN_{FEATURE}.md     ← /iterate can update
Phase 3: /build      → (code)                  ← update DESIGN, then /build
Phase 4: /ship       → (archive)               ← N/A
```

Changes ripple downstream:

```text
BRAINSTORM ────► DEFINE ────► DESIGN ────► CODE
     │              │            │           │
     ▼              ▼            ▼           ▼
  Changes      May need      May need     May need
  here         update        update       rebuild
```

| Change In | Cascades To | Example |
|-----------|-------------|---------|
| BRAINSTORM | DEFINE | New YAGNI items → update out-of-scope |
| DEFINE | DESIGN | New requirement → add component |
| DESIGN | CODE | New file in manifest → create via `/build`; removed file → delete |

**To change code during Phase 3, update the DESIGN document first** — the cascade to code
triggers a rebuild via `/build`. Editing code directly breaks traceability.

## Process

Six steps, in order:

1. **Load Target Document** — read the target file and identify the phase by file pattern
   (`BRAINSTORM_*.md` → Phase 0, `DEFINE_*.md` → Phase 1, `DESIGN_*.md` → Phase 2). Read the
   downstream documents that exist. Never classify a change before loading current state.
2. **Analyze Change** — classify the change type and assess impact (Change Classification).
3. **Apply Changes** — make the modification, bump the version, add a change note (Version
   Tracking).
4. **Assess Cascade Need** — walk the cascade rules for each downstream document (Cascade
   Analysis).
5. **Execute Cascade** — when a cascade is needed, confirm with the user first (User
   Confirmation Before Cascading), then apply.
6. **Save Updates** — write the updated target document, plus downstream documents when the
   user confirmed a cascade.

## Change Classification

Classify every change before touching the document:

| Type | Marker | Impact | Example |
|------|--------|--------|---------|
| **Additive** | + | Low — adds to existing scope | "Also support PDF" |
| **Modifying** | ~ | Medium — changes existing scope | "Change from X to Y" |
| **Removing** | − | Medium — reduces scope | "Remove feature Z" |
| **Architectural** | ! | High — fundamental approach change | "Use a different pattern entirely" |

Confidence assignment drives how to proceed:

| Situation | Confidence | Action |
|-----------|------------|--------|
| Additive change, no cascade | 0.95 | Apply directly |
| Modifying change, cascade needed | 0.85 | Ask user |
| Removing change, cascade needed | 0.80 | Ask user |
| Architectural change | 0.70 | Full review with user |

## Cascade Analysis

For each downstream document: check whether the change affects it, calculate the required
updates, and present options to the user before applying anything downstream.

**BRAINSTORM → DEFINE:**

| BRAINSTORM Change | DEFINE Impact |
|-------------------|---------------|
| Changed approach | May need different problem focus |
| New YAGNI items | Out of scope needs update |
| Changed users | Target users section needs update |
| Changed constraints | Constraints section needs update |
| New discovery answers | May affect requirements |

**DEFINE → DESIGN:**

| DEFINE Change | DESIGN Impact |
|---------------|---------------|
| New requirement | May need new component |
| Changed success criteria | May need different approach |
| Scope expansion | Needs new sections |
| Scope reduction | Can simplify |
| New constraint | Must be accommodated |

**DESIGN → CODE:**

| DESIGN Change | CODE Impact |
|---------------|-------------|
| New file in manifest | Create file |
| Removed file | Delete file |
| Changed pattern | Update affected files |
| New decision | May need refactor |
| Architecture change | Significant refactor |

Code-level cascades are never hand-applied: the DESIGN update is the deliverable here, and the
rebuild routes through `/build` (escalation to build-agent).

## User Confirmation Before Cascading

Never apply cascading edits silently. When a cascade is needed, ask the user:

```markdown
"This change to {DOCUMENT} affects {DOWNSTREAM}. Options:
(a) Update {DOWNSTREAM} automatically to match
(b) Just update {DOCUMENT}, I'll handle {DOWNSTREAM} manually
(c) Show me what would change first"
```

- **(a)** — apply the downstream updates, with a version bump and change note in every touched
  document.
- **(b)** — update only the target; record in its change note that downstream documents are now
  pending manual updates.
- **(c)** — present a preview of the downstream changes, then re-offer (a) and (b).

Architectural changes always get a full review with the user before anything is written.

## Version Tracking

Every applied change is tracked. Obligations:

1. Bump the version in the document's Revision History.
2. Add a change note with date, author, and reasoning.
3. Repeat the bump + note in every downstream document updated by a cascade.

Fields: version, date, author, changes. The section shape is owned by the templates
(`${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md`, `DESIGN_TEMPLATE.md`):

```markdown
## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-25 | define-agent | Initial version |
| 1.1 | 2026-01-25 | iterate-agent | Added PDF support |
| 1.2 | 2026-01-26 | iterate-agent | Removed OCR (out of scope) |
```

**Status fields:** document Status values are set by phase completions per
`status_transitions.update_rules` in WORKFLOW_CONTRACTS (for example, `/design` completing marks
DEFINE "✅ Complete (Designed)"). A mid-stream change can invalidate that claim — after updating
a document whose downstream phase already completed, verify the Status fields still tell the
truth, and surface any mismatch in the cascade prompt instead of silently rewriting the flow.

## Quality Gate

Verify before reporting completion:

```text
PRE-FLIGHT CHECK
├─ [ ] Target document loaded
├─ [ ] Change classified (additive/modifying/removing/architectural)
├─ [ ] Downstream documents identified
├─ [ ] Cascade impact assessed
├─ [ ] User informed of cascade requirements
├─ [ ] Version bumped in revision history
├─ [ ] Change note added with reasoning
└─ [ ] Downstream updates applied (if cascaded and confirmed)
```

### Contract Gate

Iterate has no contract of its own: after applying the edit, validate the edited document against the contract for **its own phase**. The artifact is whatever document you just edited, and the `--phase` is the phase that produced it (`define` for a DEFINE document, `design` for a DESIGN document) — repeat this for each document a cascade touched:

```bash
# --phase must match the document being validated, not the phase you came from
${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/spec-lint <EDITED_DOC.md> --phase <define|design> \
  --contracts-file ${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml
```

Which phases carry a contract is decided by `required_sections` in `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`, not by this skill — if the edited document's phase has none, the linter reports that itself; act on what it returns. Run it as `${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/USAGE.md` documents, and act on the verdict exactly as defined there. The exit-code contract and verdict semantics are owned by that document and by the `contract_enforcement` block (`exit_code_contract`, `verdict_semantics`) of the same contract file — which is also where this binding is declared. Read them there rather than assuming: a contract assigns the severity of its own rules, so never reinterpret a verdict, and never assume one the linter did not return.

## Anti-Patterns

| Never Do | Why | Instead |
|----------|-----|---------|
| Skip cascade analysis | Inconsistent documents | Always check downstream |
| Update without versioning | Lost history | Always bump version |
| Apply cascading edits without confirmation | User loses control of scope | Ask with the (a)/(b)/(c) prompt |
| Apply architectural changes silently | Major impact | Full review with user |
| Ignore downstream conflicts | Broken workflow | Resolve conflicts first |
| Edit CODE directly | Breaks traceability | Update DESIGN, rebuild via `/build` |

## When to Use /iterate vs a New /define

Thresholds (contract: `iterate.thresholds`):

| Situation | Action |
|-----------|--------|
| < 30% change | `/iterate` |
| Add/modify features | `/iterate` |
| Change constraints | `/iterate` |
| > 50% different | New `/define` |
| Different problem entirely | New `/define` |
| Different target users | New `/define` |
| Fundamental approach change | New `/define` |

An architectural change classified in-flow (0.70 confidence) triggers a full review — that
review decides between an in-place update and a fresh `/define`.

## Tips

1. **Iterate early** — catch changes before coding starts.
2. **Be specific** — "Add X" beats "make it better".
3. **Check cascade** — changes ripple downstream.
4. **Keep history** — version tracking shows evolution.
5. **Don't fight it** — requirements change; that is normal.

## References

- Contract: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` (`iterate` block: command
  surface, `works_with` chain, thresholds; `status_transitions.update_rules` for Status fields;
  `contract_enforcement` for the binding, exit-code contract, and verdict semantics)
- Contract gate runner: `${CLAUDE_PLUGIN_ROOT}/tools/spec-linter/USAGE.md`
- Templates: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DEFINE_TEMPLATE.md`,
  `${CLAUDE_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md` (Revision History shape)
- Executor: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/iterate-agent.md`
- Entrypoint: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/iterate.md`
