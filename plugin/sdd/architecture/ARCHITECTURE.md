# AgentSpec Architecture

> Visual reference for the AgentSpec 5-phase development workflow

---

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   AGENTSPEC 5-PHASE PIPELINE                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                          │
│   PHASE 0              PHASE 1              PHASE 2              PHASE 3              PHASE 4           │
│   ════════             ════════             ════════             ════════             ════════          │
│   BRAINSTORM           DEFINE               DESIGN               BUILD                SHIP              │
│   (Explore)            (What + Why)         (How)                (Do)                 (Close)           │
│   [Optional]                                                                                            │
│                                                                                                          │
│   /brainstorm          /define              /design              /build               /ship             │
│        │                    │                    │                    │                    │            │
│        ▼                    ▼                    ▼                    ▼                    ▼            │
│   ┌──────────┐         ┌─────────┐          ┌─────────┐          ┌─────────┐          ┌─────────┐      │
│   │BRAINSTORM│────────▶│ DEFINE  │─────────▶│ DESIGN  │─────────▶│  BUILD  │─────────▶│  SHIP   │      │
│   │  AGENT   │ or skip │  AGENT  │          │  AGENT  │          │  AGENT  │          │  AGENT  │      │
│   │  (Opus)  │         │ (Opus)  │          │ (Opus)  │          │(Sonnet) │          │(Haiku)  │      │
│   └──────────┘         └─────────┘          └─────────┘          └─────────┘          └─────────┘      │
│        │                    │                    │                    │                    │            │
│        ▼                    ▼                    ▼                    ▼                    ▼            │
│   features/            features/            features/            reports/ +           archive/         │
│   BRAINSTORM_*.md      DEFINE_*.md          DESIGN_*.md          CODE FILES           {FEATURE}/       │
│                                                                  BUILD_REPORT_*.md    SHIPPED_*.md     │
│                                                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                          │
│                                      CROSS-PHASE: ITERATE                                                │
│                                      ═══════════════════                                                 │
│                                                                                                          │
│                                           /iterate                                                       │
│                                                │                                                         │
│                                                ▼                                                         │
│                                           ┌─────────┐                                                    │
│                                           │ ITERATE │                                                    │
│                                           │  AGENT  │                                                    │
│                                           │(Sonnet) │                                                    │
│                                           └─────────┘                                                    │
│                                                │                                                         │
│                              ┌─────────────────┼─────────────────┐                                       │
│                              ▼                 ▼                 ▼                                       │
│                       Updates BRAINSTORM  Updates DEFINE    Updates DESIGN                               │
│                       (with cascade)      (with cascade)    (with cascade)                               │
│                                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Flow

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    WORKFLOW FLOW                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   RAW IDEA                                                                               │
│   (vague request,         PHASE 0: BRAINSTORM (Optional)                                │
│    problem)          ────────────────────────▶   BRAINSTORM_{FEATURE}.md                │
│                           One Q at a time        - Discovery Q&A                         │
│                           2-3 Approaches         - Approaches Explored                   │
│                           YAGNI Ruthlessly       - Features Removed                      │
│                                                  - Selected Approach                     │
│                                  │                                                       │
│                                  ▼                                                       │
│   RAW INPUT                                                                              │
│   (notes, emails,         PHASE 1: DEFINE                                               │
│    brainstorm doc)   ────────────────────────▶   DEFINE_{FEATURE}.md                    │
│                           Extract + Validate     - Problem Statement                     │
│                           Clarity Score ≥12      - Target Users                          │
│                                                  - Success Criteria                      │
│                                                  - Acceptance Tests                      │
│                                                  - Out of Scope                          │
│                                  │                                                       │
│                                  ▼                                                       │
│                           PHASE 2: DESIGN                                               │
│   DEFINE_{FEATURE}.md ───────────────────────▶   DESIGN_{FEATURE}.md                    │
│                           Architect + Decide     - Architecture Diagram                  │
│                           No Shared Deps         - Key Decisions (inline)                │
│                                                  - File Manifest                         │
│                                                  - Code Patterns                         │
│                                                  - Testing Strategy                      │
│                                  │                                                       │
│                                  ▼                                                       │
│                           PHASE 3: BUILD                                                │
│   DESIGN_{FEATURE}.md ───────────────────────▶   CODE + BUILD_REPORT                    │
│                           Execute + Verify       - All files from manifest               │
│                           Tests Pass             - Verification results                  │
│                                                  - Issues encountered                    │
│                                  │                                                       │
│                                  ▼                                                       │
│                           PHASE 4: SHIP                                                 │
│   All Artifacts      ────────────────────────▶   archive/{FEATURE}/                     │
│                           Archive + Learn        - All artifacts moved                   │
│                                                  - SHIPPED_{DATE}.md                     │
│                                                  - Lessons learned                       │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```text
.claude
+-- commands/                    # 31 slash commands
|   +-- workflow/                # 7 SDD commands
|   +-- data-engineering/        # 8 DE commands
|   +-- core/                    # 4 utility commands
|   +-- visual-explainer/         # 8 visual documentation commands
|   +-- knowledge/               # 1 KB command
|   +-- review/                  # 1 review command
|
+-- agents/                      # 58 specialized agents
|   +-- workflow/                # 6 SDD phase agents
|   +-- architect/               # 8 system-level design
|   +-- cloud/                   # 10 AWS, GCP, CI/CD
|   +-- platform/                # 6 Microsoft Fabric
|   +-- python/                  # 6 code quality, prompts
|   +-- test/                    # 3 testing, contracts
|   +-- data-engineering/        # 15 DE implementation
|   +-- dev/                     # 4 developer productivity
|
+-- kb/                          # 23 curated KB domains
|   +-- dbt/                     # dbt patterns
|   +-- spark/                   # PySpark, Spark SQL
|   +-- sql-patterns/            # SQL best practices
|   +-- airflow/                 # DAG patterns
|   +-- streaming/               # Flink, Kafka, CDC
|   +-- data-modeling/           # Star schema, Data Vault
|   +-- ... (17 more domains)
|
+-- sdd/
    +-- _index.md                # Workflow overview
    +-- README.md                # Comprehensive documentation
    +-- features/                # Active feature documents
    +-- reports/                 # Build reports
    +-- archive/                 # Shipped features
    +-- templates/               # 5 document templates
    +-- architecture/            # Workflow contracts
        +-- WORKFLOW_CONTRACTS.yaml
        +-- ARCHITECTURE.md      # This file
```

