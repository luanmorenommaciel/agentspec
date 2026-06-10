# Spec Linter — Gate A (spec validity) prototype

Local, self-contained prototype that validates an **AgentSpec** YAML file with a
**Pydantic v2** model and runs layered governance checks. It exists to validate an
architecture decision (ADR-002): this is a **reference prototype**, not the
production code.

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

## The four check layers (Gate A validates the spec only)

| Layer | What it checks | Where |
| --- | --- | --- |
| **L1 Schema** | Required fields, types, enums, kebab-case `id`. ValidationError → FAIL (one finding per error). Unknown keys → WARN. | `models.py` (Pydantic) + `linter.py` |
| **L2 Contract / governance** | `maturity` ⇒ `stop_conditions` + `escalation_rules`; `V2/V3` ⇒ `observability`; `V3` ⇒ `memory_backend` + `recall_strategy`; `publish` ⇒ `security_review`. | `rules.py` |
| **L3 Consistency** | Every `requirements` item has a matching `deliverables` item (exact string). | `rules.py` |
| **L4 Identity** | Duplicate `id` across files in a directory lint (single-file lint skips L4). | `rules.py` + `linter.py` |

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
| `spec_linter/models.py` | L1 schema (Pydantic v2) + JSON Schema source |
| `spec_linter/verdict.py` | `Level`, `Finding`, `Verdict` output model |
| `spec_linter/rules.py` | L2/L3/L4 check functions |
| `spec_linter/linter.py` | orchestration: `lint_spec` / `lint_file` / `lint_dir` / `emit_json_schema` |
| `spec_linter/cli.py` | CLI entry point |
| `schema/agent_spec.schema.json` | committed `model_json_schema()` output (regenerable) |

## Run it

```bash
# from this directory
uv venv --python 3.12 .venv
. .venv/bin/activate
uv pip install -e '.[dev]'      # pydantic>=2,<3, pyyaml, pytest

pytest -q

# lint a file (PASS, exit 0)
python -m spec_linter.cli examples/valid_v2_agent.yaml

# lint a failing file (FAIL, exit 1)
python -m spec_linter.cli examples/invalid_v2_no_observability.yaml

# lint a directory (runs L4 duplicate-id across files)
python -m spec_linter.cli examples/

# (re)generate the committed JSON Schema
python -m spec_linter.cli --emit-schema schema/agent_spec.schema.json
```
