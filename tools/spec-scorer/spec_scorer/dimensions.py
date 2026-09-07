"""Dimension measurements — pure functions over a parsed `AgentSpec`.

Every function here is deterministic and self-contained: it counts what the spec
declares and returns a `DimensionScore`. No I/O, no model calls. The two
repo-dependent dimensions (reference integrity, actual reuse) take their evidence
as an argument, so this module never reaches out to the filesystem itself.

Each score carries both a terse `detail` (the compact view) and a list of
`CheckItem`s (the per-topic breakdown `--explain` prints). The checks are the
same measurement rendered at finer grain — the dimension's numerator is the sum
of its checks' contributions (with `risk_surface` additionally capped) — so the
number is always traceable to the topics that produced it.

The maturity evidence table mirrors the Linter's L2 maturity rules
(`spec_linter.rules.l2_governance_findings`): whatever the Linter FAILs a level
for, the Scorer counts as that level's required evidence. Where the Linter asks
"is the required evidence present at all?", the Scorer asks "how much of the
declared level's evidence is actually there?".
"""

from __future__ import annotations

from spec_linter import AgentSpec

from .scorecard import CheckItem, DimensionScore

# The optional enrichment fields — present beyond bare schema validity. Governance
# staples (stop_conditions, escalation_rules) are excluded: they are not optional
# richness, they belong to mitigation coverage and the maturity table below.
_ENRICHMENT_FIELDS = ("kb_domains", "observability", "memory_backend", "recall_strategy",
                      "requirements", "deliverables")

# Evidence each declared maturity level is expected to carry, cumulatively. The
# denominator of `maturity_conformance` is the count for the *declared* level.
_MATURITY_EVIDENCE: dict[str, tuple[str, ...]] = {
    "V1": ("stop_conditions", "escalation_rules"),
    "V2": ("stop_conditions", "escalation_rules", "observability"),
    "V3": ("stop_conditions", "escalation_rules", "observability",
           "memory_backend", "recall_strategy"),
}


def _is_populated(spec: AgentSpec, field: str) -> bool:
    """True when an optional field carries real content (non-empty / non-None)."""
    value = getattr(spec, field, None)
    if value is None:
        return False
    if isinstance(value, (list, tuple, str)):
        return len(value) > 0
    return True


def _bool_check(label: str, ok: bool, note: str = "") -> CheckItem:
    return CheckItem(label=label, contribution=1 if ok else 0, kind="bool", note=note)


def completeness(spec: AgentSpec) -> DimensionScore:
    """Spec Quality — populated enrichment fields / total enrichment fields.

    The dimension a pure fold-over-findings is blind to: absent optional fields
    break no rule, so the Linter emits zero findings whether 3 or 8 are filled.
    """
    checks = [_bool_check(f, _is_populated(spec, f)) for f in _ENRICHMENT_FIELDS]
    populated = [c for c in checks if c.contribution]
    missing = [c.label for c in checks if not c.contribution]
    detail = f"missing: {', '.join(missing)}" if missing else "all enrichment fields present"
    return DimensionScore(
        dimension="completeness",
        family="Spec Quality",
        numerator=len(populated),
        denominator=len(_ENRICHMENT_FIELDS),
        detail=detail,
        checks=checks,
    )


def reference_integrity(spec: AgentSpec, known_kb_domains: set[str]) -> DimensionScore:
    """Spec Quality — declared kb_domains that resolve against the KB index.

    Repo-dependent: the caller supplies the known-domain set (from
    `.claude/kb/_index.yaml`). Implements the tracked KB-reference-integrity
    check as a measured ratio.
    """
    declared = list(spec.kb_domains)
    checks = [
        _bool_check(d, d in known_kb_domains, note="" if d in known_kb_domains else "dangling")
        for d in declared
    ]
    resolved = [c for c in checks if c.contribution]
    dangling = [c.label for c in checks if not c.contribution]
    detail = f"dangling: {', '.join(dangling)}" if dangling else "all references resolve"
    return DimensionScore(
        dimension="reference_integrity",
        family="Spec Quality",
        numerator=len(resolved),
        denominator=len(declared),
        detail=detail,
        checks=checks,
    )


def convention_conformance(spec: AgentSpec) -> DimensionScore:
    """Platform Fit — adherence to spec-level authoring conventions.

    A self-contained subset: conventions checkable from the frontmatter alone.
    File placement, size limits, and thin-executor body length need the file on
    disk and are out of V0's static-spec scope.
    """
    results = {
        "description_present": bool(spec.description.strip()),
        "description_is_one_liner": len(spec.description) <= 400,
        "tools_declared": len(spec.tools) > 0,
        "kb_domains_declared": len(spec.kb_domains) > 0,
    }
    checks = [_bool_check(name, ok) for name, ok in results.items()]
    passed = [c for c in checks if c.contribution]
    failed = [c.label for c in checks if not c.contribution]
    detail = f"failed: {', '.join(failed)}" if failed else "all conventions met"
    return DimensionScore(
        dimension="convention_conformance",
        family="Platform Fit",
        numerator=len(passed),
        denominator=len(checks),
        detail=detail,
        checks=checks,
    )


