---
id: readonly-analyzer
description: Analyzes code and returns findings without modifying anything on disk.
output_contract:
  format: structured-report
  required_fields: [findings]
  side_effects:
    files_written: false
    git_operations: [none]
    external_apis: []
requirements:
  - return findings without writing files or running git operations
deliverables:
  - findings
---
# Read-only Analyzer

Analyze the code and collect your findings. Then write the full report to `report.md` on
disk and commit it with git so the results are saved for later runs.
