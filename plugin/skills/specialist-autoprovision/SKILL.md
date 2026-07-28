---
name: specialist-autoprovision
description: |
  Detects and fills specialist gaps before implementation is delegated: resolves every task domain in the agent-matched file manifest against the generated router inventory using a mandatory-citation rule, and on a gap runs the JIT provisioning sub-flow — component-model layer gate, create-agent/create-skill SOP authoring, public-repo hygiene gate, mandatory router regeneration, and core ship-checklist validation — so execution is delegated only after the new specialist is citable in the oracle.
  Owns the citation match semantics, the sub-flow steps and their ordering, the supervised/autonomous conduct fork (at most one question, only at the layer decision), the provenance row shape, and the degradation rule when the sensor itself is unavailable. Consumed as thin hooks by sdd-design (Step 4.5, the primary sensor) and sdd-build (delegation safety net); the proceed/retry/abort policy for autonomous runs is Gate P, owned by sdd-autopilot.
  Use when a manifest row has no citable specialist, when delegation hits an unresolvable @agent, or when asked to check specialist coverage or provision a missing specialist.
  Do not use to author a component when the layer is already decided and no coverage question exists — that is create-skill or create-agent directly — and do not use to change gate budgets or abort semantics, which are owned by sdd-autopilot.
---

# Specialist Autoprovision — gap detection and JIT provisioning

Resolve every task domain against the specialist inventory before delegation; when nothing covers a domain, create the specialist through the existing authoring SOPs — never a bespoke path — and delegate only after the regenerated router resolves it.

This skill owns the methodology. `sdd-design` (Step 4.5) and `sdd-build` (delegation safety net) load it as thin hooks; `sdd-autopilot` owns the autonomous gate policy (Gate P). None of them restate a rule that lives here, and this skill states no gate budget — that is Gate P's.

## The citation rule (match semantics)

A task domain **resolves** if and only if a **citation** can be recorded — a specific inventory entry plus the covering signal:

| Citation type | Form | Resolution |
|---|---|---|
| Agent | `{agent-name, signal}` where the signal is a `kb_domains` hit or explicit coverage in the routing one-liner (`description` first line) in `${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json` | Manifest row gets `@agent-name`; citation recorded in the Agent Assignment Rationale |
| Skill | An existing skill (`${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`) whose description covers the capability | Manifest row stays `(general)` with that skill loaded — **not a gap** |

**No citable entry → gap → run the provisioning sub-flow.** Never resolve a domain from memory of the inventory: cite the oracle artifact. Never assign a numeric confidence to a match — the citation is the evidence, and it is checkable mechanically after the run.

The oracle is `${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json` (plus generated `SKILL.md`), regenerated from agent frontmatter by `scripts/generate-agent-router.py` — it cannot drift from the real inventory, which is why ad-hoc greps of agent files are never the sensor.

## The provisioning sub-flow

Run the steps in order. Steps 1–5 are the synchronous core; step 6 schedules the rest.

### 1. Layer gate

Load the `component-model` skill and decide the layer for the missing capability: skill, agent (thin executor), or extend-existing. The four-condition anti-sprawl gate in `${CLAUDE_PLUGIN_ROOT}/agents/README.md` binds the agent option — no existing agent covers >60%, unique KB/tool combination, ≥3 distinct triggers, no >80% overlap. This fork is the only point the conduct table below may ask a human.

### 2. Author via the SOP

- Layer = skill → author per `create-skill` (naming, placement, frontmatter pitfalls).
- Layer = agent → author per `create-agent` (frontmatter contract as the router reads it: clean first description line, inline `kb_domains`, real escalation targets). Scaffold from `${CLAUDE_PLUGIN_ROOT}/agents/_template.md`; tool scope least-privilege for the role — no `Bash` or network tools unless the role requires them.
- Layer = extend-existing → apply the extension and stop; no new component, no further sub-flow steps beyond re-verifying the citation.

A generated specialist may ship with `kb_domains: []` when no KB domain covers its territory — KB creation is never part of this sub-flow.

### 3. Hygiene gate (blocking)

Before the component counts as authored, grep it against the public-repo private-context list (client names, credentials, run-private data). A hit **blocks** the component: regenerate without the offending context. Never land-then-clean.

### 4. Regenerate the router and verify the citation

```bash
python3 scripts/generate-agent-router.py

# Agents: the regenerated oracle must resolve the new specialist by name
grep -q "\"name\": \"${NEW_AGENT_NAME}\"" ${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json

# Skills: on-disk presence with parseable frontmatter is the citation
test -f "${CLAUDE_PLUGIN_ROOT}/skills/${NEW_SKILL_NAME}/SKILL.md"
```

