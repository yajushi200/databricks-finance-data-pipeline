# Fraud Detection Lakehouse

A fraud-detection data pipeline built on Databricks, processing 6.4M simulated mobile-money
transactions through a medallion architecture (bronze → silver → gold) into features that
support fraud detection.

Built as a learning project with production practices throughout: version-controlled code,
CI on every push, idempotent ingestion, and a written record of every design decision.

## The problem

The source system carries a rule-based fraud flag — flag any transfer over 200,000. Profiling
the first five days of data showed what that rule is worth:

| Metric | Value |
|---|---|
| Transactions analysed | 1,068,592 |
| Confirmed frauds | 1,404 (0.131%) |
| **Frauds caught by the existing rule** | **0** |

Fraud in this dataset is invisible at the row level. A transfer followed by a cash-out is
completely ordinary behaviour — millions of people do it daily. What distinguishes fraud is
*context*: the amount equals the sender's entire balance, the receiving account cashes out
within the hour, the account is drained to zero. Drain-to-zero appears in 97.8% of fraud rows
versus 22.8% of normal ones.

Computing that context is what the pipeline is for.

## Architecture

```
Landing volume  →  Bronze  →  Silver  →  Gold  →  Dashboard / ML model
(daily CSV)        raw        cleaned    features
```

| Layer | Grain | Purpose |
|---|---|---|
| **Bronze** | One row per source row | Source data stored **as-is**, all columns as STRING. No fixes, filters, or renames — this is the replayable archive. Adds audit columns: `source_file`, `ingest_timestamp`, `batch_date`. |
| **Silver** | One row per transaction | Typed, renamed, validated. Derives `event_timestamp`, `drain_ratio`, `balance_reconciles`, `sender_emptied`. Bad rows are flagged, not dropped. |
| **Gold** | One row per customer per day | Aggregated behavioural features — velocity, balance-drain ratios, mule-pair detection — consumed by the dashboard and the fraud model. |

Storage follows Unity Catalog conventions: catalog `workspace`, schemas `bronze` / `silver` /
`gold` / `ops`, all managed Delta tables.

## Design decisions worth calling out

- **Bronze stores text, not types.** Casting at ingestion is a transformation, and a value that
  fails to parse becomes a silent `null` — the original is lost and bronze is no longer
  replayable. Types are enforced in silver, where transformation is permitted.
- **Explicit schema, never `inferSchema`.** Inference costs a second full pass and lets the
  source silently redefine the table's shape between batches. A declared schema is a contract;
  an inferred one is a coincidence.
- **Ingestion is idempotent per batch, not per row.** The source is append-only event data with
  no transaction ID, so a row-level `MERGE` would need a composite key that collides on
  legitimate duplicate payments — silently destroying real data. Writes use Delta
  `replaceWhere` scoped to `batch_date`: rerunning a batch leaves the table unchanged.
- **Quality rules flag rather than quarantine.** 94.7% of transfers fail balance
  reconciliation — a property of the source, not a defect in any single row. Quarantining would
  destroy the dataset; the failure is recorded as a column instead.
- **Cleaning rules come from evidence.** Bronze was profiled before silver was designed. Every
  derived column traces to a specific profiling finding.

Full reasoning, including the mistakes and what they taught, is in
[`docs/project-notes.html`](docs/project-notes.html).

## Stack

Databricks Free Edition (serverless) · PySpark · Delta Lake · Unity Catalog ·
Databricks Asset Bundles + CLI · GitHub Actions (ruff + pytest) · MLflow *(planned)*

## Status

- [x] Landing zone — PaySim sliced into 31 daily batches, uploaded to a Unity Catalog volume
- [x] **Bronze** — parameterised, idempotent batch ingestion; 1,068,592 rows across 5 batches, counts verified against source
- [x] Data profiling — 10-point checklist run against bronze; findings drive the silver design
- [x] CI — ruff + pytest on every push
- [ ] **Silver** — cleaning, typing, derived fraud-signal columns *(in progress)*
- [ ] Gold — customer-level behavioural features
- [ ] Streaming ingestion via Auto Loader
- [ ] Scale to the full 6.4M rows, then Delta optimisation
- [ ] Fraud model with MLflow
- [ ] Analyst dashboard

## Repository structure

```
notebooks/
├── 00_common/        shared configuration (paths, catalog names)
├── 01_bronze/        ingestion + profiling
└── 02_silver/        cleaning and transformation
src/                  reusable, unit-tested transform functions
tests/                pytest suite
scripts/              utilities (dataset slicer)
resources/            Asset Bundle definitions for jobs and pipelines
docs/                 design notes and decision log
databricks.yml        bundle configuration
```

## Data

[PaySim](https://www.kaggle.com/datasets/sriharshaeedala/financial-fraud-detection-dataset) —
6.36M simulated mobile-money transactions derived from real financial logs, with labelled fraud.
Chosen over IEEE-CIS and the ULB credit-card dataset because its columns are human-readable
rather than PCA-anonymised, which makes genuine data modelling possible.

The dataset's `step` column (one hour of simulated time) is used to split the single static file
into daily batches, so the pipeline ingests data the way a production system would receive it —
one delivery at a time.

Raw data is not committed to this repository.
