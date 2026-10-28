"""Load, audit and clean the customer shopping behaviour dataset.

Every cleaning rule lives here so the notebook, the PostgreSQL load and the
Tableau export all use exactly the same data. Run as a script to write the
cleaned file used by Tableau:

    python -m src.cleaning
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_PATH = REPO_ROOT / "data" / "raw" / "customer_shopping_behavior.csv"
PROCESSED_PATH = REPO_ROOT / "data" / "processed" / "customer_clean.csv"

EXPECTED_COLUMNS = [
    "Customer ID", "Age", "Gender", "Item Purchased", "Category",
    "Purchase Amount (USD)", "Location", "Size", "Color", "Season",
    "Review Rating", "Subscription Status", "Shipping Type", "Discount Applied",
    "Promo Code Used", "Previous Purchases", "Payment Method", "Frequency of Purchases",
]

# Two pairs of categories mean the same thing in the raw data.
FREQUENCY_LABELS = {
    "Weekly": "Weekly",
    "Bi-Weekly": "Fortnightly",
    "Fortnightly": "Fortnightly",
    "Monthly": "Monthly",
    "Every 3 Months": "Quarterly",
    "Quarterly": "Quarterly",
    "Annually": "Annually",
}
FREQUENCY_DAYS = {"Weekly": 7, "Fortnightly": 14, "Monthly": 30, "Quarterly": 90, "Annually": 365}

AGE_GROUP_LABELS = ["Young-Adult", "Adult", "Middle-Aged", "Senior"]

# Same thresholds as sql/business_questions.sql (Q7).
SEGMENT_BINS = [0, 1, 10, np.inf]
SEGMENT_LABELS = ["New", "Returning", "Loyal"]


def resolve_raw_path(path: str | os.PathLike | None = None) -> Path:
    """Explicit path, else the CUSTOMER_DATA_PATH environment variable, else data/raw/."""
    candidate = Path(path or os.environ.get("CUSTOMER_DATA_PATH") or DEFAULT_RAW_PATH)
    if not candidate.exists():
        raise FileNotFoundError(
            f"Dataset not found at {candidate}. See data/README.md for where to get "
            "customer_shopping_behavior.csv, or set CUSTOMER_DATA_PATH."
        )
    return candidate


def load_raw(path: str | os.PathLike | None = None) -> pd.DataFrame:
    """Load the raw CSV unchanged and check it has the expected columns."""
    raw = pd.read_csv(resolve_raw_path(path))
    missing = set(EXPECTED_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Unexpected file layout, missing columns: {sorted(missing)}")
    return raw


def to_snake_case(columns: pd.Index) -> list[str]:
    """'Purchase Amount (USD)' -> 'purchase_amount'; 'Customer ID' -> 'customer_id'."""
    return [
        c.strip().lower().replace(" (usd)", "").replace(" ", "_")
        for c in columns
    ]


def quality_report(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per data-quality check, with the number of affected rows."""
    checks = [
        ("Rows", len(raw)),
        ("Duplicate rows", int(raw.duplicated().sum())),
        ("Duplicate Customer IDs", int(raw["Customer ID"].duplicated().sum())),
        ("Missing Review Rating", int(raw["Review Rating"].isna().sum())),
        ("Missing values in other columns", int(raw.drop(columns="Review Rating").isna().sum().sum())),
        ("Age outside 18-100", int((~raw["Age"].between(18, 100)).sum())),
        ("Purchase amount <= 0", int((raw["Purchase Amount (USD)"] <= 0).sum())),
        ("Review rating outside 1-5", int((~raw["Review Rating"].dropna().between(1, 5)).sum())),
        ("Previous purchases < 1", int((raw["Previous Purchases"] < 1).sum())),
        ("Rows where Promo Code Used differs from Discount Applied",
         int((raw["Promo Code Used"] != raw["Discount Applied"]).sum())),
        ("Subscribers without a discount",
         int(((raw["Subscription Status"] == "Yes") & (raw["Discount Applied"] == "No")).sum())),
        ("Female subscribers", int(((raw["Gender"] == "Female") & (raw["Subscription Status"] == "Yes")).sum())),
        ("Female customers with a discount", int(((raw["Gender"] == "Female") & (raw["Discount Applied"] == "Yes")).sum())),
        ("Rows in duplicate frequency labels (Bi-Weekly or Every 3 Months)",
         int(raw["Frequency of Purchases"].isin(["Bi-Weekly", "Every 3 Months"]).sum())),
    ]
    return pd.DataFrame(checks, columns=["check", "rows"])


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the cleaned, analysis-ready table (one row per customer purchase).

    Rules, in order:
    1. snake_case column names; ``purchase_amount`` is in USD.
    2. Missing review ratings are filled with the median rating of the same
       category, and ``review_rating_imputed`` records which rows were filled.
    3. ``promo_code_used`` is dropped: it is identical to ``discount_applied``
       on every row (checked here, not assumed).
    4. Frequency labels with the same meaning are merged (Bi-Weekly ->
       Fortnightly, Every 3 Months -> Quarterly) and converted to days.
    5. Derived fields: ``age_group`` (four equal-sized age bands),
       ``customer_segment`` (New / Returning / Loyal by previous purchases),
       ``is_repeat_buyer`` (more than 5 previous purchases) and
       ``product_rank_in_category`` (purchase-count rank of the product within
       its category; ties share a rank, as in SQL ``RANK()``).
    """
    df = raw.copy()
    df.columns = to_snake_case(df.columns)

    df["review_rating_imputed"] = df["review_rating"].isna()
    df["review_rating"] = df.groupby("category")["review_rating"].transform(
        lambda ratings: ratings.fillna(ratings.median())
    )

    assert (df["promo_code_used"] == df["discount_applied"]).all(), (
        "promo_code_used is no longer identical to discount_applied; review before dropping it"
    )
    df = df.drop(columns="promo_code_used")

    df["purchase_frequency"] = df["frequency_of_purchases"].str.strip().map(FREQUENCY_LABELS)
    df["purchase_frequency_days"] = df["purchase_frequency"].map(FREQUENCY_DAYS)
    df = df.drop(columns="frequency_of_purchases")

    df["age_group"] = pd.qcut(df["age"], q=4, labels=AGE_GROUP_LABELS)
    df["customer_segment"] = pd.cut(df["previous_purchases"], SEGMENT_BINS, labels=SEGMENT_LABELS)
    df["is_repeat_buyer"] = df["previous_purchases"] > 5

    # Rank of each row's product within its category by number of purchases;
    # ties share a rank, like SQL RANK(). Lets Tableau filter to the top 3.
    products = df.groupby(["category", "item_purchased"]).size().rename("purchases").reset_index()
    products["product_rank_in_category"] = (
        products.groupby("category")["purchases"].rank(method="min", ascending=False).astype(int)
    )
    df = df.merge(products[["category", "item_purchased", "product_rank_in_category"]],
                  on=["category", "item_purchased"], how="left")

    validate(df, raw)
    return df


def validate(df: pd.DataFrame, raw: pd.DataFrame) -> None:
    """Fail loudly if cleaning lost rows or left gaps."""
    assert len(df) == len(raw), "cleaning must not drop rows"
    assert df["customer_id"].is_unique, "customer_id must identify one row"
    assert not df.isna().any().any(), f"missing values remain: {df.columns[df.isna().any()].tolist()}"
    assert df["purchase_amount"].sum() == raw["Purchase Amount (USD)"].sum(), "revenue changed during cleaning"
    assert int(df["review_rating_imputed"].sum()) == int(raw["Review Rating"].isna().sum())


def write_processed(df: pd.DataFrame, path: Path = PROCESSED_PATH) -> Path:
    """Write the cleaned table as CSV (used by Tableau and the PostgreSQL load)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


if __name__ == "__main__":
    cleaned = clean(load_raw())
    out = write_processed(cleaned)
    print(f"Wrote {len(cleaned):,} rows x {cleaned.shape[1]} columns to {out}")
