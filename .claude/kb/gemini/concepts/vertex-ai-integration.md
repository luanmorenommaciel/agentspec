# Vertex AI Integration

> **Purpose**: Configure Vertex AI SDK and authentication for Gemini
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Vertex AI is Google Cloud's managed ML platform. The new google-genai SDK provides a unified interface for both Vertex AI and the Gemini Developer API, with the `vertexai=True` flag determining which backend to use.

## SDK Installation

```bash
# Install the new unified SDK
pip install google-genai

# Note: vertexai.generative_models is DEPRECATED (June 2025)
# Migration deadline: June 2026
```

## Authentication Methods

### Method 1: Environment Variables (Recommended for Production)

```python
import os

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "your-project-id"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/service-account.json"

from google import genai
client = genai.Client()  # Auto-configures from env vars
```

### Method 2: Direct Client Initialization

```python
from google import genai

client = genai.Client(
    vertexai=True,
    project="your-project-id",
    location="us-central1"
)
```

### Method 3: Service Account JSON (No gcloud CLI)

```python
from google import genai
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    "/path/to/service-account.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

client = genai.Client(
    vertexai=True,
    project="your-project-id",
    location="us-central1",
    credentials=credentials
)
```

## Required IAM Permissions

| Role | Purpose |
|------|---------|
| `roles/aiplatform.user` | Invoke Gemini models |
| `roles/storage.objectViewer` | Read images from GCS |

## Quick Reference

| Config | Value | Notes |
|--------|-------|-------|
| Default region | `us-central1` | Best availability |
| Backup regions | `europe-west4`, `asia-northeast1` | For geo-redundancy |
| API endpoint | Automatic | SDK handles routing |

## Common Mistakes

### Wrong

```python
# Using deprecated SDK
from vertexai.generative_models import GenerativeModel  # DEPRECATED
```

### Correct

```python
# Using new unified SDK
from google import genai
from google.genai import types
```

## Related

- [model-capabilities.md](model-capabilities.md)
- [../patterns/error-handling-retries.md](../patterns/error-handling-retries.md)
