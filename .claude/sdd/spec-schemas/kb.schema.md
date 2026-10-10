# kb.schema.md — Spec Schema for KB Domain Creation

> Defines the ephemeral, pre-generation spec format for creating a new KB
> domain. Consumed by `kb-architect` (spec mode — generation plus the same
> advisory pre-flight it already runs in manual mode) and, going forward, by
> `tools/spec-linter/` (Gate A/B enforcement — see [Enforcement](#enforcement)
> below). Governed by ADR-007 (issue #68). Layer 2 of the `feat/spec-schemas`
> plan (issue #71).

## Naming note

This schema is the **creation-time** input a human fills in before
`kb-architect` generates anything. It is not the domain's manifest entry
(`.claude/kb/_templates/domain-manifest.yaml.template`, which is the
**output contract** this schema pairs with — the shape of the block that
lands in `.claude/kb/_index.yaml`), and it is not a KB `specs/*.yaml` file
(`.claude/kb/_templates/spec.yaml.template`, a machine-readable artifact
*inside* a domain). Three different things share the word "spec"; this file
is the one that never lands anywhere.

---

## Spec file location

Filled-in specs live at `.claude/sdd/specs/kb/{domain-key}.spec.md` while in
progress. Archival location: `.claude/sdd/archive/specs/{domain-key}/`
(ADR-004 §3.9 — provenance only, never load-bearing; the graduation rule
applies before archiving).

A spec file is a Markdown file whose body carries exactly one ` ```yaml `
fenced block holding the fields below; prose outside the block is free-form
notes for the human and is ignored by generation and gates.

---

## How this differs from `agent.schema.md`

Layer 1 maps one spec onto **one** generated file. A KB domain is a
**1-to-many fan-out**: one spec drives five output types —

```text
.claude/kb/{domain-key}/
├── index.md                 (1)
├── quick-reference.md       (1)
├── concepts/{concept}.md    (× N, N >= 3)
├── patterns/{pattern}.md    (× M, M >= 3)
└── _index.yaml entry        (1, additive — in .claude/kb/_index.yaml)
```

So the mapping below lists, for each spec field, *every* output it lands in,
and Gate B checks the *set* of outputs rather than a single file.

---

## Spec-only fields

These fields exist only in the spec. They inform generation and (eventually)
gate enforcement, but are never copied into any generated file:

```yaml
intent: >
  # Why this KB domain is being created — one specific sentence naming the
  # gap. Example: "No registered domain covers Redis caching patterns;
  # cloud-platforms mentions Redis only as a managed-service line item."

domain_scope:
  in_scope:
    - "{topic this domain covers}"
    - "{another topic}"
  out_of_scope:               # REQUIRED — an empty list fails Gate A
    - "{adjacent topic deliberately excluded, and which domain owns it}"

overlap_check: 0.0            # Fraction (0.0-1.0) of in_scope covered by
                              # the nearest domain registered in _index.yaml.
                              # Gate A input. Name the nearest domain in
                              # `nearest_domain` so the number is auditable.
nearest_domain: "{domain-key or none}"

concept_count: 0              # Planned number of concept files. Gate A: >= 3.
pattern_count: 0              # Planned number of pattern files. Gate A: >= 3.
                              # Each count must equal the length of the
                              # matching list below — a count that outruns
                              # its list is the claim Gate A exists to test.

sources:                      # Primary sources kb-architect validates against
  - "{official docs / standard / source repo URL}"
```

---

## Mapped fields

These fields are the "cube": they land in the generated outputs, transformed
as described in the mapping.

```yaml
domain_key: "{lowercase-kebab}"          # directory name + _index.yaml key
domain_name: "{Display Name}"
description: "{one line — what the domain covers, as _index.yaml shows it}"

concepts:                                # length == concept_count
  - name: "{concept-slug}"
    purpose: "{one line — what the reader learns}"
patterns:                                # length == pattern_count
  - name: "{pattern-slug}"
    purpose: "{one line — the problem the pattern solves}"

agents:                                  # which agents should list this
  - "{agent-name}"                       # domain in kb_domains (informs
                                         # index.md's Agent Usage table)
```

---

## Cube→square mapping (1-to-many)

| Spec field | Lands in | Mode |
|---|---|---|
| `domain_key` | `_index.yaml` key, `path: {domain_key}/`, directory name | copied 1:1 |
| `domain_name` | `_index.yaml` `name`; `index.md` title; `quick-reference.md` title | copied 1:1 |
| `description` | `_index.yaml` `description`; `index.md` Purpose line | copied 1:1 |
| `concepts[].name` | `_index.yaml` `concepts[].path`; `concepts/{name}.md` filename; `index.md` Concepts table | copied 1:1 |
| `concepts[].purpose` | `concepts/{name}.md` Purpose line; `index.md` Concepts table | copied 1:1 |
| `patterns[].name` / `.purpose` | same shape as concepts, under `patterns/` | copied 1:1 |
| `agents` | `index.md` Agent Usage table | copied 1:1 |
| `sources` | every generated file's `MCP Validated` header date (after validation) | consumed, not copied |
| concept / pattern **bodies** | `concepts/*.md`, `patterns/*.md` | **generated** by `kb-architect` from validated sources, following `concept.md.template` / `pattern.md.template` |
| `quick-reference.md` tables | `quick-reference.md` | **generated** from the concept/pattern bodies |
| `_index.yaml` `concepts[].confidence` | `_index.yaml` entry | **generated** from the validation confidence matrix |

`index.md` and `quick-reference.md` are always produced, from `domain_name`
+ `description` + the two lists — there is no spec field that opts out of
them. `specs/`, `reference/` and `examples/` are optional in the manifest
(see the output contract) and are **not** produced by spec mode in Layer 2;
add them through `kb-architect`'s existing manual path.

If the mapping is ambiguous for a given spec (e.g. a concept and a pattern
share a slug, or `agents` names an agent that does not exist),
`kb-architect` stops and asks rather than guessing — see its
`stop_conditions`.

---

## Gate A / Gate B criteria

**Gate A (pre-generation — should this domain exist at all):**

| Check | Threshold |
|---|---|
| `overlap_check` | < 0.60 against `nearest_domain` |
| `concept_count` | >= 3, and equal to `len(concepts)` |
| `pattern_count` | >= 3, and equal to `len(patterns)` |
| `domain_scope.out_of_scope` | non-empty — a domain with no declared exclusions has no boundary to lint |
| `intent` | non-empty and specific (not a restatement of `domain_name`) |
| `domain_key` | lowercase-kebab, not already a key in `_index.yaml` |

**Gate B (post-generation — does the artifact set honor the spec):**

Gate B is the `output_contract:` block of
`.claude/kb/_templates/domain-manifest.yaml.template` — the output contract.
It is reproduced here for reference; the template is the source of truth.

| Check | Rule |
|---|---|
| Required manifest fields | `name`, `description`, `path`, `entry_points` present on the `_index.yaml` entry |
| Entry points exist | `entry_points.index` and `entry_points.quick_reference` resolve to files on disk under `path` |
| Listed paths exist | every `concepts[].path` and `patterns[].path` resolves to a file on disk under `path` |
| Minimums | `len(concepts) >= 3`, `len(patterns) >= 3` |
| Registered | `domain_key` is a key under `domains:` in `_index.yaml` |
| Fidelity | 1:1-mapped fields match the spec exactly; the spec-only fields appear in no generated file |

Every Gate B rule except fidelity is a filesystem or YAML check — no
heading matching, no prose judgement. That is deliberate: it is what makes
this gate the first one a deterministic contract can enforce end to end.

Content checks — whether the concept and pattern bodies are correct, complete
or well written — are deliberately out of Gate B. They need judgement and
tokens, which makes them the Judger's domain (ADR-003, `behavioral_enforcement`
in `WORKFLOW_CONTRACTS.yaml`), not the Linter's. Gate B stays scoped to what a
deterministic contract can check.

---

## Enforcement

`kb-architect` in spec mode runs the **same advisory pre-flight** it already
runs in manual mode (its Quality Gate section), now reading the thresholds
from this schema (Gate A) and the template's `output_contract:` block (Gate B)
instead of carrying them in prose. That self-check is advisory — it is the
agent's own quality bar, not a verdict a consumer may rely on.

Normative enforcement belongs to `tools/spec-linter/`: a `kb-domain`
contract that evaluates the `output_contract:` block against `_index.yaml` and
the filesystem is the follow-up this schema is written to make mechanical,
not part of Layer 2. Until it lands, "Gate B passed" means "kb-architect
reported its pre-flight clean", nothing stronger.

---

## Example (abbreviated)

```yaml
intent: >
  No registered domain covers Redis caching patterns; cloud-platforms names
  Redis only as a managed-service line item and supabase covers Postgres.
domain_scope:
  in_scope: [cache-aside, write-through, TTL and eviction, Redis data types]
  out_of_scope:
    - "Managed Redis provisioning (cloud-platforms owns it)"
    - "Pub/Sub messaging (streaming owns it)"
overlap_check: 0.15
nearest_domain: cloud-platforms
concept_count: 3
pattern_count: 3
sources:
  - https://redis.io/docs/latest/

domain_key: redis-caching
domain_name: Redis Caching
description: "Redis caching patterns — cache-aside, write-through, TTL/eviction, data-type selection"
concepts:
  - { name: data-types,        purpose: "Which Redis type fits which access pattern" }
  - { name: ttl-and-eviction,  purpose: "How keys expire and what eviction policy to pick" }
  - { name: consistency-model, purpose: "What Redis guarantees under replication" }
patterns:
  - { name: cache-aside,       purpose: "Lazy-load reads with explicit invalidation" }
  - { name: write-through,     purpose: "Keep cache and store in sync on write" }
  - { name: hot-key-mitigation, purpose: "Spread load off a single hot key" }
agents: [data-platform-engineer]
```
