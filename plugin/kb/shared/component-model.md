# Component Model — agents, skills, commands, knowledge bases

> **Scope:** the canonical definition of what each component type is FOR, and the decision rule for where new logic lives. Referenced by the authoring skills (`create-skill`, `create-agent`, `kb-build`, the `component-model` skill) and exemplified by the SDD workflow components.

## The four layers

| Component | Responsibility | The test it answers |
|---|---|---|
| **Agent** | EXECUTION — runs a task or encodes a role: identity, tool scope, model tier, stop conditions, escalation. A thin shell around capabilities. | "Who does the work, with which tools and boundaries?" |
| **Skill** | CAPABILITY — teaches HOW to do something: specialized methodology, or how to use a resource or CLI properly. | "What knowledge makes the work correct and repeatable?" |
| **Command** | ENTRYPOINT — a user-facing door that sequences existing resources in the correct order: argument surface, mode selection, delegation. | "Where does the user start, and what happens in what order?" |
| **KB** | SOURCE OF TRUTH — self-contained deep dives on a topic; specialized, advanced knowledge that many components trust. | "What facts must stay consistent everywhere they are used?" |

Templates are the fifth, narrower piece: an artifact's required shape, owned in one place (`${CLAUDE_PLUGIN_ROOT}/sdd/templates/`, `${CLAUDE_PLUGIN_ROOT}/kb/_templates/`) and referenced by skills — never re-inlined.

## Out of scope: executable tools and engines

The four layers govern Claude-Code-native *instruction* artifacts — prompts and metadata the harness loads and resolves (agents, skills, commands, KBs). Executable engines under `tools/` (the Linter, ADR-002; the Judger, ADR-003) are a separate category this model deliberately does not classify: Python packages, not agents, skills, commands, or KBs. They are *consumed by* the instruction layers — via CLI invocation or contract-file wiring — never a fifth layer alongside the four.

## Where does new logic go?

| You are writing… | It belongs in |
|---|---|
| Process steps, question frameworks, quality-gate checklists, verification procedure | a **skill** |
| Identity, tool scoping, model tier, stop conditions, escalation targets, non-negotiable policies | an **agent** (frontmatter + thin shell) |
| Argument parsing, mode selection ("light vs `--validated`"), sequencing of existing pieces | a **command** |
| Reference facts, domain deep dives, standards other components must agree on | a **KB** file |
| An artifact's required shape | a **template**, pointed at by the skill |

When one piece of work spans layers, split it along these lines rather than picking the biggest layer: a new capability usually lands as a skill *plus* a one-line loading instruction in an agent or command, not as a fat agent.

## The thin-executor pattern

Agents stay thin: frontmatter (the machine-read contract — name, description, tier, model, tools, kb_domains, escalation), an identity statement, the phase's non-negotiable policies (for example decide-never-ask, halt-only-on-CRITICAL-risk), and one loading instruction — *read the corresponding skill and execute it*. Methodology lives in the skill so it can be versioned, swapped, and reused without touching the executor.

Commands stay thin the same way: parse the ask, pick the mode, load the skill (or delegate to the agent), and keep only command-only concerns such as flags.

## Anti-patterns

| Smell | Why it is wrong | Fix |
|---|---|---|
| Methodology written out inside an agent body | Duplicates the skill layer; drifts; commands cannot reuse it | Extract to a skill; the agent reads it |
| A command that re-implements its agent's process inline | Two parallel copies of one method | The command loads the same skill |
| The same guidance restated in agent + command + contract + docs | N sources of truth = N−1 stale copies | One owner per fact; everything else points |
| A KB used as a process doc, or ADRs/meeting notes stored in KB | KBs are reference truth, not workflows or logs | Process → skill; decisions → the decision log; notes → project notes |
| Facts (model, tools, size limits) duplicated outside their source | Drift — e.g. a contract disagreeing with frontmatter, or hardcoded limits disagreeing with `_index.yaml` | State the fact once; reference the owner |

## Refactoring a fat component

1. Split the body: methodology sections versus executor shell (identity, policies, escalation).
2. Move the methodology into a skill; point at templates for artifact shapes instead of re-inlining them.
3. Shrink the agent to the shell plus "read the skill and execute it".
4. Keep agent frontmatter byte-identical unless the contract itself is changing — the agent router regenerates from frontmatter.
5. Re-point every other copy (commands, contracts, docs) at the skill, keeping only contract-grade facts where they are.

The `component-model` skill carries the operational version of this procedure.

## Status

The SDD workflow components (six phase agents, their commands, and the `sdd-*` skills) follow this model and serve as the reference implementation. Other agent categories migrate opportunistically as they are touched.
