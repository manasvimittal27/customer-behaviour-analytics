# Tableau

The dashboards are built in **Tableau Public** from `data/processed/customer_clean.csv`.

- **Published dashboard:** [Customer Behaviour Dashboard on Tableau Public](https://public.tableau.com/app/profile/manasvi.mittal5409/viz/customer_behaviour_dashboard_17931679352620/Overview)
- **Build specification:** [documentation/tableau_build_guide.md](../documentation/tableau_build_guide.md) has every calculated field, sheet, dashboard layout, format and a validation checklist.
- **Design references:** [overview](../documentation/dashboard_mockup_overview.png) · [segments & programmes](../documentation/dashboard_mockup_segments.png), rendered in Python from the same data.

## Why the workbook file is not in this repository

A `.twbx` file packages a copy of the data, and the dataset's redistribution terms are not confirmed (see `data/README.md`). The Tableau Public link is the shareable version. To rebuild locally:

1. `python -m src.cleaning` (creates `data/processed/customer_clean.csv`)
2. Open Tableau Public → **Text file** → `customer_clean.csv`
3. Follow the build guide.

## Dashboards

| Dashboard | Answers | Key interactions |
|---|---|---|
| Customer & Revenue Overview | How big is the business, where does revenue come from, and does spend differ by group? | Filters (gender, age group, season, subscription) apply to all sheets; click a category or state to filter; `Compare By` parameter switches the spend comparison between 8 dimensions |
| Segments & Programmes | How do purchase history and subscription relate, and can the programmes be evaluated? | Tooltips with counts and average spend; navigation buttons between dashboards |
