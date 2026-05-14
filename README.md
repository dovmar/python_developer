# Technical Test — Senior Python Developer (Data Engineer)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Code Formatting

This project uses [ruff](https://docs.astral.sh/ruff/) for code formatting and linting.

```bash
# Format all files
python -m ruff format .

# Check for lint issues
python -m ruff check .
```

## Running

```bash
# Section 1 — SAS migration
python -m section1.sas_migration

# Section 1 tests
pytest section1/tests/ -v

# Section 2 — ETL pipeline
python -m section2.pipeline

# Section 2 — Benchmark (warning: generates 5M rows, takes a minute+)
python -m section2.benchmark

# Section 4 — Example report
python -m section4.example
```

---

## Design Decisions

### Section 1 — Data Cleaning

- **Flag-don't-drop**: all validation issues are recorded as boolean columns (`has_date_error`, `has_date_logic_error`, `has_payment_error`) so downstream consumers can decide how to handle them.
- `pd.to_datetime(errors="coerce")` converts unparseable strings to `NaT`, making null-checking straightforward.
- `customer_id` blanks are filled with `"UNKNOWN"` to maintain referential traceability.

### Section 1.2 — SAS Migration

- The SAS `BY`-group accumulator pattern maps directly to `groupby().agg()` in pandas.
- A left join back to the full customer set ensures customers with no active agreements still appear with `avg_exposure = 0`.

### Section 2.1 — Pipeline

- **Idempotency** is achieved by using `if_exists="replace"` when writing SQLite tables and overwriting output files.
- SQLAlchemy `text()` is used for all queries.
- Python `logging` replaces `print` for production traceability.

### Section 2.2 — Performance Optimisation

- **Why the original is slow**: `df.iterrows()` converts each row to a Python `Series` object, adding massive per-row overhead. The Python-level `if/elif` branching cannot exploit CPU vectorisation or columnar memory layout.
- **Vectorised pandas** replaces the loop with boolean masks and `Series.where()`, operating on entire columns in compiled C/NumPy code — typically 50–200× faster.
- **Polars** uses lazy evaluation with a query planner that can fuse, predicate-push-down, and parallelise operations across CPU cores, often beating pandas on large datasets.

### Benchmark Results

_(Results from a single run on an Intel i7 / 16 GB RAM machine — your numbers will vary.)_

| Implementation | Rows | Time |
|---|---|---|
| Original (`iterrows`) | 50 000 | ~4.5 s |
| Original (extrapolated) | 5 000 000 | ~450 s |
| Vectorised pandas | 5 000 000 | ~0.15 s |
| Polars (lazy) | 5 000 000 | ~0.08 s |

> Run `python -m section2.benchmark` to reproduce on your hardware.

### Section 3 — SQL

- Query 3.4 eliminates three performance bottlenecks: a correlated subquery (replaced by `JOIN … GROUP BY … HAVING`), `UPPER()` on the status column (use literal match), and `YEAR()` on `start_date` (use a range predicate). Both function wraps prevented index usage.

### Section 4.1 — Code Review

Six issues identified (see `section4/code_review.py` for inline annotations):

1. Hard-coded credentials in source code.
2. SQL injection via string concatenation.
3. Slow `range(len(df))` + `iloc` loop.
4. Unhandled `NaN` in `float()` cast.
5. N+1 query pattern (one SELECT per customer).
6. Shadowing built-in `id`.

### Section 4.2 — Report Generator

- The summary dict is auto-generated from numeric columns so the framework works with any DataFrame shape.

---

## AI Disclosure

GitHub Copilot was used as a coding assistant during development. All generated code was reviewed, tested, and adapted to meet the specific requirements of this test.
