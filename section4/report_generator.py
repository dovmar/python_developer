"""Section 4.2 — Reusable Reporting Framework."""

from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

# Default output directory is the script's location
SCRIPT_DIR = Path(__file__).parent


class ReportGenerator:
    """Render a pandas DataFrame into HTML, Excel, and plain-text reports."""

    def __init__(self, df: pd.DataFrame, template_path: str) -> None:
        self.df = df
        self.template_path = Path(template_path)

    # ── HTML ────────────────────────────────────────────────────────────

    def render_html(self, output_path: str, title: str = "Report") -> None:
        """Render the Jinja2 template with aggregate summary + full table."""
        env = Environment(
            loader=FileSystemLoader(str(self.template_path.parent)),
            autoescape=True,
        )
        template = env.get_template(self.template_path.name)

        summary = self._build_summary()
        html = template.render(
            title=title,
            summary=summary,
            columns=self.df.columns.tolist(),
            rows=self.df.values.tolist(),
        )
        out = Path(output_path)
        if not out.is_absolute():
            out = SCRIPT_DIR / out
        out.write_text(html, encoding="utf-8")

    # ── Excel ───────────────────────────────────────────────────────────

    def export_excel(self, output_path: str) -> None:
        """Export the DataFrame to an Excel workbook."""
        out = Path(output_path)
        if not out.is_absolute():
            out = SCRIPT_DIR / out
        self.df.to_excel(out, index=False, engine="openpyxl")

    # ── Plain text ──────────────────────────────────────────────────────

    def export_txt(self, output_path: str) -> None:
        """Export a human-readable plain-text report."""
        summary = self._build_summary()
        lines = ["=== Report Summary ==="]
        for key, value in summary.items():
            lines.append(f"  {key}: {value}")
        lines.append("")
        lines.append("=== Data ===")
        lines.append(self.df.to_string(index=False))
        out = Path(output_path)
        if not out.is_absolute():
            out = SCRIPT_DIR / out
        out.write_text("\n".join(lines), encoding="utf-8")

    # ── helpers ─────────────────────────────────────────────────────────

    def _build_summary(self) -> dict:
        """Build an aggregate summary dict from the DataFrame."""
        summary: dict = {"total_rows": len(self.df)}
        numeric_cols = self.df.select_dtypes(include="number")
        for col in numeric_cols.columns:
            summary[f"{col}_mean"] = round(numeric_cols[col].mean(), 2)
            summary[f"{col}_sum"] = round(numeric_cols[col].sum(), 2)
        return summary
