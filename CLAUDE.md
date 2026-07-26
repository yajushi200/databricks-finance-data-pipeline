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
