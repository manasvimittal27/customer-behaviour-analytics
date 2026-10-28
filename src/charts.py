"""Shared chart style and helpers, so every figure in the project looks the same."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

PRIMARY = "#2a6f97"
MUTED = "#a7b3bd"
ACCENT = "#c8553d"
INK = "#1f2933"


def set_chart_style() -> None:
    import matplotlib as mpl
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="notebook")
    mpl.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelcolor": INK,
        "axes.edgecolor": "#d0d7de",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": "#eef1f4",
        "legend.frameon": False,
    })


def mean_ci(values: pd.Series, confidence: float = 0.95) -> tuple[float, float]:
    """Mean and half-width of a t-based confidence interval."""
    values = values.dropna()
    half = stats.t.ppf((1 + confidence) / 2, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
    return values.mean(), half


def proportion_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Proportion and half-width of a normal-approximation 95% interval."""
    p = successes / n
    return p, z * np.sqrt(p * (1 - p) / n)
