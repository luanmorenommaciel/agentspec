# Environment Promotion Pattern

> **Purpose**: Safely promote infrastructure changes from dev to prod with validation
> **MCP Validated**: 2026-01-25

## When to Use

- Moving tested changes to production
- CI/CD pipeline for infrastructure
- Need audit trail for changes
- Want validation gates between environments

## Implementation

```yaml
# .github/workflows/terragrunt-promotion.yaml
name: Terragrunt Promotion

on:
  push:
    branches: [main]
    paths: ['infrastructure/**']
  pull_request:
    branches: [main]
    paths: ['infrastructure/**']

jobs:
  dev-plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terragrunt
        uses: autero1/action-terragrunt@v1
        with:
          terragrunt_version: 0.54.0

      - name: Dev Plan
        working-directory: infrastructure/environments/dev
        run: terragrunt run-all plan -out=tfplan
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GCP_DEV_SA_KEY }}

  dev-apply:
    needs: dev-plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4

      - name: Dev Apply
        working-directory: infrastructure/environments/dev
        run: terragrunt run-all apply -auto-approve
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GCP_DEV_SA_KEY }}

  prod-plan:
    needs: dev-apply
    runs-on: ubuntu-latest
    steps:
      - name: Prod Plan
        working-directory: infrastructure/environments/prod
        run: terragrunt run-all plan -out=tfplan
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GCP_PROD_SA_KEY }}

  prod-apply:
    needs: prod-plan
    runs-on: ubuntu-latest
    environment: prod  # Requires manual approval
    steps:
      - name: Prod Apply
        working-directory: infrastructure/environments/prod
        run: terragrunt run-all apply -auto-approve
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GCP_PROD_SA_KEY }}
```

## Validation Hook Pattern

```hcl
# infrastructure/terragrunt.hcl
terraform {
  before_hook "validate" {
    commands = ["apply", "plan"]
    execute  = ["./scripts/validate-env.sh"]
  }

  before_hook "cost_estimate" {
    commands = ["apply"]
    execute  = ["./scripts/estimate-cost.sh"]
  }
}
```

```bash
#!/bin/bash
# scripts/validate-env.sh

ENV=$(basename $(dirname $(pwd)))

if [[ "$ENV" == "prod" ]]; then
  echo "PRODUCTION DEPLOYMENT"
  echo "Checking prerequisites..."

  # Verify dev was applied first
  DEV_STATE=$(gsutil cat gs://invoice-processing-dev-tfstate/environments/dev/cloud-run/default.tfstate 2>/dev/null)
  if [[ -z "$DEV_STATE" ]]; then
    echo "ERROR: Dev environment not deployed. Deploy dev first."
    exit 1
  fi

  echo "Prerequisites met. Proceeding..."
fi
```

## Manual Promotion Workflow

```bash
# Step 1: Apply to dev
cd infrastructure/environments/dev
terragrunt run-all plan
terragrunt run-all apply

# Step 2: Validate dev deployment
./scripts/run-integration-tests.sh dev

# Step 3: Plan prod (review changes)
cd ../prod
terragrunt run-all plan

# Step 4: Apply to prod (after approval)
terragrunt run-all apply
```

## Configuration

| Gate | Dev | Prod | Purpose |
|------|-----|------|---------|
| Auto-apply | Yes | No | Speed vs safety |
| Manual approval | No | Yes | Human verification |
| Integration tests | Optional | Required | Quality gate |
| Cost estimate | Optional | Required | Budget control |

## Promotion Checklist

```text
PRE-PROMOTION (Dev -> Prod)
[ ] All dev modules applied successfully
[ ] Integration tests passing in dev
[ ] Cost estimate reviewed
[ ] Security scan completed
[ ] Change documented in PR

POST-PROMOTION
[ ] Prod plan reviewed
[ ] Manual approval obtained
[ ] Prod apply successful
[ ] Smoke tests passing
[ ] Monitoring alerts configured
```

## Example Usage

```bash
# Compare environments
diff <(cd dev && terragrunt run-all output -json) \
     <(cd prod && terragrunt run-all output -json)

# Selective module promotion
cd infrastructure/environments/prod/cloud-run
terragrunt plan
terragrunt apply
```

## See Also

- [multi-environment-config.md](multi-environment-config.md)
- [hooks.md](../concepts/hooks.md)
- [dependency-management.md](dependency-management.md)
