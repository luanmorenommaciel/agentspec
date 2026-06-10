# Spec Linter — Usage

> The Linter is a **contract-validation engine**: it checks whether an artifact
> adheres to a contract and returns a structured verdict. This document is
> **normative** about *what the engine does and what verdicts mean*, and
> **suggestive** about *how you might use it*. The usage choice belongs to the
> consumer.

## 1. What it is (BINDING)

- Mechanism: `lint(artifact, contract) -> Verdict` (`spec_linter/engine.py`).
  The engine has no opinion on what an artifact or contract represents: it asks
  the contract to `parse` the artifact, runs the contract's `check` on the
  result, and assembles the `Verdict` from the findings.
- A **Contract** is policy (`spec_linter/protocol.py`): anything with a `name`,
  a `parse(artifact)` that turns a raw artifact into a checkable object (or
  raises to signal an unparseable artifact), and a `check(parsed)` that returns
  findings — each finding carrying the severity the contract chose for that
  rule.
- If a contract's `parse` raises, the engine returns a single
  `<contract.name>.unparseable` FAIL finding. The engine adds nothing of its
  own beyond that.

## 2. Contracts: the three sources (BINDING shape, contract content is policy)

- (a) **Authored as code** — `AgentSpecContract`
  (`spec_linter/contracts/agent_spec.py`): the agent-spec reference contract
  (Pydantic model + governance rules). *Reference implementation pending the
  canonical agent-spec schema, owned upstream.* It also owns
  `emit_json_schema()` — the spec JSON Schema is a contract capability, not an
  engine one.
- (b) **Loaded as data** — `SddPhaseContract(phase, required_sections)`
  (`spec_linter/contracts/sdd_phase.py`): built from a phase's
  `required_sections` list (e.g., from a WORKFLOW_CONTRACTS-style YAML),
  validating a Markdown document — each required section must be present as a
  heading (matched case/punctuation-insensitively).
- (c) **Derived from an instance** — `InstanceContract(spec)`
  (`spec_linter/contracts/instance.py`): a spec's own
  `output_contract.required_fields` become the rule for the artifact it
  produces.

Findings are classified on the L1–L4 taxonomy (schema / contract / consistency
/ identity) — a finding-classification scheme, not usage vocabulary.

## 3. Verdict semantics (BINDING)

| Level | Meaning | Behavior |
|-------|---------|----------|
| PASS | fully compliant | proceed |
| WARN | advisory finding | proceed, but RECORD the finding |
| FAIL | non-compliance | BLOCK; CLI exits 1 |

- A `Verdict` aggregates to the worst finding present (FAIL > WARN > PASS); no
  findings means PASS.
- Each `Finding` is structured: `level`, `rule`, `message`, plus optional
  `field` / `expected` / `found`.
- A contract assigns severity to ITS rules; consumers MUST NOT reinterpret
  FAIL.

## 4. I/O and the CLI (BINDING)

- CLI: `python -m spec_linter.cli <path>` lints a spec file, or a directory of
  `.yaml`/`.yml` files (a directory run adds the cross-file duplicate-id
  check). Exit code is 1 if any verdict is FAIL, else 0.
- `--emit-schema OUT.json` writes the reference contract's JSON Schema to
  `OUT.json` (combine with a path to also lint; alone it just writes and exits
  0).
- Programmatic: `from spec_linter.engine import lint`; pass any Contract.

  ```python
  from spec_linter.contracts.sdd_phase import SddPhaseContract
  from spec_linter.engine import lint

  contract = SddPhaseContract("define", ["Problem Statement", "Acceptance Criteria"])
  verdict = lint(document_text, contract)  # -> verdict.level, verdict.findings
  ```

## 5. Usage patterns (SUGGESTIONS — consumers choose)

- **Pre-generation validation** (the "Gate A" pattern): validate a spec with the
  agent-spec contract before deriving artifacts from it.
- **Post-generation conformance** (the "Gate B" pattern): validate a produced
  artifact against the contract it should honor (instance- or phase-derived).
- **Two-pass loop with bounded retries**: validate → if FAIL, regenerate →
  re-validate, up to N attempts; then stop and surface the verdict.
- **CI / pre-commit**: run the CLI on changed artifacts; FAIL blocks the merge.

> These are patterns, not requirements. The engine does not mandate any of
> them. How the Linter WILL be used is declared by each consumer in its own
> canonical definition: the consumer picks its binding point and pattern; the
> engine stays usage-free.

## 6. Status & scope

- The agent-spec contract is a REFERENCE implementation; the canonical
  schema/contract content is owned upstream by the spec workstream (the
  interface between spec definition and spec validation). The engine and
  verdict semantics are the stable surface.
