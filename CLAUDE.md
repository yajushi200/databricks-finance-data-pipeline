# CLAUDE.md

# Project: Fraud Detection Lakehouse

Building a fraud-detection data pipeline on Databricks Free Edition (serverless compute only — no custom clusters or GPUs).

## Architecture
Medallion: bronze (raw) -> silver (cleaned + validated) -> gold (aggregates + ML features), all Delta tables.
Batch ingestion + Structured Streaming ingestion into the same tables.

## Stack & conventions
- Deployed via Databricks Asset Bundles + the `databricks` CLI, auth profile: `free`.
- Reusable transforms = testable Python functions in `src/`.
- Pipeline/job definitions in `pipelines/`; bundle config in `resources/` and `databricks.yml`.
- Data quality via Lakeflow expectations; bad rows quarantined, not dropped.
- MLflow for the fraud model. GitHub Actions for CI (ruff + pytest).
- Public repo — never commit secrets, tokens, or .databrickscfg.

## Storage conventions (Unity Catalog)
- Catalog: `workspace` (Free Edition default). Schemas: `bronze`, `silver`, `gold`, `ops` (ingest logs + quarantine).
- Tables: lowercase snake_case, layer expressed by schema (e.g. `workspace.bronze.transactions`).
- Landing volume: `/Volumes/workspace/bronze/landing/date=YYYY-MM-DD/transactions.csv`. Landing is disposable after ingestion (30-day retention); bronze is the source of truth.
- All tables are managed Delta tables.

## Bronze contract
- Grain: one row per source row. Source data as-is: no fixes, filters, or renames (even inconsistent source names like `oldbalanceOrg`/`newbalanceOrig` stay — renaming happens in silver).
- Explicit schema at read, never `inferSchema`.
- 11 PaySim columns + audit columns: `source_file` STRING, `ingest_timestamp` TIMESTAMP, `batch_date` DATE.
- Append-only (source is event data). Idempotent per batch_date.

## Workflow rules
- Profile bronze before designing silver: cleaning rules come from evidence, not guesses.
- Design backwards (gold grain from consumer questions), build forwards (bronze → silver → gold).
- Every design decision + its reasoning is recorded in `docs/project-notes.html` and `docs/project-notes.docx` (single running files — append, never create new note files).
- The user is learning: explain concepts, ask before writing code for them, challenge their reasoning.
