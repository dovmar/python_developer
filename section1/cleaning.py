"""Section 1.1 — Data Cleaning Pipeline for loan agreement records."""

from pathlib import Path

import pandas as pd


CSV_PATH = Path(__file__).parent / "agreements.csv"


def clean_normalise_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise ``currency`` column to uppercase."""
    df["currency"] = df["currency"].str.upper()
    return df


def clean_normalise_status(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise ``status`` column to lowercase."""
    df["status"] = df["status"].str.lower()
    return df


def clean_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse ``start_date`` and ``end_date`` as datetime, coercing failures to NaT."""
    df["start_date"] = pd.to_datetime(df["start_date"], format="mixed", errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], format="mixed", errors="coerce")
    return df


def clean_flag_date_errors(df: pd.DataFrame) -> pd.DataFrame:
    """Flag rows where either date could not be parsed (including missing)."""
    df["has_date_error"] = df["start_date"].isna() | df["end_date"].isna()
    return df


def clean_flag_date_logic_errors(df: pd.DataFrame) -> pd.DataFrame:
    """Flag rows where ``end_date <= start_date`` (only when both dates exist)."""
    both_dates = df["start_date"].notna() & df["end_date"].notna()
    df["has_date_logic_error"] = both_dates & (df["end_date"] <= df["start_date"])
    return df


def clean_flag_payment_errors(df: pd.DataFrame) -> pd.DataFrame:
    """Flag rows where ``monthly_payment`` is not positive."""
    df["has_payment_error"] = df["monthly_payment"] <= 0
    return df


def clean_fill_missing_customer_id(df: pd.DataFrame) -> pd.DataFrame:
    """Replace missing ``customer_id`` values with ``'UNKNOWN'``."""
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")
    return df


def clean_agreements(
    df: pd.DataFrame | None = None,
    *,
    csv_path: str | Path | None = None,
) -> pd.DataFrame:
    """Clean and validate loan agreement data.

    Args:
        df: Raw loan-agreement DataFrame. If ``None``, the data is read
            from *csv_path*.
        csv_path: Path to the CSV file to read when *df* is not supplied.
            Must be provided explicitly if *df* is ``None``.

    Returns:
        The full dataset with boolean flag columns added for each
        validation rule — no rows are dropped.

    Raises:
        ValueError: If *df* is ``None`` and *csv_path* is not provided.
    """
    if df is None:
        if csv_path is None:
            raise ValueError("csv_path must be provided when df is None")
        df = pd.read_csv(csv_path)
    else:
        df = df.copy()

    df = clean_normalise_currency(df)
    df = clean_normalise_status(df)
    df = clean_parse_dates(df)
    df = clean_flag_date_errors(df)
    df = clean_flag_date_logic_errors(df)
    df = clean_flag_payment_errors(df)
    df = clean_fill_missing_customer_id(df)

    return df


def summarise_errors(df: pd.DataFrame) -> dict:
    """Return a dictionary with the count of each error type.

    Automatically detects all boolean columns whose names start with
    ``has_`` and end with ``_error``, so new flag columns added to
    ``clean_agreements`` are picked up without changes here.

    Args:
        df: A cleaned DataFrame produced by ``clean_agreements``.

    Returns:
        Mapping of error-column name to the integer count of ``True`` values.
    """
    error_cols = [
        c for c in df.columns if c.startswith("has_") and c.endswith("_error")
    ]
    return {col: int(df[col].sum()) for col in error_cols}


if __name__ == "__main__":
    cleaned = clean_agreements(csv_path=CSV_PATH)
    print(cleaned.to_string())
    print("Error summary:", summarise_errors(cleaned))
