"""Render design references for the two Tableau dashboards from the real data.

    python -m src.dashboard_mockups

These are layout and number references for building the dashboards in
Tableau, not the dashboards themselves. Output: documentation/*.png
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from src.charts import ACCENT, INK, MUTED, PRIMARY, set_chart_style
from src.cleaning import REPO_ROOT, clean, load_raw

OUT = REPO_ROOT / "documentation"
LIGHT = "#7fb3d5"


def kpi(ax, label, value):
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False, edgecolor="#e1e5ea", linewidth=1.2))
    ax.text(0.08, 0.74, label, transform=ax.transAxes, fontsize=10, color="#5f6b76")
    ax.text(0.08, 0.14, value, transform=ax.transAxes, fontsize=22, fontweight="bold", color=INK)


def overview(df):
    fig = plt.figure(figsize=(14, 9))
    grid = fig.add_gridspec(3, 5, height_ratios=[0.55, 2.2, 2.0], hspace=0.55, wspace=0.35, top=0.86)
    fig.suptitle("Customer & Revenue Overview", x=0.125, y=0.97, ha="left", fontsize=17, fontweight="bold", color=INK)
    fig.text(0.125, 0.925, "3,900 customers, one purchase each. Average spend is about $60 in every group; "
             "revenue differences come from customer counts.", fontsize=10, color="#5f6b76")
    fig.text(0.9, 0.895, "Filters:  Gender ▾   Age group ▾   Season ▾   Subscription ▾", ha="right", fontsize=9, color="#5f6b76")

    subs = (df["subscription_status"] == "Yes").mean()
    for i, (label, value) in enumerate([
        ("Customers", f"{df['customer_id'].nunique() / 1000:.1f}K"),
        ("Revenue", f"${df['purchase_amount'].sum() / 1000:.1f}K"),
        ("Avg Spend", f"${df['purchase_amount'].mean():.2f}"),
        ("Avg Rating", f"{df['review_rating'].mean():.2f}"),
        ("Subscriber Share", f"{subs:.1%}"),
    ]):
        kpi(fig.add_subplot(grid[0, i]), label, value)

    ax = fig.add_subplot(grid[1, :2])
    cat = df.groupby("category")["purchase_amount"].sum().sort_values()
    ax.barh(cat.index, cat.values, color=PRIMARY)
    for y, v in enumerate(cat.values):
        ax.text(v + 1500, y, f"${v:,.0f}", va="center", fontsize=9, color=INK)
    ax.set_title("Revenue by Category")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x / 1000:.0f}K"))
    ax.set_xlim(0, cat.max() * 1.22)
    ax.grid(axis="y", visible=False)

    ax = fig.add_subplot(grid[1, 2:])
    states = df.groupby("location")["purchase_amount"].sum().sort_values(ascending=False)
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor="#f4f7fa", edgecolor="#e1e5ea"))
    ax.set_title("Revenue by State")
    ax.text(0.5, 0.62, "Filled map in Tableau\n(colour = revenue)", transform=ax.transAxes, ha="center",
            fontsize=12, color="#5f6b76")
    ax.text(0.5, 0.3, f"Highest: {states.index[0]} \\${states.iloc[0]:,}   ·   Lowest: {states.index[-1]} \\${states.iloc[-1]:,}",
            transform=ax.transAxes, ha="center", fontsize=10, color=INK)

    ax = fig.add_subplot(grid[2, :])
    g = df.groupby("gender")["purchase_amount"].agg(["mean", "count"])
    ax.scatter(g["mean"], g.index, s=90, color=PRIMARY, zorder=3)
    overall = df["purchase_amount"].mean()
    ax.axvline(overall, color=ACCENT, linestyle="--", linewidth=1.2)
    ax.text(overall + 0.05, 1.35, f"Overall ${overall:.2f}", color=ACCENT, fontsize=9)
    for y, (m, n) in enumerate(zip(g["mean"], g["count"])):
        ax.text(m + 0.08, y - 0.18, f"${m:.2f}  (n={n:,})", fontsize=9, color=INK)
    ax.set_xlim(56, 64)
    ax.set_ylim(-0.6, 1.6)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:.0f}"))
    ax.set_title("Spend by Group      Compare by: [ Gender ▾ ]")
    ax.grid(axis="y", visible=False)

    fig.text(0.5, 0.01, "Design reference rendered in Python from the cleaned data. Build the real dashboard in Tableau "
             "(documentation/tableau_build_guide.md).", ha="center", fontsize=8, color="#8a96a3")
    fig.savefig(OUT / "dashboard_mockup_overview.png")
    plt.close(fig)


def segments(df):
    fig = plt.figure(figsize=(14, 9))
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.1], hspace=0.45, wspace=0.3)
    fig.suptitle("Segments & Programmes", x=0.125, y=0.97, ha="left", fontsize=17, fontweight="bold", color=INK)

    ax = fig.add_subplot(grid[0, 0])
    order = ["New", "Returning", "Loyal"]
    rate = df.groupby("customer_segment", observed=True)["subscription_status"].apply(lambda s: (s == "Yes").mean()).reindex(order)
    n = df["customer_segment"].value_counts().reindex(order)
    ax.barh(order[::-1], rate[::-1], color=[PRIMARY, LIGHT, MUTED])
    for y, (r, c) in enumerate(zip(rate[::-1], n[::-1])):
        ax.text(r + 0.005, y, f"{r:.1%}  (n={c:,})", va="center", fontsize=9, color=INK)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlim(0, 0.4)
    ax.set_title("Subscription rate by Segment")
    ax.grid(axis="y", visible=False)

    ax = fig.add_subplot(grid[0, 1])
    combo = np.select([df["subscription_status"].eq("Yes"), df["discount_applied"].eq("Yes")],
                      ["Subscriber + discount", "Discount only"], default="Neither")
    import pandas as pd
    mix = pd.crosstab(df["gender"], combo).reindex(columns=["Subscriber + discount", "Discount only", "Neither"], fill_value=0)
    left = np.zeros(len(mix))
    for col, color in zip(mix.columns, [PRIMARY, LIGHT, MUTED]):
        ax.barh(mix.index, mix[col], left=left, color=color, label=col)
        for i, (v, s) in enumerate(zip(mix[col], left)):
            if v:
                ax.text(s + v / 2, i, f"{v:,}", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        left += mix[col].to_numpy()
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
    ax.set_title("Programme Overlap")
    ax.grid(axis="y", visible=False)

    ax = fig.add_subplot(grid[1, :])
    counts = df.groupby(["category", "item_purchased"]).size().rename("customers").reset_index()
    counts["rank"] = counts.groupby("category")["customers"].rank(ascending=False, method="min")
    top = counts[counts["rank"] <= 3].sort_values(["category", "rank", "item_purchased"])
    labels = [f"{c} · #{int(r)} {i}" for c, r, i in zip(top["category"], top["rank"], top["item_purchased"])]
    ax.barh(labels[::-1], top["customers"].to_numpy()[::-1], color=PRIMARY)
    for y, v in enumerate(top["customers"].to_numpy()[::-1]):
        ax.text(v + 1, y, str(v), va="center", fontsize=9, color=INK)
    ax.set_title("Top 3 Products per Category (ties share a rank)")
    ax.set_xlim(0, 190)
    ax.grid(axis="y", visible=False)

    fig.text(0.5, 0.01, "Design reference rendered in Python from the cleaned data. Build the real dashboard in Tableau "
             "(documentation/tableau_build_guide.md).", ha="center", fontsize=8, color="#8a96a3")
    fig.savefig(OUT / "dashboard_mockup_segments.png")
    plt.close(fig)


if __name__ == "__main__":
    set_chart_style()
    OUT.mkdir(exist_ok=True)
    data = clean(load_raw())
    overview(data)
    segments(data)
    print(f"Wrote mockups to {OUT}")
