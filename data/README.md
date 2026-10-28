# Data

The dataset is **not committed** to this repository: its licence and redistribution terms have not been confirmed.

## Get the data

1. The file used here is `customer_shopping_behavior.csv` (3,900 rows, 18 columns), taken from the materials of the YouTube tutorial "COMPLETE Data Analytics Portfolio Project in 6 EASY Steps | Python + SQL + Power BI". Its columns match the Kaggle [Customer Shopping Trends Dataset](https://www.kaggle.com/datasets/iamsouravbanerjee/customer-shopping-trends-dataset) (`iamsouravbanerjee`), which appears to be the original source. Confirm the source and its licence on Kaggle before reusing the data.
2. Save it as `data/raw/customer_shopping_behavior.csv`, or set the `CUSTOMER_DATA_PATH` environment variable to its location.

`src/cleaning.py` checks the 18 column names on load and stops with a clear error if they differ.

## Files

| Path | Created by | Contents |
|---|---|---|
| `raw/customer_shopping_behavior.csv` | You (download) | Original data, never modified |
| `processed/customer_clean.csv` | `python -m src.cleaning` | Cleaned table used by Tableau and PostgreSQL (3,900 rows, 23 columns) |

Both folders are ignored by Git.

## Data dictionary (cleaned table)

| Column | Type | Description |
|---|---|---|
| `customer_id` | int | Unique customer ID (1–3,900); one row per customer |
| `age` | int | Age, 18–70 |
| `gender` | text | Male / Female |
| `item_purchased` | text | One of 25 products |
| `category` | text | Clothing, Accessories, Footwear, Outerwear |
| `purchase_amount` | int | Purchase value in USD (20–100) |
| `location` | text | US state (50) |
| `size`, `color` | text | Product attributes |
| `season` | text | Season of purchase (the only time-like field; no dates) |
| `review_rating` | float | 2.5–5.0; 37 missing values filled with the category median |
| `review_rating_imputed` | bool | True where the rating was filled |
| `subscription_status` | text | Yes / No |
| `shipping_type` | text | 6 shipping options |
| `discount_applied` | text | Yes / No (`Promo Code Used` was identical and is dropped) |
| `previous_purchases` | int | Number of earlier purchases, 1–50 |
| `payment_method` | text | 6 payment methods |
| `purchase_frequency` | text | Weekly, Fortnightly, Monthly, Quarterly, Annually (duplicate labels merged) |
| `purchase_frequency_days` | int | 7, 14, 30, 90, 365 |
| `age_group` | text | Young-Adult 18–31, Adult 32–44, Middle-Aged 45–57, Senior 58–70 (equal-sized bands) |
| `customer_segment` | text | New (1 previous purchase), Returning (2–10), Loyal (11+) |
| `is_repeat_buyer` | bool | More than 5 previous purchases |
| `product_rank_in_category` | int | Rank of the product within its category by purchase count; ties share a rank (as SQL `RANK()`) |

## Known limitations

- **Probably synthetic:** near-uniform category counts; subscribers, discount users and male customers stored as nested blocks of rows; spend and ratings unrelated to every other field.
- **No dates or order IDs:** no time trends, retention or lifetime value.
- **No costs or prices:** revenue only.
