"""Unit tests for the cleaning rules and comparison helpers, on a small hand-made dataset."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analysis import compare_rate, compare_spend  # noqa: E402
from src.cleaning import EXPECTED_COLUMNS, clean, quality_report, to_snake_case  # noqa: E402


def make_raw(n=8):
    rows = []
    for i in range(n):
        rows.append({
            "Customer ID": i + 1,
            "Age": 20 + i * 6,
            "Gender": "Male" if i % 2 else "Female",
            "Item Purchased": "Shirt",
            "Category": "Clothing" if i < 5 else "Footwear",
            "Purchase Amount (USD)": 40 + i * 5,
            "Location": "Ohio",
            "Size": "M",
            "Color": "Blue",
            "Season": "Fall",
            "Review Rating": None if i == 0 else 3.0 + i * 0.1,
            "Subscription Status": "Yes" if i % 3 == 0 else "No",
            "Shipping Type": "Standard",
            "Discount Applied": "Yes" if i % 2 else "No",
            "Promo Code Used": "Yes" if i % 2 else "No",
            "Previous Purchases": [1, 2, 10, 11, 30, 5, 6, 50][i],
            "Payment Method": "Cash",
            "Frequency of Purchases": ["Bi-Weekly", "Fortnightly", "Every 3 Months", "Quarterly",
                                       "Weekly", "Monthly", "Annually", "Weekly"][i],
        })
    raw = pd.DataFrame(rows)
    assert list(raw.columns) == EXPECTED_COLUMNS
    return raw


def test_snake_case_names():
    assert to_snake_case(pd.Index(["Purchase Amount (USD)", "Customer ID"])) == ["purchase_amount", "customer_id"]


def test_clean_keeps_every_row_and_revenue():
    raw = make_raw()
    df = clean(raw)
    assert len(df) == len(raw)
    assert df["purchase_amount"].sum() == raw["Purchase Amount (USD)"].sum()


def test_missing_rating_filled_with_category_median_and_flagged():
    df = clean(make_raw())
    clothing_known = [3.1, 3.2, 3.3, 3.4]
    assert df.loc[0, "review_rating"] == pytest.approx(pd.Series(clothing_known).median())
    assert df["review_rating_imputed"].tolist() == [True] + [False] * 7


def test_duplicate_frequency_labels_merged():
    df = clean(make_raw())
    assert set(df["purchase_frequency"]) == {"Weekly", "Fortnightly", "Monthly", "Quarterly", "Annually"}
    assert df.loc[0, "purchase_frequency_days"] == df.loc[1, "purchase_frequency_days"] == 14


def test_promo_column_dropped_only_when_identical():
    df = clean(make_raw())
    assert "promo_code_used" not in df.columns
    raw = make_raw()
    raw.loc[0, "Promo Code Used"] = "Yes"
    with pytest.raises(AssertionError):
        clean(raw)


def test_segments_match_sql_thresholds():
    df = clean(make_raw())
    by_previous = dict(zip(df["previous_purchases"], df["customer_segment"].astype(str)))
    assert by_previous[1] == "New"
    assert by_previous[2] == by_previous[10] == "Returning"
    assert by_previous[11] == by_previous[50] == "Loyal"


def test_quality_report_counts_missing_ratings():
    report = quality_report(make_raw()).set_index("check")["rows"]
    assert report["Missing Review Rating"] == 1


def test_compare_spend_shares_sum_to_one():
    table, p_value = compare_spend(clean(make_raw()), "gender")
    assert table["share_of_customers"].sum() == pytest.approx(1)
    assert table["share_of_revenue"].sum() == pytest.approx(1)
    assert 0 <= p_value <= 1


def test_compare_rate():
    df = clean(make_raw())
    df["is_subscriber"] = df["subscription_status"].eq("Yes")
    table, _ = compare_rate(df, "gender", "is_subscriber")
    assert table["customers"].sum() == len(df)


def test_product_rank_ties_share_rank():
    raw = make_raw()
    raw.loc[5:, "Item Purchased"] = ["Shoes", "Boots", "Boots"]
    df = clean(raw)
    footwear = df[df["category"] == "Footwear"].set_index("item_purchased")["product_rank_in_category"]
    assert footwear["Boots"].iloc[0] == 1 and footwear["Shoes"] == 2
