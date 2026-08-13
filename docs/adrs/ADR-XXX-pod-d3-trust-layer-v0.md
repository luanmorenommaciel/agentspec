# ADR-XXX — Trust Layer V0 (cosign + manifest)

> **Status:** Proposed
> **Date:** 2026-07-22
> **Related:** Issue #23. Builds on ADR-001 (#31), ADR-002 (#54), and ADR-003 (#57). Family peer to the Scorer proposal.

---

## 1. Context

AgentSpec ships as a Claude Code plugin whose payload is entirely declarative: 58 agents, 31 commands, and 24 knowledge-base domains, distributed as `.md`, `.yaml`, `.json`, and `.toml` files. Once installed, each file is read by the runtime and executed as instruction — **the prompt is the code**. A single-byte edit to an agent markdown is a silent prompt injection, indistinguishable from the original at load time.

Git proves history, not integrity at rest. Once the plugin is packaged and pushed to the marketplace, the guarantees git offered on the source repository are gone: consumers install the payload without any mechanical way to verify that (a) the bytes on disk match what the author published, or (b) the publisher is who they claim to be.

Issue #23 tracks this gap as the "marketplace / trust-layer spike". V0 scope is Sigstore + cosign; portability (npm, non-Claude runtimes) is deferred to V1/V2.

Two implementation shapes converge here:

- **Atomic** — a single `.md` agent signed via `cosign sign-blob` with keyless OIDC, verified end-to-end against a local checkout. Proves the primitive works and the toolchain is installable without private-key management.
- **Collective manifest** — a JSON manifest listing SHA-256 + size for every file under a target directory, plus git provenance (commit, branch, dirty), with a single signature covering the whole lot. Proves the primitive scales to a directory without an N× cost in signatures.

The two coexist by construction, not by accident: they answer different granularity questions. The collective form is the "envelope" — one signature over N files.

The trust layer follows the same discipline as the Scorer proposal: deterministic, off the gating path, symmetric in shape to its siblings. It does not judge and does not block runtime; it *verifies*.

## 2. Problem

The AgentSpec plugin needs a mechanical way to answer, at any point after packaging, two questions:

| Question | What is being asked |
|---|---|
| **Integrity** | "Are the bytes on disk exactly what the publisher put in the plugin?" |
| **Authenticity** | "Did this come from a signer whose identity we can prove?" |

Four sub-decisions must be resolved together:

- **What to sign** — an individual file, a directory grouped as a manifest, or both. A single artifact does not cover the 58-file distribution; a manifest-only path breaks the "one file, one signature" case that the atomic PoC already validated.
- **How to sign** — key-based (long-lived secret to manage and rotate) or keyless (identity-bound, no secret at rest). The trade-off is operational cost versus binding strength.
- **Where the guarantee is evaluated** — at build (once, per release), at install (once, per consumer), at load (every session), or a subset.
- **What is out of scope for V0** — what the record explicitly defers, so future work does not inherit the impression of being under-specified.

## 3. Decision

AgentSpec adopts a **four-step chain of trust** on top of `cosign` with Sigstore keyless signing:

```
┌─────────┐   ┌─────────┐   ┌────────────┐   ┌─────────┐
│  HASH   │──▶│  SIGN   │──▶│ DISTRIBUTE │──▶│ VERIFY  │
└─────────┘   └─────────┘   └────────────┘   └─────────┘
     │             │              │                │
generate_       cosign         manifest +      verify_
manifest.py     sign-blob      bundle ship     signature.sh
                (keyless)      with plugin     (cosign +
                                                hash re-check)
```

The four steps map to a single command each and are implemented as four scripts under `scripts/`, all shipped in the companion PR:

1. **HASH — `scripts/generate_manifest.py`.** Walks a target directory, computes SHA-256 of every file with an allowed extension (`.md`, `.yaml`, `.yml`, `.json`, `.toml` by default), captures git provenance (commit hash, branch, dirty flag), and writes a deterministic JSON manifest (`plugin/security/manifest.json`) with `sort_keys=True`. The same input directory at the same commit produces the same manifest bytes (modulo `created_at`).
2. **SIGN — `scripts/sign_manifest.sh`.** Runs `cosign sign-blob` in keyless mode against the manifest, using an OIDC identity (Google or GitHub) at signing time and recording the transparency entry in the public **Rekor** log. Produces `plugin/security/manifest.sigstore.json` (the signature bundle).
3. **DISTRIBUTE.** The manifest and the bundle live under `plugin/security/` — inside the plugin payload itself — and are committed to the repository (no `.gitignore` exclusion). The consumer receives both together when installing the plugin; the bundle carries the transparency log entry that allows offline verification of the identity. No separate distribution step is needed.
4. **VERIFY — `scripts/verify_signature.sh`.** Two-stage: `cosign verify-blob` establishes authenticity (Rekor lookup, certificate identity check), then `scripts/verify_manifest.py` recomputes SHA-256 of every file on disk and diffs against the manifest.

