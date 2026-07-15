---
name: sdd-brainstorm
description: |
  Runs Phase 0 of the SDD workflow: collaborative exploration that turns a raw idea into a validated approach and a BRAINSTORM document ready for requirements capture.
  Owns the brainstorm methodology: KB-first grounding with confidence-scored recommendations, one-question-at-a-time discovery, sample collection for LLM grounding, comparison of 2-3 approaches with trade-offs, YAGNI scope pruning, incremental validation, and the quality gate that must pass before the document is written and /define is suggested.
  Use when the user wants to brainstorm a feature, explore an idea, compare approaches ("should I use X or Y?"), clarify a vague request ("I want to build..."), or run Phase 0 explicitly.
  Not for requirements capture: when requirements are already clear and validated, or a BRAINSTORM document already exists, use sdd-define (Phase 1) instead.
---

# SDD Brainstorm — Phase 0 exploration

Turn a raw idea into a validated approach and a BRAINSTORM document ready for `/define`.

This skill owns the Phase 0 methodology. The `brainstorm-agent` executes it and the `/brainstorm` command is the user entrypoint; both load this file instead of restating it. Contract-grade facts below mirror `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml` — when in doubt, the contract wins.

## Output contract

| Obligation | Value |
|---|---|
| Input types | raw idea, problem statement, feature request, rough notes, comparison request |
| Output file | `.claude/sdd/features/BRAINSTORM_{FEATURE}.md` — `{FEATURE}` in SCREAMING_SNAKE_CASE |
| Artifact shape | `${CLAUDE_PLUGIN_ROOT}/sdd/templates/BRAINSTORM_TEMPLATE.md` — follow the template; do not invent or drop sections |
| Status values | `Exploring` → `Approaches Identified` → `Ready for Define` |
| Handoff | suggest `/define .claude/sdd/features/BRAINSTORM_{FEATURE}.md` |

Set `Status: Exploring` while questioning, `Approaches Identified` once options are on the table, and `Ready for Define` only after the quality gate passes. Phase 1 later stamps the document `✅ Complete (Defined)` — leave that transition to `/define`.

## Scope boundary

Brainstorm explores; Define captures. Route by readiness:

| Situation | Do |
|---|---|
| Vague idea, approach unknown | Run this skill |
| Comparison request ("X or Y?") | Run this skill, centered on approach exploration |
| Requirements already clear and validated | Skip to `/define` directly |
| A BRAINSTORM document already exists | `/define` with that file as input |

## Knowledge architecture

KB-first resolution is mandatory: ground every recommendation before proposing it, in this order.

1. **KB discovery** — read `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml` and note which KB domains bear on the idea; they feed both your recommendations and the Define phase.
2. **Codebase exploration** — read `CLAUDE.md` for project context; Glob the project structure (for example `**/*.py`, `**/*.yaml`) for existing patterns.
3. **Confidence assignment** — score each candidate approach by its evidence:

| Evidence level | Confidence | Action |
|---|---|---|
| KB pattern + codebase match | 0.95 | Strong recommendation |
| KB pattern, no codebase match | 0.85 | Recommend with adaptation notes |
| Codebase pattern only | 0.80 | Suggest, validate with MCP |
| No precedent found | 0.70 | Present multiple options, ask the user |

State the evidence behind a recommendation when you make it — a cited KB pattern persuades better than an unbacked preference.

## Process

Run the seven steps in order. Steps 2-6 are conversational — never batch them into a single message.

### 1. Gather context

Read `CLAUDE.md`, `${CLAUDE_PLUGIN_ROOT}/sdd/templates/BRAINSTORM_TEMPLATE.md`, and `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml`, then explore the project structure and recent commits. Note the likely code location, relevant KB domains, and any IaC patterns — the template's Technical Context table expects these observations.

### 2. Ask discovery questions

Ask at least 3 questions, one at a time. Pick the form by terrain:

| Question type | When to use |
|---|---|
| Multiple choice | Options are clear (preferred — easier to answer) |
| Open-ended | Exploring unknown territory |
| Clarifying | The previous answer was vague |

Cover purpose, users, constraints, and success criteria. Record each question, answer, and its impact on the solution in the template's Discovery table.

### 3. Collect samples

Ask about available samples explicitly — sample inputs, expected output examples, ground truth, related code. This grounds the solution: few-shot examples raise LLM accuracy, ground truth prevents hallucination, and schema examples lock output format. If samples exist, analyze them and fill the template's Sample Data Inventory with locations, counts, and how each sample will be used.

### 4. Explore approaches

Present 2-3 distinct approaches (minimum 2, maximum 3). Lead with your recommendation and explain why — cite the KB or codebase evidence and its confidence score; never just list options. Format:

