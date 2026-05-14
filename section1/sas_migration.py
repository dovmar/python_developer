"""Section 1.2 — SAS-to-Python Migration: monthly risk exposure score."""

from section1.cleaning import CSV_PATH, clean_agreements

import pandas as pd


def calculate_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate the SAS risk-score logic using idiomatic pandas.

    For each customer_id, computes:
      - total_exposure: sum of monthly_payment for active agreements
      - agreement_count: number of active agreements
      - avg_exposure: total_exposure / agreement_count (0 when no active agreements)

    Returns one row per customer_id.
    """
    # Filter to active agreements only for the aggregation
    active = df[df["status"].str.lower() == "active"]

    # Aggregate per customer
    agg = active.groupby("customer_id", as_index=False).agg(
        total_exposure=("monthly_payment", "sum"),
        agreement_count=("monthly_payment", "count"),
    )

    # Ensure every customer_id present in the original data appears in the output
    all_customers = df[["customer_id"]].drop_duplicates()
    result = all_customers.merge(agg, on="customer_id", how="left")

    # Customers with no active agreements get zeros
    result["total_exposure"] = result["total_exposure"].fillna(0)
    result["agreement_count"] = result["agreement_count"].fillna(0).astype(int)
    result["avg_exposure"] = result.apply(
        lambda r: (
            r["total_exposure"] / r["agreement_count"]
            if r["agreement_count"] > 0
            else 0
        ),
        axis=1,
    )

    return result[["customer_id", "total_exposure", "agreement_count", "avg_exposure"]]


if __name__ == "__main__":
    cleaned = clean_agreements(csv_path=CSV_PATH)
    scores = calculate_risk_scores(cleaned)
    print(scores.to_string(index=False))
