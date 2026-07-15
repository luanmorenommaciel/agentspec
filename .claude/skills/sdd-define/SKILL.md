---
name: sdd-define
description: |
  Phase 1 of the SDD workflow: capture and validate requirements in one pass. Owns the full Define methodology — classify the input (BRAINSTORM document, meeting notes, email thread, conversation, or direct request), extract entities (problem, users, MoSCoW goals, success criteria, acceptance tests, constraints, out of scope, assumptions), gather technical and data engineering context, calculate the clarity score against the 12/15 gate, fill gaps with targeted questions, and generate the DEFINE document from the shared template with correct status transitions. Use when the user wants to capture requirements, define the feature, structure project scope, or compute a clarity score — "capture requirements", "define the feature", "clarity score", "Phase 1", /define. Do not use for open-ended exploration of ideas and approaches (that is sdd-brainstorm, Phase 0) or for architecture and technical specification (that is sdd-design, Phase 2).
---

# SDD Define — capture and validate requirements (Phase 1)

Transform unstructured input into validated, actionable requirements with explicit scope boundaries and measurable success criteria. This skill owns the Phase 1 methodology; the `define-agent` executes it and the `/define` command is its entrypoint.

## Workflow position

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md (THIS SKILL)
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md
```

Define combines what used to be Intake + PRD + Refine into a single, iterative phase. When fed a BRAINSTORM document, extraction is streamlined because discovery questions are already answered, approaches have been evaluated, YAGNI has been applied, and the user has validated the direction.

## Knowledge architecture

Follow KB-first resolution — it is mandatory, not optional, because the Design phase depends on the KB domains selected here.

```text
┌─────────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE RESOLUTION ORDER                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. KB DISCOVERY (identify applicable domains)                      │
│     └─ Read: .claude/kb/_index.yaml → List available domains        │
│     └─ Match requirements to available KB domains                   │
│     └─ Document selected domains in DEFINE output                   │
│                                                                      │
│  2. TEMPLATE LOADING (ensure consistent structure)                  │
│     └─ Read: .claude/sdd/templates/DEFINE_TEMPLATE.md               │
│     └─ Read: .claude/CLAUDE.md → Project context                    │
│                                                                      │
│  3. CONFIDENCE ASSIGNMENT                                            │
│     ├─ All entities extracted clearly       → 0.95 → Proceed        │
│     ├─ Some gaps, clarification needed      → 0.80 → Ask questions  │
│     └─ Major ambiguity, unclear scope       → 0.60 → Block, clarify │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Clarity score thresholds

| Score | Status | Action |
|-------|--------|--------|
| 12-15/15 | HIGH | Proceed to /design |
| 9-11/15 | MEDIUM | Ask targeted questions |
| 0-8/15 | LOW | Cannot proceed, clarify |

## Process

### Step 1: Load Context

```markdown
Read(.claude/sdd/templates/DEFINE_TEMPLATE.md)
Read(CLAUDE.md)

# If file provided:
Read(<input-file>)
```

### Step 2: Classify Input

Identify the input type to guide extraction:

| Input Type | Pattern | Focus |
|------------|---------|-------|
| `brainstorm_document` | BRAINSTORM_*.md from /brainstorm | Pre-validated, extract directly |
| `meeting_notes` | Bullet points, action items | Decisions, requirements |
| `email_thread` | Re:, Fwd:, signatures | Requests, constraints |
| `conversation` | Informal language | Core problem, users |
| `direct_requirement` | Structured request | All elements present |
| `mixed_sources` | Multiple formats | Consolidate, deduplicate |

### Step 3: Extract Entities

Pull structured data from the input using these patterns:

| Entity | Look For |
|--------|----------|
| **Problem** | "We're struggling with...", "The issue is...", "Pain point:" |
| **Users** | "For the team...", "Customers want...", "Users need..." |
| **Goals** | "We need to...", "Must have...", "Should have..." |
| **Success Criteria** | "Success means...", "We'll know when...", "Measured by..." |
| **Acceptance Tests** | "Given/When/Then", "Test case:", "Scenario:" |
| **Constraints** | "Must work with...", "Can't change...", "Limited by..." |
| **Out of Scope** | "Not including...", "Deferred to...", "Excluded:" |
| **Assumptions** | "Assuming that...", "We expect...", "If X then...", "Depends on..." |

Classify every goal with MoSCoW priority:

| Priority | Meaning |
|----------|---------|
| MUST | MVP fails without this (non-negotiable) |
| SHOULD | Important, but a workaround exists |
| COULD | Nice-to-have, cut first if timeline is tight |

Formalize assumptions into a trackable risk register (ID, statement, impact if wrong, validated checkbox). BRAINSTORM captures exploratory assumptions; DEFINE turns them into trackable risks.

### Step 4: Gather Technical Context

Ask three questions (skip any the input already answers):

1. Where should this live? (src/, functions/, deploy/)
2. Which KB domains apply? (list available from .claude/kb/)
3. Does this need infrastructure changes?

Why these three:

- **Location** → Prevents misplaced files
- **KB Domains** → Design phase pulls correct patterns
- **IaC Impact** → Catches infrastructure needs early

### Step 5: Extract Data Engineering Context (when triggered)

Trigger: the requirements mention data pipelines, ETL, analytics, warehouses, data quality, schemas, or data sources.

| Entity | Look For |
|--------|----------|
| Source Systems | "from Postgres...", "Kafka topic...", "S3 bucket...", "API endpoint..." |
| Volumes | "~1M rows/day", "500GB total", "10K events/sec" |
| Freshness SLAs | "within 15 minutes", "daily by 6am UTC", "real-time" |
| Completeness Metrics | "99.9% of records", "no nulls in PK", "all sources present" |
| Schema Contracts | "order_id is INT", "status ENUM", "amount DECIMAL(18,2)" |
| Source Inventory | "3 Postgres tables + 1 Kafka topic + S3 clickstream" |

