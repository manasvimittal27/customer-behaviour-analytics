# Metric Definitions

Each metric has one definition, implemented the same way in Python, SQL and Tableau. The "Value" column is the full-dataset result, and it was checked to match across all three.

| Metric | Business meaning | Python (`df` = cleaned data) | SQL (`customer` table) | Tableau | Value |
|---|---|---|---|---|---|
| Customers | Distinct customers in the data | `df["customer_id"].nunique()` | `COUNT(DISTINCT customer_id)` | `COUNTD([customer_id])` | 3,900 |
| Revenue | Total purchase value, USD | `df["purchase_amount"].sum()` | `SUM(purchase_amount)` | `SUM([purchase_amount])` | $233,081 |
| Avg Spend | Revenue per customer, which equals average order value here because each customer has one purchase | `df["purchase_amount"].mean()` | `AVG(purchase_amount)` | `SUM([purchase_amount]) / COUNTD([customer_id])` | $59.76 |
| Avg Rating | Average review rating, 1–5 scale (37 imputed values included) | `df["review_rating"].mean()` | `AVG(review_rating)` | `AVG([review_rating])` | 3.75 |
| Subscriber Share | Share of customers with an active subscription | `df["subscription_status"].eq("Yes").mean()` | `AVG((subscription_status = 'Yes')::int)` | `COUNTD(IF [subscription_status]="Yes" THEN [customer_id] END) / COUNTD([customer_id])` | 27.0% |
| Discount Share | Share of customers whose purchase had a discount | `df["discount_applied"].eq("Yes").mean()` | `AVG((discount_applied = 'Yes')::int)` | as Subscriber Share, on `discount_applied` | 43.0% |
| % of Revenue | A group's share of total revenue | `group_sum / total` | `SUM(x) / SUM(SUM(x)) OVER ()` | `SUM([purchase_amount]) / TOTAL(SUM([purchase_amount]))` | e.g. Male 67.7% |
| Customer Segment | Purchase history band: New = 1, Returning = 2–10, Loyal = 11+ previous purchases | `pd.cut(previous_purchases, [0, 1, 10, inf])` | `CASE WHEN ... END` (Q7) | `customer_segment` column | 83 / 701 / 3,116 |
| Repeat Buyer | More than 5 previous purchases | `previous_purchases > 5` | `previous_purchases > 5` (Q9) | `is_repeat_buyer` column | 3,476 customers |
| Subscription Rate (by group) | Subscribers ÷ customers within a group | `compare_rate(df, group, "is_subscriber")` | `COUNT(*) FILTER (WHERE subscription_status='Yes') / COUNT(*)` | `Subscriber Share` with the group on Rows | New 18.1%, Returning 24.1%, Loyal 27.9% |
| Purchase Frequency (days) | Stated buying interval converted to days | `FREQUENCY_DAYS` map in `src/cleaning.py` | `purchase_frequency_days` column | same column | Weekly 7 … Annually 365 |

## Statistical tests used

| Test | Used for | Reading the result |
|---|---|---|
| Welch's t-test | Average spend, 2 groups (e.g. subscribers vs not) | p < 0.05: the gap is unlikely to be chance, if this were the only test |
| One-way ANOVA | Average spend or rating, 3+ groups | Same reading, across all groups at once |
| Chi-square test | Rates such as subscription share by segment | Same reading, for proportions |
| Bonferroni correction | 12 spend comparisons run together | Requires p < 0.05 / 12 = 0.0042, because many tests produce some small p-values by chance |

## Metrics deliberately not calculated

| Metric | Why not |
|---|---|
| Revenue trend over time, month-on-month growth | No date column; `season` is the only time-like field |
| Retention, churn, cohorts | One purchase per customer; no repeat transactions to follow |
| Customer lifetime value | Needs repeat purchases over time and margins |
| Profit, margin, ROI of discounts | No cost, price or discount-amount data |
| Effect of subscription or discount on spend | The programmes are confounded with each other and with gender (Finding 2) |
| Conversion rate | No data on visitors or non-buyers |
