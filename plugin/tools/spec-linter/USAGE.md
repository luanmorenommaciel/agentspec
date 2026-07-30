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
| PASS | fully compliant | proceed (CLI exits 0) |
| WARN | advisory finding | proceed, but RECORD the finding (CLI exits 0) |
| FAIL | non-compliance | BLOCK; CLI exits 1 |

- A `Verdict` aggregates to the worst finding present (FAIL > WARN > PASS); no
  findings means PASS.
- Each `Finding` is structured: `level`, `rule`, `message`, plus optional
  `field` / `expected` / `found`. Findings are immutable value objects.
- A contract assigns severity to ITS rules; consumers MUST NOT reinterpret
  FAIL.
- `Verdict` is exactly these three levels. An *operational* failure (an artifact
  that cannot even be loaded) is NOT a verdict — it is signalled by exit code 2
  (see §4), never by a fourth Level.

## 4. I/O and the CLI (BINDING)

### Entry point

`spec-lint` (the executable wrapper in this directory) is the documented entry
point. It verifies that `python3`, `pydantic`, and `pyyaml` are available; if any
is missing it prints `ERROR: spec-linter unavailable …` to stderr and exits 2, so
"linter not installed" fails loudly and deterministically rather than silently
passing. When the environment is healthy it forwards all arguments to the CLI.

```bash
./spec-lint <path>                    # lint a spec file or directory
./spec-lint <doc.md> --phase design   # lint a Markdown phase document
./spec-lint --emit-schema OUT.json    # write the spec JSON Schema
```

`python -m spec_linter.cli <args>` is equivalent when the dependencies are
already on the interpreter being used.

### Exit codes (BINDING)

| Exit | Meaning |
|------|---------|
| 0 | PASS or WARN verdict |
| 1 | FAIL verdict — a loadable artifact that violates its contract |
| 2 | ERROR — operational failure: file not found, YAML syntax error, non-mapping top level, a `.md` file with no frontmatter block or an invalid/non-mapping frontmatter block, unknown phase, missing dependencies, or any unexpected exception |

The boundary is decisive: a valid YAML mapping that breaks the contract is a
FAIL (exit 1, decided by the engine); input that cannot be loaded as a YAML
mapping — or a missing file — is an ERROR (exit 2). ERROR messages go to stderr;
verdict output goes to stdout.

### Modes

- **Spec linting** (default): lints a single spec file, or every spec file
  under a directory, against the agent-spec contract.
  - A `.yaml`/`.yml` file is loaded as a YAML mapping, as before.
  - A `.md` file is treated as a **self-contained artifact**: its leading
    `---`-fenced YAML frontmatter block IS the spec. The extracted mapping is
    linted exactly as a YAML spec file's mapping is — same contract, same
    verdicts, same output, same exit codes. A `.md` file with no frontmatter
    block, or a frontmatter block that is not valid YAML or not a mapping, is
    an operational ERROR (exit 2) — LOUD, never a silent pass.
  - **Directory walk**: recurses into subdirectories, so a category tree
    (e.g. `plugin/agents/<category>/*.md`) lints as one fleet in a single run. It
    selects every `.yaml`, `.yml`, and `.md` file. Files named exactly
    `README.md`, or whose name starts with `_` (scaffolding/templates), are
    excluded and reported once in a single `skipped (non-spec): ...` summary
    line — never silently dropped. The cross-file duplicate-id (L4) check
    spans YAML and MD entries alike; per-file verdicts and the final
    `OVERALL:` line are otherwise unchanged.
- **Phase linting** (`--phase NAME`): lints the path as a Markdown phase
  document against an `SddPhaseContract` whose `required_sections` are read from a
  WORKFLOW_CONTRACTS-style YAML. The source defaults to the repo's
  `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`; override it with
  `--contracts-file PATH`. Each required section must appear as a Markdown
  heading (matched case/punctuation-insensitively); a missing one is a FAIL.
  `--phase` takes precedence over frontmatter extraction exactly as before: a
  `.md` path given with `--phase` is always read as a raw phase document,
  never as a self-contained spec, even if it happens to open with a `---`
  block.
- **Schema emission** (`--emit-schema OUT.json`): writes the reference
  contract's JSON Schema to `OUT.json`, creating parent directories as needed
  (combine with a path to also lint; alone it just writes and exits 0).

### Programmatic use

`from spec_linter.engine import lint`; pass any Contract.

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