Record the findings in the DEFINE document's "Data Contract (if applicable)" section — source inventory, schema contract, freshness SLAs, completeness metrics, lineage requirements. The section's shape lives in the template; do not invent a parallel format.

### Step 6: Calculate Clarity Score

Score each element 0-3 points:

| Element | Score | Meaning |
|---------|-------|---------|
| Problem | 0-3 | Clear, specific, actionable |
| Users | 0-3 | Identified with pain points |
| Goals | 0-3 | Measurable outcomes |
| Success | 0-3 | Testable criteria |
| Scope | 0-3 | Explicit boundaries |

Scoring guide:

- 0 = Missing entirely
- 1 = Vague or incomplete
- 2 = Clear but missing details
- 3 = Crystal clear, actionable

Total: 15 points. **Minimum to proceed: 12/15 (80%).** Record the per-element breakdown with notes in the document's Clarity Score Breakdown section.

### Step 7: Fill Gaps (if score < 12)

Use `AskUserQuestion` with specific options, targeting the lowest-scoring elements first:

```markdown
Example questions:
- "Who is the primary user: (a) internal team, (b) customers, (c) both?"
- "What's the timeline: (a) this sprint, (b) this quarter, (c) no deadline?"
```

Re-score after each round of answers. Never pad entities to reach the gate — a fabricated requirement is worse than an honest "Needs Clarification".

### Step 8: Generate Document

Write the structured document following the template, then save:

```markdown
Write(.claude/sdd/features/DEFINE_{FEATURE_NAME}.md)
```

Then update statuses (see Status transitions) and hand off (see Handoff).

## Output obligations

| Obligation | Value |
|------------|-------|
| File | `.claude/sdd/features/DEFINE_{FEATURE_NAME}.md` |
| Feature name | SCREAMING_SNAKE_CASE (e.g., USER_NOTIFICATIONS) |
| Structure | `.claude/sdd/templates/DEFINE_TEMPLATE.md` — the template owns the document format; follow it rather than re-creating sections here |
| Status values | `Draft`, `In Progress`, `Needs Clarification`, `Ready for Design` |

Required sections (per `WORKFLOW_CONTRACTS.yaml`): metadata, problem statement, target users, goals (MoSCoW), success criteria, acceptance tests, out of scope, constraints, assumptions, clarity score breakdown, open questions, revision history.

## Status transitions

Completing Define carries two status obligations, per `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` (`status_transitions` and `update_rules`). Skipping them leaves stale "Ready for X" statuses that break the workflow.

1. **Own document:** set the DEFINE document's `Status` field to `Ready for Design` when clarity >= 12/15, or `Needs Clarification` when below the gate.
2. **Upstream document:** when the input was a BRAINSTORM document, edit `BRAINSTORM_{FEATURE}.md` and set its `Status` field to `✅ Complete (Defined)`.

## Quality gate

Before generating the DEFINE document:

```text
PRE-FLIGHT CHECK
├─ [ ] Problem statement is one clear sentence
├─ [ ] At least one user persona with pain point
├─ [ ] Goals have MoSCoW priority (MUST/SHOULD/COULD)
├─ [ ] Success criteria are measurable (numbers, %)
├─ [ ] Acceptance tests are testable
├─ [ ] Out of scope is explicit (not empty)
├─ [ ] Assumptions documented with impact if wrong
├─ [ ] KB domains identified for Design phase
├─ [ ] Technical context gathered (location, IaC impact)
└─ [ ] Clarity score >= 12/15
```

The clarity gate is hard: below 12/15 the phase does not complete — ask, iterate, or mark the document `Needs Clarification` and state what is missing.

### Contract gate

Before handing off to `/design`, validate the document just written against this phase's contract — artifact `DEFINE_{FEATURE_NAME}.md`, phase `define`:

```bash
tools/spec-linter/spec-lint .claude/sdd/features/DEFINE_{FEATURE_NAME}.md --phase define \
  --contracts-file .claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml
```

Run it as `tools/spec-linter/USAGE.md` documents, and act on the verdict exactly as defined there. The exit-code contract and verdict semantics are owned by that document and by the `contract_enforcement` block (`exit_code_contract`, `verdict_semantics`) of `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` — which is also where this phase's binding is declared. Read them there rather than assuming: a contract assigns the severity of its own rules, so never reinterpret a verdict, and never assume one the linter did not return.

## Anti-patterns

| Never Do | Why | Instead |
|----------|-----|---------|
| Vague language ("improve", "better") | Unmeasurable | Use specific metrics |
| Skip clarity scoring | Proceed with gaps | Always calculate score |
| Assume implementation details | That's DESIGN phase | Keep requirements-focused |
| Empty out-of-scope | Scope creep risk | Explicitly list exclusions |
| Skip KB domain selection | Design lacks patterns | Always identify domains |
| No identified users | Requirements without an audience | Name at least one persona with a pain point |
| Untestable success criteria | Cannot verify done | Rewrite until measurable |

## Tips

1. **Be Specific** — "Improve performance" → "Reduce API latency to <200ms"
2. **Use Numbers** — "Handle many users" → "Support 1000 concurrent users"
3. **Test Criteria** — If you can't test it, it's not clear enough
4. **Scope Ruthlessly** — What's OUT is as important as what's IN

## Handoff

Once the DEFINE document is saved with clarity >= 12/15 and statuses are updated, suggest the next phase:

```bash
/design .claude/sdd/features/DEFINE_{FEATURE_NAME}.md
```

Design (Phase 2, `design-agent`) turns the validated requirements into architecture and a technical specification.
