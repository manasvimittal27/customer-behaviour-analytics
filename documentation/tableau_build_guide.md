# Tableau Build Guide

Step-by-step specification for the two dashboards, written for **Tableau Public** (free, runs on Mac). Every number in the validation checklist comes from the Python analysis, so you can confirm the dashboard is correct.

> Current state of `customer_behaviour.twbx`: one sheet (a "number of customers" text mark), three calculated fields (`number of customers`, `avg_purchase_amount`, `avg_Review_Rating`) and no dashboards. It connects to `~/Downloads/customer.csv`. This guide builds on it; nothing in it needs to be deleted.

## 1. Connect to the cleaned data

1. Run `python -m src.cleaning` to create `data/processed/customer_clean.csv`.
2. In your workbook: **Data → Replace Data Source**, or on the Data Source tab click the connection → **Edit Connection**, and choose `customer_clean.csv`.
   Your three existing calculated fields keep working because the column names (`customer_id`, `purchase_amount`, `review_rating`) are unchanged.
3. New columns now available: `customer_segment`, `purchase_frequency`, `purchase_frequency_days`, `age_group`, `is_repeat_buyer`, `review_rating_imputed`. (`promo_code_used` is gone: it duplicated `discount_applied`.)
4. Set the geographic role: right-click `location` → **Geographic Role → State/Province**. Tableau recognises all 50 US state names.

## 2. Calculated fields

Create each with **Analysis → Create Calculated Field**. Rename your existing three to match the first column of this table so every name is consistent.

| Name | Formula | Notes |
|---|---|---|
| `Customers` | `COUNTD([customer_id])` | Your existing "number of customers" |
| `Revenue` | `SUM([purchase_amount])` | Format: Currency, 0 decimals |
| `Avg Spend` | `SUM([purchase_amount]) / COUNTD([customer_id])` | Revenue per customer. Equals `AVG([purchase_amount])` here because each customer has one purchase; this form stays correct if a customer ever has several rows. Currency, 2 decimals |
| `Avg Rating` | `AVG([review_rating])` | Your existing avg_Review_Rating. Number, 2 decimals |
| `Subscriber Share` | `COUNTD(IF [subscription_status] = "Yes" THEN [customer_id] END) / COUNTD([customer_id])` | Percentage, 1 decimal |
| `Discount Share` | `COUNTD(IF [discount_applied] = "Yes" THEN [customer_id] END) / COUNTD([customer_id])` | Percentage, 1 decimal |
| `Overall Avg Spend` | `{FIXED : SUM([purchase_amount])} / {FIXED : COUNTD([customer_id])}` | LOD: ignores the view's dimensions, so it gives one catalogue-wide benchmark |
| `Spend vs Overall` | `[Avg Spend] - MIN([Overall Avg Spend])` | Positive = group spends above average. Currency, 2 decimals, show + sign |
| `% of Revenue` | `SUM([purchase_amount]) / TOTAL(SUM([purchase_amount]))` | Table calculation. Percentage, 1 decimal |
| `% of Customers` | `COUNTD([customer_id]) / TOTAL(COUNTD([customer_id]))` | Table calculation. Percentage, 1 decimal |
| `Programme Group` | `IF [subscription_status] = "Yes" THEN "Subscriber + discount" ELSEIF [discount_applied] = "Yes" THEN "Discount only" ELSE "Neither" END` | Dimension |
| `Segment Order` | `CASE [customer_segment] WHEN "New" THEN 1 WHEN "Returning" THEN 2 WHEN "Loyal" THEN 3 END` | Used only to sort segments |

**Parameter** (right-click in the Data pane → **Create Parameter**):

| Parameter | Type | Values | Current value |
|---|---|---|---|
| `Compare By` | String, list | Gender, Age Group, Category, Season, Shipping Type, Payment Method, Customer Segment, Subscription | Gender |

Then the calculated field that uses it:

