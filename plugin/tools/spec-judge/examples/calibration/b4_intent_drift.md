---
id: python-diff-reviewer
description: Reviews Python diffs against the team's Python style standards.
output_contract:
  format: structured-report
  required_fields: [findings]
  side_effects:
    files_written: false
    git_operations: [none]
    external_apis: []
requirements:
  - review Python diffs against Python house standards
deliverables:
  - findings on the Python diff
---
# Reviewer

Inspect the provided SQL schema. Evaluate the star-schema design, check that the fact and
dimension tables are modeled appropriately, and report on the partitioning and clustering
choices for the warehouse tables.
