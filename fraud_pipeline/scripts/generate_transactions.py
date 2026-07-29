"""
generate_transactions.py

Simulates a batch of bank transactions, including a small percentage of
deliberately suspicious/fraudulent-looking transactions, so we have
realistic data to build a fraud-flagging pipeline against.

Usage:
    python generate_transactions.py --n_customers 200 --n_transactions 5000 --output ../data/transactions.csv
"""

import argparse
import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

MERCHANT_CATEGORIES = [
    "Grocery", "Electronics", "Restaurant", "Fuel Station", "Online Retail",
    "Utility Bill", "ATM Withdrawal", "Travel", "Pharmacy", "Entertainment"
]

CITIES_MU = [
    "Port Louis", "Curepipe", "Quatre Bornes", "Rose Hill", "Vacoas",
    "Beau Bassin", "Flacq", "Grand Baie", "Mahebourg", "Tamarin"
]

# A few "unusual" foreign locations used to simulate location-anomaly fraud
FOREIGN_CITIES = ["Lagos", "Manila", "Kyiv", "Bogota", "Jakarta"]


def build_customer_base(n_customers: int) -> pd.DataFrame:
    """Create a customer profile table with a 'typical' home city and average spend."""
    customers = []
    for i in range(n_customers):
        customers.append({
            "customer_id": f"CUST{i:05d}",
            "customer_name": fake.name(),
            "home_city": random.choice(CITIES_MU),
            "avg_transaction_amount": round(np.random.gamma(shape=2.0, scale=800), 2),
            "account_open_date": fake.date_between(start_date="-5y", end_date="-30d"),
        })
    return pd.DataFrame(customers)


def generate_normal_transaction(customer: pd.Series, ts: datetime) -> dict:
    """A transaction that fits the customer's normal behavior pattern."""
    amount = max(50, np.random.normal(loc=customer["avg_transaction_amount"], scale=customer["avg_transaction_amount"] * 0.3))
    return {
        "transaction_id": str(uuid.uuid4()),
        "customer_id": customer["customer_id"],
        "timestamp": ts,
        "amount": round(amount, 2),
        "merchant_category": random.choice(MERCHANT_CATEGORIES),
        "location": customer["home_city"],
        "is_simulated_fraud": 0,
    }


def generate_suspicious_transaction(customer: pd.Series, ts: datetime) -> dict:
    """
    Injects one of a few common fraud signatures:
    - Amount far above the customer's normal spend
    - Transaction from an unusual/foreign location
    - Rapid repeat transaction (handled at the batch level, see main())
    """
    pattern = random.choice(["high_amount", "foreign_location", "odd_hour"])

    amount = customer["avg_transaction_amount"]
    location = customer["home_city"]
    hour_shift = 0

    if pattern == "high_amount":
        amount = customer["avg_transaction_amount"] * random.uniform(4, 10)
    elif pattern == "foreign_location":
        location = random.choice(FOREIGN_CITIES)
        amount = customer["avg_transaction_amount"] * random.uniform(1, 3)
    elif pattern == "odd_hour":
        hour_shift = random.choice([-6, -5, -4])  # push into very early hours
        amount = customer["avg_transaction_amount"] * random.uniform(1, 2)

    ts = ts + timedelta(hours=hour_shift)

    return {
        "transaction_id": str(uuid.uuid4()),
        "customer_id": customer["customer_id"],
        "timestamp": ts,
        "amount": round(amount, 2),
        "merchant_category": random.choice(MERCHANT_CATEGORIES),
        "location": location,
        "is_simulated_fraud": 1,  # ground-truth label, kept ONLY for evaluation, not used by rules/model as a feature
    }


def main(n_customers: int, n_transactions: int, fraud_rate: float, output_path: str, customers_output_path: str):
    customers_df = build_customer_base(n_customers)

    transactions = []
    start_date = datetime.now() - timedelta(days=30)

    n_fraud = int(n_transactions * fraud_rate)
    n_normal = n_transactions - n_fraud

    # Normal transactions, spread across the last 30 days
    for _ in range(n_normal):
        customer = customers_df.sample(1).iloc[0]
        ts = start_date + timedelta(
            seconds=random.randint(0, 30 * 24 * 3600)
        )
        transactions.append(generate_normal_transaction(customer, ts))

    # Suspicious transactions
    for _ in range(n_fraud):
        customer = customers_df.sample(1).iloc[0]
        ts = start_date + timedelta(
            seconds=random.randint(0, 30 * 24 * 3600)
        )
        transactions.append(generate_suspicious_transaction(customer, ts))

    tx_df = pd.DataFrame(transactions).sort_values("timestamp").reset_index(drop=True)

    # Inject a handful of "rapid repeat transaction" fraud patterns:
    # take a few random normal transactions and clone them 3-5x within a few minutes
    rapid_repeat_batches = []
    sample_idxs = tx_df[tx_df["is_simulated_fraud"] == 0].sample(min(15, len(tx_df))).index
    for idx in sample_idxs:
        base_row = tx_df.loc[idx].copy()
        repeats = random.randint(3, 5)
        for r in range(repeats):
            new_row = base_row.copy()
            new_row["transaction_id"] = str(uuid.uuid4())
            new_row["timestamp"] = base_row["timestamp"] + timedelta(minutes=random.randint(1, 8) * (r + 1))
            new_row["is_simulated_fraud"] = 1
            rapid_repeat_batches.append(new_row)

    if rapid_repeat_batches:
        tx_df = pd.concat([tx_df, pd.DataFrame(rapid_repeat_batches)], ignore_index=True)

    tx_df = tx_df.sort_values("timestamp").reset_index(drop=True)

    tx_df.to_csv(output_path, index=False)
    customers_df.to_csv(customers_output_path, index=False)

    print(f"Generated {len(tx_df)} transactions for {n_customers} customers.")
    print(f"  - Ground-truth simulated fraud rate: {tx_df['is_simulated_fraud'].mean():.2%}")
    print(f"Saved transactions to: {output_path}")
    print(f"Saved customer profiles to: {customers_output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate bank transaction data with injected fraud patterns.")
    parser.add_argument("--n_customers", type=int, default=200)
    parser.add_argument("--n_transactions", type=int, default=5000)
    parser.add_argument("--fraud_rate", type=float, default=0.02, help="Base fraud injection rate (excludes rapid-repeat extras)")
    parser.add_argument("--output", type=str, default="../data/transactions.csv")
    parser.add_argument("--customers_output", type=str, default="../data/customers.csv")
    args = parser.parse_args()

    main(args.n_customers, args.n_transactions, args.fraud_rate, args.output, args.customers_output)
