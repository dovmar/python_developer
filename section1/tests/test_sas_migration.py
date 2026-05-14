"""Unit tests for section1.sas_migration — 3 tests."""

import pandas as pd

from ..sas_migration import calculate_risk_scores


def _make_df(rows: list[dict]) -> pd.DataFrame:
    cols = [
        "agreement_id",
        "customer_id",
        "asset_type",
        "start_date",
        "end_date",
        "monthly_payment",
        "currency",
        "status",
    ]
    return pd.DataFrame(rows, columns=cols)


# ── Test 1: single customer with active agreements ───────────────────────


def test_single_customer_active():
    df = _make_df(
        [
            {
                "agreement_id": "LN-001",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "2022-01-01",
                "end_date": "2025-01-01",
                "monthly_payment": 400.0,
                "currency": "EUR",
                "status": "active",
            },
            {
                "agreement_id": "LN-002",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "2023-01-01",
                "end_date": "2026-01-01",
                "monthly_payment": 600.0,
                "currency": "EUR",
                "status": "active",
            },
        ]
    )
    result = calculate_risk_scores(df)
    assert len(result) == 1
    assert result.iloc[0]["total_exposure"] == 1000.0
    assert result.iloc[0]["agreement_count"] == 2
    assert result.iloc[0]["avg_exposure"] == 500.0


# ── Test 2: customer with no active agreements ────────────────────────────


def test_customer_no_active():
    """Customers with only closed agreements should have avg_exposure = 0."""
    df = _make_df(
        [
            {
                "agreement_id": "LN-001",
                "customer_id": "C200",
                "asset_type": "CAR",
                "start_date": "2020-01-01",
                "end_date": "2023-01-01",
                "monthly_payment": 500.0,
                "currency": "EUR",
                "status": "closed",
            },
        ]
    )
    result = calculate_risk_scores(df)
    assert len(result) == 1
    assert result.iloc[0]["total_exposure"] == 0
    assert result.iloc[0]["agreement_count"] == 0
    assert result.iloc[0]["avg_exposure"] == 0


# ── Test 3: multiple customers, mixed statuses ───────────────────────────


def test_multiple_customers_mixed():
    df = _make_df(
        [
            {
                "agreement_id": "LN-001",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "2022-01-01",
                "end_date": "2025-01-01",
                "monthly_payment": 300.0,
                "currency": "EUR",
                "status": "active",
            },
            {
                "agreement_id": "LN-002",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "2020-01-01",
                "end_date": "2023-01-01",
                "monthly_payment": 200.0,
                "currency": "EUR",
                "status": "closed",
            },
            {
                "agreement_id": "LN-003",
                "customer_id": "C200",
                "asset_type": "FLEET",
                "start_date": "2023-01-01",
                "end_date": "2026-01-01",
                "monthly_payment": 1000.0,
                "currency": "EUR",
                "status": "active",
            },
        ]
    )
    result = calculate_risk_scores(df)
    assert len(result) == 2

    c100 = result[result["customer_id"] == "C100"].iloc[0]
    assert c100["total_exposure"] == 300.0
    assert c100["agreement_count"] == 1
    assert c100["avg_exposure"] == 300.0

    c200 = result[result["customer_id"] == "C200"].iloc[0]
    assert c200["total_exposure"] == 1000.0
    assert c200["agreement_count"] == 1
    assert c200["avg_exposure"] == 1000.0
