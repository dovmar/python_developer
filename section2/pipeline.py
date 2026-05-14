"""Section 2.1 — ETL Pipeline: extract → transform → load."""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from section1.cleaning import CSV_PATH, clean_agreements, summarise_errors
from section1.sas_migration import calculate_risk_scores

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)

DB_PATH = Path(__file__).parent / "pipeline.db"
DB_URL = f"sqlite:///{DB_PATH}"


class AgreementPipeline:
    """Idempotent ETL pipeline for loan-agreement data."""

    def __init__(self, db_url: str = DB_URL):
        self.engine = create_engine(db_url)
        self._raw: pd.DataFrame | None = None
        self._cleaned: pd.DataFrame | None = None
        self._risk_scores: pd.DataFrame | None = None

    # ── seed ────────────────────────────────────────────────────────────

    def seed(self) -> None:
        """Create and populate the source table (if it doesn't already exist)."""
        raw = pd.read_csv(CSV_PATH)
        raw.to_sql("raw_agreements", self.engine, if_exists="replace", index=False)
        logger.info("Seeded raw_agreements table (%d rows).", len(raw))

    # ── extract ─────────────────────────────────────────────────────────

    def extract(self) -> pd.DataFrame:
        """Read raw records from the SQLite source table."""
        with self.engine.connect() as conn:
            self._raw = pd.read_sql(text("SELECT * FROM raw_agreements"), conn)
        logger.info("Extracted %d raw records.", len(self._raw))
        return self._raw

    # ── transform ───────────────────────────────────────────────────────

    def transform(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Apply cleaning and risk-score logic."""
        if self._raw is None:
            raise RuntimeError("Call extract() before transform().")

        self._cleaned = clean_agreements(self._raw)
        self._risk_scores = calculate_risk_scores(self._cleaned)
        logger.info(
            "Transform complete — %d cleaned rows, %d risk-score rows.",
            len(self._cleaned),
            len(self._risk_scores),
        )
        return self._cleaned, self._risk_scores

    # ── load ────────────────────────────────────────────────────────────

    def load(
        self, excel_path: str = "report.xlsx", txt_path: str = "report.txt"
    ) -> None:
        """Write results to SQLite, Excel, and a plain-text summary."""
        if self._cleaned is None or self._risk_scores is None:
            raise RuntimeError("Call transform() before load().")

        # 1. SQLite — replace ensures idempotency
        self._cleaned.to_sql(
            "processed_agreements",
            self.engine,
            if_exists="replace",
            index=False,
        )
        logger.info("Loaded processed_agreements table.")

        # 2. Excel — one sheet per asset_type
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for asset_type, group in self._cleaned.groupby("asset_type"):
                group.to_excel(writer, sheet_name=str(asset_type), index=False)
        logger.info("Written Excel report to %s.", excel_path)

        # 3. Plain-text run summary
        errors = summarise_errors(self._cleaned)
        lines = [
            "=== Pipeline Run Summary ===",
            f"Total records processed: {len(self._cleaned)}",
            "",
            "Error flag counts:",
        ]
        for flag, count in errors.items():
            lines.append(f"  {flag}: {count}")
        lines.append("")
        lines.append("Risk-score aggregates:")
        lines.append(
            self._risk_scores.to_string(index=False),
        )
        Path(txt_path).write_text("\n".join(lines), encoding="utf-8")
        logger.info("Written text summary to %s.", txt_path)

    # ── run (full pipeline) ─────────────────────────────────────────────

    def run(self) -> None:
        """Execute the full extract → transform → load pipeline."""
        self.seed()
        self.extract()
        self.transform()
        self.load()
        logger.info("Pipeline finished successfully.")


if __name__ == "__main__":
    AgreementPipeline().run()
