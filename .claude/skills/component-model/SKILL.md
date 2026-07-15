---
name: component-model
description: |
  Decides where new logic lives in the component model — agent, skill, command, KB, or
  template — and how to keep components in their layer, routing each decision to the
  right authoring resource and running the fat-to-thin refactor when a component has
  outgrown its layer. Loaded by the authoring flows (create-skill, create-agent,
  kb-build, create-kb) as their layer-decision gate. Use for "should this be an agent
  or a skill", "where does this logic go", adding a new component, "this agent is too
  big", or restructuring/refactoring an agent into skills. Do not use to author the
  chosen component itself — that is create-skill, create-agent, or /create-kb.
---

# Component Model — layer decision and fat-to-thin refactor

The operational side of the repository's component model: place new logic in the right
layer, and pull overgrown components back into theirs. The canonical definitions — the
four layers, the placement table, the thin-executor pattern — live in
`.claude/kb/shared/component-model.md`; this skill applies that model, it does not
restate it.

## When to use

- Deciding whether new functionality should be an agent, a skill, a command, a KB file,
  or a template.
- Planning a new component before authoring it — the authoring flows load this skill
  first as their layer-decision gate.
- A component has grown fat — an agent body full of process steps, a command
  re-implementing methodology inline — and needs restructuring.
- Reviewing a change that spans component types and looks misplaced.

## Skip if

- The layer is already decided and you are authoring the component — go straight to
  `create-skill`, `create-agent`, or `/create-kb`.
- The change is content-only inside an existing component (fixing a step in a skill,
  updating a KB fact) — no layer question exists.

## The decision procedure

1. **Read the canonical model.** Open `.claude/kb/shared/component-model.md` — the four
   layers, the "where does new logic go" table, and the thin-executor pattern are
   defined there, and every classification below is grounded in that file. Read it
   before classifying, not after.

2. **Classify the new logic.** Ask, in order, and stop at the first yes:

   - Does it say *how* to do something — process steps, question frameworks,
     quality-gate checklists, a verification procedure? → **skill**.
   - Does it define *who* does the work — identity, tool scope, model tier, stop
     conditions, escalation targets, non-negotiable policies? → **agent** (frontmatter
     plus thin shell).
   - Does it define *where the user starts* — argument surface, mode selection,
     sequencing of existing pieces? → **command**.
   - Is it a *fact* other components must agree on — reference truth, standards, domain
     deep dives? → **KB file**; if it is an artifact's required shape, it is a
     **template** the skill points at.

   A piece of work that answers yes more than once spans layers — go to step 3.

3. **Split multi-layer work along layer lines.** Do not pick the biggest layer and stuff
   everything into it. A new capability normally lands as a skill *plus* a one-line
   loading instruction in the agent or command that uses it — not as a fat agent. A new
   entrypoint lands as a thin command that sequences existing agents and skills, never
   one that re-implements them. Worked example — "add a code-review capability" splits
   four ways: the review method is a skill; the reviewer identity and tool scope are
   agent frontmatter; the user-facing entrypoint is a thin command; the severity
   taxonomy every component must agree on is a KB fact.

4. **Route to the authoring resource.**

   | Chosen layer | Author it with |
   |---|---|
   | Skill | `create-skill` — repo naming, placement, frontmatter, ship checklist; defers to upstream `skill-creator` for general craft |
   | Agent | `create-agent` |
   | KB domain | `/create-kb`; add `--validated` (the `kb-build` skill) when every claim must be source-verified |
   | Command | no authoring skill — keep it thin: parse arguments, pick the mode, load the skill or delegate to the agent |
   | Template | own it in the template directories (`.claude/sdd/templates/`, `.claude/kb/_templates/`) and have skills reference it |

## Misclassification smells

Concrete tells that logic sits in the wrong layer, with the fix:

| Smell | Fix |
|---|---|
| Agent body carrying more than ~50 lines of process steps | Extract the methodology into a skill; the agent loads it — see the refactor below |
| A command re-implementing its agent's method inline | The command loads the same skill the agent does, so one copy of the method exists |
| The same fact stated in two components | Pick the owner; the other points at it — N copies means N−1 stale ones |
| A KB file describing a workflow ("first do X, then Y") | That is a skill; KBs hold reference truth, not procedures |
| A skill inlining an artifact's full required shape | Move the shape to a template; the skill references it |
| An agent's contract facts (model, tools, limits) restated in commands or docs | Frontmatter is the owner; point at it instead of copying |

## Refactoring a fat component

The operational version of the recipe in the KB — run it when a component (usually an
agent) has absorbed methodology that belongs a layer down:

1. **Split the body** into methodology (process steps, frameworks, checklists) versus
   executor shell (identity, non-negotiable policies, escalation).
2. **Create the skill** — named `<domain>-<verb>` per `create-skill` conventions — and
   move the methodology into it; point at templates for artifact shapes instead of
   re-inlining them.
3. **Shrink the agent** to identity + policies + one loading instruction: read the
   skill and execute it.
4. **Keep agent frontmatter byte-identical** unless the contract itself is changing —
   the agent router regenerates from frontmatter, so an accidental frontmatter diff
   silently changes routing.
5. **Re-point every other copy** — commands, contracts, docs — at the new skill,
   keeping only contract-grade facts where they are.
6. **Verify with a rebuild** — run the plugin build and confirm the router output and
   mirrored skills change only where intended.

The SDD workflow components are the reference implementation of the end state: thin
`*-agent` executors, `sdd-*` skills carrying the methodology, and thin phase commands
sequencing them.

## References

| Resource | When to read |
|---|---|
| `.claude/kb/shared/component-model.md` | Always — the source of truth for layer definitions, the placement table, and anti-pattern rationale |
| `create-skill` skill | The decision landed on "skill" |
| `create-agent` skill | The decision landed on "agent" |
| `kb-build` skill / `/create-kb` command | The decision landed on "KB domain" |
