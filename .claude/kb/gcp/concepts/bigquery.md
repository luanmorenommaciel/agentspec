# BigQuery

> **Purpose**: Serverless data warehouse with streaming inserts for real-time analytics
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

BigQuery is a fully managed, serverless data warehouse that supports streaming inserts for real-time data ingestion. For invoice processing, extracted data flows from Cloud Run to BigQuery via streaming API, enabling immediate analytics on processed invoices.

## The Pattern

```python
from google.cloud import bigquery
from datetime import datetime

def insert_invoice_data(project_id: str, dataset_id: str, table_id: str, invoice: dict):
    """Stream invoice data to BigQuery."""
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Prepare row with schema-aligned fields
    row = {
        "invoice_id": invoice["invoice_id"],
        "vendor_name": invoice["vendor_name"],
        "invoice_date": invoice["invoice_date"],
        "total_amount": float(invoice["total_amount"]),
        "line_items": invoice.get("line_items", []),
        "processed_at": datetime.utcnow().isoformat(),
        "source_file": invoice["source_file"]
    }

    errors = client.insert_rows_json(table_ref, [row])

    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    return row["invoice_id"]
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| JSON row | Streaming buffer | Available for query in seconds |
| Batch load | Table partition | Use for historical data |
| Query | Result set | SQL syntax |

## Invoice Table Schema

```sql
CREATE TABLE IF NOT EXISTS `project.invoices.extracted_data` (
  invoice_id STRING NOT NULL,
  vendor_name STRING,
  invoice_date DATE,
  total_amount NUMERIC,
  line_items ARRAY<STRUCT<
    description STRING,
    quantity INT64,
    unit_price NUMERIC,
    total NUMERIC
  >>,
  processed_at TIMESTAMP,
  source_file STRING,
  extraction_confidence FLOAT64
)
PARTITION BY invoice_date
CLUSTER BY vendor_name;
```

## Partitioning Strategy

| Strategy | Use Case | Invoice Pipeline |
|----------|----------|------------------|
| **Time-unit (DATE)** | Query by date range | Partition by `invoice_date` |
| Ingestion time | When date unknown | Fallback option |
| Integer range | ID-based queries | Not recommended |

## Common Mistakes

### Wrong

```python
# No error handling, no deduplication logic
client.insert_rows_json(table, [row])
```

### Correct

```python
def insert_with_dedup(client, table_ref: str, row: dict, insert_id: str):
    """Insert with deduplication via insertId."""
    rows_to_insert = [{
        "insertId": insert_id,  # Deduplicate within buffer window
        "json": row
    }]

    errors = client.insert_rows_json(
        table_ref,
        [row],
        row_ids=[insert_id]  # Client library handles insertId
    )

    if errors:
        for error in errors:
            if "already exists" not in str(error):
                raise RuntimeError(f"Insert failed: {error}")

    return True
```

## Streaming Constraints

| Constraint | Value | Mitigation |
|------------|-------|------------|
| Past partition limit | 31 days | Buffer old data, batch load |
| Future partition limit | 16 days | Validate dates before insert |
| Dedup window | Minutes | Use unique insertId |
| Max row size | 10 MB | Validate payload size |

## Query Best Practices

```sql
-- Good: Specific columns, partition filter
SELECT invoice_id, vendor_name, total_amount
FROM `project.invoices.extracted_data`
WHERE invoice_date BETWEEN '2026-01-01' AND '2026-01-31'
  AND vendor_name = 'Restaurant ABC';

-- Bad: SELECT *, no partition filter
SELECT * FROM `project.invoices.extracted_data`;
```

## Related

- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [Cloud Run](../concepts/cloud-run.md)
- [IAM](../concepts/iam.md)