```markdown
### Approach A: {Name} ⭐ Recommended
**What:** {description}
**Pros:** {advantages}
**Cons:** {honest trade-offs}
**Why I recommend:** {reasoning — cite KB or codebase evidence}

### Approach B: {Name}
**What:** {description}
**Pros / Cons:** {...}
**Why not recommended:** {reasoning}
```

The user decides — never assume the choice, and record their confirmation.

### 5. Apply YAGNI

For every feature mentioned, ask three questions: Do we need this for MVP? Does it solve the core problem? Would the user miss it? A "no" to any removes the feature. Document every removal with its reasoning in the Features Removed section — deferred features often return later, so the record matters.

### 6. Validate incrementally

Present the emerging design in sections of 200-300 words. After each section, check "Does this look right so far?" and adjust before moving on. Complete at least 2 validation checkpoints. If an answer contradicts your understanding, go back and revise the earlier section — never plow forward past a misalignment.

### 7. Generate the document

Run the quality gate below. When every box checks, write `.claude/sdd/features/BRAINSTORM_{FEATURE}.md` following the template — including the draft requirements and sample inventory the Define phase will consume — then hand off as described in Transition to Define.

## Entry modes

The full sequence fits a raw idea; other triggers enter the same process with a different center of gravity:

| Mode | Trigger | Emphasis |
|---|---|---|
| Idea exploration | "I want to build...", vague requirement | Steps 1-3: understand problem, users, constraints, success criteria |
| Approach comparison | "Should I use X or Y?", multiple valid solutions | Step 4: check the KB and grep the codebase for each option, compare with evidence |
| Scope definition | Feature creep, unclear boundaries | Steps 5-6: list every mentioned feature, challenge each against MVP, confirm in-scope and out-of-scope lists |

Every mode still ends at the quality gate and the written document — a comparison answered in chat but never recorded is a lost decision.

## Question patterns

Multiple choice (preferred):

```markdown
"What's the primary goal?
(a) Speed up existing process
(b) Add new capability
(c) Replace legacy system
(d) Something else"
```

Clarifying (when an answer was vague):

```markdown
"You mentioned 'fast' - what does fast mean?
(a) Under 1 second
(b) Under 10 seconds
(c) Under 1 minute"
```

Sample collection:

```markdown
"Do you have any of the following to help ground the solution?
(a) Sample input files
(b) Expected output examples
(c) Ground truth / verified data
(d) None yet"
```

## Interaction style

- **One question at a time.** "What's the primary use case? (a) Internal reporting (b) Customer-facing (c) Both" — never "What's the use case? Who are the users? What's the timeline?"
- **Lead with the recommendation.** "I recommend Approach A because [reasoning]. Here are the alternatives..." — never "Here are three approaches. Which one do you want?"
- **Be ready to go back.** "That's different from what I understood. Let me revise..." — never "Moving on to the next section..."
- **Ask why.** "Why do you need this?" reveals the true requirement behind a stated feature.
- **Trust the user.** They know their domain; you know the patterns. Exploration is about understanding, not speed.

## Quality gate

Every box must check before the document is written:

```text
[ ] Minimum 3 discovery questions asked and answered
[ ] Sample data question asked (inputs, outputs, ground truth)
[ ] At least 2 approaches explored with trade-offs
[ ] User explicitly confirmed the selected approach
[ ] YAGNI applied — removed-features section populated
[ ] Minimum 2 incremental validations completed
[ ] KB domains identified for the Define phase
[ ] Draft requirements ready for /define
```

If a box fails, return to the corresponding process step — do not write a partial document.

## Anti-patterns

| Never do | Why | Instead |
|---|---|---|
| Ask multiple questions per message | Overwhelms the user | One question at a time |
| Assume answers | Misses real needs | Ask explicitly |
| Present a single approach | No comparison means no informed choice | Present 2-3 options |
| Skip sample collection | Solution is less grounded | Ask about inputs, outputs, ground truth |
| Skip validation checkpoints | Misalignment surfaces at Define or later, where it costs more | Validate every 200-300 words |
| Let scope creep through | Bloats every downstream phase | Apply YAGNI and document removals |
| Jump to the solution | Solves the wrong problem | Understand the problem first |

## Transition to Define

When the quality gate passes:

1. Save the document to `.claude/sdd/features/BRAINSTORM_{FEATURE}.md` with `Status: Ready for Define`.
2. Confirm the KB domains for Phase 1 are recorded in the document.
3. Tell the user: "Ready for `/define .claude/sdd/features/BRAINSTORM_{FEATURE}.md`".

## References

- Contracts (phase obligations): `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Template (artifact shape): `${CLAUDE_PLUGIN_ROOT}/sdd/templates/BRAINSTORM_TEMPLATE.md`
- Executor: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/brainstorm-agent.md`
- Entrypoint: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/brainstorm.md`
- Next phase: `sdd-define` / `${CLAUDE_PLUGIN_ROOT}/commands/workflow/define.md`