---

## Model Assignment

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              STRATEGIC MODEL ASSIGNMENT                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │                                    OPUS                                         │    │
│   │                    (Nuanced Understanding & Creative Thinking)                  │    │
│   │                                                                                 │    │
│   │   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │    │
│   │   │   BRAINSTORM    │    │     DEFINE      │    │     DESIGN      │            │    │
│   │   │     AGENT       │    │     AGENT       │    │     AGENT       │            │    │
│   │   │                 │    │                 │    │                 │            │    │
│   │   │ Collaborative   │    │ Requirements    │    │ Architecture    │            │    │
│   │   │ exploration     │    │ extraction      │    │ decisions       │            │    │
│   │   └─────────────────┘    └─────────────────┘    └─────────────────┘            │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │                                   SONNET                                        │    │
│   │                           (Fast, Accurate Coding)                               │    │
│   │                                                                                 │    │
│   │   ┌─────────────────┐              ┌─────────────────┐                         │    │
│   │   │      BUILD      │              │     ITERATE     │                         │    │
│   │   │      AGENT      │              │      AGENT      │                         │    │
│   │   │                 │              │                 │                         │    │
│   │   │ Code generation │              │ Change          │                         │    │
│   │   │ & verification  │              │ management      │                         │    │
│   │   └─────────────────┘              └─────────────────┘                         │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
│   ┌────────────────────────────────────────────────────────────────────────────────┐    │
│   │                                    HAIKU                                        │    │
│   │                             (Fast, Simple Tasks)                                │    │
│   │                                                                                 │    │
│   │   ┌─────────────────┐                                                          │    │
│   │   │      SHIP       │                                                          │    │
│   │   │      AGENT      │                                                          │    │
│   │   │                 │                                                          │    │
│   │   │ Archive &       │                                                          │    │
│   │   │ document        │                                                          │    │
│   │   └─────────────────┘                                                          │    │
│   └────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA FLOW                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ╔═══════════════════╗                                                                 │
│   ║    RAW IDEA       ║   (Optional Phase 0)                                            │
│   ║  (Vague request)  ║                                                                 │
│   ╚═════════╤═════════╝                                                                 │
│             │                                                                            │
│             ▼                                                                            │
│   ┌───────────────────┐                                                                 │
│   │ BRAINSTORM_*.md   │─────┐                                                           │
│   │                   │     │                                                           │
│   │ - Discovery Q&A   │     │                                                           │
│   │ - Approaches      │     │ (or skip to DEFINE                                        │
│   │ - YAGNI List      │     │  with raw input)                                          │
│   │ - Selected Path   │     │                                                           │
│   └─────────┬─────────┘     │                                                           │
│             │               │                                                           │
│             ▼               ▼                                                           │
│   ┌───────────────────┐         ┌───────────────────┐                                   │
│   │ DEFINE_*.md       │────────▶│ DESIGN_*.md       │                                   │
│   │                   │         │                   │                                   │
│   │ - Problem         │         │ - Architecture    │                                   │
│   │ - Users           │         │ - Decisions       │                                   │
│   │ - Success         │         │ - File Manifest   │                                   │
│   │ - Tests           │         │ - Patterns        │                                   │
│   │ - Scope           │         │ - Testing         │                                   │
│   └───────────────────┘         └─────────┬─────────┘                                   │
│                                           │                                              │
│             ┌─────────────────────────────┴─────────────────────────────┐               │
│             │                                                           │               │
│             ▼                                                           ▼               │
│   ┌───────────────────┐                                       ┌───────────────────┐    │
│   │ CODE FILES        │                                       │ BUILD_REPORT_*.md │    │
│   │                   │                                       │                   │    │
│   │ (From manifest)   │                                       │ - Tasks completed │    │
│   │                   │                                       │ - Verification    │    │
│   │                   │                                       │ - Issues          │    │
│   └─────────┬─────────┘                                       └─────────┬─────────┘    │
│             │                                                           │               │
│             └─────────────────────────────┬─────────────────────────────┘               │
│                                           │                                              │
│                                           ▼                                              │
│                              ╔═══════════════════════╗                                  │
│                              ║  archive/{FEATURE}/   ║                                  │
│                              ║                       ║                                  │
│                              ║  - BRAINSTORM_*.md    ║                                  │
│                              ║  - DEFINE_*.md        ║                                  │
│                              ║  - DESIGN_*.md        ║                                  │
│                              ║  - BUILD_REPORT_*.md  ║                                  │
│                              ║  - SHIPPED_*.md       ║                                  │
│                              ╚═══════════════════════╝                                  │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Iteration Flow

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  ITERATION FLOW                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│                         /iterate DEFINE_*.md "change"                                   │
│                                      │                                                   │
│                                      ▼                                                   │
│                              ┌──────────────┐                                            │
│                              │ DETECT PHASE │                                            │
│                              └──────┬───────┘                                            │
│                                     │                                                    │
│                    ┌────────────────┴────────────────┐                                   │
│                    ▼                                 ▼                                   │
│            ┌──────────────┐                  ┌──────────────┐                            │
│            │   DEFINE_*   │                  │   DESIGN_*   │                            │
│            │   (Phase 1)  │                  │   (Phase 2)  │                            │
│            └──────┬───────┘                  └──────┬───────┘                            │
│                   │                                 │                                    │
│                   ▼                                 ▼                                    │
│            ┌──────────────┐                  ┌──────────────┐                            │
│            │ APPLY CHANGE │                  │ APPLY CHANGE │                            │
│            │ + VERSION    │                  │ + VERSION    │                            │
│            └──────┬───────┘                  └──────┬───────┘                            │
│                   │                                 │                                    │
│                   ▼                                 ▼                                    │
│            ┌──────────────┐                  ┌──────────────┐                            │
│            │ CASCADE      │                  │ CASCADE      │                            │
│            │ CHECK        │                  │ CHECK        │                            │
│            └──────┬───────┘                  └──────┬───────┘                            │
│                   │                                 │                                    │
│          ┌───────┴────────┐                ┌───────┴────────┐                            │
│          ▼                ▼                ▼                ▼                            │
│   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐                      │
│   │  No Impact │   │ DESIGN     │   │  No Impact │   │   CODE     │                      │
│   │            │   │ may need   │   │            │   │ may need   │                      │
│   │            │   │ update     │   │            │   │ update     │                      │
│   └────────────┘   └────────────┘   └────────────┘   └────────────┘                      │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Quality Gates

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   QUALITY GATES                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   PHASE 0: BRAINSTORM (Optional)                                                         │
│   ══════════════════════════════                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐                   │
│   │ Exploration Checklist                                            │                   │
│   ├─────────────────────────────────────────────────────────────────┤                   │
│   │ [ ] Minimum 3 discovery questions asked                          │                   │
│   │ [ ] 2-3 approaches explored with trade-offs                      │                   │
│   │ [ ] YAGNI applied (features removed section not empty)           │                   │
│   │ [ ] Minimum 2 incremental validations completed                  │                   │
│   │ [ ] User confirmed selected approach                             │                   │
│   │ [ ] Draft requirements ready for /define                         │                   │
│   └─────────────────────────────────────────────────────────────────┘                   │
│                                                                                          │
│   PHASE 1: DEFINE                                                                        │
│   ═══════════════                                                                        │
│   ┌─────────────────────────────────────────────────────────────────┐                   │
│   │ Clarity Score Breakdown                         Minimum: 12/15  │                   │
│   ├─────────────────────────────────────────────────────────────────┤                   │
│   │ Problem:  [0-3] Clear, specific, actionable?                    │                   │
│   │ Users:    [0-3] Identified with pain points?                    │                   │
│   │ Goals:    [0-3] Measurable outcomes?                            │                   │
│   │ Success:  [0-3] Testable criteria?                              │                   │
│   │ Scope:    [0-3] Explicit boundaries?                            │                   │
│   └─────────────────────────────────────────────────────────────────┘                   │
│                                                                                          │
│   PHASE 2: DESIGN                                                                        │
│   ═══════════════                                                                        │
│   ┌─────────────────────────────────────────────────────────────────┐                   │
│   │ Checklist                                                        │                   │
│   ├─────────────────────────────────────────────────────────────────┤                   │
│   │ [ ] Architecture diagram present                                 │                   │
│   │ [ ] At least one decision with rationale                         │                   │
│   │ [ ] Complete file manifest                                       │                   │
│   │ [ ] Code patterns are copy-paste ready                           │                   │
│   │ [ ] Testing strategy defined                                     │                   │
│   │ [ ] No shared dependencies across units                          │                   │
│   └─────────────────────────────────────────────────────────────────┘                   │
│                                                                                          │
│   PHASE 3: BUILD                                                                         │
│   ══════════════                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐                   │
│   │ Verification                                                     │                   │
│   ├─────────────────────────────────────────────────────────────────┤                   │
│   │ [ ] All files from manifest created                              │                   │
│   │ [ ] All verification commands pass                               │                   │
│   │ [ ] Lint check passes                                              │                   │
│   │ [ ] Tests pass                                                    │                   │
│   │ [ ] No TODO comments in code                                     │                   │
│   └─────────────────────────────────────────────────────────────────┘                   │
│                                                                                          │
│   PHASE 4: SHIP                                                                          │
│   ═════════════                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐                   │
│   │ Pre-Ship Checklist                                               │                   │
│   ├─────────────────────────────────────────────────────────────────┤                   │
│   │ [ ] BUILD_REPORT shows 100% completion                           │                   │
│   │ [ ] All tests passing                                            │                   │
│   │ [ ] No blocking issues                                           │                   │
│   │ [ ] Acceptance tests verified                                    │                   │
│   └─────────────────────────────────────────────────────────────────┘                   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2026-03-26 | Updated folder structure for 58 agents, 8 categories, 23 KB domains |
| 2.0.0 | 2026-03-26 | Data engineering pivot |
| 1.0.0 | 2026-02-17 | Public release as AgentSpec v1.0.0 |
