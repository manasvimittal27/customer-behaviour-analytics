"""Group comparisons with significance tests.

Revenue totals by group mostly reflect how many customers are in each group.
These helpers always report the count, the share and the per-customer average
next to the total, plus a test of whether the averages genuinely differ.
"""
from __future__ import annotations

import pandas as pd
from scipy import stats


def compare_spend(df: pd.DataFrame, group: str, metric: str = "purchase_amount") -> tuple[pd.DataFrame, float]:
    """Customers, share, revenue and average spend per group, plus a p-value.

    Uses Welch's t-test for two groups and one-way ANOVA for more. The
    p-value answers: if every group truly spent the same on average, how
    likely is a gap at least this large by chance?
    """
    grouped = df.groupby(group, observed=True)[metric]
    table = pd.DataFrame({
        "customers": grouped.size(),
        "share_of_customers": grouped.size() / len(df),
        "revenue": grouped.sum(),
        "share_of_revenue": grouped.sum() / df[metric].sum(),
        "avg_spend": grouped.mean(),
    }).sort_values("revenue", ascending=False)

    samples = [values.to_numpy() for _, values in grouped]
    if len(samples) == 2:
        p_value = stats.ttest_ind(*samples, equal_var=False).pvalue
    else:
        p_value = stats.f_oneway(*samples).pvalue
    return table, float(p_value)


def compare_rate(df: pd.DataFrame, group: str, flag: str) -> tuple[pd.DataFrame, float]:
    """Share of each group where ``flag`` is true, plus a chi-square p-value."""
    counts = pd.crosstab(df[group], df[flag])
    table = pd.DataFrame({
        "customers": counts.sum(axis=1),
        "with_flag": counts.get(True, 0),
    })
    table["rate"] = table["with_flag"] / table["customers"]
    p_value = stats.chi2_contingency(counts)[1]
    return table, float(p_value)


def spend_test_summary(df: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    """One row per grouping: lowest and highest average spend, gap and p-value.

    ``significant_after_correction`` applies a Bonferroni correction for the
    number of groupings tested, because running many tests makes a few
    "significant" results likely by chance alone.
    """
    rows = []
    for group in groups:
        table, p_value = compare_spend(df, group)
        rows.append({
            "grouping": group,
            "groups": len(table),
            "lowest_avg_spend": table["avg_spend"].min(),
            "highest_avg_spend": table["avg_spend"].max(),
            "gap_usd": table["avg_spend"].max() - table["avg_spend"].min(),
            "p_value": p_value,
        })
    summary = pd.DataFrame(rows).set_index("grouping").sort_values("p_value")
    alpha = 0.05 / len(groups)
    summary["significant_at_5pct"] = summary["p_value"] < 0.05
    summary["significant_after_correction"] = summary["p_value"] < alpha
    return summary
