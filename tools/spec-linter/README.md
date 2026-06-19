# Spec Linter — Gate A (spec validity) prototype

Local, self-contained prototype of a **contract-validation engine**: one mechanism,
`lint(artifact, contract) -> Verdict`, with pluggable contracts as policy and a CLI
that validates **AgentSpec** YAML files with a **Pydantic v2** model and layered
governance checks. It exists to validate an architecture decision (ADR-002): this is
a **reference prototype**, not the production code.

## What it proves

1. A YAML agent-spec is validated by a **Pydantic v2 model** (Layer 1 schema checks).
2. The **same** Pydantic model emits a **JSON Schema** via `model_json_schema()` —
   so "YAML + Pydantic + emit JSON Schema" is one pipeline, not a
   JSON-Schema-vs-Pydantic either/or.
3. **L2 cross-field governance rules** (the Policy Layer) are enforced as pure
   functions over a validated model.
4. A clean **PASS / WARN / FAIL** verdict with structured findings (rule, field,
   expected vs. found).
5. A **CLI** that lints a file or directory and exits non-zero on FAIL.
6. **One mechanism, many policies**: the same engine runs the agent-spec contract, a
   data-loaded SDD-phase contract, and an instance-derived contract; usage policy
   stays in consumers (here, the CLI).

## The four check layers (Gate A validates the spec only)

| Layer | What it checks | Where |
| --- | --- | --- |
| **L1 Schema** | Required fields, types, enums, kebab-case `id`. A schema violation makes the contract's `parse` raise, which the engine reports as a single `agent-spec.unparseable` FAIL (the raised message carries the per-field detail). Unknown keys → WARN. | `models.py` (Pydantic) + `contracts/agent_spec.py` |
| **L2 Contract / governance** | `maturity` ⇒ `stop_conditions` + `escalation_rules`; `V2/V3` ⇒ `observability`; `V3` ⇒ `memory_backend` + `recall_strategy`; `publish` ⇒ `security_review`. | `rules.py` |
| **L3 Consistency** | Every `requirements` item has a matching `deliverables` item (exact string). | `rules.py` |
| **L4 Identity** | Duplicate `id` across files in a directory lint (single-file lint skips L4). | `rules.py` + `cli.py` |

**Why L2/L3 are functions, not `model_validator`s that raise:** the spec model uses
`extra="allow"`, and a spec can be schema-valid yet governance-invalid. Keeping
governance out of L1 lets those surface as clean, individually-attributed L2/L3
findings instead of being collapsed into an L1 `ValidationError`. L1 (Pydantic) and
L2 (governance) stay cleanly separated — which is the architectural point.

## File → ADR mapping

This prototype backs **ADR-002 (Contract Enforcement Layer)**. The layered model
maps to the ADR as: L1 = schema validity (Pydantic-native), L2 = the Policy /
contract-enforcement layer, L3/L4 = consistency + identity guards. Each module owns
a single layer or concern:

| Module | Role |
| --- | --- |
| `spec_linter/engine.py` | the single mechanism: `lint(artifact, contract) -> Verdict` |
| `spec_linter/protocol.py` | the `Contract` protocol (`parse` + `check`) |
| `spec_linter/contracts/agent_spec.py` | agent-spec reference contract + `emit_json_schema` |
| `spec_linter/contracts/sdd_phase.py` | SDD-phase contract built from a `required_sections` list |
| `spec_linter/contracts/instance.py` | contract derived from a spec instance's `output_contract` |
| `spec_linter/models.py` | the `AgentSpec` model — L1 schema (Pydantic v2) + JSON Schema source |
| `spec_linter/verdict.py` | `Level`, `Finding`, `Verdict` output model |
| `spec_linter/rules.py` | L2/L3/L4 check functions |
| `spec_linter/cli.py` | CLI consumer: file/dir linting (incl. L4 wiring), `--phase` Markdown linting, schema emission, and the 0/1/2 exit-code contract |
| `spec-lint` | executable wrapper — the documented entry point; verifies dependencies (exit 2 if unavailable) then forwards to the CLI |
| `schema/agent_spec.schema.json` | committed `model_json_schema()` output (regenerable) |

## Run it

```bash
# from this directory
uv venv --python 3.12 .venv
. .venv/bin/activate
uv pip install -e '.[dev]'      # pydantic>=2,<3, pyyaml, pytest

pytest -q
```

`spec-lint` (the executable wrapper in this directory) is the entry point. It
checks that `python3`, `pydantic`, and `pyyaml` are present and exits 2 with a
clear message if not, then forwards to the CLI.

```bash
# lint a file (PASS, exit 0)
./spec-lint examples/valid_v2_agent.yaml

# lint a failing file (FAIL, exit 1)
./spec-lint examples/invalid_v2_no_observability.yaml

# lint a directory (runs L4 duplicate-id across files)
./spec-lint examples/

# lint a Markdown phase document against its phase contract
./spec-lint path/to/DESIGN_FEATURE.md --phase design

# (re)generate the committed JSON Schema
./spec-lint --emit-schema schema/agent_spec.schema.json
```

`python -m spec_linter.cli <args>` is equivalent when the interpreter already
has the dependencies.

### Exit codes

| Exit | Meaning |
|------|---------|
| 0 | PASS or WARN verdict |
| 1 | FAIL verdict (a loadable artifact that violates its contract) |
| 2 | ERROR — operational failure (missing file, YAML syntax error, non-mapping top level, unknown phase, missing dependencies, or any unexpected exception) |

A valid YAML mapping that breaks the contract is a FAIL (exit 1); input that
cannot be loaded as a YAML mapping, or a missing file, is an ERROR (exit 2).