The verifier detects **three failure modes**, each with a distinct label in the report:

- **MODIFIED** — a listed file is present, but its hash no longer matches.
- **REMOVED** — a listed file is missing from disk.
- **UNREGISTERED** — a file exists on disk (with an allowed extension) that was never in the manifest — the injected backdoor case.

Any single divergence returns `exit 1`; a clean run returns `exit 0`. The verifier makes no network call after the initial `cosign verify-blob`; the hash check is fully local.

**Two variants coexist by design:**

- **Atomic** — sign a single blob directly with `cosign sign-blob`. Retained for isolated agent handling, migration cases, and the original PoC path.
- **Collective (envelope)** — sign the manifest that lists N files. This is the primary distribution mode: one signature covers the payload; verification cost is linear in files but constant in signatures.

The two are not exclusive and neither supersedes the other.

**The signed tree is the built `plugin/` payload, not the `.claude/` source.** `build-plugin.sh` rewrites `.claude/` paths to `${CLAUDE_PLUGIN_ROOT}/` on the way into `plugin/`, so the two trees are byte-different for the same logical file (e.g., `dbt-specialist.md` hashes `f034b047…` at 7307 bytes under `.claude/` and `fa7f7cab…` at 7419 bytes under `plugin/`). The consumer installs `plugin/`, so that is what the manifest must cover. The default target of `generate_manifest.py` is `plugin/agents/…`; the atomic variant (`cosign sign-blob <file>`) accepts either tree if a caller needs to sign a specific source file.

**Keyless is non-negotiable for V0.** No private key is generated, stored, or rotated. The signature is bound to the OIDC identity that signed it, verifiable against the Rekor log. This trades key management for identity infrastructure — a trade V0 explicitly accepts because the target consumer already lives inside identity-bound tooling (GitHub, Google).

## 4. Consequences

**Positive**

- **Zero private-key surface.** No secret to leak, rotate, or commit by accident. The most expensive failure mode of PKI is removed at V0.
- **Public transparency for free.** Every signature is logged in Rekor with a timestamp and the signer's identity. Auditability is a side effect of signing, not a separate build.
- **Deterministic and offline-verifiable.** `verify_manifest.py` is pure Python + `hashlib`; runs in CI, in a container, on an air-gapped laptop.
- **Ship-time cost is a single command per release.** `generate_manifest.py` + `sign_manifest.sh` fits inside `build-plugin.sh` without a re-architecture.
- **The two variants cover both granularities without a second implementation.** The atomic case is `cosign sign-blob <file>`; the collective case signs the manifest that *lists* files. Same tool, same trust model, same command.
- **Family-consistent shape.** Deterministic (like the Linter), off the gating path (like the Scorer), symmetric verb-noun interface (`sign(...)` / `verify(...)`). Fits ADR-005's component model without inventing a new layer.

**Negative / risks**

