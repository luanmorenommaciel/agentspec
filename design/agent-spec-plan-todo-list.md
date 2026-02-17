# AgentSpec Master Plan

> **The Complete Blueprint for Open-Sourcing AgentSpec**

---

## Executive Summary

| Aspect | Details |
|--------|---------|
| **Project** | AgentSpec - Spec-Driven Development Framework |
| **Tagline** | Spec-Driven Development for AI-Native Teams |
| **Business Problem** | Gap between unstructured "vibe coding" and stale traditional specifications |
| **Solution** | 5-phase workflow with 40+ AI agents and curated knowledge bases |
| **Target Launch** | Q1 2026 |
| **License** | MIT |

### What This Is

AgentSpec transforms requirements into working code with full traceability. It provides a structured 5-phase development workflow (Brainstorm → Define → Design → Build → Ship) powered by specialized AI agents that match to tasks automatically, grounded by curated knowledge bases for accuracy.

### Health Score: 8.5/10

| Criterion | Score | Evidence |
|-----------|-------|----------|
| Architecture Clarity | 9/10 | Well-defined 5-phase pipeline |
| Documentation | 8/10 | Comprehensive but needs polish for OSS |
| Agent Coverage | 9/10 | 40+ agents across 8 categories |
| KB Grounding | 8/10 | 8 domains, MCP-validated |
| Testability | 7/10 | Framework needs validation tests |
| Community Readiness | 8/10 | Plugin architecture defined |

### Key Insights

1. **Strength:** Automatic agent matching + KB grounding = unique differentiator
2. **Concern:** No Judge layer to validate specs before expensive BUILD phase
3. **Opportunity:** Local telemetry can drive continuous improvement

---

## Table of Contents

