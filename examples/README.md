# AgentSpec Examples

Real-world examples of using AgentSpec.

## Invoice Pipeline (Complete Example)

The original project that inspired AgentSpec - an AI-powered invoice extraction pipeline.

See the SDD flow in `../sdd/examples/`:

1. `BRAINSTORM_GCP_PIPELINE_DEPLOYMENT.md` - Initial exploration
2. `DEFINE_GCP_PIPELINE_DEPLOYMENT.md` - Requirements capture
3. `DESIGN_GCP_PIPELINE_DEPLOYMENT.md` - Architecture design
4. `BUILD_REPORT_GCP_PIPELINE_DEPLOYMENT.md` - Implementation report

## Quick Start Example

### 1. Initialize SDD in Your Project

```bash
mkdir -p .claude/sdd/{features,reports,archive}
```

### 2. Start a New Feature

```bash
claude> /brainstorm "Add user authentication"
```

### 3. Follow the Flow

```bash
claude> /define AUTH_FEATURE
# Creates: .claude/sdd/features/DEFINE_AUTH_FEATURE.md

claude> /design AUTH_FEATURE
# Creates: .claude/sdd/features/DESIGN_AUTH_FEATURE.md

claude> /build AUTH_FEATURE
# Creates: .claude/sdd/reports/BUILD_REPORT_AUTH_FEATURE.md

claude> /ship AUTH_FEATURE
# Moves to: .claude/sdd/archive/AUTH_FEATURE/SHIPPED_*.md
```

## Adding Your Examples

We welcome example contributions! See CONTRIBUTING.md.
