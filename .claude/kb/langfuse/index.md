# Langfuse Knowledge Base

> **Purpose**: LLMOps observability platform for tracking LLM calls, costs, latency, and quality
> **MCP Validated**: 2026-01-25

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/traces-spans.md](concepts/traces-spans.md) | Trace hierarchy and observation types |
| [concepts/generations.md](concepts/generations.md) | LLM call tracking with model/tokens |
| [concepts/cost-tracking.md](concepts/cost-tracking.md) | Token usage and cost calculation |
| [concepts/scoring.md](concepts/scoring.md) | Quality feedback and evaluation metrics |
| [concepts/prompt-management.md](concepts/prompt-management.md) | Version control and deployment |
| [concepts/model-comparison.md](concepts/model-comparison.md) | A/B testing and model analytics |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/python-sdk-integration.md](patterns/python-sdk-integration.md) | Basic SDK setup and instrumentation |
| [patterns/cloud-run-instrumentation.md](patterns/cloud-run-instrumentation.md) | GCP Cloud Run function tracing |
| [patterns/quality-feedback-loops.md](patterns/quality-feedback-loops.md) | User feedback and LLM-as-Judge |
| [patterns/cost-alerting.md](patterns/cost-alerting.md) | Cost monitoring thresholds |
| [patterns/trace-linking.md](patterns/trace-linking.md) | Distributed tracing across services |
| [patterns/dashboard-metrics.md](patterns/dashboard-metrics.md) | Key metrics and monitoring setup |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | Single request/operation container for observations |
| **Generation** | Specialized span for LLM calls with token/cost data |
| **Score** | Numeric/categorical/boolean quality metric |
| **Session** | Groups multiple traces (e.g., chat thread) |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/traces-spans.md, concepts/generations.md |
| **Intermediate** | patterns/python-sdk-integration.md, concepts/scoring.md |
| **Advanced** | patterns/trace-linking.md, patterns/quality-feedback-loops.md |

---

## Project Integration

| Use Case | Pattern | Target |
|----------|---------|--------|
| Invoice extraction | python-sdk-integration | Cloud Run function |
| Cost monitoring | cost-alerting | $0.003/invoice threshold |
| Quality tracking | quality-feedback-loops | 90% accuracy target |
| Latency monitoring | dashboard-metrics | P95 < 3s target |
