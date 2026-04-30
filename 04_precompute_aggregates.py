"""
04_precompute_aggregates.py
Run locally to generate small aggregate files for the Streamlit dashboard.
Streamlit free tier cannot load the 1GB transactions CSV, so this script
produces tiny summary files (~KB each) + a stratified sample parquet (~15MB).
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
AGG  = BASE / "aggregates"
AGG.mkdir(exist_ok=True)

print("Loading parquet...")
df = pd.read_parquet(BASE / "cleaned_transactions.parquet")
print(f"  {len(df):,} rows | fraud rate: {df['is_fraud'].mean():.4%}")

# ── 1. Overall stats ──────────────────────────────────────────────────────────
legit  = df[(df["is_fraud"] == 0) & (df["amount"] >= 0.01)]["amount"]
fraud_ = df[(df["is_fraud"] == 1) & (df["amount"] >= 0.01)]["amount"]

stats = {
    "total_transactions": int(len(df)),
    "fraud_count":        int(df["is_fraud"].sum()),
    "legit_count":        int((df["is_fraud"] == 0).sum()),
    "fraud_rate_pct":     float(df["is_fraud"].mean() * 100),
    "median_legit_amount": float(legit.median()),
    "median_fraud_amount": float(fraud_.median()),
    "mean_legit_amount":   float(legit.mean()),
    "mean_fraud_amount":   float(fraud_.mean()),
    "date_min": str(df["date"].min().date()),
    "date_max": str(df["date"].max().date()),
}
with open(AGG / "overall_stats.json", "w") as f:
    json.dump(stats, f, indent=2)
print("  overall_stats.json")

# ── 2. Fraud by MCC ───────────────────────────────────────────────────────────
mcc = (
    df.groupby("mcc_label", observed=True)
    .agg(
        fraud_rate_pct=("is_fraud", lambda x: x.mean() * 100),
        fraud_count=("is_fraud", "sum"),
        total_count=("is_fraud", "count"),
    )
    .query("total_count >= 200")
    .sort_values("fraud_rate_pct", ascending=False)
    .reset_index()
)
mcc.to_csv(AGG / "fraud_by_mcc.csv", index=False)
print("  fraud_by_mcc.csv")

# ── 3. Amount histogram bins ──────────────────────────────────────────────────
bins = np.linspace(0, 4.5, 91)   # log10 scale: $1 to $31,623
legit_hist,  _ = np.histogram(np.log10(legit),  bins=bins)
fraud_hist,  _ = np.histogram(np.log10(fraud_), bins=bins)
bin_centers = (bins[:-1] + bins[1:]) / 2

hist_df = pd.DataFrame({
    "log10_amount": bin_centers,
    "legit_density": legit_hist / legit_hist.sum(),
    "fraud_density": fraud_hist / fraud_hist.sum(),
})
hist_df.to_csv(AGG / "amount_histogram.csv", index=False)
print("  amount_histogram.csv")

# ── 4. Fraud heatmap (hour × day_of_week) ────────────────────────────────────
day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
heatmap = (
    df.groupby(["day_of_week", "hour"], observed=True)["is_fraud"]
    .mean()
    .mul(100)
    .unstack(level="hour")
    .reindex(day_order)
)
heatmap.to_csv(AGG / "fraud_heatmap.csv")
print("  fraud_heatmap.csv")

# ── 5. Fraud by demographics ──────────────────────────────────────────────────
for col, fname in [("age_group", "fraud_by_age"), ("income_bracket", "fraud_by_income")]:
    out = (
        df.groupby(col, observed=True)
        .agg(
            fraud_rate_pct=("is_fraud", lambda x: x.mean() * 100),
            fraud_count=("is_fraud", "sum"),
            total_count=("is_fraud", "count"),
        )
        .reset_index()
    )
    out[col] = out[col].astype(str)
    out.to_csv(AGG / f"{fname}.csv", index=False)
    print(f"  {fname}.csv")

# ── 6. Fraud by card/transaction attributes ───────────────────────────────────
for col, fname in [
    ("use_chip",   "fraud_by_use_chip"),
    ("card_type",  "fraud_by_card_type"),
    ("card_brand", "fraud_by_card_brand"),
    ("has_chip",   "fraud_by_has_chip"),
]:
    out = (
        df.groupby(col, observed=True)
        .agg(
            fraud_rate_pct=("is_fraud", lambda x: x.mean() * 100),
            fraud_count=("is_fraud", "sum"),
            total_count=("is_fraud", "count"),
        )
        .reset_index()
    )
    out[col] = out[col].astype(str)
    out.to_csv(AGG / f"{fname}.csv", index=False)
    print(f"  {fname}.csv")

# ── 7. Correlation matrix ─────────────────────────────────────────────────────
num_cols = ["is_fraud","amount","current_age","yearly_income","credit_score",
            "num_credit_cards","credit_limit","hour","dow_num","month"]
corr = df[num_cols].astype(float).corr()
corr.to_csv(AGG / "correlation_matrix.csv")
print("  correlation_matrix.csv")

# ── 8. Fraud by month-year trend ─────────────────────────────────────────────
df["year_month"] = df["date"].dt.to_period("M").astype(str)
trend = (
    df.groupby("year_month")
    .agg(
        fraud_rate_pct=("is_fraud", lambda x: x.mean() * 100),
        fraud_count=("is_fraud", "sum"),
        total_count=("is_fraud", "count"),
    )
    .reset_index()
)
trend.to_csv(AGG / "fraud_by_month.csv", index=False)
print("  fraud_by_month.csv")

# ── 9. Fraud by gender ────────────────────────────────────────────────────────
gender = (
    df.groupby("gender", observed=True)
    .agg(
        fraud_rate_pct=("is_fraud", lambda x: x.mean() * 100),
        fraud_count=("is_fraud", "sum"),
        total_count=("is_fraud", "count"),
    )
    .reset_index()
)
gender["gender"] = gender["gender"].astype(str)
gender.to_csv(AGG / "fraud_by_gender.csv", index=False)
print("  fraud_by_gender.csv")

# ── 10. Stratified sample for explorer ───────────────────────────────────────
# All fraud + random 80K legit = ~93K rows, comfortable for Streamlit memory
fraud_rows = df[df["is_fraud"] == 1]
legit_rows = df[df["is_fraud"] == 0].sample(n=80_000, random_state=42)
sample = pd.concat([fraud_rows, legit_rows]).sample(frac=1, random_state=42)

keep_cols = ["date","amount","use_chip","mcc_label","merchant_city","merchant_state",
             "is_fraud","current_age","gender","yearly_income","card_type","has_chip",
             "card_brand","age_group","income_bracket","hour","day_of_week","month"]
sample = sample[keep_cols].copy()
sample["use_chip"]        = sample["use_chip"].astype(str)
sample["mcc_label"]       = sample["mcc_label"].astype(str)
sample["merchant_city"]   = sample["merchant_city"].astype(str)
sample["merchant_state"]  = sample["merchant_state"].astype(str)
sample["card_type"]       = sample["card_type"].astype(str)
sample["card_brand"]      = sample["card_brand"].astype(str)
sample["has_chip"]        = sample["has_chip"].astype(str)
sample["age_group"]       = sample["age_group"].astype(str)
sample["income_bracket"]  = sample["income_bracket"].astype(str)
sample["day_of_week"]     = sample["day_of_week"].astype(str)

out_path = AGG / "sample_transactions.parquet"
sample.to_parquet(out_path, index=False)
size_mb = out_path.stat().st_size / 1_048_576
print(f"  sample_transactions.parquet ({len(sample):,} rows, {size_mb:.1f} MB)")

print(f"\nAll aggregates saved to: {AGG}")
print(f"Files:")
for f in sorted(AGG.iterdir()):
    print(f"  {f.name}: {f.stat().st_size / 1024:.1f} KB")
