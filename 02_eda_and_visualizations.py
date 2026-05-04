"""
02_eda_and_visualizations.py
Generate 6 visualizations at 300 DPI → figures/

Falls back gracefully when cleaned_transactions.parquet is absent:
  - Fig 2: computed from sample_transactions.parquet (density plot, correct)
  - Figs 1,3,4,5: loaded from pre-computed aggregates/ CSVs (full-dataset values)
  - Fig 6: loaded from aggregates/correlation_matrix.csv
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)
AGG = Path(__file__).parent / "aggregates"

sns.set_theme(style="whitegrid", font_scale=1.1)
FRAUD_COLOR = "#e74c3c"
LEGIT_COLOR = "#2ecc71"
DPI         = 300

# ── Load data ─────────────────────────────────────────────────────────────────
FULL   = Path(__file__).parent / "cleaned_transactions.parquet"
SAMPLE = AGG / "sample_transactions.parquet"

print("Loading data...")
if FULL.exists():
    df = pd.read_parquet(FULL)
    USE_PRECOMPUTED = False
    print(f"  Full parquet: {len(df):,} rows | fraud rate: {df['is_fraud'].mean():.4%}")
else:
    df = pd.read_parquet(SAMPLE)
    USE_PRECOMPUTED = True
    print(f"  Sample parquet: {len(df):,} rows (fraud rates will load from pre-computed aggregates)")


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")

# ═════════════════════════════════════════════════════════════════════════════
# Fig 1 — Fraud Rate by MCC Category (Top 15 highest-risk)
# ═════════════════════════════════════════════════════════════════════════════
print("Fig 1: Fraud rate by MCC...")
if USE_PRECOMPUTED:
    mcc_stats = (
        pd.read_csv(AGG / "fraud_by_mcc.csv")
        .rename(columns={"total_count": "count"})
        .query("count >= 500")
        .sort_values("fraud_rate_pct", ascending=False)
        .head(15)
        .sort_values("fraud_rate_pct")
        .set_index("mcc_label")
    )
else:
    mcc_stats = (
        df.groupby("mcc_label", observed=True)
        .agg(fraud_rate_pct=("is_fraud", lambda x: x.mean() * 100),
             count=("is_fraud", "count"))
        .query("count >= 500")
        .sort_values("fraud_rate_pct", ascending=False)
        .head(15)
        .sort_values("fraud_rate_pct")
    )

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(mcc_stats.index, mcc_stats["fraud_rate_pct"], color=FRAUD_COLOR, edgecolor="white")
ax.bar_label(bars, fmt="%.2f%%", padding=4, fontsize=9)
ax.set_xlabel("Fraud Rate (%)")
ax.set_title("Top 15 Merchant Categories by Fraud Rate", fontsize=13, fontweight="bold", pad=12)
ax.set_xlim(0, mcc_stats["fraud_rate_pct"].max() * 1.25)
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))
sns.despine(left=True)
save(fig, "fig1_fraud_by_mcc.png")

# ═════════════════════════════════════════════════════════════════════════════
# Fig 2 — Transaction Amount Distribution: Fraud vs. Legitimate (log scale)
# Always computed from available data — density plot is not affected by oversampling
# ═════════════════════════════════════════════════════════════════════════════
print("Fig 2: Amount distribution...")
legit  = df.loc[(df["is_fraud"] == 0) & (df["amount"] >= 0.01), "amount"]
fraud_ = df.loc[(df["is_fraud"] == 1) & (df["amount"] >= 0.01), "amount"]

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(np.log10(legit),  bins=80, color=LEGIT_COLOR, alpha=0.6, label="Legitimate", density=True)
ax.hist(np.log10(fraud_), bins=80, color=FRAUD_COLOR, alpha=0.8, label="Fraudulent",  density=True)
ax.set_xlabel(r"Transaction Amount ($\log_{10}$ USD)")
ax.set_ylabel("Density")
ax.set_title("Transaction Amount Distribution: Fraud vs. Legitimate",
             fontsize=13, fontweight="bold", pad=12)
x_ticks = [0, 1, 2, 3, 4]
ax.set_xticks(x_ticks)
ax.set_xticklabels(["$1", "$10", "$100", "$1K", "$10K"])
ax.legend(frameon=False)
sns.despine()
save(fig, "fig2_amount_distribution.png")

# ═════════════════════════════════════════════════════════════════════════════
# Fig 3 — Fraud Rate Heatmap: Hour of Day × Day of Week
# ═════════════════════════════════════════════════════════════════════════════
print("Fig 3: Time heatmap...")
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
if USE_PRECOMPUTED:
    pivot = pd.read_csv(AGG / "fraud_heatmap.csv", index_col=0).reindex(day_order)
    pivot.columns = [int(c) for c in pivot.columns]
else:
    pivot = (
        df.groupby(["day_of_week", "hour"], observed=True)["is_fraud"]
        .mean().mul(100)
        .unstack(level="hour")
        .reindex(day_order)
    )

fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap(pivot, ax=ax, cmap="YlOrRd",
            linewidths=0.3, linecolor="white",
            cbar_kws={"label": "Fraud Rate (%)"},
            fmt=".2f", annot=False)
ax.set_xlabel("Hour of Day (0–23)")
ax.set_ylabel("")
ax.set_title("Fraud Rate Heatmap: Hour of Day × Day of Week",
             fontsize=13, fontweight="bold", pad=12)
ax.tick_params(axis="x", rotation=0)
save(fig, "fig3_fraud_heatmap_time.png")

# ═════════════════════════════════════════════════════════════════════════════
# Fig 4 — Fraud Rate by Customer Demographics (Age Group & Income Bracket)
# ═════════════════════════════════════════════════════════════════════════════
print("Fig 4: Demographic fraud rates...")
if USE_PRECOMPUTED:
    age_rates    = pd.read_csv(AGG / "fraud_by_age.csv").set_index("age_group")["fraud_rate_pct"]
    income_rates = pd.read_csv(AGG / "fraud_by_income.csv").set_index("income_bracket")["fraud_rate_pct"]
else:
    age_rates    = df.groupby("age_group",    observed=True)["is_fraud"].mean().mul(100)
    income_rates = df.groupby("income_bracket", observed=True)["is_fraud"].mean().mul(100)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

ax1.bar(age_rates.index.astype(str), age_rates.values, color=FRAUD_COLOR, edgecolor="white")
for i, v in enumerate(age_rates.values):
    ax1.text(i, v + 0.001, f"{v:.3f}%", ha="center", va="bottom", fontsize=9)
ax1.set_xlabel("Age Group")
ax1.set_ylabel("Fraud Rate (%)")
ax1.set_title("Fraud Rate by Age Group", fontweight="bold")
ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f%%"))
sns.despine(ax=ax1)

ax2.bar(income_rates.index.astype(str), income_rates.values, color="#e67e22", edgecolor="white")
for i, v in enumerate(income_rates.values):
    ax2.text(i, v + 0.001, f"{v:.3f}%", ha="center", va="bottom", fontsize=9)
ax2.set_xlabel("Annual Income Bracket")
ax2.set_ylabel("Fraud Rate (%)")
ax2.set_title("Fraud Rate by Income Bracket", fontweight="bold")
ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f%%"))
ax2.tick_params(axis="x", rotation=15)
sns.despine(ax=ax2)

fig.suptitle("Fraud Rate by Customer Demographics", fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
save(fig, "fig4_fraud_by_demographic.png")

# ═════════════════════════════════════════════════════════════════════════════
# Fig 5 — Fraud Rate by Card Type / Transaction Method
# ═════════════════════════════════════════════════════════════════════════════
print("Fig 5: Card type fraud rates...")
if USE_PRECOMPUTED:
    chip_rates  = pd.read_csv(AGG / "fraud_by_use_chip.csv").set_index("use_chip")["fraud_rate_pct"].sort_values(ascending=False)
    ctype_rates = pd.read_csv(AGG / "fraud_by_card_type.csv").set_index("card_type")["fraud_rate_pct"].sort_values(ascending=False)
    chip_yn     = pd.read_csv(AGG / "fraud_by_has_chip.csv").set_index("has_chip")["fraud_rate_pct"]
else:
    chip_rates  = df.groupby("use_chip",  observed=True)["is_fraud"].mean().mul(100).sort_values(ascending=False)
    ctype_rates = df.groupby("card_type", observed=True)["is_fraud"].mean().mul(100).sort_values(ascending=False)
    chip_yn     = df.groupby("has_chip",  observed=True)["is_fraud"].mean().mul(100)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
colors_tx = [FRAUD_COLOR, "#e67e22", LEGIT_COLOR]
colors_ct = [FRAUD_COLOR, "#e67e22", LEGIT_COLOR]

axes[0].bar(chip_rates.index, chip_rates.values, color=colors_tx[:len(chip_rates)], edgecolor="white")
for i, v in enumerate(chip_rates.values):
    axes[0].text(i, v + 0.001, f"{v:.3f}%", ha="center", va="bottom", fontsize=9)
axes[0].set_title("By Transaction Method", fontweight="bold")
axes[0].set_ylabel("Fraud Rate (%)")
axes[0].tick_params(axis="x", rotation=12)
sns.despine(ax=axes[0])

axes[1].bar(ctype_rates.index, ctype_rates.values, color=colors_ct[:len(ctype_rates)], edgecolor="white")
for i, v in enumerate(ctype_rates.values):
    axes[1].text(i, v + 0.001, f"{v:.3f}%", ha="center", va="bottom", fontsize=9)
axes[1].set_title("By Card Type", fontweight="bold")
axes[1].set_ylabel("Fraud Rate (%)")
sns.despine(ax=axes[1])

axes[2].bar(chip_yn.index, chip_yn.values, color=[LEGIT_COLOR, FRAUD_COLOR], edgecolor="white")
for i, v in enumerate(chip_yn.values):
    axes[2].text(i, v + 0.001, f"{v:.3f}%", ha="center", va="bottom", fontsize=9)
axes[2].set_title("Chip-Enabled Card vs. No Chip", fontweight="bold")
axes[2].set_ylabel("Fraud Rate (%)")
axes[2].set_xlabel("Has Chip")
sns.despine(ax=axes[2])

fig.suptitle("Fraud Rate by Card Type and Transaction Method", fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
save(fig, "fig5_fraud_by_card_type.png")

# ═════════════════════════════════════════════════════════════════════════════
# Fig 6 — Correlation Heatmap of Numerical Features vs. is_fraud
# ═════════════════════════════════════════════════════════════════════════════
print("Fig 6: Correlation heatmap...")
num_cols  = ["is_fraud", "amount", "current_age", "yearly_income", "credit_score",
             "num_credit_cards", "credit_limit", "hour", "dow_num", "month"]
_corr_csv = AGG / "correlation_matrix.csv"
available = [c for c in num_cols if c in df.columns]
if len(available) == len(num_cols):
    corr = df[num_cols].astype(float).corr()
elif _corr_csv.exists():
    print("  Using pre-computed correlation_matrix.csv")
    corr = pd.read_csv(_corr_csv, index_col=0)
else:
    corr = df[available].astype(float).corr()

fig, ax = plt.subplots(figsize=(10, 8))
mask = np.zeros_like(corr, dtype=bool)
mask[np.triu_indices_from(mask)] = True
sns.heatmap(corr, mask=mask, ax=ax,
            cmap="coolwarm", center=0, vmin=-0.3, vmax=0.3,
            annot=True, fmt=".3f", linewidths=0.5,
            cbar_kws={"label": "Pearson r"})
ax.set_title("Correlation Matrix of Numerical Features (incl. is_fraud)",
             fontsize=13, fontweight="bold", pad=12)
fig.tight_layout()
save(fig, "fig6_correlation_heatmap.png")

print("\nAll 6 figures saved to figures/")

# ── EDA summary ───────────────────────────────────────────────────────────────
print("\n=== EDA SUMMARY ===")
if USE_PRECOMPUTED and (AGG / "overall_stats.json").exists():
    with open(AGG / "overall_stats.json") as f:
        stats = json.load(f)
    print(f"Total transactions: {stats['total_transactions']:,}")
    print(f"Fraud transactions: {stats['fraud_count']:,}")
    print(f"Fraud rate: {stats['fraud_rate_pct']:.4f}%")
    print(f"Median legit amount:  ${stats['median_legit_amount']:.2f}")
    print(f"Median fraud amount:  ${stats['median_fraud_amount']:.2f}")
else:
    print(f"Total transactions: {len(df):,}")
    print(f"Fraud transactions: {df['is_fraud'].sum():,}")
    print(f"Fraud rate: {df['is_fraud'].mean():.4%}")
    print(f"Median legit amount: ${legit.median():.2f}")
    print(f"Median fraud amount: ${fraud_.median():.2f}")

print(f"\nTop 3 fraud MCC categories:")
print(mcc_stats.tail(3)[["fraud_rate_pct"]].to_string())
print(f"\nFraud rate by transaction method:")
print(chip_rates.to_string())
print(f"\nFraud rate by card type:")
print(ctype_rates.to_string())
