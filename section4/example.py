"""Example usage of the ReportGenerator (Section 4.2)."""

from pathlib import Path

import pandas as pd

from .report_generator import ReportGenerator

TEMPLATE = Path(__file__).parent / "template.html"

# Sample data
df = pd.DataFrame(
    {
        "agreement_id": ["LN-001", "LN-002", "LN-003"],
        "customer_id": ["C100", "C101", "C102"],
        "asset_type": ["CAR", "EQUIPMENT", "FLEET"],
        "monthly_payment": [450.00, 1200.50, 800.00],
        "status": ["active", "active", "closed"],
    }
)

if __name__ == "__main__":
    rg = ReportGenerator(df, str(TEMPLATE))

    rg.render_html("sample_report.html", title="Loan Agreements Report")
    print("HTML report written to sample_report.html")

    rg.export_excel("sample_report.xlsx")
    print("Excel report written to sample_report.xlsx")

    rg.export_txt("sample_report.txt")
    print("Text report written to sample_report.txt")
