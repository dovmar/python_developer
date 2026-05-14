"""Section 2.2 — Benchmark: compare original, vectorised pandas, and Polars."""

import time

import numpy as np
import pandas as pd
import polars as pl

from section2.optimisation import (
    calculate_total_cost_original,
    calculate_total_cost_pandas,
    calculate_total_cost_polars,
)

ROWS = 5_000_000


def generate_dataset(n: int = ROWS) -> pd.DataFrame:
    """Create a synthetic DataFrame with n rows."""
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "agreement_id": [f"LN-{i:07d}" for i in range(n)],
            "customer_id": rng.choice(["C100", "C101", "C102", "C103"], n),
            "asset_type": rng.choice(["CAR", "FLEET", "EQUIPMENT"], n),
            "start_date": "2023-01-01",
            "end_date": "2026-01-01",
            "monthly_payment": rng.uniform(100, 2000, n).round(2),
            "currency": rng.choice(["EUR", "USD", "GBP"], n),
            "status": rng.choice(["active", "closed"], n, p=[0.8, 0.2]),
        }
    )


def bench(label: str, fn, *args, **kwargs) -> float:
    """Time a single execution and return elapsed seconds."""
    start = time.perf_counter()
    fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    print(f"  {label}: {elapsed:.3f}s")
    return elapsed


def main() -> None:
    print(f"Generating {ROWS:,} row dataset …")
    df_pd = generate_dataset()
    df_pl = pl.from_pandas(df_pd).lazy()

    print("\nBenchmark results:")

    # Only run the original on a small subset to avoid waiting forever
    ORIGINAL_SAMPLE = 50_000
    df_sample = df_pd.head(ORIGINAL_SAMPLE).copy()
    t_orig = bench(
        f"Original (iterrows, {ORIGINAL_SAMPLE:,} rows)",
        calculate_total_cost_original,
        df_sample,
    )

    t_pandas = bench(
        "Vectorised pandas  (5M rows)", calculate_total_cost_pandas, df_pd.copy()
    )
    t_polars = bench(
        "Polars lazy        (5M rows)",
        lambda: calculate_total_cost_polars(df_pl).collect(),
    )

    # Extrapolate original to 5M
    t_orig_est = t_orig * (ROWS / ORIGINAL_SAMPLE)
    print(f"\n  Original estimated for 5M rows: {t_orig_est:.1f}s")
    print(f"  Pandas speedup vs original:  ~{t_orig_est / t_pandas:.0f}×")
    print(f"  Polars speedup vs original:  ~{t_orig_est / t_polars:.0f}×")


if __name__ == "__main__":
    main()
