# AUTOPILOT RUN: {Feature Name}

> Autonomous run record for {FEATURE} — the run's single source of state (resume replays the Gate Ledger) and its authoritative report. Created at run start; rows appended the moment each gate resolves.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Artifact Suffix** | {FEATURE_NAME} — immutable; DEFINE, DESIGN, BUILD_REPORT, and AUTOPILOT_RUN must all use this exact suffix |
| **Started** | {YYYY-MM-DD HH:MMZ} |
| **Entrypoint** | /auto (interactive) / autopilot.sh (headless) |
| **Intent** | {verbatim intent string} |
| **Flags** | {flags passed, or "none"} |
| **Branch** | {feat/auto-{feature-kebab}} |
| **Status** | 🔄 In Progress / ✅ Success (PR: {url}) / ⚠ Partial Success / ❌ Aborted ({gate}) |

---

## Gate Ledger

> One row per gate evaluation — every retry, every visible skip (exit code or reason named), every skipped-by-flag stage. Appended live, never batched. Tokens/Cost are optional (COULD-scope); leave `-` when not measured.

| Gate | Phase | Attempt | Sensor result | Outcome | Timestamp | Tokens | Cost |
|------|-------|---------|---------------|---------|-----------|--------|------|
| {0/L/J/B/S/PR} | {phase} | {n} | {e.g., spec-lint exit 0 · clarity 13/15 · spec-judge WARN (B1 ×1) · exit 3 budget} | {PASS / FAIL / REFINE (budget x/y) / SKIP:exit2 / SKIP:unavailable / SKIPPED (flag) / ABORT} | {ISO-8601} | - | - |

**Outcome legend:** PASS · FAIL (recoverable, retry follows) · REFINE (judge WARN fed one regeneration) · SKIP:{reason} (visible skip — sensor could not run; never an assumed PASS) · SKIPPED (flag) · ABORT (terminal)

---

## Phase Artifacts

| Phase | Artifact | Checkpoint Commit | Gate Summary |
|-------|----------|-------------------|--------------|
| Brainstorm | {path or "skipped (flag)"} | {short SHA} | {e.g., L:SKIP:exit2 · J:PASS} |
| Define | {path} | {short SHA} | {e.g., 0:13/15 · L:PASS · J:REFINE→PASS} |
| Design | {path} | {short SHA} | {…} |
| Build | {BUILD_REPORT path} | {short SHA} | {B: 100% complete} |
| Ship | {archive folder} | {short SHA} | {S: 4/4 checklist} |
| PR | {URL or "skipped (flag)" or "failed — see Partial Success"} | - | {…} |

---

## Autonomous Decisions

> Every self-answered discovery question, every `[ASSUMED]` marker, every decision fork resolved without a human. This table is why the run is reviewable despite never asking.

| # | Phase | Decision Point | Chose | Confidence | Rationale |
|---|-------|----------------|-------|------------|-----------|
| 1 | {phase} | {what was open} | {choice} | {0.00–1.00} | {why this is the safest documented default} |

---

## Retry & Budget Accounting

| Budget | Limit | Spent | Notes |
|--------|-------|-------|-------|
| Gate L regenerations | 1 per document | {n} | {which documents} |
| Gate J refinements | 1 per document | {n} | {which documents} |
| Build per-file retries | 3 per file | {n} | {which files} |
| `--max-iterations` cap | {N or "default"} | {n} | {hit? → terminal} |

---

## Gap Report (on Gate 0 abort — otherwise "N/A")

> One row per clarity element scoring < 3: what the intent must add for the run to proceed. This is the actionable output of an aborted run.

| Element | Score | What is missing |
|---------|-------|-----------------|
| {Problem / Users / Goals / Success / Scope} | {0–2} | {precisely what information would raise this to 3} |

**To relaunch:** restate the intent including the missing elements above, then re-run `/auto "<revised intent>"`.

---

## Notification Attempts

| Tier | Target | Result |
|------|--------|--------|
| Terminal summary | stdout | {shown} |
| OS notification | {osascript / notify-send / n/a} | {sent / tool absent / failed — run outcome unchanged} |
| Webhook | {set? (URL never printed)} | {2xx / failed — run outcome unchanged / not configured} |

---

## Terminal Summary

| Metric | Value |
|--------|-------|
| **Terminal Status** | {✅ / ⚠ / ❌ as in Metadata} |
| **Phases Completed** | {n}/6 |
| **Gates Evaluated** | {n} ({p} PASS · {f} FAIL · {s} skips) |
| **Total Regenerations** | {n} |
| **Human Interactions** | 0 (invariant) |
| **PR** | {URL or "-"} |
| **Manual Follow-up** | {none / exact command, on Partial Success} |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {YYYY-MM-DD} | autopilot | Run opened |
