-- =============================================================================
-- Section 3 — SQL & Databases
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 3.1 — Customer Total Active Exposure (CORPORATE segment)
-- -----------------------------------------------------------------------------
-- Return each customer's total active exposure (sum of monthly_payment for 
-- active agreements in EUR), only for customers in the 'CORPORATE' segment 
-- with at least 2 active agreements.
-- Include: customer_id, country, agreement_count, total_monthly_exposure
-- Order by: total_monthly_exposure descending
-- -----------------------------------------------------------------------------

SELECT
    c.customer_id,
    c.country,
    COUNT(*)               AS agreement_count,
    SUM(a.monthly_payment) AS total_monthly_exposure
FROM customers  c
JOIN agreements a ON a.customer_id = c.customer_id
WHERE c.segment  = 'CORPORATE'
  AND a.status   = 'active'
  AND a.currency = 'EUR'
GROUP BY c.customer_id, c.country
HAVING COUNT(*) >= 2
ORDER BY total_monthly_exposure DESC;


-- -----------------------------------------------------------------------------
-- 3.2 — Late Payment Rate by Asset Type
-- -----------------------------------------------------------------------------
-- For each asset_type, calculate the late payment rate: percentage of payments 
-- that are late, rounded to 2 decimal places.
-- Only include asset types where total number of payments exceeds 100.
-- -----------------------------------------------------------------------------

SELECT
    a.asset_type,
    ROUND(
        SUM(CASE WHEN p.is_late THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS late_payment_rate
FROM payments   p
JOIN agreements a ON a.agreement_id = p.agreement_id
GROUP BY a.asset_type
HAVING COUNT(*) > 100;

-- Note: Multiplied by 100.0 (with decimal) before division to ensure floating-
-- point arithmetic and avoid integer division issues in some SQL engines.


-- -----------------------------------------------------------------------------
-- 3.3 — Customers with No Recent Payments but Active Agreements
-- -----------------------------------------------------------------------------
-- Find all customers who have made no payments in the last 90 days but still 
-- have at least one active agreement.
-- Return: customer_id, segment, last_payment_date (NULL if never paid)
-- Use today's date as CURRENT_DATE.
-- -----------------------------------------------------------------------------

SELECT
    c.customer_id,
    c.segment,
    lp.last_payment_date
FROM customers c
JOIN agreements a ON a.customer_id = c.customer_id AND a.status = 'active'
LEFT JOIN (
    SELECT
        ag.customer_id,
        MAX(p.payment_date) AS last_payment_date
    FROM payments   p
    JOIN agreements ag ON ag.agreement_id = p.agreement_id
    GROUP BY ag.customer_id
) lp ON lp.customer_id = c.customer_id
GROUP BY c.customer_id, c.segment, lp.last_payment_date
HAVING lp.last_payment_date IS NULL
    OR lp.last_payment_date < DATE('now', '-90 days');

-- Note: The subquery aggregates the most recent payment per customer across all
-- their agreements, then we filter for those with no payments or stale payments.
-- GROUP BY on the outer query ensures one row per customer when they have 
-- multiple active agreements.


-- -----------------------------------------------------------------------------
-- 3.4 — Performance Optimisation
-- -----------------------------------------------------------------------------
-- Rewrite the query below to eliminate the performance bottleneck.
-- -----------------------------------------------------------------------------

-- ORIGINAL (slow) QUERY:
-- SELECT *
-- FROM agreements a
-- WHERE (SELECT COUNT(*) FROM payments p WHERE p.agreement_id = a.agreement_id) > 5
--   AND UPPER(a.status) = 'ACTIVE'
--   AND YEAR(a.start_date) = 2023;

-- ISSUES WITH THE ORIGINAL QUERY:
-- 1. Correlated subquery: The COUNT(*) subquery runs once per row in agreements,
--    resulting in O(n*m) complexity. For large tables this is extremely slow.
-- 2. UPPER(a.status) = 'ACTIVE': Applying a function to a column prevents index
--    usage (non-sargable). If status is stored consistently, compare directly.
-- 3. YEAR(a.start_date) = 2023: Same issue — wrapping start_date in a function
--    disables index seeks. Use a range condition instead.
-- 4. SELECT *: Returns all columns, which is inefficient if only specific 
--    columns are needed and can prevent covering index usage.

-- OPTIMISED QUERY:
SELECT
    a.*,
    COUNT(p.payment_id) AS payment_count
FROM agreements a
JOIN payments   p ON p.agreement_id = a.agreement_id
WHERE a.status     = 'ACTIVE'
  AND a.start_date >= '2023-01-01'
  AND a.start_date <  '2024-01-01'
GROUP BY a.agreement_id
HAVING COUNT(p.payment_id) > 5;

-- EXPLANATION OF CHANGES:
-- 1. Replaced correlated subquery with a JOIN + GROUP BY + HAVING pattern.
--    This allows the database to perform a single aggregation pass instead of
--    executing a subquery for every row.
-- 2. Removed UPPER(): Compare status directly to 'ACTIVE'. If data can have
--    mixed case, normalise it at insert time or add a functional index.
-- 3. Replaced YEAR(start_date) = 2023 with a range condition:
--    start_date >= '2023-01-01' AND start_date < '2024-01-01'
--    This is sargable and can leverage an index on start_date.
-- 4. Added payment_count to output for transparency; SELECT a.* retained per
--    original intent, but in production consider selecting only needed columns.
--
-- RECOMMENDED INDEXES for further optimisation:
--   CREATE INDEX idx_agreements_status_start ON agreements(status, start_date);
--   CREATE INDEX idx_payments_agreement      ON payments(agreement_id);
