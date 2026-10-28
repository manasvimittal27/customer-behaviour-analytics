# Case Study: Do Customer Groups Really Spend Differently?

*Customer shopping behaviour analysis · Python, PostgreSQL, Tableau · Manasvi Mittal*

## Executive summary

A retailer's 3,900 customers were analysed to find which groups, products and programmes drive revenue. The headline answer is that **in this data, no customer group spends meaningfully more than another**. Average spend is about $60 everywhere, and revenue differences between groups come entirely from how many customers each group has. The subscription and discount programmes cannot be evaluated, because they were applied to the same customers. The one relationship that holds up is that customers with more purchase history subscribe more often (18% → 24% → 28%).

The value of the project is in **not over-reading the data**: every comparison is tested for significance, corrected for multiple testing, and checked for confounding before it is called a finding.

## Business context

Retail marketing budgets are often allocated by segment revenue: "men drive 68% of revenue, so target men". That logic only works if the segment's customers are individually more valuable. If they are simply more numerous, targeting them buys volume at the same value per customer, and the money might do more acquiring new customers or increasing purchase frequency.

## Problem statement

1. Which customer groups are most valuable per customer?
2. Do subscribers and discount users spend more?
3. What predicts subscription?
4. Are seasonal or product differences large enough to act on?

## Dataset and data quality

3,900 customers × 18 fields, one purchase each, with no dates, order IDs or costs.

| Check | Result |
|---|---|
| Duplicates, impossible values | None |
| Missing review ratings | 37 (1%): filled with the category median and flagged |
| `Promo Code Used` | Identical to `Discount Applied` on every row: dropped |
| Frequency labels | "Bi-Weekly" = "Fortnightly" and "Every 3 Months" = "Quarterly" (1,131 rows): merged |
| Programme flags | All subscribers have a discount; no women have either |
| Signs of synthetic data | Near-uniform categories; subscribers, discount users and men stored as nested row blocks; spend unrelated to every other field |

## Methodology

1. **Clean once, use everywhere.** A single Python module produces the table used by the notebook, PostgreSQL and Tableau, so all three tools report identical numbers.
2. **Separate volume from value.** Each revenue figure is shown with customer count and average spend.
3. **Test before concluding.** Welch's t-test and ANOVA for spend, chi-square for rates, and a Bonferroni correction because 12 groupings were compared.
4. **Check for confounding.** Programme flags were cross-tabulated with each other and with gender before any programme was evaluated.
5. **Reproduce in SQL.** Twelve business questions written in PostgreSQL with CTEs and window functions, matching the Python results.

## Key findings

**1. Spend per customer is flat; revenue follows headcount.**
Average spend ranges from $57.17 to $61.56 across all gender, age, category, season, shipping, payment, size, frequency and loyalty groups (overall $59.76). No difference survives the multiple-testing correction. Men give 67.7% of revenue and are 68.0% of customers; women average slightly more ($60.25 vs $59.54, p = 0.38). State revenue correlates 0.90 with state customer count.
*So what:* segment revenue rankings here are headcount rankings. Growth comes from more customers or more frequent purchases, not from targeting a demographic.

**2. The programmes cannot be evaluated from this data.**
All 1,053 subscribers received a discount; 624 other customers did too; no woman received either. Subscribers average $59.49 vs $59.87 (p = 0.66).
*So what:* any claimed effect of the subscription would be indistinguishable from the discount and from gender. The fix is measurement design, not more analysis.

**3. Purchase history and subscription move together.**
Subscription rate: New 18.1% (n = 83), Returning 24.1% (n = 701), Loyal 27.9% (n = 3,116); chi-square p = 0.023. Repeat buyers (more than 5 previous purchases) subscribe at 27.6% vs 22.4%.
*So what:* subscription offers may convert better once customers have some history, but the direction of cause is unknown and needs a test.

**4. The seasonal gap is likely chance.**
Fall $61.56 vs Summer $58.41 (p = 0.011), not significant after correction (threshold 0.0042).
*So what:* not a basis for seasonal budget shifts without another year of data.

**5. Ratings do not separate products.**
Average 3.75/5; the top product is 0.11 above average; ANOVA across 25 products p = 0.66. The top-5 list is unchanged when imputed ratings are excluded.
*So what:* don't promote products on these ratings; combine ratings with review counts and returns data.

## Tableau dashboard overview

- **Customer & Revenue Overview:** five KPI cards (customers, revenue, average spend, average rating, subscriber share), revenue by category and by state, and a spend comparison where a `Compare By` parameter switches between eight dimensions against an overall-average reference line, so viewers can confirm Finding 1 themselves.
- **Segments & Programmes:** subscription rate by segment, the programme-overlap chart behind Finding 2, and top products per category with tie-aware ranking.
- Filters for gender, age group, season and subscription apply across sheets; clicking a category or state filters the dashboard.

## Business recommendations

| # | Recommendation | Evidence | Risk / next step |
|---|---|---|---|
| 1 | Report revenue with customer count and average spend; set growth targets on acquisition and frequency | Finding 1 | Validate on real transaction data |
| 2 | Record subscriptions and discounts independently; evaluate discounts with a randomised experiment | Finding 2 | Requires a process change before any answer exists |
| 3 | Test timing subscription offers at the Returning stage (2nd–10th purchase) | Finding 3 | Association only; the A/B test is the evidence |
| 4 | Do not shift seasonal budgets or rank products on current gaps | Findings 4–5 | Revisit with more data |

## Limitations

- The data is probably synthetic, so the findings describe this dataset only.
- With one purchase per customer and no dates, there are no trends, retention, cohorts or lifetime value.
- There are no costs, so the analysis says nothing about profit or discount ROI.
- The segment thresholds (1 / 2–10 / 11+) come from the business question, and they put 80% of customers in "Loyal".

## What I would investigate next

1. **With real transaction data:** cohort retention by first-purchase month, RFM segmentation, and repeat-purchase intervals compared with stated frequency.
2. **A discount experiment:** randomly assign the discount to half of eligible customers and measure spend, conversion and repeat purchase.
3. **Subscription timing test:** offer at the 1st vs the 3rd purchase and compare conversion and 90-day revenue.
