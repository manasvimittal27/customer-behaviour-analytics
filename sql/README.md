# SQL analysis (PostgreSQL)

`business_questions.sql` answers 12 business questions on the `customer` table. Questions 1–10 are the original project questions, rewritten where the first version could mislead; Q11 and Q12 are new. Every result below matches the Python notebook.

## Run it

```bash
createdb -U postgres customer_behaviour
python -m src.load_to_postgres            # cleans the raw CSV and loads table `customer`
psql -U postgres -d customer_behaviour -f sql/business_questions.sql
```

`load_to_postgres` reads PGHOST, PGPORT, PGUSER, PGDATABASE and PGPASSWORD if set, and otherwise asks for the password without displaying it. No credentials are stored in the code.

## What changed from the first version, and why

| Q | Question | Change | Why |
|---|---|---|---|
| 1 | Revenue by gender | Added customers, shares and average spend | Totals alone imply men spend more; they are just 68% of customers |
| 2 | Discount users spending above average | `>=` → `>`; added a summary row | "More than" means `>`; a count is more useful than 839 IDs |
| 3 | Top 5 products by rating | Added rating count, gap to average, imputed count; sort on unrounded average | Shows the gaps are ~0.1 points; ties at 2 d.p. had been sorted arbitrarily |
| 4 | Express vs Standard spend | Added counts | Context for a $2 gap |
| 5 | Do subscribers spend more? | Removed redundant `WHERE`; added revenue share | Simpler; note that subscription is confounded with discounts |
| 6 | Products with highest discount rate | Added male-buyer share | Only men received discounts, so discount rate tracks gender mix |
| 7 | Customer segments | Explicit `WHEN` for Loyal, `'Unknown'` fallback; added spend and subscription rate | `ELSE 'Loyal'` would silently label bad data as Loyal |
| 8 | Top 3 products per category | `ROW_NUMBER` → `RANK` | `ROW_NUMBER` dropped Sunglasses (tied with Belt) and mis-ranked Pants (tied with Blouse) |
| 9 | Are repeat buyers more likely to subscribe? | Rate for both groups, not a count for one | "More likely" needs a comparison |
| 10 | Revenue by age group | Added age range, counts and average spend | Age groups are quartiles, so revenue rank mostly reflects group size |
| 11 | *New:* programme overlap | Gender × subscription × discount | Shows why the programmes cannot be evaluated separately |
| 12 | *New:* revenue by state | Top and bottom 3 states plus count–revenue correlation | Shows state revenue follows customer count (r = 0.90) |

## Selected results

**Q1. Revenue by gender**

| gender | customers | % customers | revenue | % revenue | avg spend |
|---|---|---|---|---|---|
| Male | 2,652 | 68.0 | 157,890 | 67.7 | 59.54 |
| Female | 1,248 | 32.0 | 75,191 | 32.3 | 60.25 |

**Q7. Segments**

| segment | customers | % customers | avg spend | subscription rate % |
|---|---|---|---|---|
| New | 83 | 2.1 | 58.47 | 18.1 |
| Returning | 701 | 18.0 | 60.93 | 24.1 |
| Loyal | 3,116 | 79.9 | 59.54 | 27.9 |

**Q8. Top products per category** (ties share a rank): Accessories: Jewelry (171), Belt and Sunglasses (161 each) · Clothing: Blouse and Pants (171 each), Shirt (169) · Footwear: Sandals (160), Shoes (150), Sneakers (145) · Outerwear: Jacket (163), Coat (161).

**Q9. Repeat buyers:** subscription rate 27.6% for customers with more than 5 previous purchases vs 22.4% for the rest.

**Q11. Programme overlap**

| gender | subscribed | discount | customers | avg spend |
|---|---|---|---|---|
| Female | No | No | 1,248 | 60.25 |
| Male | Yes | Yes | 1,053 | 59.49 |
| Male | No | Yes | 624 | 58.92 |
| Male | No | No | 975 | 59.98 |

**Q12. States:** Montana is top ($5,784 from 96 customers) and Kansas bottom ($3,437 from 63); across the 50 states, revenue correlates 0.90 with customer count.

## SQL techniques used

CTEs · window functions (`RANK() OVER (PARTITION BY …)`, `SUM(…) OVER ()` for shares of total) · conditional aggregation with `FILTER` · `CASE` segmentation · scalar subqueries · `CORR` · `CROSS JOIN` to a benchmark row.