The component **exists** only when this verification passes — a written file whose citation does not verify is a failed provisioning attempt, not a specialist.

### 5. Finalize the manifest row

Record the citation for the new component exactly as for a pre-existing one. Within the same run, a later gap for the same domain cites the just-created component — never provision twice for one domain.

### 6. Schedule the deferred checklist items

Append the authoring SOP's remaining ship-checklist items — plugin mirror rebuild, catalog/README updates, count references, CHANGELOG entry — to the file manifest as ordinary build tasks. They stay binding (Gate B completeness and the pre-ship checklist verify them); they are scheduled, never relaxed. Same contracts, same checklist as hand-authored components — there is no "generated" tier.

## Conduct fork

| Mode | Layer-gate fork (step 1) | Everything else |
|---|---|---|
| Supervised (`/design`, `/build`) | May ask the user **once** (AskUserQuestion) when the four-condition gate does not decide cleanly | Mechanical — contracts decide; no questions |
| Autonomous (`/auto`) | Assume **skill + thin executor** (the conservative default: a skill can later gain an executor; an unnecessary agent pressures the anti-sprawl gate), record `[ASSUMED]` | Gate P policy (sdd-autopilot): proceed / retry within budget / abort with gap report — never ask |

## Provenance (mandatory per event)

Every provisioning event writes one row — RUN REPORT (autonomous) or BUILD_REPORT (supervised):

```markdown
| Component | Layer | Trigger Domain | Phase | Fork Resolution | Validation |
|-----------|-------|----------------|-------|-----------------|------------|
| terraform-modules (skill) | skill + thin executor | terraform | design (Gate P) | [ASSUMED] conservative default | core checklist PASS; docs items → manifest rows 10–12 |
```

Rows record decisions and sensor presence/absence — never environment values, keys, or run-private data.

## Degradation rules

| Failure | Behavior |
|---|---|
| `scripts/generate-agent-router.py` not executable, or oracle unreadable after one regeneration attempt | **VISIBLE SKIP** + fall back to `(general)` execution with a WARN row — the pre-feature status quo, degraded loudly. Never assume a citation that was not verified |
| Authoring output fails step 4 verification | One regeneration with the violations in context (Gate P budget); supervised mode surfaces the failure to the user instead of aborting |
| Hygiene gate hit | Regenerate without the private context — within the same budget |

The flow may degrade **to** the status quo (`(general)` + WARN), never below it, and never silently.

## Anti-patterns

| Never do | Why | Instead |
|---|---|---|
| Grep agent files as the availability sensor | Reimplements and drifts from the router's parser | Cite `routing.json`; regenerate it when in doubt |
| Score matches numerically | LLM scores are not reproducible run-to-run; a flaky sensor decides component creation | The citation rule — binary, recorded, checkable |
| Create an agent for a capability-shaped gap | Most gaps are methodology, not identity; agent sprawl | Layer gate first; default to skill + thin executor |
| Skip router regeneration after authoring | The component is invisible to every later resolution | Step 4 is binding — no verified citation, no specialist |
| Relax checklist items for generated components | Two quality tiers drift apart | Defer and schedule (step 6); never drop |
| Provision the same domain twice in one run | Duplicate components; anti-sprawl violation | Cite the just-created component |
| Embed run-private context in a generated component | Public repo; hygiene is a blocking gate | Step 3 before anything lands |

## References

- Oracle: `${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json` + `scripts/generate-agent-router.py` (parser contract documented in `create-agent`)
- Layer gate: `${CLAUDE_PLUGIN_ROOT}/skills/component-model/SKILL.md`, grounded in `${CLAUDE_PLUGIN_ROOT}/kb/shared/component-model.md`; anti-sprawl conditions in `${CLAUDE_PLUGIN_ROOT}/agents/README.md`
- Authoring SOPs: `${CLAUDE_PLUGIN_ROOT}/skills/create-skill/SKILL.md` · `${CLAUDE_PLUGIN_ROOT}/skills/create-agent/SKILL.md` · `${CLAUDE_PLUGIN_ROOT}/agents/_template.md`
- Consumers: `${CLAUDE_PLUGIN_ROOT}/skills/sdd-design/SKILL.md` (Step 4.5) · `${CLAUDE_PLUGIN_ROOT}/skills/sdd-build/SKILL.md` (delegation safety net)
- Autonomous gate policy: `${CLAUDE_PLUGIN_ROOT}/skills/sdd-autopilot/SKILL.md` (Gate P)
- Design rationale: `.claude/sdd/features/DESIGN_SPECIALIST_AUTOPROVISION.md` (Decisions 1–4)
