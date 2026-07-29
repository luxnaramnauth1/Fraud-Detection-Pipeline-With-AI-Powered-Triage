# Bank Transaction Fraud Detection — ETL Pipeline

A rule-based fraud-flagging pipeline built on a realistic ETL/ELT architecture:
simulated transaction data → loaded into a database → transformed with dbt →
suspicious transactions flagged using behavioral SQL logic.

Designed to mirror the kind of infrastructure banks use for real-time
transaction monitoring and fraud prevention.

## Architecture

```
generate_transactions.py          load_to_db.py                dbt (staging → intermediate → marts)
   (Python + Faker)        --->     (Python)         --->              (SQL)
                                                                          |
                                                                          v
     data/transactions.csv    raw.transactions (DuckDB)         flagged_transactions
     data/customers.csv       raw.customers    (DuckDB)          (final output table)

Orchestration: Apache Airflow (hourly DAG — see dags/fraud_pipeline_dag.py)
```

**Tech stack:** Python, pandas, Faker, DuckDB (local dev database — same SQL
portable to PostgreSQL/Snowflake), dbt-core, Apache Airflow

## Why DuckDB instead of PostgreSQL?

This project uses **DuckDB** as the warehouse so the entire pipeline runs
locally with zero external setup (no server, no credentials, no Docker
required just to try it out). DuckDB is a modern, actively-maintained
analytical database used in real production data-engineering workflows.

The dbt SQL models are standard ANSI SQL and require only a connection
change (a different `profiles.yml` target) to run against PostgreSQL or
Snowflake instead — see `dbt_project/profiles_postgres_example.yml` for
the config needed to point this at a real Postgres instance.

## Project Structure

```
fraud_pipeline/
├── data/
│   ├── transactions.csv          # simulated raw transactions
│   └── customers.csv             # simulated customer profiles
├── scripts/
│   ├── generate_transactions.py  # Step 1: simulate data
│   └── load_to_db.py             # Step 2: load raw CSVs into the database
├── dbt_project/
│   ├── dbt_project.yml
│   ├── fraud_pipeline.duckdb     # the local database file (generated)
│   └── models/
│       ├── staging/              # stg_transactions, stg_customers — cleaning only
│       ├── intermediate/         # customer behavior baselines + velocity checks
│       ├── marts/                # flagged_transactions — final fraud-flag output
│       └── schema.yml            # dbt tests (uniqueness, not-null) for data quality
├── dags/
│   └── fraud_pipeline_dag.py     # Airflow DAG orchestrating the full pipeline hourly
└── README.md
```

## How the Fraud-Flagging Logic Works

Three independent SQL-based rules, each modeling a real fraud signal:

| Rule | Logic | Real-world signal |
|---|---|---|
| `flag_high_amount` | Amount > customer's own average + 3×stddev | Card is being used for an unusually large purchase |
| `flag_unusual_location` | Transaction location ≠ customer's home city | Card used somewhere the customer doesn't normally transact |
| `flag_rapid_repeat` | Another transaction by the same customer within 10 minutes | Classic "stolen card being drained quickly" pattern |

A transaction is flagged (`is_flagged = true`) if it trips **any** rule.
`flag_count` shows how many rules it tripped — useful for prioritizing a
fraud-review queue (higher `flag_count` = higher risk).

This mirrors how many real fraud systems start: **explainable, rule-based
logic** first (which auditors and compliance teams can understand and
approve), before layering in ML-based anomaly detection.

## Results

Run against 5,057 simulated transactions (with a known ~3.1% injected
fraud rate used only for evaluation, never as a model input):

| Metric | Value |
|---|---|
| Total transactions | 5,057 |
| Transactions flagged | 138 (2.7%) |
| Recall (fraud caught) | 70.1% (110 / 157) |
| Precision (flags that were real fraud) | 79.7% (110 / 138) |

**Data quality:** all 14 dbt tests pass (uniqueness and not-null checks on
every model in the pipeline).

## How to Run It Yourself

```bash
# 1. Install dependencies
pip install faker pandas duckdb dbt-core dbt-duckdb

# 2. Generate simulated transaction data
cd scripts
python generate_transactions.py --n_customers 200 --n_transactions 5000

# 3. Load raw data into the database
python load_to_db.py

# 4. Run the dbt transformation pipeline
cd ../dbt_project
dbt run

# 5. Run data quality tests
dbt test

# 6. (Optional) generate and view the lineage docs
dbt docs generate
dbt docs serve
```

## Running the Full Pipeline on a Schedule (Airflow)

`dags/fraud_pipeline_dag.py` contains a ready-to-use Airflow DAG that runs
all four steps above on an hourly schedule. To use it:

1. Set up Airflow via Docker (`docker compose` — official Airflow quick-start)
2. Copy `dags/fraud_pipeline_dag.py` into your Airflow `dags/` folder
3. Mount/copy `scripts/` and `dbt_project/` so their paths match the DAG
4. Trigger `fraud_detection_pipeline` from the Airflow UI

## Migrating to PostgreSQL (Production Path)

To move this from a local demo to a production-style setup:

1. Swap the dbt adapter: `pip install dbt-postgres` instead of `dbt-duckdb`
2. Update `profiles.yml` to point at a Postgres connection (host, user,
   password, database)
3. Update `load_to_db.py` to use `psycopg2`/`SQLAlchemy` with a Postgres
   connection string instead of DuckDB
4. No changes needed to the dbt SQL models themselves — they're standard SQL

## Next Steps / Extensions

- Add an ML-based anomaly detection layer (Isolation Forest) on top of the
  rule-based flags, and compare the two approaches
- Add incremental loading (only new transactions each run, not a full reload)
- Add Slack/email alerting for high `flag_count` transactions
- Deploy `flagged_transactions` results to a lightweight dashboard (Streamlit)
