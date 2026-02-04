# Iterate Command

> Update any phase document when requirements or design changes (Cross-Phase)

## Usage

```bash
/iterate <file> "<change-description>"
```

## Examples

```bash
/iterate BRAINSTORM_CLOUD_RUN.md "Consider batch processing instead of real-time"
/iterate DEFINE_CLOUD_RUN.md "Add support for PDF invoices, not just TIFF"
/iterate DESIGN_CLOUD_RUN.md "Functions need to be self-contained, no shared common/"
/iterate .claude/sdd/features/DEFINE_AUTH.md "Change from JWT to session-based auth"
```

---

## Overview

The `/iterate` command works with **document phases** of the AgentSpec workflow:

```text
Phase 0: /brainstorm → BRAINSTORM_{FEATURE}.md ← /iterate can update
Phase 1: /define     → DEFINE_{FEATURE}.md     ← /iterate can update
Phase 2: /design     → DESIGN_{FEATURE}.md     ← /iterate can update
Phase 3: /build      → (code)                  ← Update DESIGN, then /build
Phase 4: /ship       → (archive)               ← N/A
```

Use `/iterate` when you discover something that needs to change mid-stream.

**Important:** To change code during Phase 3, update the DESIGN document first. The cascade to code triggers a rebuild via `/build`. This ensures traceability.

---

## What This Command Does

1. **Detect Phase** - Identify which phase document is being updated
2. **Analyze Impact** - Determine downstream effects
3. **Update Document** - Apply changes with version tracking
4. **Cascade** - Propagate changes to downstream documents if needed

---

## Process

### Step 1: Load Target Document

```markdown
Read(<target-file>)

# Identify document type:
# - BRAINSTORM_*.md → Phase 0
# - DEFINE_*.md → Phase 1
# - DESIGN_*.md → Phase 2
```

### Step 2: Analyze Change

Determine the change type:

| Change Type | Example | Impact |
|-------------|---------|--------|
| **Additive** | "Also support PDF" | Low - adds to existing |
| **Modifying** | "Change from X to Y" | Medium - updates existing |
| **Removing** | "Remove feature Z" | Medium - simplifies |
| **Architectural** | "Use different pattern" | High - may require redesign |

### Step 3: Apply Changes

Update the document with:

1. **Change Applied** - The actual modification
2. **Version Bump** - Increment version in revision history
3. **Change Note** - What changed and why

### Step 4: Assess Cascade Need

| Source | Cascades To |
|--------|-------------|
| DEFINE change | May need DESIGN update |
| DESIGN change | May need code update |

Determine if downstream documents need updates based on cascade rules.

### Step 5: Execute Cascade (if needed)

If cascade needed, prompt user:

```markdown
"This DEFINE change affects the DESIGN. Options:
(a) Update DESIGN automatically to match
(b) Just update DEFINE, I'll handle DESIGN manually
(c) Show me what would change first"
```

### Step 6: Save Updates

```markdown
Write(<target-file>)
# If cascade:
Write(<downstream-document>)
```

---

## Output

| Artifact | Location |
|----------|----------|
| **Updated Document** | Same location as input |
| **Cascade Updates** | Downstream documents (if applicable) |

---

## Cascade Rules

### DEFINE Changes → DESIGN Impact

| DEFINE Change | DESIGN Impact |
|---------------|---------------|
| New requirement | May need new component |
| Changed success criteria | May need different approach |
| Scope expansion | Needs new sections |
| Scope reduction | Can simplify |
| New constraint | Must be accommodated |

### DESIGN Changes → Code Impact

| DESIGN Change | Code Impact |
|---------------|-------------|
| New file in manifest | Create file |
| Removed file | Delete file |
| Changed pattern | Update affected files |
| New decision | May need refactor |
| Architecture change | Significant updates needed |

---

## Version Tracking

Each document maintains revision history:

```markdown
## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-25 | define-agent | Initial version |
| 1.1 | 2026-01-25 | iterate-agent | Added PDF support per user request |
```

---

## Tips

1. **Iterate Early** - Catch changes before coding starts
2. **Be Specific** - "Add X" is better than "make it better"
3. **Check Cascade** - Changes ripple downstream
4. **Keep History** - Version tracking shows evolution
5. **Don't Fight It** - Requirements change, that's normal

---

## When to Use /iterate vs Starting Over

| Situation | Action |
|-----------|--------|
| < 30% change | `/iterate` |
| Add/modify features | `/iterate` |
| Change constraints | `/iterate` |
| > 50% different | New `/define` |
| Different problem entirely | New `/define` |
| Different target users | New `/define` |

---

## References

- Agent: `.claude/agents/workflow/iterate-agent.md`
- Contracts: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
