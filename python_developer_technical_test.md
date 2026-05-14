# Technical Test: Senior Python Developer (Data Engineer)
### Asset Finance — Danske Bank

**Estimated time:** 2 hours  
**Submission:** Push your solution to a  GitHub repository and share access with the interviewer.
** AI assistance: ** Allowed, but please disclose any significant AI-generated code in your README and remember that your code will be reviewed for quality and correctness, so blindly accepting AI suggestions without understanding them may lead to issues.

---

## Instructions

- Write production-grade code: clean, readable, tested, and documented where appropriate.
- You may use any standard Python libraries plus: `pandas`, `polars`, `pyspark`, `sqlalchemy`, `numpy`, `openpyxl`, `jinja2`, `pytest`.
- Each section is independent — you do not need to complete them in order.
- Where choices are made (e.g. data structure, algorithm), briefly justify them in a comment or README section.

---

## Section 1 — Python & Data Processing Fundamentals (30 pts)

### 1.1 — Data Cleaning Pipeline (15 pts)

You receive a raw CSV export from a legacy system. Its contents (provided inline below) represent **loan agreements** in the Asset Finance domain.

```
agreement_id,customer_id,asset_type,start_date,end_date,monthly_payment,currency,status
LN-001,C100,CAR,2022-01-15,2025-01-15,450.00,EUR,active
LN-002,C101,EQUIPMENT,,2024-06-01,1200.5,eur,ACTIVE
LN-003,C102,FLEET,2021-03-01,2024-03-01,800,USD,closed
LN-004,C100,CAR,2023-07-01,2026-07-01,450.00,EUR,active
LN-005,,CAR,2022-11-01,2025-11-01,300.00,EUR,active
LN-006,C104,EQUIPMENT,2023-01-01,2022-01-01,950.00,EUR,active
LN-007,C105,FLEET,2023-05-01,2026-05-01,-200.00,EUR,active
LN-008,C106,CAR,not-a-date,2025-09-01,560.00,EUR,active
```

**Tasks:**

1. Load the data and implement a `clean_agreements(df: pd.DataFrame) -> pd.DataFrame` function that:
   - Normalises `currency` to uppercase and `status` to lowercase.
   - Parses `start_date` and `end_date` as dates; rows with unparseable dates should be **flagged** (add a boolean column `has_date_error`) rather than dropped.
   - Validates that `end_date > start_date`; flag violations in a `has_date_logic_error` column.
   - Validates that `monthly_payment > 0`; flag violations in `has_payment_error`.
   - Fills missing `customer_id` with the string `"UNKNOWN"`.
   - Returns the full dataset (no rows dropped) with all flag columns added.

2. Write a `summarise_errors(df: pd.DataFrame) -> dict` function that returns a dictionary with the count of each error type.

3. Write **at least 4 unit tests** using `pytest` covering edge cases (e.g. all-valid input, all-invalid input, mixed).

---

### 1.2 — SAS-to-Python Migration (15 pts)

The following SAS snippet calculates a **monthly risk exposure score** per customer. Translate it into an equivalent, idiomatic Python/pandas function.

```sas
DATA risk_scores;
    SET agreements;
    BY customer_id;

    IF first.customer_id THEN DO;
        total_exposure = 0;
        agreement_count = 0;
    END;

    IF status = 'active' THEN DO;
        total_exposure + monthly_payment;
        agreement_count + 1;
    END;

    IF last.customer_id THEN DO;
        IF agreement_count > 0 THEN
            avg_exposure = total_exposure / agreement_count;
        ELSE
            avg_exposure = 0;
        OUTPUT;
    END;
RUN;
```

**Tasks:**

1. Implement `calculate_risk_scores(df: pd.DataFrame) -> pd.DataFrame` that replicates the logic above and returns one row per `customer_id` with columns: `customer_id`, `total_exposure`, `agreement_count`, `avg_exposure`.
2. Ensure the function handles customers with no active agreements (result should show `avg_exposure = 0`).
3. Write 3 unit tests.

---

## Section 2 — Data Pipelines & Architecture (30 pts)

### 2.1 — Pipeline Design (15 pts)

Design and implement a small **ETL pipeline class** that:

- **Extracts** loan agreement records from a SQLite database (you must create and seed the DB as part of your solution).
- **Transforms** the data: apply the cleaning logic from Section 

1.1 and compute the risk scores from Section 1.2.
- **Loads** the transformed results into:
  - A second SQLite table `processed_agreements`.
  - An Excel file `report.xlsx` (one sheet per `asset_type`).

- A plain text file `report.txt` containing a concise run summary (total records processed, number of records with each error flag, and risk score aggregates).

