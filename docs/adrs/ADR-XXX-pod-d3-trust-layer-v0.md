# ADR-XXX — Pod D3 Trust Layer V0 (cosign + manifest)

> **Status:** Proposed
> **Author:** Giulia Parede (Pod D3)
> **Date:** 2026-07-22
> **Related:** Issue #23 (D3 marketplace/trust-layer spike). Builds on ADR-001 (#31) — the artifact is the source of truth we sign — and on ADR-002 (#54) + ADR-003 (#57), which handle "well-formed?" and "does it honor its contract?"; this ADR closes the outer question of "did this artifact reach the user unchanged, and from whom?". Family peer to the Scorer proposal (2026-07-19, Emerson). Companion PR: `feat/pod-d3-trust-layer-scripts` on `wallgiu/agentspec`.

---

## 1. Context

AgentSpec ships as a Claude Code plugin whose payload is entirely declarative: 58 agents, 31 commands, and 24 knowledge-base domains, distributed as `.md`, `.yaml`, `.json`, and `.toml` files. Once installed, each file is read by the runtime and executed as instruction — **the prompt is the code**. A single-byte edit to an agent markdown is a silent prompt injection, indistinguishable from the original at load time.

Git proves history, not integrity at rest. Once the plugin is packaged and pushed to the marketplace, the guarantees git offered on the source repository are gone: consumers install the payload without any mechanical way to verify that (a) the bytes on disk match what the author published, or (b) the publisher is who they claim to be.