- **V0 provides no adversarial authenticity guarantee — it is an accidental-corruption checksum, not a trust boundary.** Two wildcard filters compose in the verifier — `--certificate-identity-regexp=".*"` and `--certificate-oidc-issuer-regexp=".*"` — so any signer from any OIDC issuer verifies as equivalent to the intended one. Because the manifest is regenerated by the same tool that verifies it, an attacker with write access to the tree can modify a file, re-run `generate_manifest.py`, sign under any free OIDC identity, and `verify_signature.sh` returns 0 (reproduced against these scripts). V0 detects accidental corruption in transit; it does not distinguish a legitimate publisher from a hostile one. Closing this needs both filters pinned to concrete values simultaneously and the tree scope enforced externally — see §7 · Identity pinning (V1).
- **Requires cosign on the consumer.** The verify path is not zero-install; a runtime that cannot execute `cosign` cannot verify. Fallback is out of scope for V0.
- **Interactive OIDC on first sign.** `cosign sign-blob` opens a browser for the OIDC handshake the first time; unattended CI signing needs an ambient credential (GitHub Actions token or workload identity) — not the default developer flow, and out of V0's happy path.
- **Adds a step to the release ritual.** `build-plugin.sh` gains a `sign` phase and CI gains a `verify` phase; the version-bump gate proposed in PR #82 will need to know that `security/manifest.sigstore.json` is a legitimate artifact and not a stale build product.
- **Manifest schema is now load-bearing.** Any file type ADR-005 (component model, #66) introduces that is not in the allowed extensions list is invisible to the manifest, and therefore invisible to the verifier. The extension list is now a schema decision, not a convenience.

## 5. Alternatives considered

| Alternative | Rejected because |
|---|---|
| **GPG with a fixed private key** | Reintroduces the exact operational cost keyless was chosen to avoid: key generation, storage, distribution, rotation, revocation. Value of the guarantee does not offset the risk that the key leaks or is committed. |
| **Hashes only, no signature** | Answers integrity ("did it change?") but not authenticity ("who published this?"). A hash without a signer is a checksum, not a trust boundary — anyone can regenerate it after modifying the payload. |
| **Full PKI with a Crew-D CA** | Overkill for the current scale (one publisher, one plugin, one distribution channel). The infrastructure cost of running a certificate authority dwarfs the trust decision it would enforce. Sigstore already runs this infrastructure publicly. |
| **Signing only individual files (atomic-only)** | Signature count scales linearly with the payload; 58 signatures for the agents directory alone. Verification cost and orchestration overhead are unacceptable at the target scale. |
| **Signing only the manifest (collective-only)** | Loses the atomic case validated by the earlier PoC and forces every use case through a manifest — including the ones that only need to sign one blob. The two variants coexist for one flat marginal cost. |
| **In-repo trust (assume git is enough)** | Git guarantees stop at the source repository. Once the plugin is packaged and shipped, git offers nothing about the payload the consumer receives. This is exactly the gap this ADR closes. |
| **Skip trust for V0, add it later** | The value scales with adoption: every day the plugin ships unverified is another day of consumers running code we cannot vouch for. The design is inexpensive; delay is not. |

## 6. Confirmation

The decision holds if the following remain true:

- **Deterministic manifest.** Regenerating the manifest on the same commit produces byte-identical `security/manifest.json`, modulo the `created_at` timestamp and git dirty flag. Enforced by `sort_keys=True` and stable file ordering.
- **Tampering is detected.** Three tampering scenarios were exercised against the signed tree (15 files under `plugin/agents/data-engineering/`):
    - Modifying one file → `MODIFIED: 1`, exit 1.
    - Removing one file → `REMOVED: 1`, exit 1.
    - Injecting an unregistered file → `UNREGISTERED: 1`, exit 1.
    - Restored state → `OK: 15/15`, exit 0.
- **End-to-end signature.** A live Sigstore signature against the 15-file manifest of `plugin/agents/data-engineering/` returned `Verified OK` from `cosign verify-blob`, with the transparency entry recorded on Rekor.
- **Fitness for CI.** `verify_manifest.py` runs in under a second on the current corpus size on commodity hardware. `verify_signature.sh` adds only the cosign network call.

Any regression in the first three items breaks the guarantee this ADR is establishing and should be treated as a release blocker.

## 7. Open questions

- **Identity pinning (V1).** The `--certificate-identity-regexp=".*"` needs to be replaced with a real identity or a small allowlist. The right shape (single identity / OIDC-issuer + email allowlist / GitHub Actions workload identity) depends on how signing gets wired into `build-plugin.sh` and CI.
- **Signing scope beyond agents.** ADR-005 (component model, #66) formalized four artifact types: agents, skills, commands, KBs. V0 covers agents; extending to the other three needs a decision on where the boundary of "one plugin release" is drawn — one manifest per type, one per plugin, or one per component tree.
- **Harness integration point.** Two placements are on the table: `make sign` in the build (once per release) and a `SessionStart` hook that runs `verify_signature.sh` before Claude loads the agents. The first is uncontroversial; the second interacts with the plugin lifecycle in ways that need coordination with the release-pipeline and observability owners.
- **Interaction with the release pipeline.** PR #82 introduces version gating and a headless e2e; the trust layer must not turn a legitimate release into a lint failure because the manifest is regenerated after a version bump. Sequencing needs to be worked out with the release-pipeline owner.
- **Revocation.** Rekor makes signatures immutably logged, not revocable. A revoked signer is not un-published from the log; the check must move to "is the signer still on the allowlist at verification time?" Follow-up ADR territory.
- **Adjacent auto-generated files.** Any file emitted by another script (agent-router output, generated schemas) that lands in a signed tree needs a policy: either it is added to the manifest (and the tool that produced it is now part of the signing chain), or it is placed outside the signed tree by convention. The trust layer's own outputs (`plugin/security/manifest.json` and `plugin/security/manifest.sigstore.json`) are committed as release artifacts and live in a sibling directory to the signed tree, so they are outside the scan by convention.
