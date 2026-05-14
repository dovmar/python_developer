"""Section 4.1 — Code Review.

ORIGINAL CODE (annotated with issues)
──────────────────────────────────────
"""

# ── Original code with ISSUE annotations ────────────────────────────────

import pandas as pd
import sqlalchemy

# ISSUE 1 — SECURITY: Hard-coded credentials in source code.
# Database passwords must never be committed to version control.
# Use environment variables or a secrets manager instead.
engine = sqlalchemy.create_engine("postgresql://admin:password123@prod-db:5432/finance")


def get_customer_data(customer_id):
    # ISSUE 2 — SECURITY (SQL Injection): String concatenation to build SQL
    # allows arbitrary SQL injection. Use parameterised queries instead.
    query = "SELECT * FROM customers WHERE customer_id = '" + customer_id + "'"
    df = pd.read_sql(query, engine)

    data = []
    # ISSUE 3 — PERFORMANCE: `range(0, len(df))` with `iloc` is slow and
    # un-Pythonic.  Use `df.itertuples()` or, better still, vectorised
    # operations / `df.to_dict('records')`.
    for i in range(0, len(df)):
        row = df.iloc[i]
        data.append(
            {
                "id": row["customer_id"],
                "name": row["customer_name"],
                # ISSUE 4 — CORRECTNESS: `float(row['balance'])` will raise if
                # balance is NULL/NaN.  Handle missing values explicitly.
                "balance": float(row["balance"]),
            }
        )
    return data


def process_all_customers():
    all_ids = pd.read_sql("SELECT customer_id FROM customers", engine)
    results = []
    # ISSUE 5 — PERFORMANCE (N+1 query): Executes one SELECT per customer,
    # producing thousands of round-trips.  Fetch all data in a single query.
    # ISSUE 6 — MAINTAINABILITY: `id` shadows the built-in `id()` function.
    # Use a more descriptive variable name like `cust_id`.
    for id in all_ids["customer_id"]:
        results.append(get_customer_data(id))
    return results


# ═══════════════════════════════════════════════════════════════════════
# CORRECTED VERSION
# ═══════════════════════════════════════════════════════════════════════

import os  # noqa: E402

from sqlalchemy import create_engine, text  # noqa: E402

# Credentials from environment variables
_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://localhost:5432/finance",  # safe default for local dev
)
_engine = create_engine(_DB_URL)


def get_customer_data_v2(customer_id: str) -> list[dict]:
    # Not needed for the bulk mode, could be used for queries for individual customers
    """Return customer records for a single customer (parameterised query)."""
    query = text(
        "SELECT customer_id, customer_name, balance FROM customers WHERE customer_id = :cid"
    )
    df = pd.read_sql(query, _engine, params={"cid": customer_id})
    # Vectorised conversion; coerce NaN balances to 0.0
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce").fillna(0.0)
    return df.rename(columns={"customer_id": "id", "customer_name": "name"}).to_dict(
        "records"
    )


def process_all_customers_v2() -> list[dict]:
    """Fetch all customer data in a single query — no N+1 problem."""
    query = text("SELECT customer_id, customer_name, balance FROM customers")
    df = pd.read_sql(query, _engine)
    df["balance"] = pd.to_numeric(df["balance"], errors="coerce").fillna(0.0)
    return df.rename(columns={"customer_id": "id", "customer_name": "name"}).to_dict(
        "records"
    )
