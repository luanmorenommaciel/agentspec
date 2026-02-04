# AgentSpec Commands

Slash commands for the SDD workflow.

## Workflow Commands

| Command | Phase | Description |
|---------|-------|-------------|
| `/brainstorm` | 0 | Explore ideas through dialogue |
| `/define` | 1 | Capture requirements |
| `/design` | 2 | Create architecture |
| `/build` | 3 | Execute implementation |
| `/ship` | 4 | Archive completed feature |
| `/iterate` | Any | Update documents mid-stream |
| `/create-pr` | Any | Create pull request |

## Core Commands

| Command | Description |
|---------|-------------|
| `/memory` | Save session insights |
| `/sync-context` | Update CLAUDE.md |
| `/readme-maker` | Generate README |
| `/telemetry` | View usage stats |

## Knowledge Commands

| Command | Description |
|---------|-------------|
| `/create-kb` | Create KB domain |

## Review Commands

| Command | Description |
|---------|-------------|
| `/review` | Code review workflow |

## Usage

Commands are invoked in Claude Code:

```bash
claude> /define USER_AUTH
```
