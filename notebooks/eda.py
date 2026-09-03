"""Reproducible EDA for the validated workforce-planning sample.

Creates three purposeful, aggregate charts: workforce productivity by organization,
missingness after cleaning, and a correlation view of capacity/cost/output drivers.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Keep graphics/font caches inside the project when HOME is read-only (e.g. CI).
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INPUT = ROOT / "data/staging/workforce_snapshot_clean.csv"
FIGURES = ROOT / "reports/figures"


def main() -> None:
    if not INPUT.exists():
        raise FileNotFoundError("Run `python3 src/pipeline.py` before EDA.")
    FIGURES.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT, parse_dates=["snapshot_date", "hire_date", "termination_date"])
    numeric = ["fte_fraction", "scheduled_hours", "productive_hours", "accepted_output_units", "labor_cost_inr"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame["productivity_per_hour"] = frame["accepted_output_units"] / frame["productive_hours"].replace(0, np.nan)
    frame["capacity_shortfall_hours"] = frame["scheduled_hours"] - frame["productive_hours"]

    # Aggregate chart: avoids publishing worker-level productivity.
    by_org = frame.groupby("org_name", as_index=False).agg(productive_hours=("productive_hours", "sum"), accepted_output_units=("accepted_output_units", "sum"))
    by_org["productivity_per_hour"] = by_org["accepted_output_units"] / by_org["productive_hours"]
    ax = by_org.sort_values("productivity_per_hour").plot.barh(x="org_name", y="productivity_per_hour", legend=False, color="#1f77b4", figsize=(7, 4))
    ax.set(title="Quality-accepted output per productive hour", xlabel="Output units per hour", ylabel="Organization")
    plt.tight_layout(); plt.savefig(FIGURES / "productivity_by_organization.png", dpi=160); plt.close()

    missing = frame.isna().mean().mul(100).sort_values(ascending=False)
    ax = missing[missing > 0].plot.bar(color="#ff7f0e", figsize=(8, 4))
    ax.set(title="Post-cleaning missingness (optional fields only)", xlabel="Field", ylabel="Missing values (%)")
    plt.tight_layout(); plt.savefig(FIGURES / "missingness_profile.png", dpi=160); plt.close()

    q1, q3 = frame["productivity_per_hour"].quantile([.25, .75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    ax = frame["productivity_per_hour"].dropna().plot.hist(bins=8, color="#2ca02c", edgecolor="white", figsize=(7, 4))
    ax.axvline(lower, color="#d62728", linestyle="--", label="IQR outlier bounds")
    ax.axvline(upper, color="#d62728", linestyle="--")
    ax.set(title="Distribution of productivity per productive hour", xlabel="Output units per hour", ylabel="Worker records")
    ax.legend(); plt.tight_layout(); plt.savefig(FIGURES / "productivity_distribution_outliers.png", dpi=160); plt.close()

    correlation_fields = ["fte_fraction", "scheduled_hours", "productive_hours", "accepted_output_units", "labor_cost_inr", "capacity_shortfall_hours", "productivity_per_hour"]
    corr = frame[correlation_fields].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7, 6)); image = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(range(len(corr)), corr.columns, rotation=40, ha="right"); ax.set_yticks(range(len(corr)), corr.index)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=ax, label="Pearson correlation"); ax.set_title("Capacity, cost, output, and productivity drivers")
    plt.tight_layout(); plt.savefig(FIGURES / "workforce_driver_correlations.png", dpi=160); plt.close()

    outliers = ((frame["productivity_per_hour"] < lower) | (frame["productivity_per_hour"] > upper)).sum()
    print("Rows:", len(frame), "| Outlier candidates (IQR productivity):", int(outliers))


if __name__ == "__main__":
    main()
