# Project Audit

Review of the first version of the project: `Untitled.ipynb`, `customer_behaviour.sql` and `customer_behaviour.twbx`. Original files are unchanged; this repository holds the revised versions.

## Starting point

| Component | State found | Verdict |
|---|---|---|
| Notebook | Loads data, checks types and missing values, imputes ratings by category median, renames columns, creates age groups and frequency-in-days, loads to PostgreSQL with a hidden password | Correct core steps; no analysis, charts or findings yet |
| SQL | 10 business questions | Runs correctly; 6 queries could mislead (below) |
| Tableau | One sheet with a "number of customers" KPI; 3 calculated fields; no dashboard | Early stage |
| Documentation | None | Missing |

## Issues found and fixed

| # | Issue | Evidence | Impact | Fix |
|---|---|---|---|---|
| 1 | `df.drop("promo_code_used", axis=1)` was not assigned back | Column still present in the table loaded to PostgreSQL | Redundant column in database and Tableau | Drop inside `clean()` after asserting it equals `discount_applied` |
| 2 | Duplicate frequency labels | "Bi-Weekly" and "Fortnightly", "Every 3 Months" and "Quarterly" were separate categories (1,131 rows) | Frequency charts split one group into two | Merged in `clean()` |
| 3 | Group revenue presented without counts (SQL Q1, Q10) | Men: 68.0% of customers, 67.7% of revenue | Implies men spend more; they don't (p = 0.38) | Added counts, shares, average spend |
| 4 | `ROW_NUMBER` in top products (Q8) | Belt and Sunglasses tie at 161; Blouse and Pants at 171 | Sunglasses silently dropped; Pants ranked 2nd instead of joint 1st | `RANK()` |
| 5 | Q9 counted subscribers among repeat buyers only | No rate for the comparison group | Question "more likely?" unanswered | Rates for both groups (27.6% vs 22.4%) |
| 6 | Q7 `ELSE 'Loyal'` | Would label 0 or NULL as Loyal | Silent misclassification if data changes | Explicit `WHEN` + `'Unknown'` |
| 7 | Q2 used `>=` for "more than" | — | Off-by-definition (no rows affected here) | `>` |
| 8 | Q3 sorted by rounded average | Skirt (3.785) and T-shirt (3.779) both round to 3.78 | 5th place chosen arbitrarily | Sort on unrounded average |
| 9 | No significance testing | All 12 spend comparisons p > 0.0042 | Chance gaps would be reported as findings | Tests + Bonferroni correction |
| 10 | Programme confounding not noticed | 100% of subscribers had a discount; 0 women had either | "Do subscribers spend more?" has no valid answer | Reported as Finding 2; Q11 added |
| 11 | Notebook not reproducible as a single run | Repeated `head()` cells, no validation | Hard to review | Rebuilt notebook with logic in `src/`, validation cell, tests |

## What was kept

The cleaning choices (category-median imputation, snake_case names, quartile age groups, frequency in days), all 10 business questions, the PostgreSQL workflow with a hidden password, and Tableau as the dashboard tool.

## Ranked improvements for the portfolio

1. **Build and publish the two Tableau dashboards** using the build guide; add the link and screenshots to the README. *(Highest impact: recruiters click dashboards.)*
2. **Be able to explain Findings 1 and 2 in your own words.** They are what separates this from the many tutorial copies of this dataset.
3. **Push to GitHub** with the README as the landing page.
4. *Optional:* repeat the analysis on a real transaction dataset with dates (for example, an e-commerce orders dataset) to add retention and cohort analysis.