```
// Compare Dimension
CASE [Compare By]
    WHEN "Gender"           THEN [gender]
    WHEN "Age Group"        THEN [age_group]
    WHEN "Category"         THEN [category]
    WHEN "Season"           THEN [season]
    WHEN "Shipping Type"    THEN [shipping_type]
    WHEN "Payment Method"   THEN [payment_method]
    WHEN "Customer Segment" THEN [customer_segment]
    WHEN "Subscription"     THEN [subscription_status]
END
```

Right-click `Compare By` → **Show Parameter** on the sheet where you use it.

## 3. Worksheets

Rename each sheet tab exactly as listed so dashboards are easy to assemble.

| Sheet | Build | Sort / format | Tooltip |
|---|---|---|---|
| `KPI Customers` | `Customers` on **Text** | Number (Custom), Thousands (K), 1 decimal → "3.9K" | — |
| `KPI Revenue` | `Revenue` on **Text** | Currency, Thousands (K), 1 decimal → "$233.1K" | — |
| `KPI Avg Spend` | `Avg Spend` on **Text** | Currency, 2 decimals | — |
| `KPI Avg Rating` | `Avg Rating` on **Text** | Number, 2 decimals | — |
| `KPI Subscriber Share` | `Subscriber Share` on **Text** | Percentage, 1 decimal | — |
| `Revenue by Category` | `category` on Rows, `Revenue` on Columns, bar | Sort descending by Revenue; `Revenue` on Label | Customers, Avg Spend, % of Revenue |
| `Revenue by State` | Double-click `location` (map), `Revenue` on **Color** | Colour: single-hue blue, 5 stepped | Customers, Revenue, Avg Spend |
| `Spend by Group` | `Compare Dimension` on Rows, `Avg Spend` on Columns, **Circle** mark; drag `Overall Avg Spend` to **Detail** | Right-click the Avg Spend axis → **Add Reference Line**: scope Entire Table, value `MIN(Overall Avg Spend)`, label "Overall $59.76", dashed red. (Not "Average": that would average the group averages unweighted.) Show the `Compare By` parameter | Customers, Avg Spend, Spend vs Overall |
| `Segments` | `customer_segment` on Rows (sort by `Segment Order`), `Subscriber Share` on Columns, bar | Label: Subscriber Share; colour by `customer_segment` (3 shades of one blue) | Customers, % of Customers, Avg Spend |
| `Programme Overlap` | `gender` on Rows, `Customers` on Columns, `Programme Group` on **Color**, stacked bar | Colours: Subscriber + discount = dark blue, Discount only = light blue, Neither = grey; `Customers` on Label | Programme Group, Customers, Avg Spend |
| `Top Products` | `category` and `item_purchased` on Rows, `Customers` on Columns | Create `Product Rank` = `RANK(COUNTD([customer_id]))`, drag it to Filters, right-click → **Compute Using → item_purchased** (so it ranks within each category), keep 1 to 3. Tied products share a rank, like SQL `RANK()` | Customers, Avg Rating |

## 4. Dashboards

Size: **Fixed, 1400 × 900** (Dashboard → Size). Background white; containers with 12 px outer padding.

### Dashboard 1: `Customer & Revenue Overview`

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Customer & Revenue Overview                       [Filters: Gender ▾ ... ] │
├─────────────┬─────────────┬─────────────┬─────────────┬───────────────────┤
│ Customers   │ Revenue     │ Avg Spend   │ Avg Rating  │ Subscriber Share  │
│ 3.9K        │ $233.1K     │ $59.76      │ 3.75        │ 27.0%             │
├─────────────┴─────────────┴──────┬──────┴─────────────┴───────────────────┤
│ Revenue by Category              │ Revenue by State (map)                  │
│                                  │                                         │
├──────────────────────────────────┴─────────────────────────────────────────┤
│ Spend by Group   [Compare By: Gender ▾]                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

