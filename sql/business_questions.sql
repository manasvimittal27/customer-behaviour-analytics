-- ============================================================================
-- Customer shopping behaviour: business questions in PostgreSQL
--
-- Table: customer (one row per customer, each with one purchase), loaded by
--        `python -m src.load_to_postgres` from the cleaned data.
-- Run:   psql -d customer_behaviour -f sql/business_questions.sql
--
-- Each question keeps its original intent. Where the first version could
-- mislead (totals that only reflect group size, ties dropped silently, a
-- question answered for one group only), the query below fixes it and the
-- comment says why. Results are in sql/README.md.
-- ============================================================================


-- Q1. Revenue by gender ----------------------------------------------------
-- Totals alone mislead: men are 68% of customers, so they generate more
-- revenue even though average spend is the same. Show count, shares and the
-- per-customer average side by side.
SELECT
    gender,
    COUNT(*)                                                       AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)             AS pct_of_customers,
    SUM(purchase_amount)                                           AS revenue,
    ROUND(100.0 * SUM(purchase_amount) / SUM(SUM(purchase_amount)) OVER (), 1) AS pct_of_revenue,
    ROUND(AVG(purchase_amount), 2)                                 AS avg_spend
FROM customer
GROUP BY gender
ORDER BY revenue DESC;


-- Q2. Customers who used a discount and still spent more than average -------
-- "More than" means >, not >=. The summary is more useful than a list of
-- 800+ IDs; the detail query is kept below it.
WITH benchmark AS (
    SELECT AVG(purchase_amount) AS avg_spend FROM customer
)
SELECT
    COUNT(*) FILTER (WHERE c.purchase_amount > b.avg_spend)                    AS above_avg_spenders,
    COUNT(*)                                                                   AS discount_users,
    ROUND(100.0 * COUNT(*) FILTER (WHERE c.purchase_amount > b.avg_spend) / COUNT(*), 1) AS pct_above_avg,
    ROUND(b.avg_spend, 2)                                                      AS overall_avg_spend
FROM customer c
CROSS JOIN benchmark b
WHERE c.discount_applied = 'Yes'
GROUP BY b.avg_spend;

-- Detail: the customer list
SELECT customer_id, purchase_amount
FROM customer
WHERE discount_applied = 'Yes'
  AND purchase_amount > (SELECT AVG(purchase_amount) FROM customer)
ORDER BY purchase_amount DESC, customer_id;


-- Q3. Top 5 products by average review rating ------------------------------
-- Added the number of ratings and the gap to the overall average. The gaps
-- are about 0.1 points on a 5-point scale: too small to rank products on.
-- 37 ratings were missing and filled with the category median; the last
-- column shows how many of each product's ratings were filled in.
SELECT
    item_purchased,
    COUNT(*)                                                         AS ratings,
    ROUND(AVG(review_rating)::numeric, 2)                            AS avg_rating,
    ROUND((AVG(review_rating) - (SELECT AVG(review_rating) FROM customer))::numeric, 2) AS vs_overall_avg,
    COUNT(*) FILTER (WHERE review_rating_imputed)                    AS imputed_ratings
FROM customer
GROUP BY item_purchased
ORDER BY AVG(review_rating) DESC   -- order by the unrounded average so ties at 2 d.p. resolve correctly
LIMIT 5;


-- Q4. Average spend: Standard vs Express shipping --------------------------
-- Added customer counts. The two averages differ by about $2 (see the
-- notebook: the difference is not statistically significant).
SELECT
    shipping_type,
    COUNT(*)                          AS customers,
    ROUND(AVG(purchase_amount), 2)    AS avg_spend
FROM customer
WHERE shipping_type IN ('Express', 'Standard')
GROUP BY shipping_type
ORDER BY avg_spend DESC;


-- Q5. Do subscribers spend more? -------------------------------------------
-- Removed the redundant WHERE clause and ordered by revenue. The answer is
-- no: average spend is almost identical. Caution: every subscriber also
-- received a discount, so the subscription cannot be evaluated on its own
-- (see Q11).
SELECT
    subscription_status,
    COUNT(*)                                                   AS customers,
    SUM(purchase_amount)                                       AS revenue,
    ROUND(100.0 * SUM(purchase_amount) / SUM(SUM(purchase_amount)) OVER (), 1) AS pct_of_revenue,
    ROUND(AVG(purchase_amount), 2)                             AS avg_spend
FROM customer
GROUP BY subscription_status
ORDER BY revenue DESC;


-- Q6. Top 5 products by share of purchases with a discount ------------------
-- Unchanged logic, written with FILTER. Caution: only male customers ever
-- received discounts, so a product's discount rate largely reflects how
-- many of its buyers are men (correlation 0.56 across products).
SELECT
    item_purchased,
    COUNT(*)                                                               AS purchases,
    ROUND(100.0 * COUNT(*) FILTER (WHERE discount_applied = 'Yes') / COUNT(*), 1) AS discount_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE gender = 'Male') / COUNT(*), 1)          AS male_buyers_pct