The Pod D3 was created in the Crew D internal sync of 2026-05-28 as the "marketplace / trust-layer spike" (issue #23) precisely to close this gap. Its scope was confirmed in Sync 04 with the Commander (2026-06-03) as a V0 based on Sigstore + cosign, deferring portability (npm, non-Claude runtimes) to V1/V2.

Two implementations have converged during the wave:

- **Atomic PoC (2026-06-03, Giulia)** — a single `.md` agent signed via `cosign sign-blob` with keyless OIDC, verified end-to-end against a local checkout. Proved the primitive works and the toolchain is installable without private-key management.
- **Collective manifest (2026-06-17, Carlos)** — a JSON manifest listing SHA-256 + size for every file under `.claude/agents/data-engineering/`, plus git provenance (commit, branch, dirty), with a single signature covering the whole lot. Proved the primitive scales to a directory without an N× cost in signatures.

The two coexist by construction, not by accident: they answer different granularity questions. The manifest form was recognized on 2026-06-26 by the Captain, in the formal report to the Commander, as aligning with the "envelope" concept the Commander had raised in Sync 04.

The design was presented in the Crew D sync of 2026-07-15 in a ten-slide deck ("AgentSpec Assinado — Cosign para Integridade de Supply Chain") and approved in principle by the Captain. It has stood without an issue, branch, or PR since then. This ADR is what closes that gap.

The Scorer proposal (2026-07-19, Emerson) sets a precedent worth naming: a component in the enforcement family that is deterministic, off the gating path, symmetric in shape to its siblings. The trust layer proposed here follows the same discipline — it does not judge and does not block runtime, it *verifies*.

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

1. **HASH — `scripts/generate_manifest.py`.** Walks a target directory, computes SHA-256 of every file with an allowed extension (`.md`, `.yaml`, `.yml`, `.json`, `.toml` by default), captures git provenance (commit hash, branch, dirty flag), and writes a deterministic JSON manifest (`security/manifest.json`) with `sort_keys=True`. The same input directory at the same commit produces the same manifest bytes.
2. **SIGN — `scripts/sign_manifest.sh`.** Runs `cosign sign-blob` in keyless mode against the manifest, using an OIDC identity (Google or GitHub) at signing time and recording the transparency entry in the public **Rekor** log. Produces `security/manifest.sigstore.json` (the signature bundle).
3. **DISTRIBUTE.** The manifest and the bundle travel with the plugin payload under `security/`. The consumer receives both together; the bundle carries the transparency log entry that allows offline verification of the identity.
4. **VERIFY — `scripts/verify_signature.sh`.** Two-stage: `cosign verify-blob` establishes authenticity (Rekor lookup, certificate identity check), then `scripts/verify_manifest.py` recomputes SHA-256 of every file on disk and diffs against the manifest.

The verifier detects **three failure modes**, each with a distinct label in the report:

- **MODIFIED** — a listed file is present, but its hash no longer matches.
- **REMOVED** — a listed file is missing from disk.
- **UNREGISTERED** — a file exists on disk (with an allowed extension) that was never in the manifest — the injected backdoor case.

Any single divergence returns `exit 1`; a clean run returns `exit 0`. The verifier makes no network call after the initial `cosign verify-blob`; the hash check is fully local.

**Two variants coexist by design:**

- **Atomic** — sign a single blob directly with `cosign sign-blob`. Retained for isolated agent handling, migration cases, and the original PoC path.
- **Collective (envelope)** — sign the manifest that lists N files. This is the primary distribution mode: one signature covers the payload; verification cost is linear in files but constant in signatures.

The two are not exclusive and neither supersedes the other. The manifest is the envelope form the Commander asked for in Sync 04 (2026-05-27) and that the Captain publicly recognized in the report of 2026-06-26.

**Keyless is non-negotiable for V0.** No private key is generated, stored, or rotated. The signature is bound to the OIDC identity that signed it, verifiable against the Rekor log. This trades key management for identity infrastructure — a trade V0 explicitly accepts because the Crew D consumer already lives inside identity-bound tooling (GitHub, Google).

## 4. Consequences

**Positive**

- **Zero private-key surface.** No secret to leak, rotate, or commit by accident. The most expensive failure mode of PKI is removed at V0.
- **Public transparency for free.** Every signature is logged in Rekor with a timestamp and the signer's identity. Auditability is a side effect of signing, not a separate build.
- **Deterministic and offline-verifiable.** `verify_manifest.py` is pure Python + `hashlib`; runs in CI, in a container, on an air-gapped laptop.
- **Ship-time cost is a single command per release.** `generate_manifest.py` + `sign_manifest.sh` fits inside `build-plugin.sh` without a re-architecture.
- **The two variants cover both granularities without a second implementation.** The atomic case is `cosign sign-blob <file>`; the collective case signs the manifest that *lists* files. Same tool, same trust model, same command.
- **Family-consistent shape.** Deterministic (like the Linter), off the gating path (like the Scorer), symmetric verb-noun interface (`sign(...)` / `verify(...)`). Fits ADR-005's component model without inventing a new layer.

**Negative / risks**

- **V0 accepts any signer.** The verifier passes `--certificate-identity-regexp=".*"`, which accepts any OIDC identity that can produce a Sigstore certificate. This is deliberate to unblock adoption and is explicitly out of V0 scope, but the door stays open until V1 pins the identity to an allowlist of signers.
- **Requires cosign on the consumer.** The verify path is not zero-install; a runtime that cannot execute `cosign` cannot verify. Fallback is out of scope for V0.
- **Interactive OIDC on first sign.** `cosign sign-blob` opens a browser for the OIDC handshake the first time; unattended CI signing needs an ambient credential (GitHub Actions token or workload identity) — not the default developer flow, and out of V0's happy path.
- **Adds a step to the release ritual.** `build-plugin.sh` gains a `sign` phase and CI gains a `verify` phase; the version-bump gate proposed in PR #82 will need to know that `security/manifest.sigstore.json` is a legitimate artifact and not a stale build product.
- **Manifest schema is now load-bearing.** Any file type ADR-006 (component model, #66) introduces that is not in the allowed extensions list is invisible to the manifest, and therefore invisible to the verifier. The extension list is now a schema decision, not a convenience.

## 5. Alternatives considered

| Alternative | Rejected because |
|---|---|
| **GPG with a fixed private key** | Reintroduces the exact operational cost keyless was chosen to avoid: key generation, storage, distribution, rotation, revocation. Value of the guarantee does not offset the risk that the key leaks or is committed. |
| **Hashes only, no signature** | Answers integrity ("did it change?") but not authenticity ("who published this?"). A hash without a signer is a checksum, not a trust boundary — anyone can regenerate it after modifying the payload. |
| **Full PKI with a Crew-D CA** | Overkill for the current scale (one publisher, one plugin, one distribution channel). The infrastructure cost of running a certificate authority dwarfs the trust decision it would enforce. Sigstore already runs this infrastructure publicly. |
| **Signing only individual files (atomic-only)** | Signature count scales linearly with the payload; 58 signatures for the agents directory alone. Verification cost and orchestration overhead are unacceptable at the target scale. |
| **Signing only the manifest (collective-only)** | Loses the atomic case validated by the PoC of 2026-06-03 and forces every use case through a manifest — including the ones that only need to sign one blob. The two variants coexist for one flat marginal cost. |
| **In-repo trust (assume git is enough)** | Git guarantees stop at the source repository. Once the plugin is packaged and shipped, git offers nothing about the payload the consumer receives. This is exactly the gap this ADR closes. |
| **Skip trust for V0, add it later** | The value scales with adoption: every day the plugin ships unverified is another day of consumers running code we cannot vouch for. The design is inexpensive; delay is not. |

## 6. Confirmation

The decision holds if the following remain true:

- **Deterministic manifest.** Regenerating the manifest on the same commit produces byte-identical `security/manifest.json`, modulo the `created_at` timestamp and git dirty flag. Enforced by `sort_keys=True` and stable file ordering.
- **Byte-level match with the collective PoC (2026-06-17).** The SHA-256 for `dbt-specialist.md` produced by `generate_manifest.py` on 2026-07-22 (`f034b047ab2072ec3e22e41a3c2ef81640d38d9d8bf6cf883a6af4945452241e`, size 7307) matches the entry Carlos committed to the PoC manifest of 2026-06-17. Same tool would have produced the same output.
- **Tampering is detected.** On 2026-07-22, three tampering scenarios were exercised against `.claude/agents/data-engineering/` (15 files):
    - Modifying one file → `MODIFIED: 1`, exit 1.
    - Removing one file → `REMOVED: 1`, exit 1.
    - Injecting an unregistered file → `UNREGISTERED: 1`, exit 1.
    - Restored state → `OK: 15/15`, exit 0.
- **End-to-end signature.** A live Sigstore signature by the ADR author against the 15-file manifest returned `Verified OK` from `cosign verify-blob`, with the transparency entry recorded on Rekor.
- **Fitness for CI.** `verify_manifest.py` runs in under a second on the current corpus size on commodity hardware. `verify_signature.sh` adds only the cosign network call.

Any regression in the first three items breaks the guarantee this ADR is establishing and should be treated as a release blocker.

## 7. Open questions

- **Identity pinning (V1).** The `--certificate-identity-regexp=".*"` needs to be replaced with a real identity or a small allowlist. The right shape (single identity / OIDC-issuer + email allowlist / GitHub Actions workload identity) depends on how signing gets wired into `build-plugin.sh` and CI.
- **Signing scope beyond agents.** ADR-005 (component model, #66) formalized four artifact types: agents, skills, commands, KBs. V0 covers agents; extending to the other three needs a decision on where the boundary of "one plugin release" is drawn — one manifest per type, one per plugin, or one per component tree.
- **Harness integration point.** Two placements are on the table: `make sign` in the build (once per release) and a `SessionStart` hook that runs `verify_signature.sh` before Claude loads the agents. The first is uncontroversial; the second interacts with the plugin lifecycle in ways that need Lucas (D2, Captain) and Emerson (Observer / Scorer) at the table.
- **Interaction with the release pipeline.** PR #82 introduces version gating and a headless e2e; the trust layer must not turn a legitimate release into a lint failure because the manifest is regenerated after a version bump. Sequencing needs to be worked out with the D2 owner of that PR.
- **Revocation.** Rekor makes signatures immutably logged, not revocable. A revoked signer is not un-published from the log; the check must move to "is the signer still on the allowlist at verification time?" Follow-up ADR territory.
- **Adjacent auto-generated files.** Any file emitted by another script (agent-router output, generated schemas) that lands in a signed tree needs a policy: either it is added to the manifest (and the tool that produced it is now part of the signing chain), or it is placed outside the signed tree by convention. The generated `security/manifest.json` and `security/manifest.sigstore.json` are already excluded via `security/.gitignore` in the companion PR — the same problem for other generators is unresolved.

---

### Notes for reviewers

- **Companion PR:** [`wallgiu/agentspec`, branch `feat/pod-d3-trust-layer-scripts`](https://github.com/wallgiu/agentspec/tree/feat/pod-d3-trust-layer-scripts) — five new files under `scripts/` and a `security/.gitignore`, tested against `.claude/agents/data-engineering/`.
- **Design credit:** Carlos Medeiros (Pod D3). Deck presented 2026-07-15; the scripts in the companion PR are a faithful materialization of that design, with a byte-level match to Carlos's collective manifest of 2026-06-17 for the shared file.
- **Implementation credit:** Giulia Parede (Pod D3). Atomic PoC of 2026-06-03, replication guide of 2026-06-03, and the companion PR of 2026-07-22.
- **Endorsements to date:** Luan Moreno (approved in principle at Sync 04, 2026-06-03; re-approved in principle at Sync of 2026-07-15). Lucas Brandão / Captain (formal report to the Commander of 2026-06-26 recognizing the manifest as the "envelope" of Sync 04).
