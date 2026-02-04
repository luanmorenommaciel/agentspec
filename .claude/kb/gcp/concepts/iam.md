# IAM (Identity and Access Management)

> **Purpose**: Manage access to GCP resources with least-privilege service accounts
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

GCP IAM controls who (identity) can do what (role) on which resource. For serverless pipelines, each Cloud Run function should have a dedicated service account with only the permissions required for its task. This limits blast radius if a component is compromised.

## The Pattern

```bash
# Create dedicated service account for invoice extractor
gcloud iam service-accounts create invoice-extractor \
  --display-name="Invoice Extractor Service Account"

# Grant only required permissions
PROJECT_ID=$(gcloud config get-value project)
SA_EMAIL="invoice-extractor@${PROJECT_ID}.iam.gserviceaccount.com"

# Read from GCS (processed bucket)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectViewer" \
  --condition="expression=resource.name.startsWith('projects/_/buckets/invoices-processed'),title=processed-bucket-only"

# Write to BigQuery
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataEditor"

# Access secrets
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

## Quick Reference

| Task | Role | Scope |
|------|------|-------|
| Read GCS objects | `roles/storage.objectViewer` | Bucket-level |
| Write GCS objects | `roles/storage.objectCreator` | Bucket-level |
| Invoke Cloud Run | `roles/run.invoker` | Service-level |
| Publish Pub/Sub | `roles/pubsub.publisher` | Topic-level |
| Insert BigQuery | `roles/bigquery.dataEditor` | Dataset-level |
| Access secrets | `roles/secretmanager.secretAccessor` | Secret-level |

## Invoice Pipeline Service Accounts

| Function | Service Account | Roles |
|----------|-----------------|-------|
| TIFF Converter | `tiff-converter@` | GCS read (input), GCS write (processed), Pub/Sub publish |
| Classifier | `invoice-classifier@` | GCS read (processed), Pub/Sub publish |
| Extractor | `invoice-extractor@` | GCS read, Secret Manager access, Pub/Sub publish |
| BQ Writer | `bigquery-writer@` | BigQuery dataEditor, Pub/Sub subscribe |

## Common Mistakes

### Wrong

```bash
# Using default compute service account (overly permissive)
gcloud run deploy my-function --image gcr.io/project/image
# Default SA has Editor role on project!
```

### Correct

```bash
# Dedicated service account with least privilege
gcloud run deploy my-function \
  --image gcr.io/project/image \
  --service-account my-function@project.iam.gserviceaccount.com
```

## IAM Conditions

```yaml
# Terraform: Conditional IAM binding
resource "google_storage_bucket_iam_member" "viewer" {
  bucket = google_storage_bucket.processed.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.extractor.email}"

  condition {
    title       = "only_png_files"
    expression  = "resource.name.endsWith('.png')"
  }
}
```

## Audit Logging

```bash
# Enable data access logging for security audit
gcloud projects get-iam-policy $PROJECT_ID --format=json > policy.json
# Add auditConfigs section for storage.googleapis.com
```

## Best Practices

1. **One service account per function** - Isolate permissions
2. **Avoid basic roles** (Owner, Editor, Viewer) - Use predefined roles
3. **Resource-level bindings** - Not project-level when possible
4. **IAM conditions** - Further restrict access scope
5. **Regular audits** - Review unused permissions

## Related

- [Secret Manager](../concepts/secret-manager.md)
- [Cloud Run](../concepts/cloud-run.md)
- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
