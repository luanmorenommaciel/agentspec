# BRAINSTORM: {Feature Name}

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Date** | {YYYY-MM-DD} |
| **Author** | brainstorm-agent |
| **Status** | Exploring / Approaches Identified / Ready for Define |

---

## Initial Idea

**Raw Input:** {Original idea or request as stated by user}

**Context Gathered:**
- {Project state observation 1}
- {Project state observation 2}
- {Relevant existing code or patterns found}

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | {src/ \| functions/ \| gen/ \| deploy/} | {Where code should live} |
| Relevant KB Domains | {pydantic, gcp, gemini, etc.} | {Patterns to consult} |
| IaC Patterns | {Existing Terraform/Terragrunt or N/A} | {Infrastructure approach} |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | {Question about purpose} | {User's answer} | {How this shapes the solution} |
| 2 | {Question about users} | {User's answer} | {How this shapes the solution} |
| 3 | {Question about constraints} | {User's answer} | {How this shapes the solution} |
| 4 | {Question about success criteria} | {User's answer} | {How this shapes the solution} |

**Minimum Questions:** 3 (to ensure clarity before proceeding)

---

## Sample Data Inventory

> Samples improve LLM accuracy through in-context learning and few-shot prompting.

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | {Path or N/A} | {N} | {Format, size, patterns} |
| Output examples | {Path or N/A} | {N} | {Schema, structure} |
| Ground truth | {Path or N/A} | {N} | {Verified correct values} |
| Related code | {Path or N/A} | {N} | {Patterns to reuse} |

**How samples will be used:**

- {e.g., Few-shot examples in extraction prompts}
- {e.g., Schema validation reference}
- {e.g., Test fixtures for validation}

---

## Approaches Explored

### Approach A: {Name} ⭐ Recommended

**Description:** {Brief description of approach}

**Pros:**
- {Advantage 1}
- {Advantage 2}

**Cons:**
- {Trade-off 1}
- {Trade-off 2}

**Why Recommended:** {Clear reasoning for why this is the suggested path}

---

### Approach B: {Name}

**Description:** {Brief description of approach}

**Pros:**
- {Advantage 1}
- {Advantage 2}

**Cons:**
- {Trade-off 1}
- {Trade-off 2}

---

### Approach C: {Name} (Optional)

**Description:** {Brief description of approach}

**Pros:**
- {Advantage 1}

**Cons:**
- {Trade-off 1}

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach {A/B/C} |
| **User Confirmation** | {Date/Time of confirmation} |
| **Reasoning** | {Why user selected this approach} |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | {Decision made during brainstorm} | {Why} | {What we didn't do} |
| 2 | {Decision made during brainstorm} | {Why} | {What we didn't do} |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| {Feature that seemed good but unnecessary} | {YAGNI reasoning} | Yes/No |
| {Another deferred feature} | {Why not needed now} | Yes/No |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Architecture concept | ✅ | {Feedback} | Yes/No |
| Component breakdown | ✅ | {Feedback} | Yes/No |
| Data flow | ✅ | {Feedback} | Yes/No |
| Error handling | ✅ | {Feedback} | Yes/No |

**Minimum Validations:** 2 (to ensure alignment)

---

## Suggested Requirements for /define

Based on this brainstorm session, the following should be captured in the DEFINE phase:

### Problem Statement (Draft)
{One clear sentence describing the problem to solve}

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| {User 1} | {Pain} |

### Success Criteria (Draft)
- [ ] {Measurable criterion 1}
- [ ] {Measurable criterion 2}

### Constraints Identified
- {Constraint 1}
- {Constraint 2}

### Out of Scope (Confirmed)
- {Item 1 - explicitly excluded during brainstorm}
- {Item 2}

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | {N} |
| Approaches Explored | {2-3} |
| Features Removed (YAGNI) | {N} |
| Validations Completed | {N} |
| Duration | {Approx time} |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_{FEATURE_NAME}.md`