FROM customer
GROUP BY item_purchased
ORDER BY discount_rate_pct DESC
LIMIT 5;


-- Q7. Customer segments by previous purchases --------------------------------
-- Explicit WHEN for every segment, so unexpected values (0, NULL) fall into
-- 'Unknown' instead of silently becoming 'Loyal'. Added shares, average
-- spend and subscription rate per segment.
WITH segmented AS (
    SELECT
        *,
        CASE
            WHEN previous_purchases = 1              THEN 'New'
            WHEN previous_purchases BETWEEN 2 AND 10 THEN 'Returning'
            WHEN previous_purchases > 10             THEN 'Loyal'
            ELSE 'Unknown'
        END AS segment
    FROM customer
)
SELECT
    segment,
    COUNT(*)                                                         AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)               AS pct_of_customers,
    ROUND(AVG(purchase_amount), 2)                                   AS avg_spend,
    ROUND(100.0 * COUNT(*) FILTER (WHERE subscription_status = 'Yes') / COUNT(*), 1) AS subscription_rate_pct
FROM segmented
GROUP BY segment
ORDER BY MIN(previous_purchases);


-- Q8. Top 3 products within each category ------------------------------------
-- RANK instead of ROW_NUMBER: ROW_NUMBER breaks ties arbitrarily, which here
-- silently dropped Sunglasses (tied with Belt) and mis-ranked Pants (tied
-- with Blouse). With RANK, tied products share a rank.
WITH item_counts AS (
    SELECT
        category,
        item_purchased,
        COUNT(*)                                                          AS purchases,
        RANK() OVER (PARTITION BY category ORDER BY COUNT(*) DESC)        AS item_rank
    FROM customer
    GROUP BY category, item_purchased
)
SELECT category, item_rank, item_purchased, purchases
FROM item_counts
WHERE item_rank <= 3
ORDER BY category, item_rank, item_purchased;


-- Q9. Are repeat buyers (more than 5 previous purchases) more likely to subscribe?
-- The first version counted subscribers among repeat buyers only, which
-- cannot answer "more likely": it needs the rate for both groups.
SELECT
    CASE WHEN previous_purchases > 5 THEN 'Repeat buyer (>5)' ELSE 'Not repeat (<=5)' END AS buyer_type,
    COUNT(*)                                                                         AS customers,
    COUNT(*) FILTER (WHERE subscription_status = 'Yes')                              AS subscribers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE subscription_status = 'Yes') / COUNT(*), 1) AS subscription_rate_pct
FROM customer
GROUP BY 1
ORDER BY 1;


-- Q10. Revenue contribution of each age group ------------------------------
-- The age groups are quartiles (equal-sized by design), so revenue rankings
-- mostly reflect small differences in group size. Show both.
SELECT
    age_group,
    MIN(age) || '-' || MAX(age)                                         AS age_range,
    COUNT(*)                                                            AS customers,
    SUM(purchase_amount)                                                AS revenue,
    ROUND(100.0 * SUM(purchase_amount) / SUM(SUM(purchase_amount)) OVER (), 1) AS pct_of_revenue,
    ROUND(AVG(purchase_amount), 2)                                      AS avg_spend
FROM customer
GROUP BY age_group
ORDER BY MIN(age);


-- Q11 (new). How do subscription, discounts and gender overlap? --------------
-- Explains why the subscription and discount programmes cannot be evaluated
-- from this data: every subscriber received a discount, and no female
-- customer either subscribed or received a discount.
SELECT
    gender,
    subscription_status,
    discount_applied,
    COUNT(*)                         AS customers,
    ROUND(AVG(purchase_amount), 2)   AS avg_spend
FROM customer
GROUP BY gender, subscription_status, discount_applied
ORDER BY gender, subscription_status DESC, discount_applied DESC;


-- Q12 (new). Revenue by state: driven by customer count or by spend? -------
-- Top and bottom 3 states by revenue, with customer counts and average spend.
WITH states AS (
    SELECT
        location,
        COUNT(*)                         AS customers,
        SUM(purchase_amount)             AS revenue,
        ROUND(AVG(purchase_amount), 2)   AS avg_spend,
        RANK() OVER (ORDER BY SUM(purchase_amount) DESC) AS revenue_rank
    FROM customer
    GROUP BY location
)
SELECT revenue_rank, location, customers, revenue, avg_spend
FROM states
WHERE revenue_rank <= 3 OR revenue_rank > (SELECT COUNT(*) FROM states) - 3
ORDER BY revenue_rank;

-- Correlation across the 50 states between customer count and revenue
SELECT ROUND(CORR(customers, revenue)::numeric, 2) AS corr_customers_revenue
FROM (
    SELECT location, COUNT(*) AS customers, SUM(purchase_amount) AS revenue
    FROM customer
    GROUP BY location
) s;
