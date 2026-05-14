"""Section 2.2 — Performance Optimisation: vectorised pandas + Polars."""

import pandas as pd
import polars as pl


# ── Original (slow) implementation ──────────────────────────────────────


def calculate_total_cost_original(df: pd.DataFrame) -> pd.DataFrame:
    """Row-by-row loop — provided as the baseline."""
    results = []
    for _, row in df.iterrows():
        if row["status"] == "active" and row["currency"] == "EUR":
            cost = row["monthly_payment"] * 12
            if row["asset_type"] == "CAR":
                cost *= 0.95  # 5 % discount
            elif row["asset_type"] == "FLEET":
                cost *= 0.90  # 10 % discount
        else:
            cost = 0
        results.append(cost)
    df["annual_cost"] = results
    return df


# ── Vectorised pandas implementation ───────────────────────────────────


def calculate_total_cost_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """Fully vectorised — no Python-level loops.

    Uses boolean masking and np.select-style conditional assignment via
    pandas where/multiply to compute annual_cost in a single pass.
    """
    df = df.copy()

    is_active_eur = (df["status"] == "active") & (df["currency"] == "EUR")

    base_cost = df["monthly_payment"] * 12

    # Build a discount multiplier column: CAR → 0.95, FLEET → 0.90, else → 1.0
    discount = pd.Series(1.0, index=df.index)
    discount = discount.where(df["asset_type"] != "CAR", 0.95)
    discount = discount.where(df["asset_type"] != "FLEET", 0.90)

    df["annual_cost"] = (base_cost * discount).where(is_active_eur, 0)
    return df


# ── Polars (lazy) implementation ───────────────────────────────────────


def calculate_total_cost_polars(df: pl.LazyFrame) -> pl.LazyFrame:
    """Polars lazy implementation with when/then/otherwise expressions."""
    return df.with_columns(
        pl.when((pl.col("status") == "active") & (pl.col("currency") == "EUR"))
        .then(
            pl.col("monthly_payment")
            * 12
            * pl.when(pl.col("asset_type") == "CAR")
            .then(pl.lit(0.95))
            .when(pl.col("asset_type") == "FLEET")
            .then(pl.lit(0.90))
            .otherwise(pl.lit(1.0))
        )
        .otherwise(pl.lit(0.0))
        .alias("annual_cost")
    )
