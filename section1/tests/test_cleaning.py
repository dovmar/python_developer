"""Unit tests for section1.cleaning — at least 4 edge-case tests."""

import pandas as pd

from ..cleaning import clean_agreements, summarise_errors


def _make_df(rows: list[dict]) -> pd.DataFrame:
    """Helper to build a DataFrame from a list of row dicts."""
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


# ── Test 1: all-valid input ────────────────────────────────────────────────


def test_all_valid_no_flags():
    """When every field is valid, no error flags should be True."""
    df = _make_df(
        [
            {
                "agreement_id": "LN-001",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "2022-01-01",
                "end_date": "2025-01-01",
                "monthly_payment": 500.0,
                "currency": "EUR",
                "status": "active",
            },
        ]
    )
    result = clean_agreements(df)
    assert result["has_date_error"].sum() == 0
    assert result["has_date_logic_error"].sum() == 0
    assert result["has_payment_error"].sum() == 0


# ── Test 2: all-invalid input ──────────────────────────────────────────────


def test_all_invalid_flags_set():
    """Row with every possible error should flag all columns."""
    df = _make_df(
        [
            {
                "agreement_id": "LN-BAD",
                "customer_id": None,
                "asset_type": "CAR",
                "start_date": "not-a-date",
                "end_date": "also-bad",
                "monthly_payment": -100.0,
                "currency": "eur",
                "status": "ACTIVE",
            },
        ]
    )
    result = clean_agreements(df)
    assert result["has_date_error"].iloc[0]
    assert result["has_payment_error"].iloc[0]
    # With both dates unparseable, date logic error is False (needs two valid dates)
    assert not result["has_date_logic_error"].iloc[0]
    # Missing customer_id should be filled
    assert result["customer_id"].iloc[0] == "UNKNOWN"


# ── Test 3: mixed valid/invalid rows ──────────────────────────────────────


def test_mixed_rows_preserves_all():
    """No rows should be dropped; flags should be set row-by-row."""
    df = _make_df(
        [
            {
                "agreement_id": "LN-001",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "2022-01-01",
                "end_date": "2025-01-01",
                "monthly_payment": 500.0,
                "currency": "EUR",
                "status": "active",
            },
            {
                "agreement_id": "LN-002",
                "customer_id": "C101",
                "asset_type": "CAR",
                "start_date": "2023-01-01",
                "end_date": "2022-01-01",
                "monthly_payment": 300.0,
                "currency": "eur",
                "status": "ACTIVE",
            },
        ]
    )
    result = clean_agreements(df)
    assert len(result) == 2
    assert result["has_date_logic_error"].iloc[1]
    assert not result["has_date_logic_error"].iloc[0]


# ── Test 4: normalisation ─────────────────────────────────────────────────


def test_currency_and_status_normalised():
    """currency should be uppercase, status should be lowercase."""
    df = _make_df(
        [
            {
                "agreement_id": "LN-001",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "2022-01-01",
                "end_date": "2025-01-01",
                "monthly_payment": 500.0,
                "currency": "eur",
                "status": "ACTIVE",
            },
        ]
    )
    result = clean_agreements(df)
    assert result["currency"].iloc[0] == "EUR"
    assert result["status"].iloc[0] == "active"


# ── Test 5: summarise_errors counts ──────────────────────────────────────


def test_summarise_errors():
    """summarise_errors returns correct counts for each flag."""
    df = _make_df(
        [
            {
                "agreement_id": "LN-001",
                "customer_id": "C100",
                "asset_type": "CAR",
                "start_date": "bad",
                "end_date": "2025-01-01",
                "monthly_payment": -10.0,
                "currency": "EUR",
                "status": "active",
            },
            {
                "agreement_id": "LN-002",
                "customer_id": "C101",
                "asset_type": "CAR",
                "start_date": "2023-01-01",
                "end_date": "2022-01-01",
                "monthly_payment": 100.0,
                "currency": "EUR",
                "status": "active",
            },
        ]
    )
    result = clean_agreements(df)
    summary = summarise_errors(result)
    assert summary["has_date_error"] == 1
    assert summary["has_date_logic_error"] == 1
    assert summary["has_payment_error"] == 1


# ── Test 6: missing customer_id filled ────────────────────────────────────


def test_missing_customer_id_filled():
    """Null customer_id values should be replaced with 'UNKNOWN'."""
    df = _make_df(
        [
            {
                "agreement_id": "LN-005",
                "customer_id": None,
                "asset_type": "CAR",
                "start_date": "2022-11-01",
                "end_date": "2025-11-01",
                "monthly_payment": 300.0,
                "currency": "EUR",
                "status": "active",
            },
        ]
    )
    result = clean_agreements(df)
    assert result["customer_id"].iloc[0] == "UNKNOWN"
