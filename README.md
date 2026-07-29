# Fraud-Detection-Pipeline-With-AI-Powered-Triage
**SQL-based fraud detection (dbt) + AI-powered triage agent (n8n + Claude) + analyst review dashboard**

An end-to-end fraud detection system built for a banking context  from raw transaction data to a human analyst's decision. Transactions are simulated, flagged using explainable SQL rules in dbt, enriched by an AI agent, and surfaced in a lightweight review dashboard  all with a human-in-the-loop at every stage.

---
<img width="918" height="830" alt="fraud dashboard" src="https://github.com/user-attachments/assets/e50b3c06-a75d-4ac3-bc0f-dc219afe470e" />

## Demo

**Pipeline walkthrough** (data generation → dbt → AI agent, ~57s):

https://github.com/luxnaramnauth1/Fraud-Detection-Pipeline-With-AI-Powered-Triage/blob/main/fraud_app_demo%20(1).mp4

**Fraud Review Console app demo** (~22s):

https://github.com/user-attachments/assets/PASTE-YOUR-UPLOADED-VIDEO-LINK-HERE


## What This Project Does

- **Simulates realistic bank transactions** (5,000+) with injected fraud patterns: unusual amounts, foreign locations, rapid repeat transactions
- **Flags suspicious activity using explainable SQL rules** in dbt - no black-box model, every flag traces back to a specific, auditable rule
- **Enriches flagged transactions with AI** - an n8n workflow sends each flag to Claude, which writes a plain-language risk summary and routes it to Slack by severity
- **Gives analysts a working review dashboard** - filter by risk level, see exactly which rules triggered per transaction ("flag DNA"), and check route/amount at a glance
- **Validates itself** -14 automated dbt tests for data quality, and detection performance measured against ground truth

## Results

| Metric | Value |
|---|---|
| Transactions processed | 5,057 |
| Flagged for review | 138 (2.7%) |
| **Recall** (fraud caught) | **70.1%** |
| **Precision** (flags correct) | **79.7%** |
| Data quality tests passing | 14 / 14 |

## Architecture

```
Python + Faker          Python              dbt (SQL)                 n8n + Claude              HTML dashboard
generate data  ────►  load to DB  ────►  clean, baseline,   ────►   enrich + route     ────►   analyst review
                     (DuckDB /          flag suspicious              by risk level
                      Postgres)          transactions
                                              │
                                              ▼
                                    flagged_transactions
                                      (14 dbt tests passing)
```

**Detection rules** (each an independent, explainable SQL check):

| Rule | Logic | Signal |
|---|---|---|
| High amount | Amount > customer's own avg + 3×stddev | Unusually large purchase |
| Unusual location | Transaction city ≠ home city | Card used somewhere atypical |
| Rapid repeat | Another transaction within 10 minutes | Card being drained quickly |

## Tech Stack

| Category | Tools |
|---|---|
| Data generation & processing | Python, Pandas, Faker |
| Data warehouse | DuckDB (dev) — Postgres/Snowflake-ready |
| Transformation & data quality | dbt (SQL models + automated tests) |
| Orchestration | Apache Airflow |
| AI agent / automation | n8n, Claude API (Anthropic) |
| Alerting | Slack |
| Dashboard | HTML, CSS, vanilla JavaScript |
| Documentation | ReportLab (PDF generation) |

## Project Structure

```
fraud_pipeline/
├── scripts/
│   ├── generate_transactions.py   # simulates transactions with fraud patterns
│   └── load_to_db.py              # loads raw CSVs into the warehouse
├── dbt_project/
│   └── models/
│       ├── staging/               # cleaning
│       ├── intermediate/          # customer baselines, velocity checks
│       └── marts/                 # flagged_transactions (final output)
├── dags/
│   └── fraud_pipeline_dag.py      # Airflow DAG for scheduled runs
├── n8n/
│   └── fraud_triage_agent.json    # AI triage workflow (import into n8n)
├── app/
│   └── fraud_dashboard.html       # analyst review dashboard (open directly, no server needed)
├── docs/
│   ├── demo_video_script.md
│   └── n8n_fraud_triage_guide.md
├── Fraud_Pipeline_Build_Guide.pdf # full build guide with screenshots
├── Fraud_Review_Steps.pdf         # analyst workflow guide with screenshots
└── README.md
```

## How to Run

**1. Install dependencies**
```bash
pip install faker pandas duckdb dbt-core dbt-duckdb --break-system-packages
```

**2. Generate transaction data**
```bash
cd scripts
python generate_transactions.py --n_customers 200 --n_transactions 5000 --fraud_rate 0.02
python load_to_db.py
```

**3. Run the dbt pipeline**

Create `~/.dbt/profiles.yml`:
```yaml
fraud_pipeline:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: fraud_pipeline.duckdb
      threads: 4
```

Then:
```bash
cd ../dbt_project
dbt run
dbt test
```

**4. Open the dashboard**

Just open `app/fraud_dashboard.html` in any browser — it's fully self-contained.

**5. (Optional) Run the AI triage agent**
```bash
npm install -g n8n
n8n start
```
Import `n8n/fraud_triage_agent.json` via the n8n UI, add your Postgres/Claude/Slack credentials, and activate.

## Design Principles

- **Explainable by default** - every flag traces to a specific SQL rule, not a black box. Important for audit and compliance in banking.
- **Human-in-the-loop** - the AI agent enriches and routes; it never autonomously blocks a card or closes an account.
- **Portable** - DuckDB is used for a zero-setup local demo, but every model is standard SQL that runs unchanged on PostgreSQL or Snowflake.
- **Tested** - 14 automated dbt tests guard data quality throughout the pipeline.

## Next Steps / Extensions

- Add an ML-based anomaly detection layer (Isolation Forest) alongside the SQL rules
- Migrate to PostgreSQL/Snowflake for a production-style deployment
- Add incremental loading instead of full-batch reloads
- Extend the n8n agent with tool-calling (native AI Agent node) for deeper account investigation


