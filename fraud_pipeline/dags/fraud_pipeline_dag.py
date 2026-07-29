"""
fraud_pipeline_dag.py

Airflow DAG that orchestrates the full fraud-detection ETL pipeline:

    1. generate_transactions  -> simulate a new batch of transactions
    2. load_to_db             -> load raw CSVs into the warehouse (DuckDB/Postgres)
    3. dbt_run                -> transform raw data into flagged_transactions
    4. dbt_test               -> run data quality tests on the output

Run this with Airflow via Docker:
    1. Copy this file into your Airflow project's `dags/` folder
    2. Make sure the `scripts/` and `dbt_project/` folders are mounted/available
       at the paths referenced below (adjust SCRIPTS_DIR / DBT_PROJECT_DIR as needed)
    3. Start Airflow: `docker compose up -d`
    4. Trigger the DAG `fraud_detection_pipeline` from the Airflow UI

NOTE: This file is provided as a ready-to-use reference. It was not executed
in this environment (no Airflow scheduler running here), but the underlying
scripts (generate_transactions.py, load_to_db.py) and dbt project it calls
have been fully tested and run successfully on their own.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

SCRIPTS_DIR = "/opt/airflow/scripts"
DBT_PROJECT_DIR = "/opt/airflow/dbt_project"
DBT_PROFILES_DIR = "/opt/airflow/dbt_project"  # profiles.yml can also live alongside the project

default_args = {
    "owner": "data_engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="fraud_detection_pipeline",
    description="Simulate, load, and transform transaction data to flag suspicious activity",
    default_args=default_args,
    schedule_interval="@hourly",   # simulates a recurring near-real-time batch pipeline
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["fraud", "etl", "dbt", "banking"],
) as dag:

    generate_transactions = BashOperator(
        task_id="generate_transactions",
        bash_command=(
            f"cd {SCRIPTS_DIR} && "
            f"python generate_transactions.py "
            f"--n_customers 200 --n_transactions 500 --fraud_rate 0.02"
        ),
    )

    load_to_db = BashOperator(
        task_id="load_to_db",
        bash_command=f"cd {SCRIPTS_DIR} && python load_to_db.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"DBT_PROFILES_DIR={DBT_PROFILES_DIR} dbt run"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"DBT_PROFILES_DIR={DBT_PROFILES_DIR} dbt test"
        ),
    )

    generate_transactions >> load_to_db >> dbt_run >> dbt_test
