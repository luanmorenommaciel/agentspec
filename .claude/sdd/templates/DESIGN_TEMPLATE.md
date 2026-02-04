# DESIGN: {Feature Name}

> Technical design for implementing {Feature Name}

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Date** | {YYYY-MM-DD} |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_{FEATURE}.md](./DEFINE_{FEATURE}.md) |
| **Status** | Draft / Ready for Build |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────┐
│                   SYSTEM DIAGRAM                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  {ASCII diagram showing components and data flow}   │
│                                                      │
│  [Input] → [Component A] → [Component B] → [Output] │
│                ↓                 ↓                   │
│           [Storage]         [External API]          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| {Component A} | {What it does} | {Tech stack} |
| {Component B} | {What it does} | {Tech stack} |
| {Component C} | {What it does} | {Tech stack} |

---

## Key Decisions

### Decision 1: {Decision Name}

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | {YYYY-MM-DD} |

**Context:** {Why this decision was needed}

**Choice:** {What we decided to do}

**Rationale:** {Why this is the right choice}

**Alternatives Rejected:**
1. {Option A} - Rejected because {reason}
2. {Option B} - Rejected because {reason}

**Consequences:**
- {Trade-off we accept}
- {Benefit we gain}

---

### Decision 2: {Decision Name}

{Repeat structure above}

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `{path/to/file.py}` | Create | {Purpose} | @{agent-name} | None |
| 2 | `{path/to/config.yaml}` | Create | {Purpose} | @{agent-name} | None |
| 3 | `{path/to/handler.py}` | Create | {Purpose} | @{agent-name} | 1, 2 |
| 4 | `{path/to/test.py}` | Create | {Purpose} | @{agent-name} | 3 |

**Total Files:** {N}

---

## Agent Assignment Rationale

> Agents discovered from `.claude/agents/` - Build phase invokes matched specialists.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @{agent-1} | 1, 3 | {Specialization match: e.g., "Cloud Run patterns"} |
| @{agent-2} | 2 | {Specialization match: e.g., "Pydantic + LLM output"} |
| @{agent-3} | 4 | {Specialization match: e.g., "pytest fixtures"} |
| (general) | {if any} | {No specialist found - Build handles directly} |

**Agent Discovery:**
- Scanned: `.claude/agents/**/*.md`
- Matched by: File type, purpose keywords, path patterns, KB domains

---

## Code Patterns

### Pattern 1: {Pattern Name}

```python
# {Brief description of when to use this pattern}

{Copy-paste ready code snippet}
```

### Pattern 2: {Pattern Name}

```python
{Copy-paste ready code snippet}
```

### Pattern 3: Configuration Structure

```yaml
# config.yaml structure
{YAML configuration template}
```

---

## Data Flow

```text
1. {Step 1: e.g., "User submits request via API"}
   │
   ▼
2. {Step 2: e.g., "Request validated and queued"}
   │
   ▼
3. {Step 3: e.g., "Background worker processes request"}
   │
   ▼
4. {Step 4: e.g., "Results stored in database"}
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| {System A} | {REST API / SDK / Queue} | {Method} |
| {System B} | {REST API / SDK / Queue} | {Method} |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | Functions | `test_*.py` | pytest | 80% |
| Integration | API calls | `test_integration.py` | pytest + mocks | Key paths |
| E2E | Full flow | Manual | - | Happy path |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| {Error A} | {How to handle} | Yes/No |
| {Error B} | {How to handle} | Yes/No |
| {Error C} | {How to handle} | Yes/No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `{key_1}` | string | `{default}` | {What it controls} |
| `{key_2}` | int | `{default}` | {What it controls} |
| `{key_3}` | bool | `{default}` | {What it controls} |

---

## Security Considerations

- {Security consideration 1}
- {Security consideration 2}
- {Security consideration 3}

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | {Approach: e.g., "Structured JSON to Cloud Logging"} |
| Metrics | {Approach: e.g., "Custom metrics via Cloud Monitoring"} |
| Tracing | {Approach: e.g., "OpenTelemetry spans"} |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {YYYY-MM-DD} | design-agent | Initial version |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_{FEATURE_NAME}.md`
