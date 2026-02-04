# Getting Started with AgentSpec

This guide walks you through installing and using AgentSpec.

## Prerequisites

- Claude Code CLI installed
- Git

## Installation

### Option 1: Clone to Plugins Directory

```bash
git clone https://github.com/YOUR_ORG/agentspec.git ~/.claude/plugins/agentspec
```

### Option 2: Use Plugin Flag

```bash
claude --plugin-dir /path/to/agentspec
```

## Initialize Your Project

Create the SDD directory structure:

```bash
mkdir -p .claude/sdd/{features,reports,archive}
```

## Your First Feature

### Step 1: Brainstorm (Optional)

```bash
claude> /brainstorm "I want to add user authentication"
```

Have a conversation about your feature. No artifacts required.

### Step 2: Define Requirements

```bash
claude> /define USER_AUTH
```

This creates `.claude/sdd/features/DEFINE_USER_AUTH.md` with:
- Problem statement
- Functional requirements
- Non-functional requirements
- Acceptance criteria

### Step 3: Design Architecture

```bash
claude> /design USER_AUTH
```

This creates `.claude/sdd/features/DESIGN_USER_AUTH.md` with:
- Architecture overview
- Component specifications
- API contracts
- Implementation plan

### Step 4: Build

```bash
claude> /build USER_AUTH
```

This:
- Matches specialized agents to the task
- Executes implementation
- Creates `BUILD_REPORT_USER_AUTH.md`

### Step 5: Ship

```bash
claude> /ship USER_AUTH
```

Archives everything to `.claude/sdd/archive/USER_AUTH/` with lessons learned.

## Next Steps

- Read the [SDD Workflow Guide](../../sdd/README.md)
- Explore the [Agent Reference](../../agents/README.md)
- Create a [KB Domain](../../kb/README.md)