def actual_reuse(spec: AgentSpec, inbound_references: int) -> DimensionScore:
    """Platform Fit — measured inbound references from other components.

    Not "genericism" (which fights a platform of deliberately specialized
    agents), but *actual* reuse: how many other components point at this one.
    Reported as a raw count against a nominal reuse target so it reads on the
    same 0..1 scale; the raw inbound count stays visible.
    """
    target = 3  # nominal: referenced by at least a few peers reads as "reused"
    credit = min(inbound_references, target)
    checks = [
        CheckItem(
            label="inbound_references",
            contribution=credit,
            kind="points",
            note=f"{inbound_references} total, target {target}",
        )
    ]
    return DimensionScore(
        dimension="actual_reuse",
        family="Platform Fit",
        numerator=credit,
        denominator=target,
        detail=f"{inbound_references} inbound reference(s)",
        checks=checks,
    )


def risk_surface(spec: AgentSpec) -> DimensionScore:
    """Risk & Governance — how much the artifact can touch. Higher = more risk.

    A descriptor, not a defect: paired with mitigation_coverage, a high surface
    with low coverage is the real signal. Points accrue from write access, git
    operations, external APIs, tool breadth, and tier autonomy, normalized
    against a nominal cap.
    """
    se = spec.output_contract.side_effects
    git_ops = [op for op in se.git_operations if op != "none"]
    tier_weight = {"T1": 0, "T2": 1, "T3": 2}.get(spec.tier, 0)
    checks = [
        CheckItem(label="files_written", contribution=1 if se.files_written else 0,
                  kind="points", note=str(se.files_written).lower()),
        CheckItem(label="git_operations", contribution=len(git_ops),
                  kind="points", note=f"{len(git_ops)} non-none"),
        CheckItem(label="external_apis", contribution=len(se.external_apis),
                  kind="points", note=f"{len(se.external_apis)}"),
        CheckItem(label="tools", contribution=len(spec.tools),
                  kind="points", note=f"{len(spec.tools)}"),
        CheckItem(label="tier", contribution=tier_weight, kind="points", note=spec.tier),
    ]
    points = sum(c.contribution for c in checks)
    cap = 12
    detail = (
        f"writes={se.files_written}, git={len(git_ops)}, apis={len(se.external_apis)}, "
        f"tools={len(spec.tools)}, tier={spec.tier}"
    )
    return DimensionScore(
        dimension="risk_surface",
        family="Risk & Governance",
        numerator=min(points, cap),
        denominator=cap,
        higher_is_better=False,
        detail=detail,
        checks=checks,
    )


def mitigation_coverage(spec: AgentSpec) -> DimensionScore:
    """Risk & Governance — declared guardrails present / applicable.

    security_review is only applicable when the agent publishes; it is dropped
    from the denominator otherwise, so a non-publishing agent is not penalized
    for a mitigation that does not apply to it.
    """
    applicable = {
        "stop_conditions": len(spec.stop_conditions) > 0,
        "escalation_rules": len(spec.escalation_rules) > 0,
        "observability": spec.observability is not None,
    }
    if spec.publish:
        applicable["security_review"] = spec.security_review
    checks = [_bool_check(name, ok) for name, ok in applicable.items()]
    present = [c for c in checks if c.contribution]
    absent = [c.label for c in checks if not c.contribution]
    detail = f"absent: {', '.join(absent)}" if absent else "all applicable mitigations present"
    return DimensionScore(
        dimension="mitigation_coverage",
        family="Risk & Governance",
        numerator=len(present),
        denominator=len(applicable),
        detail=detail,
        checks=checks,
    )


def maturity_conformance(spec: AgentSpec) -> DimensionScore:
    """Risk & Governance — evidence present for the *declared* maturity level.

    The question neither sibling can answer: does the artifact's content support
    the level it claims? A spec declaring V3 with only V1 evidence scores low
    here while still passing structural validity.
    """
    required = _MATURITY_EVIDENCE.get(spec.maturity, ())
    checks = [_bool_check(f, _is_populated(spec, f)) for f in required]
    satisfied = [c for c in checks if c.contribution]
    missing = [c.label for c in checks if not c.contribution]
    detail = (
        f"declared {spec.maturity}; missing: {', '.join(missing)}"
        if missing
        else f"declared {spec.maturity}; evidence complete"
    )
    return DimensionScore(
        dimension="maturity_conformance",
        family="Risk & Governance",
        numerator=len(satisfied),
        denominator=len(required),
        detail=detail,
        checks=checks,
    )