1. Drag a **Horizontal** container to the top; drop the five KPI sheets into it. Select the container → **Distribute Contents Evenly**. Hide each KPI sheet's title and put the metric name in the Text mark instead (small grey label line above a large bold value; see your earlier card).
2. Below, a Horizontal container with `Revenue by Category` (40%) and `Revenue by State` (60%).
3. Bottom: `Spend by Group` across the full width, with the `Compare By` parameter control above it.
4. **Filters:** on `Revenue by Category`, show filters for `gender`, `age_group`, `season` and `subscription_status`. For each filter: drop-down menu → **Apply to Worksheets → All Using This Data Source**. Place them in a horizontal container at the top right.
5. **Action:** Dashboard → Actions → Add Action → **Filter**: source `Revenue by Category` and `Revenue by State`, run on **Select**, target all sheets, clearing the selection shows all values. Clicking a category or state then filters the whole dashboard.
6. Title text: "Customer & Revenue Overview". Subtitle: "3,900 customers, one purchase each. Average spend is about $60 in every group; revenue differences come from customer counts."

### Dashboard 2: `Segments & Programmes`

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Segments & Programmes                                                      │
├──────────────────────────────────┬────────────────────────────────────────┤
│ Subscription rate by Segment     │ Programme Overlap (gender x programme) │
├──────────────────────────────────┴────────────────────────────────────────┤
│ Top 3 Products per Category                                                │
└───────────────────────────────────────────────────────────────────────────┘
```

1. Top row: `Segments` (left) and `Programme Overlap` (right).
2. Bottom: `Top Products`.
3. Add a **Text** object under `Programme Overlap`: "Every subscriber also received a discount, and no female customer received either, so the effect of each programme cannot be separated in this data."
4. **Navigation:** add a **Navigation** button object on each dashboard pointing to the other one.

## 5. Formatting standard

| Element | Setting |
|---|---|
| Font | Tableau Book (default) throughout; titles 15 pt bold, labels 10 pt |
| Primary colour | `#2A6F97` (bars, marks) |
| Secondary | `#7FB3D5` (second series), `#A7B3BD` (neutral / "other") |
| Highlight | `#C8553D` (reference lines only) |
| Gridlines | Format → Lines → Grid Lines: None on bar charts; light grey on the dot plot |
| Borders | None on sheets; KPI cards: 1 px `#E1E5EA` border via Layout → Border |
| Numbers | Currency $ with thousands separator; percentages to 1 decimal; ratings to 2 decimals |

## 6. Validation checklist

With **no filters applied**, the dashboard must show these values (from `notebooks/customer_behaviour_analysis.ipynb`):

| Check | Expected |
|---|---|
| Customers | 3,900 |
| Revenue | $233,081 |
| Avg Spend | $59.76 |
| Avg Rating | 3.75 |
| Subscriber Share | 27.0% |
| Revenue by Category | Clothing $104,264 · Accessories $74,200 · Footwear $36,093 · Outerwear $18,524 |
| Avg Spend by Season | Fall $61.56 · Winter $60.36 · Spring $58.74 · Summer $58.41 |
| Segments: customers / subscriber share | New 83 / 18.1% · Returning 701 / 24.1% · Loyal 3,116 / 27.9% |
| Programme Overlap (Male) | Subscriber + discount 1,053 · Discount only 624 · Neither 975 |
| Programme Overlap (Female) | Neither 1,248 |
| Top state by revenue | Montana $5,784 (96 customers) |

If any value differs, check that the data source is `customer_clean.csv` and that no filter is active.

## 7. Publish

1. **File → Save to Tableau Public As…**, sign in, and name it "Customer Shopping Behaviour Analysis".
2. On the Tableau Public page, open the visualisation's settings and allow it to be shown on your profile.
3. Copy the link into the README (section "Tableau dashboard") and take screenshots of both dashboards into `dashboards/screenshots/` as `overview.png` and `segments_programmes.png`.
4. Keep the `.twbx` out of Git: it contains a copy of the dataset, whose redistribution terms are not confirmed. The Tableau Public link is the shareable version.

## What is deliberately not in the dashboard

- **No revenue trend over time:** the data has no dates (season is the only time-like field).
- **No retention, cohort, lifetime value or profit:** each customer has a single purchase, and there are no costs.
- **No ranking of products by rating:** ratings do not differ significantly across products (see Finding 5).