Requirements:
- The pipeline must be **idempotent** — re-running it should not create duplicates.
- Use **SQLAlchemy** for all database interactions (no raw `sqlite3` calls).
- Structure your code as a class `AgreementPipeline` with at least the methods `extract()`, `transform()`, `load()`, and `run()`.
- Include basic logging (use Python's `logging` module, not `print`).

---

### 2.2 — Performance Optimisation (15 pts)

You are given the following slow pandas code that runs on a DataFrame with ~5 million rows:

```python
def calculate_total_cost(df):
    results = []
    for _, row in df.iterrows():
        if row['status'] == 'active' and row['currency'] == 'EUR':
            cost = row['monthly_payment'] * 12
            if row['asset_type'] == 'CAR':
                cost *= 0.95  # 5% discount
            elif row['asset_type'] == 'FLEET':
                cost *= 0.90  # 10% discount
        else:
            cost = 0
        results.append(cost)
    df['annual_cost'] = results
    return df
```

**Tasks:**

1. Rewrite this function using **vectorised pandas operations** (no loops).
2. Additionally, provide an alternative implementation using **Polars** (lazy evaluation preferred).
3. Benchmark both your pandas and Polars implementations against the original on a generated dataset of 5,000,000 rows and include the benchmark results in your README.
4. Briefly explain (2–4 sentences) why the original implementation is slow and what makes your solution faster.

---

## Section 3 — SQL & Databases (20 pts)

Given the following schema:

```sql
CREATE TABLE customers (
    customer_id   VARCHAR(20) PRIMARY KEY,
    country       VARCHAR(3),
    segment       VARCHAR(50)  -- e.g. 'RETAIL', 'CORPORATE'
);

CREATE TABLE agreements (
    agreement_id      VARCHAR(20) PRIMARY KEY,
    customer_id       VARCHAR(20) REFERENCES customers(customer_id),
    asset_type        VARCHAR(20),
    start_date        DATE,
    end_date          DATE,
    monthly_payment   DECIMAL(12,2),
    currency          CHAR(3),
    status            VARCHAR(20)
);

CREATE TABLE payments (
    payment_id    SERIAL PRIMARY KEY,
    agreement_id  VARCHAR(20) REFERENCES agreements(agreement_id),
    payment_date  DATE,
    amount_paid   DECIMAL(12,2),
    is_late       BOOLEAN
);
```

Write SQL queries for the following:

### 3.1
Return each customer's **total active exposure** (sum of `monthly_payment` for active agreements in EUR), only for customers in the `'CORPORATE'` segment with at least 2 active agreements. Include `customer_id`, `country`, `agreement_count`, and `total_monthly_exposure`. Order by `total_monthly_exposure` descending.

### 3.2
For each `asset_type`, calculate the **late payment rate**: the percentage of payments that are late, rounded to 2 decimal places. Only include asset types where the total number of payments exceeds 100.

### 3.3
Find all **customers who have made no payments in the last 90 days** but still have at least one active agreement. Return `customer_id`, `segment`, and `last_payment_date` (NULL if never paid). Use today's date as `CURRENT_DATE`.

### 3.4
Rewrite the query below to **eliminate the performance bottleneck** and explain what was wrong:

```sql
SELECT *
FROM agreements a
WHERE (SELECT COUNT(*) FROM payments p WHERE p.agreement_id = a.agreement_id) > 5
  AND UPPER(a.status) = 'ACTIVE'
  AND YEAR(a.start_date) = 2023;
```

---

## Section 4 — Code Quality & Engineering Standards (20 pts)

### 4.1 — Code Review (10 pts)

Review the following code snippet and provide your feedback as inline comments. Identify at least **6 distinct issues** (correctness, security, performance, maintainability, Python best practices).

```python
import pandas as pd
import sqlalchemy

engine = sqlalchemy.create_engine("postgresql://admin:password123@prod-db:5432/finance")

def get_customer_data(customer_id):
    query = "SELECT * FROM customers WHERE customer_id = '" + customer_id + "'"
    df = pd.read_sql(query, engine)
    data = []
    for i in range(0, len(df)):
        row = df.iloc[i]
        data.append({
            'id': row['customer_id'],
            'name': row['customer_name'],
            'balance': float(row['balance'])
        })
    return data

def process_all_customers():
    all_ids = pd.read_sql("SELECT customer_id FROM customers", engine)
    results = []
    for id in all_ids['customer_id']:
        results.append(get_customer_data(id))
    return results
```

Submit your review as a Python file with the original code annotated with `# ISSUE:` comments, plus a rewritten corrected version below it.

---

### 4.2 — Reusable Framework Design (10 pts)

The team needs a small **reusable reporting framework** that:

- Accepts a pandas DataFrame and a **Jinja2 HTML template**.
- Renders the template with the DataFrame's data (aggregate summary + full table).
- Saves the output as an HTML file.
- Supports an optional **Excel export** of the same data alongside the HTML.
- Supports an optional **plain text (.txt) export** of the same data (human-readable summary + tabular section) alongside the HTML.

Implement a `ReportGenerator` class with at least:
- `__init__(self, df: pd.DataFrame, template_path: str)`
- `render_html(self, output_path: str, title: str = "Report") -> None`
- `export_excel(self, output_path: str) -> None`
- `export_txt(self, output_path: str) -> None`

Include a sample Jinja2 template (`template.html`) and a usage example script (`example.py`).

---

## Evaluation Criteria

| Area | Weight | What we look at |
|---|---|---|
| Correctness | 30% | Does the code produce correct results? Are edge cases handled? |
| Code Quality | 25% | Readability, structure, naming, no dead code |
| Testing | 20% | Coverage, meaningful assertions, edge cases |
| Performance | 15% | Efficient use of pandas/Polars, no unnecessary loops |
| Architecture | 10% | Design decisions, separation of concerns, extensibility |

---

## Deliverables

Your repository should contain:

```
.
├── README.md               # Setup instructions, design decisions, benchmark results
├── requirements.txt
├── section1/
│   ├── cleaning.py
│   ├── sas_migration.py
│   └── tests/
│       └── test_cleaning.py
│       └── test_sas_migration.py
├── section2/
│   ├── pipeline.py
│   ├── optimisation.py
│   └── benchmark.py
├── section3/
│   └── queries.sql
└── section4/
    ├── code_review.py
    ├── report_generator.py
    ├── template.html
    ├── example.py
    └── sample_report.txt
```

Good luck!
