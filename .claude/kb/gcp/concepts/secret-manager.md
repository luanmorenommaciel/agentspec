# Secret Manager

> **Purpose**: Store and manage API keys, passwords, and certificates securely
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Secret Manager stores sensitive data like API keys with versioning, encryption, and access control. For the invoice pipeline, it secures Gemini API keys and LangFuse credentials. Cloud Run accesses secrets at runtime, avoiding hardcoded credentials.

## The Pattern

```python
from google.cloud import secretmanager

def get_secret(project_id: str, secret_id: str, version: str = "latest") -> str:
    """Access secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"

    # Access the secret version
    response = client.access_secret_version(request={"name": name})

    # Return the decoded payload
    return response.payload.data.decode("UTF-8")

# Usage in Cloud Run function
def process_with_llm(invoice_image: bytes) -> dict:
    """Extract invoice data using Gemini."""
    import google.generativeai as genai

    # Get API key from Secret Manager
    api_key = get_secret("my-project", "gemini-api-key")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-flash")
    # ... extraction logic
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| Secret name | Secret value | Decrypted at runtime |
| Version number | Specific version | Use for rollback |
| "latest" alias | Current version | Default behavior |

## Invoice Pipeline Secrets

| Secret | Purpose | Accessing Function |
|--------|---------|-------------------|
| `gemini-api-key` | Vertex AI / Gemini API | Invoice Extractor |
| `langfuse-public-key` | LLMOps observability | Invoice Extractor |
| `langfuse-secret-key` | LLMOps authentication | Invoice Extractor |

## Version Management

```bash
# Create a new secret
gcloud secrets create gemini-api-key \
  --replication-policy="automatic"

# Add a version
echo -n "sk-abc123" | gcloud secrets versions add gemini-api-key --data-file=-

# List versions
gcloud secrets versions list gemini-api-key

# Disable old version (don't delete immediately)
gcloud secrets versions disable gemini-api-key --version=1

# Access specific version in code
get_secret("project", "gemini-api-key", version="2")
```

## Common Mistakes

### Wrong

```python
# Hardcoded secret (never do this)
API_KEY = "sk-abc123xyz"

# Using environment variables with plain text
os.environ["API_KEY"] = "sk-abc123"
```

### Correct

```python
# Access from Secret Manager at runtime
from functools import lru_cache

@lru_cache(maxsize=1)
def get_api_key() -> str:
    """Cached secret access (minimize API calls)."""
    return get_secret(
        project_id=os.environ["GCP_PROJECT"],
        secret_id="gemini-api-key",
        version="latest"
    )
```

## Cloud Run Integration

```yaml
# Deploy with secret as environment variable
gcloud run deploy invoice-extractor \
  --image gcr.io/project/extractor \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --set-secrets="LANGFUSE_PUBLIC_KEY=langfuse-public-key:latest"
```

## Terraform Configuration

```hcl
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "gemini-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "access" {
  secret_id = google_secret_manager_secret.gemini_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.extractor.email}"
}
```

## Rotation Strategy

1. Add new version to secret
2. Deploy new Cloud Run revision (pulls latest)
3. Verify new version works
4. Disable old version
5. Delete old version after grace period

## Related

- [IAM](../concepts/iam.md)
- [Cloud Run](../concepts/cloud-run.md)
- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
