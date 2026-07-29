"""
load_to_db.py

Loads the raw simulated transaction and customer CSVs into a DuckDB database
as 'raw' tables, ready for dbt to transform.

Using DuckDB here so the whole pipeline is runnable locally with zero setup.
The exact same load logic (and all the dbt SQL downstream) works against
PostgreSQL or Snowflake with only a connection-string / adapter change --
see README.md for notes on migrating to Postgres for production use.

Usage:
    python load_to_db.py
"""

import duckdb
import pandas as pd

DB_PATH = "../dbt_project/fraud_pipeline.duckdb"
TRANSACTIONS_CSV = "../data/transactions.csv"
CUSTOMERS_CSV = "../data/customers.csv"


def load_table(con: duckdb.DuckDBPyConnection, csv_path: str, table_name: str, df: pd.DataFrame):
    """
    Idempotent load: fully replaces the raw table each run.
    In a real production system this would instead be an incremental
    append/upsert keyed on transaction_id -- kept simple here since this
    represents the 'raw' landing zone, not the transformed layer.
    """
    con.execute(f"CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(f"CREATE OR REPLACE TABLE raw.{table_name} AS SELECT * FROM df")
    count = con.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
    print(f"Loaded {count} rows into raw.{table_name}")


def main():
    con = duckdb.connect(DB_PATH)

    transactions_df = pd.read_csv(TRANSACTIONS_CSV, parse_dates=["timestamp"])
    customers_df = pd.read_csv(CUSTOMERS_CSV, parse_dates=["account_open_date"])

    load_table(con, TRANSACTIONS_CSV, "transactions", transactions_df)
    load_table(con, CUSTOMERS_CSV, "customers", customers_df)

    con.close()
    print(f"\nDatabase ready at: {DB_PATH}")


if __name__ == "__main__":
    main()