1. [Key Decisions](#1-key-decisions)
2. [Action Items](#2-action-items)
3. [Requirements](#3-requirements)
4. [Blockers & Risks](#4-blockers--risks)
5. [Architecture & Technical Decisions](#5-architecture--technical-decisions)
6. [Open Questions](#6-open-questions)
   - 6.1 [Deferred Items](#61-deferred-items)
7. [Next Steps & Timeline](#7-next-steps--timeline)
8. [Stakeholders & Roles](#8-stakeholders--roles)
   - 8.4 [Marketing Messaging](#84-marketing-messaging)
   - 8.5 [Community Guidelines](#85-community-guidelines)
9. [Success Metrics](#9-success-metrics)
10. [Appendices](#10-appendices)

---

## 1. Key Decisions

### 1.1 Business Decisions

| # | Decision | Owner | Source | Status | Rationale |
|---|----------|-------|--------|--------|-----------|
| D1 | Open-source under MIT license | Project Lead | Planning Session | **Approved** | Maximum adoption, business-friendly |
| D2 | Monorepo with plugins architecture | Project Lead | Planning Session | **Approved** | Easier contribution, single versioning |
| D3 | Local-only telemetry (opt-in) | Project Lead | Planning Session | **Approved** | Privacy-first, user controlled |
| D4 | MkDocs Material for documentation | Project Lead | Planning Session | **Approved** | Python/AI ecosystem standard |
| D5 | Discord for community | Project Lead | Planning Session | **Approved** | Real-time, threaded discussions |

### 1.2 Technical Decisions

| # | Decision | Owner | Source | Status | Rationale |
|---|----------|-------|--------|--------|-----------|
| D6 | Add LLM-as-Judge layer (Phase 1.5) | Tech Lead | Improvement Analysis | **Approved** | Catch errors before expensive BUILD |
| D7 | Multi-LLM review via OpenRouter | Tech Lead | Improvement Analysis | **Approved** | Diverse perspectives, fair comparison |
| D8 | Add confidence scoring to agent matching | Tech Lead | Improvement Analysis | **Approved** | Handle edge cases with fallbacks |
| D9 | Add KB freshness indicators | Tech Lead | Improvement Analysis | **Approved** | Prevent stale pattern recommendations |
| D10 | Unified /report command | Tech Lead | Planning Session | **Approved** | Single source of truth for health |

### 1.3 Process Decisions

| # | Decision | Owner | Source | Status | Rationale |
|---|----------|-------|--------|--------|-----------|
| D11 | 7-week implementation timeline | Project Lead | Planning Session | **Approved** | Aggressive but achievable |
| D12 | Beta test with 5-10 users | Project Lead | Planning Session | **Approved** | Validate before public launch |
| D13 | Semantic versioning (X.Y.Z) | Tech Lead | Planning Session | **Approved** | Clear breaking change signals |

---

## 2. Action Items

### 2.1 By Phase

#### Phase 1: Foundation (Week 1-2)

- [ ] **Project Lead**: Create GitHub repository (`agentspec`) (Due: Day 1)
- [ ] **Project Lead**: Add LICENSE (MIT) (Due: Day 1)
- [ ] **Project Lead**: Add CODE_OF_CONDUCT.md (Contributor Covenant 2.1) (Due: Day 1)
- [ ] **Project Lead**: Add CONTRIBUTING.md (Due: Day 2)
- [ ] **Project Lead**: Set up branch protection (main) (Due: Day 2)
- [ ] **Project Lead**: Create issue templates (bug, feature, new-agent) (Due: Day 3)
- [ ] **Project Lead**: Create PR template (Due: Day 3)
- [ ] **Tech Lead**: Extract and sanitize SDD templates (Due: Week 1)
- [ ] **Tech Lead**: Extract WORKFLOW_CONTRACTS.yaml (Due: Week 1)
- [ ] **Tech Lead**: Extract ARCHITECTURE.md (Due: Week 1)
- [ ] **Tech Lead**: Create CLAUDE.md.template (Due: Week 1)
- [ ] **Tech Lead**: Create KB _index.yaml.template (Due: Week 1)
- [ ] **Tech Lead**: Extract 6 workflow agents (Due: Week 2)
- [ ] **Tech Lead**: Extract 6 code-quality agents (Due: Week 2)
- [ ] **Tech Lead**: Extract 3 communication agents (Due: Week 2)
- [ ] **Tech Lead**: Extract 2 exploration agents (Due: Week 2)
- [ ] **Tech Lead**: Sanitize all agent prompts (Due: Week 2)
- [ ] **Tech Lead**: Extract KB _templates/ (Due: Week 2)
- [ ] **Tech Lead**: Extract pydantic/ domain (Due: Week 2)

#### Phase 2: Core Improvements (Week 2-3)

- [ ] **Tech Lead**: Add confidence scoring algorithm to design-agent (Due: Week 2)
- [ ] **Tech Lead**: Update DESIGN_TEMPLATE.md with Confidence/Fallback columns (Due: Week 2)
- [ ] **Tech Lead**: Add freshness fields to _index.yaml schema (Due: Week 3)
- [ ] **Tech Lead**: Implement freshness check in /report (Due: Week 3)
- [ ] **Tech Lead**: Add Complexity column (S/M/L) to file manifest (Due: Week 3)
- [ ] **Tech Lead**: Add cross-feature dependencies section to DEFINE_TEMPLATE (Due: Week 3)

#### Phase 3: Judge Implementation (Week 3-4)

- [ ] **Tech Lead**: Create `/judge` command (Due: Week 3)
- [ ] **Tech Lead**: Create `judge-agent.md` (Due: Week 3)
- [ ] **Tech Lead**: Create JUDGE_REPORT_TEMPLATE.md (Due: Week 3)
- [ ] **Tech Lead**: Update WORKFLOW_CONTRACTS.yaml with judge phase (Due: Week 3)
- [ ] **Tech Lead**: Integrate OpenRouter for GPT-4 review (Due: Week 4)
- [ ] **Tech Lead**: Integrate OpenRouter for Gemini review (Due: Week 4)
- [ ] **Tech Lead**: Implement consensus logic (2/3 agreement) (Due: Week 4)
- [ ] **Tech Lead**: Implement MCP validation checks (Due: Week 4)
- [ ] **Tech Lead**: Add auto-trigger logic (Due: Week 4)

#### Phase 4: Telemetry & Report (Week 4-5)

- [ ] **Tech Lead**: Create `.claude/telemetry/` structure (Due: Week 4)
- [ ] **Tech Lead**: Create SESSION_SCHEMA.yaml (Due: Week 4)
- [ ] **Tech Lead**: Update `/ship` to capture telemetry (Due: Week 4)
- [ ] **Tech Lead**: Create `report.md` command (Due: Week 5)
- [ ] **Tech Lead**: Implement all 6 report sections (Due: Week 5)

#### Phase 5: Plugins (Week 5)

- [ ] **Tech Lead**: Create plugin manifest schema (Due: Week 5)
- [ ] **Tech Lead**: Create plugin-gcp (Due: Week 5)
- [ ] **Tech Lead**: Create plugin-aws (Due: Week 5)
- [ ] **Tech Lead**: Create plugin-data-engineering (Due: Week 5)
- [ ] **Tech Lead**: Create plugin-ai-ml (Due: Week 5)
- [ ] **Tech Lead**: Create plugin-crewai (Due: Week 5)

#### Phase 6: Documentation (Week 5-6)

- [ ] **Docs Lead**: Set up MkDocs with Material theme (Due: Week 5)
- [ ] **Docs Lead**: Write hero README with demo GIF (Due: Week 5)
- [ ] **Docs Lead**: Write Getting Started guide (15-min quickstart) (Due: Week 5)
- [ ] **Docs Lead**: Write SDD Workflow deep-dive (Due: Week 6)
- [ ] **Docs Lead**: Write Agent creation guide (Due: Week 6)
- [ ] **Docs Lead**: Write KB domain creation guide (Due: Week 6)
- [ ] **Docs Lead**: Write Plugin development guide (Due: Week 6)
- [ ] **Tech Lead**: Sanitize invoice-pipeline as example (Due: Week 6)
- [ ] **Tech Lead**: Create minimal "simple-api" example (Due: Week 6)

#### Phase 7: Launch (Week 6-7)

- [ ] **Marketing**: Create logo and visual identity (Due: Week 6)
- [ ] **Marketing**: Create demo video (30 seconds for social) (Due: Week 6)
- [ ] **Marketing**: Create "Zero to Feature" video (5 minutes) (Due: Week 6)
- [ ] **Marketing**: Write launch blog post (Due: Week 7)
- [ ] **Project Lead**: Post to Hacker News (Show HN) (Due: Launch Day)
- [ ] **Project Lead**: Post to Reddit (r/programming, r/artificial, r/ClaudeAI) (Due: Launch Day)
- [ ] **Project Lead**: Post to Twitter/X, LinkedIn (Due: Launch Day)
- [ ] **Project Lead**: Submit to Product Hunt (Due: Launch Day)
- [ ] **Project Lead**: Set up Discord community (Due: Week 7)

### 2.2 By Owner

#### Project Lead

| Action | Due | Status |
|--------|-----|--------|
| Create GitHub repository | Day 1 | [ ] Pending |
| Add LICENSE, CODE_OF_CONDUCT, CONTRIBUTING | Day 1-2 | [ ] Pending |
| Set up branch protection | Day 2 | [ ] Pending |
| Create issue/PR templates | Day 3 | [ ] Pending |
| Post to launch channels | Launch Day | [ ] Pending |
| Set up Discord | Week 7 | [ ] Pending |

#### Tech Lead

| Action | Due | Status |
|--------|-----|--------|
| Extract core framework | Week 1-2 | [ ] Pending |
| Extract all agents (17) | Week 2 | [ ] Pending |
| Implement core improvements (6) | Week 2-3 | [ ] Pending |
| Implement Judge layer | Week 3-4 | [ ] Pending |
| Implement telemetry + /report | Week 4-5 | [ ] Pending |
| Create all plugins (5) | Week 5 | [ ] Pending |
| Sanitize examples | Week 6 | [ ] Pending |

#### Docs Lead

| Action | Due | Status |
|--------|-----|--------|
| Set up MkDocs | Week 5 | [ ] Pending |
| Write hero README | Week 5 | [ ] Pending |
| Write all guides (5) | Week 5-6 | [ ] Pending |

#### Marketing

| Action | Due | Status |
|--------|-----|--------|
| Create visual identity | Week 6 | [ ] Pending |
| Create demo videos (2) | Week 6 | [ ] Pending |
| Write launch blog post | Week 7 | [ ] Pending |

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Source | Status |
|----|-------------|----------|--------|--------|
| FR-001 | System must provide 5-phase SDD workflow (Brainstorm, Define, Design, Build, Ship) | P0-Critical | Core | Exists |
| FR-002 | System must match agents to files automatically | P0-Critical | Core | Exists |
| FR-004 | System must ground agent responses in KB patterns | P0-Critical | Core | Exists |
| FR-005 | System must provide Judge layer for spec validation | P1-High | Improvement | Planned |
| FR-006 | System must capture local telemetry (opt-in) | P1-High | Improvement | Planned |
| FR-007 | System must provide unified /report command | P1-High | Improvement | Planned |
| FR-008 | System must support plugin architecture | P0-Critical | OSS | Designed |
| FR-009 | System must provide confidence scoring for agent matching | P1-High | Improvement | Planned |
| FR-010 | System must warn on stale KB domains | P2-Medium | Improvement | Planned |

### 3.2 Non-Functional Requirements

| ID | Requirement | Priority | Target | Source |
|----|-------------|----------|--------|--------|
| NFR-001 | Documentation must enable 15-min quickstart | P0-Critical | 15 min | OSS |
| NFR-002 | Framework must work with Claude Code CLI | P0-Critical | 100% | Core |
| NFR-003 | All code examples must be tested and working | P0-Critical | 100% | Docs |
| NFR-004 | KB domains must be MCP-validated | P1-High | All domains | Core |
| NFR-005 | Judge consensus must require 2/3 agreement | P1-High | 67% | Improvement |
| NFR-006 | Plugin installation must work via manual copy | P0-Critical | Works today | OSS |
| NFR-007 | Telemetry must be local-only, no external calls | P0-Critical | 100% local | Privacy |

### 3.3 Constraints

| ID | Constraint | Type | Impact |
|----|------------|------|--------|
| C-001 | Must not include company-specific content | Legal | Sanitization required |
| C-002 | Must not expose API keys or secrets | Security | Audit before publish |
| C-003 | Must use MIT license | Legal | Already decided |
| C-004 | Must work without external dependencies beyond Claude Code | Technical | Self-contained |
| C-005 | Must launch by end of Q1 2026 | Timeline | 7-week execution |

### 3.4 Assumptions

| ID | Assumption | Risk if Wrong | Mitigation |
|----|------------|---------------|------------|
| A-001 | Users have Claude Code CLI installed | Won't work | Document as prerequisite |
| A-002 | OpenRouter available for Judge layer | No multi-LLM | Fallback to single-LLM judge |
| A-003 | Beta users available for testing | Untested launch | Use internal team as beta |
| A-004 | GitHub remains primary platform | Migration needed | N/A (very low risk) |
| A-005 | Community will contribute plugins | Slower growth | Build official plugins first |

---

## 4. Blockers & Risks

### 4.1 Risk Matrix

```text
                    IMPACT
                    Low    Medium   High
            ┌───────┬────────┬────────┐
    High    │       │   R3   │   R1   │
            ├───────┼────────┼────────┤
LIKELIHOOD  Medium  │       │   R4   │   R2   │
            ├───────┼────────┼────────┤
    Low     │       │   R5   │   R6   │
            └───────┴────────┴────────┘
```

### 4.2 Risk Register

| # | Type | Description | Impact | Likelihood | Owner | Mitigation | Status |
|---|------|-------------|--------|------------|-------|------------|--------|
| R1 | Risk | Sanitization incomplete - internal data exposed | HIGH | High | Tech Lead | Automated scan + manual review | Active |
| R2 | Risk | 7-week timeline too aggressive | HIGH | Medium | Project Lead | Prioritize core, defer plugins | Active |
| R3 | Risk | OpenRouter rate limits block Judge | MEDIUM | High | Tech Lead | Implement local cache, rate limiting | Active |
| R4 | Risk | Documentation not tested, examples broken | MEDIUM | Medium | Docs Lead | CI validation of all examples | Active |
| R5 | Risk | Community adoption slower than expected | MEDIUM | Low | Marketing | Focus on quality over quantity | Monitoring |
| R6 | Risk | Claude Code CLI breaking changes | HIGH | Low | Tech Lead | Pin to known working version | Monitoring |

### 4.3 Active Blockers

| # | Blocker | Blocked By | Impact | Owner | Resolution Path | ETA |
|---|---------|------------|--------|-------|-----------------|-----|
| B1 | Cannot publish | Sanitization not complete | Launch delayed | Tech Lead | Complete sanitization checklist | Week 2 |
| B2 | Cannot test Judge | OpenRouter integration pending | Feature incomplete | Tech Lead | Complete OpenRouter setup | Week 4 |

---

## 5. Architecture & Technical Decisions

### 5.1 Repository Structure

```text
agentspec/
├── README.md                          # Hero README with demo
├── LICENSE                            # MIT License
├── CONTRIBUTING.md                    # Contribution guidelines
├── CODE_OF_CONDUCT.md                 # Contributor Covenant 2.1
├── CHANGELOG.md                       # Version history
│
├── packages/                          # Core framework (always required)
│   │
│   ├── core/                          # SDD framework
│   │   ├── sdd/
│   │   │   ├── architecture/
│   │   │   │   ├── ARCHITECTURE.md
│   │   │   │   └── WORKFLOW_CONTRACTS.yaml
│   │   │   └── templates/
│   │   │       ├── BRAINSTORM_TEMPLATE.md
│   │   │       ├── DEFINE_TEMPLATE.md
│   │   │       ├── DESIGN_TEMPLATE.md
│   │   │       ├── BUILD_REPORT_TEMPLATE.md
│   │   │       ├── SHIPPED_TEMPLATE.md
│   │   │       └── JUDGE_REPORT_TEMPLATE.md    # NEW
│   │   │
│   │   ├── commands/
│   │   │   ├── workflow/              # /brainstorm, /define, /design, /build, /ship, /iterate, /judge
│   │   │   ├── core/                  # /memory, /sync-context, /create-kb, /report
│   │   │   └── review/                # /review, /create-pr
│   │   │
│   │   ├── telemetry/                 # NEW: Local telemetry system
│   │   │   ├── readme.md
│   │   │   ├── SESSION_SCHEMA.yaml
│   │   │   └── REPORT_TEMPLATE.md
│   │   │
│   │   ├── CLAUDE.md.template         # Template for user's CLAUDE.md
│   │   └── README.md
│   │
│   ├── agents/                        # Agent library (18 universal agents)
│   │   ├── workflow/                  # 7 SDD agents (including judge-agent)
│   │   ├── code-quality/              # 6 code quality agents
│   │   ├── communication/             # 3 explanation agents
│   │   └── exploration/               # 2 codebase agents
│   │
│   └── kb/                            # KB framework
│       ├── _index.yaml.template
│       ├── _templates/
│       └── pydantic/                  # Universal domain (always included)
│
├── plugins/                           # Domain-specific plugins (5)
│   ├── plugin-gcp/                    # 3 agents + 3 KB domains
│   ├── plugin-aws/                    # 4 agents + 1 KB domain
│   ├── plugin-data-engineering/       # 8 agents + 2 KB domains
│   ├── plugin-ai-ml/                  # 5 agents + 3 KB domains
│   └── plugin-crewai/                 # 1 agent + 1 KB domain
│
├── examples/                          # Full example projects
│   ├── invoice-pipeline/              # Real-world sanitized example
│   └── simple-api/                    # Minimal "hello world" example
│
├── docs/                              # Documentation site (MkDocs)
│   ├── getting-started/
│   ├── guides/
│   ├── reference/
│   └── examples/
│
├── cli/                               # Future CLI tool (placeholder)
│
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

### 5.2 Component Details

#### 5.2.1 Core Package

| Component | Files | Purpose |
|-----------|-------|---------|
| SDD Templates | 6 | Phase document templates |
| Commands | 12 | Slash commands for workflow |
| Telemetry | 3 | Local usage tracking |
| CLAUDE.md Template | 1 | User customization base |

#### 5.2.2 Agent Library

| Category | Count | Agents |
|----------|-------|--------|
| Workflow | 7 | brainstorm, define, design, build, ship, iterate, **judge** |
| Code Quality | 6 | code-reviewer, code-cleaner, code-documenter, python-developer, test-generator, dual-reviewer |
| Communication | 3 | adaptive-explainer, meeting-analyst, the-planner |
| Exploration | 2 | codebase-explorer, kb-architect |
| **Total** | **18** | |

#### 5.2.3 Plugin Architecture

```yaml
# manifest.yaml
name: "plugin-{name}"
version: "1.0.0"
description: "Plugin description"
author: "Author Name"
license: "MIT"

requires:
  agentspec: ">=1.0.0"

agents:
  - path: "agents/agent-name.md"
    target: ".claude/agents/category/agent-name.md"

commands:
  - path: "commands/command-name.md"
    target: ".claude/commands/category/command-name.md"

kb_domains:
  - path: "kb/domain-name"
    target: ".claude/kb/domain-name"
    depends: []                        # Domain dependencies

depends:
  - plugin-core                        # Required plugins

post_install:
  - "Configuration instructions"
```

### 5.3 Key Technical Decisions (ADRs)

#### ADR-001: LLM-as-Judge Layer

| Attribute | Value |
|-----------|-------|
| **Status** | Approved |
| **Date** | 2026-01-31 |
| **Context** | BUILD failures often trace back to incomplete DEFINE specs |
| **Decision** | Add Phase 1.5 (Judge) between DEFINE and DESIGN |
| **Rationale** | Catching errors before DESIGN saves 3-5x the cost of fixing in BUILD |
| **Alternatives Rejected** | Post-BUILD review (too late), Mandatory human review (doesn't scale) |

#### ADR-002: Multi-LLM via OpenRouter

| Attribute | Value |
|-----------|-------|
| **Status** | Approved |
| **Date** | 2026-01-31 |
| **Context** | Single LLM may have blind spots |
| **Decision** | Use OpenRouter for GPT-4 and Gemini as secondary reviewers |
| **Rationale** | Diverse perspectives catch different issues |
| **Alternatives Rejected** | Single LLM (bias risk), Direct API calls (complexity) |

#### ADR-003: Local-Only Telemetry

| Attribute | Value |
|-----------|-------|
| **Status** | Approved |
| **Date** | 2026-01-31 |
| **Context** | Users want privacy, we need learning data |
| **Decision** | Telemetry stored in `.claude/telemetry/`, never sent externally |
| **Rationale** | Privacy-first approach builds trust |
| **Alternatives Rejected** | Cloud telemetry (privacy concerns), No telemetry (no learning) |

### 5.4 Judge Layer Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1.5: JUDGE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DEFINE_*.md                                                    │
│       │                                                         │
│       ├────────────┬────────────┬────────────┐                 │
│       ▼            ▼            ▼            ▼                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ Claude  │ │ GPT-4   │ │ Gemini  │ │   MCP   │              │
│  │ (Opus)  │ │(via OR) │ │(via OR) │ │ Validate│              │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘              │
│       │           │           │           │                    │
│       └───────────┴───────────┴───────────┘                    │
│                        │                                        │
│                        ▼                                        │
│              ┌─────────────────────┐                           │
│              │   JUDGE_REPORT.md   │                           │
│              │                     │                           │
│              │ ## Critique Summary │                           │
│              │ | Reviewer | Score | │                           │
│              │ |----------|-------| │                           │
│              │ | Claude   | 8/10  | │                           │
│              │ | GPT-4    | 7/10  | │                           │
│              │ | MCP      | PASS  | │                           │
│              └──────────┬──────────┘                           │
│                         │                                       │
│                         ▼                                       │
│              ┌─────────────────────┐                           │
│              │   DECISION GATE     │                           │
│              │                     │                           │
│              │ Score >= 8 AND      │                           │
│              │ MCP PASS?           │                           │
│              │   YES → DESIGN      │                           │
│              │   NO  → /iterate    │                           │
│              └─────────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Judge Trigger Conditions

```yaml
auto_trigger:
  - clarity_score_lt: 15          # Not perfect clarity
  - file_count_gt: 10             # Complex feature
  - iac_impact: "new_resources"   # Infrastructure changes
  - cross_feature_deps_gt: 0      # Has dependencies

skip_when:
  - clarity_score_eq: 15          # Perfect clarity
  - file_count_lte: 3             # Simple feature
  - user_flag: "--no-judge"       # User override

manual_trigger:
  - user_flag: "--judge"
```

#### Judge Quality Gate

```yaml
judge:
  quality_gate:
    minimum_score: 8              # Average across reviewers
    mcp_must_pass: true           # MCP validation required
    consensus_threshold: 0.67     # 2/3 agreement
    max_iterations: 2             # Prevent infinite loops
```

### 5.5 Data Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTSPEC DATA FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER                                                           │
│    │                                                            │
│    ▼                                                            │
│  /brainstorm ──► BRAINSTORM_*.md                               │
│    │              (explores, clarifies)                         │
│    ▼                                                            │
│  /define ─────► DEFINE_*.md                                    │
│    │              (requirements, clarity score)                 │
│    ▼                                                            │
│  /judge ──────► JUDGE_REPORT_*.md  ◄── Multi-LLM Review        │
│    │              (validation, consensus)     + MCP Validation  │
│    ▼                                                            │
│  /design ─────► DESIGN_*.md                                    │
│    │              (architecture, file manifest, agent matching) │
│    ▼                                                            │
│  /build ──────► CODE FILES + BUILD_REPORT_*.md                 │
│    │              (implementation, verification)                │
│    ▼                                                            │
│  /ship ───────► archive/{FEATURE}/ + SHIPPED_*.md              │
│    │              (lessons learned, telemetry capture)          │
│    ▼                                                            │
│  /report ─────► Ecosystem Health Report                        │
│                   (SDD status, agent usage, KB health)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Open Questions

| # | Question | Context | Proposed Owner | Priority | Status |
|---|----------|---------|----------------|----------|--------|
| Q1 | Should we support multiple Claude Code versions? | Breaking changes could affect users | Tech Lead | HIGH | Open |
| Q2 | What's the versioning strategy for plugins vs core? | Independent or coupled versioning | Tech Lead | HIGH | Open |
| Q3 | Should there be a plugin registry website? | Discovery for community plugins | Project Lead | MEDIUM | Open |
| Q4 | How to handle KB domain dependencies? | Some domains reference others | Tech Lead | MEDIUM | Open |
| Q5 | Should we create a migration guide for existing users? | Many have custom .claude/ setups | Docs Lead | MEDIUM | Open |
| Q6 | What CI checks should validate examples? | Ensure docs stay accurate | Tech Lead | HIGH | Open |
| Q7 | Should Judge be opt-in or opt-out by default? | User experience vs safety | Product | MEDIUM | Open |

---

## 6.1 Deferred Items

Items identified during planning but deferred due to complexity or timeline constraints. These should be revisited post-launch.

### 6.1.1 Technical Improvements (Deferred)

| # | Item | Complexity | Rationale for Deferral | Revisit When |
|---|------|------------|------------------------|--------------|
| DEF-001 | **Agent Composition** (multi-agent per file) | HIGH | Requires significant architecture changes to support collaborative agents on same file | Post-launch, based on user feedback |
| DEF-002 | **Build→Design Auto-Feedback Loop** | MEDIUM | Needs robust error classification to trigger auto-iterate | After Judge layer proves value |
| DEF-003 | **Plan Competition** (parallel plan generation) | HIGH | Advanced Judge variant with Claude-based merger | Judge Phase 3 (if Phase 1-2 prove value) |

### 6.1.2 Judge Phased Rollout

| Phase | Scope | Trigger |
|-------|-------|---------|
| **Phase 1 (MVP)** | Single Judge (GPT-4) + MCP Validation | Launch |
| **Phase 2** | Multi-Judge Consensus (add Gemini) | If MVP proves 60%+ failure reduction |
| **Phase 3** | Plan Competition with merger | If consensus catches 90%+ edge cases |

### 6.1.3 Edge Cases & Mitigations (Judge Layer)

| Edge Case | Problem | Mitigation |
|-----------|---------|------------|
| LLM Disagreement | Claude says go, GPT says no | Consensus threshold (2/3 agree) |
| MCP Timeout | External validation slow | Timeout + local KB cache |
| Cost Explosion | 3 LLMs × every DEFINE | Opt-in: `--judge` flag |
| Circular Feedback | Endless judge iterations | Max 2 iterations |
| Judge Hallucination | Invents non-existent KB | MCP must cite file paths |
| Latency | Parallel calls slow | Async + progress indicator |
| Context Limits | Large DEFINE | Chunk into sections |

---

## 7. Next Steps & Timeline

### 7.1 Visual Timeline

```text
Week 1    Week 2    Week 3    Week 4    Week 5    Week 6    Week 7
├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ FOUNDATION      │ IMPROVEMENTS   │ TELEMETRY     │ DOCS + LAUNCH │
│ ═══════════════ │ ═══════════════│ ═════════════ │ ═════════════ │
│                 │                │               │               │
│ [Repo Setup]    │ [Confidence]   │ [Telemetry]   │ [MkDocs]      │
│ [Extract Core]  │ [KB Fresh]     │ [/report]     │ [README]      │
│ [Extract Agents]│ [Complexity]   │ [Plugins]     │ [Guides]      │
│ [Extract KB]    │ [Judge Impl]   │               │ [Examples]    │
│                 │                │               │               │
│                 │                │               │ [BETA TEST]   │
│                 │                │               │ [LAUNCH!]     │
└─────────────────┴────────────────┴───────────────┴───────────────┘
```

### 7.2 Milestones

| Date | Milestone | Owner | Deliverables |
|------|-----------|-------|--------------|
| Week 1 End | Repository Live | Project Lead | GitHub repo, LICENSE, templates |
| Week 2 End | Core Extracted | Tech Lead | All core files sanitized and organized |
| Week 3 End | Improvements Done | Tech Lead | Confidence scoring, KB freshness, complexity |
| Week 4 End | Judge Working | Tech Lead | Multi-LLM review with MCP validation |
| Week 5 End | Plugins Ready | Tech Lead | All 5 plugins packaged |
| Week 6 End | Docs Complete | Docs Lead | MkDocs site, all guides written |
| Week 7 | PUBLIC LAUNCH | Project Lead | HN, Reddit, ProductHunt |

### 7.3 Immediate Actions (This Week)

1. **Day 1:** Create GitHub repository, add LICENSE
2. **Day 2:** Add CODE_OF_CONDUCT, CONTRIBUTING, branch protection
3. **Day 3:** Create issue/PR templates
4. **Day 4-5:** Begin extracting core framework files
5. **End of Week:** Core SDD templates extracted and sanitized

### 7.4 Launch Day Schedule

| Time | Action | Owner |
|------|--------|-------|
| 9:00 AM | Publish blog post | Marketing |
| 9:30 AM | Tweet + LinkedIn post | Marketing |
| 10:00 AM | Post to Hacker News (Show HN) | Project Lead |
| 10:30 AM | Post to Reddit (r/programming) | Project Lead |
| 11:00 AM | Post to Reddit (r/artificial, r/ClaudeAI) | Project Lead |
| 12:00 PM | Submit to Product Hunt | Marketing |
| All Day | Monitor and respond to comments | All |

---

## 8. Stakeholders & Roles

### 8.1 Core Team

| Name | Role | Responsibilities | Communication |
|------|------|------------------|---------------|
| Project Lead | Product Owner | Vision, decisions, launch | Slack, Email |
| Tech Lead | Architecture | Implementation, code review | Slack, GitHub |
| Docs Lead | Documentation | Guides, examples, README | Slack, GitHub |
| Marketing | Growth | Content, launch, community | Slack, Email |

### 8.2 RACI Matrix

| Task | Project Lead | Tech Lead | Docs Lead | Marketing |
|------|--------------|-----------|-----------|-----------|
| Repository Setup | A | R | C | I |
| Core Extraction | A | R | I | I |
| Agent Extraction | A | R | C | I |
| Improvements | A | R | I | I |
| Judge Implementation | A | R | I | I |
| Plugin Creation | A | R | I | I |
| Documentation | C | C | R | I |
| Examples | C | R | C | I |
| Visual Identity | A | I | I | R |
| Launch Content | A | I | C | R |
| Community Setup | R | I | I | C |
| Beta Testing | A | R | R | C |

**Legend:** R = Responsible, A = Accountable, C = Consulted, I = Informed

### 8.3 External Stakeholders

| Stakeholder | Interest | Engagement |
|-------------|----------|------------|
| Beta Users (5-10) | Early adopters, feedback providers | Discord, direct testing |
| Claude Code Team | Platform alignment | Awareness only |
| OpenRouter | Judge layer dependency | API access |
| Community | Future contributors | Discord, GitHub |

### 8.4 Marketing Messaging

Tailored messaging for different audience segments:

| Audience | Message | Key Value Proposition |
|----------|---------|----------------------|
| **Individual Developers** | "Ship features faster with structured AI workflows and specialized agents." | Speed, consistency, reduced cognitive load |
| **Team Leads** | "Bring consistency to AI-assisted development with quality gates and traceability." | Standardization, review process, team alignment |
| **Enterprise** | "Governance-first AI development with full audit trail from requirement to deployment." | Compliance, auditability, risk reduction |

### 8.5 Community Guidelines

#### Issue Triage SLA

| Label | Response SLA | Resolution Target |
|-------|--------------|-------------------|
| `bug` | 48 hours | 7 days |
| `security` | 24 hours | 3 days |
| `feature` | 7 days | Backlog |
| `docs` | 7 days | 14 days |
| `question` | 48 hours | 48 hours |

#### Contribution Types

| Type | Description | Approval Process |
|------|-------------|------------------|
| **Bug Fix** | Fix issues in core/plugins | PR review by 1 maintainer |
| **New Agent** | Add specialist agent | PR review + docs + example |
| **New KB Domain** | Add knowledge domain | PR review + MCP validation |
| **New Plugin** | Add domain plugin | Separate repo or PR + full docs |
| **Documentation** | Improve docs | PR review |
| **Example** | Add example project | PR review + working tests |

---

## 9. Success Metrics

### 9.1 Framework Quality Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| Agent matching accuracy | 7.5/10 | 9.2/10 | Judge scores |
| Features with agents | 60% | 95% | Audit DESIGN files |
| Judge adoption rate | 0% | 50% | Telemetry |
| KB freshness | 85% | 95% | /report |
| DEFINE→DESIGN failures | ~15% | ~5% | Telemetry |
| BUILD rework rate | ~20% | ~8% | Telemetry |

### 9.2 Open Source Traction Metrics

| Metric | 3 Month | 6 Month | 12 Month | Measurement |
|--------|---------|---------|----------|-------------|
| GitHub Stars | 500 | 2,000 | 5,000 | GitHub API |
| Monthly Downloads | 100 | 500 | 2,000 | Clone stats |
| Contributors | 5 | 15 | 30 | GitHub contributors |
| Community Plugins | 2 | 10 | 25 | Plugin registry |
| Discord Members | 50 | 200 | 500 | Discord stats |

### 9.3 Documentation Quality Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Quickstart completion | 15 min | User testing |
| Example code passes tests | 100% | CI validation |
| Broken links | 0 | Automated scan |
| Guide completeness | All sections | Checklist |

### 9.4 Key Differentiators vs Competition

| Feature | GitHub Spec-Kit | OpenSpec | AgentSpec |
|---------|-----------------|----------|-----------|
| Agent Matching | Manual | None | **Automatic** |
| Agent Validation | None | None | **Judge layer** |
| KB Grounding | None | None | **8+ domains** |
| Multi-LLM Review | None | None | **OpenRouter** |
| Usage Analytics | None | None | **Local telemetry** |
| Ecosystem Report | None | None | **/report command** |
| Session Recovery | None | None | **PROGRESS bridge** |
| Quality Gates | Informal | Informal | **Objective, automated** |

---

## 10. Appendices

### 10.1 Extraction Checklist

#### A. Core Framework (Required)

| Source Path | Target Path | Sanitized | Verified |
|-------------|-------------|-----------|----------|
| `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | `packages/core/sdd/architecture/` | [ ] | [ ] |
| `.claude/sdd/architecture/ARCHITECTURE.md` | `packages/core/sdd/architecture/` | [ ] | [ ] |
| `.claude/sdd/templates/BRAINSTORM_TEMPLATE.md` | `packages/core/sdd/templates/` | [ ] | [ ] |
| `.claude/sdd/templates/DEFINE_TEMPLATE.md` | `packages/core/sdd/templates/` | [ ] | [ ] |
| `.claude/sdd/templates/DESIGN_TEMPLATE.md` | `packages/core/sdd/templates/` | [ ] | [ ] |
| `.claude/sdd/templates/BUILD_REPORT_TEMPLATE.md` | `packages/core/sdd/templates/` | [ ] | [ ] |
| `.claude/sdd/templates/SHIPPED_TEMPLATE.md` | `packages/core/sdd/templates/` | [ ] | [ ] |

#### B. Commands (Required)

| Source Path | Target Path | Sanitized | Verified |
|-------------|-------------|-----------|----------|
| `.claude/commands/workflow/brainstorm.md` | `packages/core/commands/workflow/` | [ ] | [ ] |
| `.claude/commands/workflow/define.md` | `packages/core/commands/workflow/` | [ ] | [ ] |
| `.claude/commands/workflow/design.md` | `packages/core/commands/workflow/` | [ ] | [ ] |
| `.claude/commands/workflow/build.md` | `packages/core/commands/workflow/` | [ ] | [ ] |
| `.claude/commands/workflow/ship.md` | `packages/core/commands/workflow/` | [ ] | [ ] |
| `.claude/commands/workflow/iterate.md` | `packages/core/commands/workflow/` | [ ] | [ ] |
| `.claude/commands/core/memory.md` | `packages/core/commands/core/` | [ ] | [ ] |
| `.claude/commands/core/sync-context.md` | `packages/core/commands/core/` | [ ] | [ ] |
| `.claude/commands/knowledge/create-kb.md` | `packages/core/commands/knowledge/` | [ ] | [ ] |
| `.claude/commands/review/review.md` | `packages/core/commands/review/` | [ ] | [ ] |

#### C. Agents (Required)

| Source Path | Count | Sanitized | Verified |
|-------------|-------|-----------|----------|
| `.claude/agents/workflow/*.md` | 6 | [ ] | [ ] |
| `.claude/agents/code-quality/*.md` | 6 | [ ] | [ ] |
| `.claude/agents/communication/*.md` | 3 | [ ] | [ ] |
| `.claude/agents/exploration/*.md` | 2 | [ ] | [ ] |

#### D. KB Framework (Required)

| Source Path | Target Path | Sanitized | Verified |
|-------------|-------------|-----------|----------|
| `.claude/kb/_index.yaml` | `packages/kb/_index.yaml.template` | [ ] | [ ] |
| `.claude/kb/_templates/` | `packages/kb/_templates/` | [ ] | [ ] |
| `.claude/kb/pydantic/` | `packages/kb/pydantic/` | [ ] | [ ] |

#### E. Plugins (Optional)

| Source | Plugin | Sanitized | Verified |
|--------|--------|-----------|----------|
| `.claude/agents/domain/function-developer.md` | plugin-gcp | [ ] | [ ] |
| `.claude/agents/domain/infra-deployer.md` | plugin-gcp | [ ] | [ ] |
| `.claude/kb/gcp/` | plugin-gcp | [ ] | [ ] |
| `.claude/kb/terraform/` | plugin-gcp | [ ] | [ ] |
| `.claude/kb/terragrunt/` | plugin-gcp | [ ] | [ ] |
| `.claude/agents/aws/*.md` | plugin-aws | [ ] | [ ] |
| `.claude/agents/data-engineering/*.md` | plugin-data-engineering | [ ] | [ ] |
| `.claude/agents/ai-ml/*.md` | plugin-ai-ml | [ ] | [ ] |
| `.claude/kb/gemini/` | plugin-ai-ml | [ ] | [ ] |
| `.claude/kb/langfuse/` | plugin-ai-ml | [ ] | [ ] |
| `.claude/kb/openrouter/` | plugin-ai-ml | [ ] | [ ] |
| `.claude/agents/domain/dataops-builder.md` | plugin-crewai | [ ] | [ ] |
| `.claude/kb/crewai/` | plugin-crewai | [ ] | [ ] |

### 10.2 Sanitization Checklist

Before publishing, remove or anonymize:

#### A. Business-Specific Content

- [ ] Company names ("BTC Zero", internal project names)
- [ ] Client names (UberEats, DoorDash, etc.)
- [ ] Internal project references
- [ ] Business-specific success metrics
- [ ] Vendor-specific extraction prompts
- [ ] Internal meeting notes references
- [ ] Specific R$ currency amounts

#### B. Technical Secrets

- [ ] API keys (even expired ones)
- [ ] Secrets and credentials
- [ ] Internal URLs and endpoints
- [ ] Private repository URLs
- [ ] Internal IP addresses or hostnames
- [ ] Service account emails

#### C. Personal Information

- [ ] Personal names (unless permission granted)
- [ ] Email addresses
- [ ] Slack handles or user IDs
- [ ] GitHub usernames (internal)

#### D. Project-Specific Logic

- [ ] Invoice-specific schemas → Generic document schemas
- [ ] Restaurant-specific fields → Generic business fields
- [ ] Currency references → Generic placeholders

#### E. Hardcoded Paths

- [ ] `/Users/*/...` → Relative paths
- [ ] Project-specific absolute paths
- [ ] Environment-specific configurations

### 10.3 Quality Checklists

#### A. Documentation Quality Checklist

```text
CONTENT
[ ] Executive summary is clear and compelling
[ ] All code examples tested and working
[ ] Prerequisites clearly listed
[ ] Setup instructions tested

FORMAT
[ ] No inline comments in code blocks
[ ] ASCII-safe characters (no Unicode issues)
[ ] Tables properly formatted
[ ] All links validated

ACCURACY
[ ] Matches current code behavior
[ ] Versions and dependencies correct
[ ] Error scenarios documented
[ ] Security considerations covered
```

#### B. Agent Quality Checklist

```text
STRUCTURE
[ ] Has name, description, tools in frontmatter
[ ] Has Quick Reference section
[ ] Has Validation System
[ ] Has Capabilities section
[ ] Has Anti-Patterns section

CONTENT
[ ] Examples are realistic
[ ] Thresholds are appropriate
[ ] Error recovery documented
[ ] Extension points defined
```

#### C. KB Domain Quality Checklist

```text
STRUCTURE
[ ] Has index.md with overview
[ ] Has quick-reference.md
[ ] Has concepts/ folder
[ ] Has patterns/ folder

CONTENT
[ ] MCP validated
[ ] Freshness date recorded
[ ] Cross-references work
[ ] Code examples tested
```

### 10.4 Document References

| Document | Purpose | Location |
|----------|---------|----------|
| Open Source Plan | Original GitHub structure plan | `design/agentspec-open-source-plan.md` |
| Improvement Analysis | Core improvements + Judge proposal | `design/agentspec-improvement-analysis.md` |
| Plan Summary | Executive summary | `design/AGENTSPEC_PLAN_SUMMARY.md` |
| **Master Plan** | **Consolidated blueprint (this document)** | **`design/AGENTSPEC_MASTER_PLAN.md`** |

### 10.5 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.2 | 2026-02-03 | AgentSpec Team | Added Section 6.1 (Deferred Items), Section 8.4 (Marketing Messaging), Section 8.5 (Community Guidelines) |
| 1.1 | 2026-02-03 | AgentSpec Team | Removed Dev Loop to focus exclusively on SDD workflow |
| 1.0 | 2026-02-03 | AgentSpec Team | Initial consolidated master plan |

---

## Document Verification

```text
COMPLETENESS CHECK
[x] Section 1: Key Decisions - 13 decisions documented
[x] Section 2: Action Items - 50+ items with owners and dates
[x] Section 3: Requirements - FR, NFR, Constraints, Assumptions
[x] Section 4: Blockers & Risks - Risk matrix + 6 risks + 2 blockers
[x] Section 5: Architecture - Full structure + 3 ADRs + Judge architecture
[x] Section 6: Open Questions - 7 questions tracked
[x] Section 6.1: Deferred Items - 3 technical items + Judge phases + edge cases
[x] Section 7: Timeline - Visual + milestones + launch schedule
[x] Section 8: Stakeholders - RACI matrix + external stakeholders
[x] Section 8.4: Marketing Messaging - 3-tier audience messaging
[x] Section 8.5: Community Guidelines - Issue triage SLA + contribution types
[x] Section 9: Metrics - Quality + OSS + Documentation metrics
[x] Section 10: Appendices - Extraction + Sanitization + Quality checklists

QUALITY VERIFICATION
[x] All decisions have owners and status
[x] All action items have due dates
[x] All risks have mitigations
[x] All metrics have measurement methods
[x] Cross-references are complete
[x] Document is self-contained

CONSOLIDATION VERIFICATION (v1.2)
[x] agentspec-open-source-plan.md - 100% consolidated
[x] agentspec-improvement-analysis.md - 100% consolidated (deferred items tracked)
[x] AGENTSPEC_PLAN_SUMMARY.md - 100% consolidated
```

---

*Master Plan Created: 2026-02-03*
*Version: 1.2*
*Status: Ready for Execution*
*Frameworks Applied: Meeting Analyst (10-section), Codebase Explorer (Executive Summary), Code Documenter (Quality Checklists)*
