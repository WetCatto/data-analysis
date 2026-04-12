"""
01_load_and_clean.py
Load, merge, clean all datasets → save cleaned_transactions.parquet
"""
import json
import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT  = Path(__file__).parent

# ── 1. Fraud labels ──────────────────────────────────────────────────────────
print("Loading fraud labels...")
with open(DATA / "train_fraud_labels.json") as f:
    raw = json.load(f)
fraud_dict = raw["target"]  # {str(id): "Yes"/"No"}
fraud_series = pd.Series(fraud_dict).rename("is_fraud")
fraud_series.index = fraud_series.index.astype(int)
fraud_series = (fraud_series == "Yes").astype("int8")
print(f"  Labels: {len(fraud_series):,} | fraud rate: {fraud_series.mean():.4%}")

# ── 2. Transactions (optimized dtypes) ───────────────────────────────────────
print("Loading transactions...")
dtypes = {
    "id":           "int32",
    "client_id":    "int32",
    "card_id":      "int32",
    "use_chip":     "category",
    "merchant_id":  "int32",
    "merchant_city":"category",
    "merchant_state":"category",
    "mcc":          "int16",
    "errors":       "category",
}
tx = pd.read_csv(
    DATA / "transactions_data.csv",
    dtype=dtypes,
    parse_dates=["date"],
    low_memory=False,
)
print(f"  Rows: {len(tx):,} | cols: {list(tx.columns)}")

# Clean amount: strip "$", cast float32
tx["amount"] = tx["amount"].str.replace(r"[\$,]", "", regex=True).astype("float32")

# Merge fraud labels (inner join keeps only labelled rows)
tx = tx.set_index("id").join(fraud_series, how="inner").reset_index()
print(f"  After label join: {len(tx):,} rows | fraud rate: {tx['is_fraud'].mean():.4%}")

# ── 3. Users ─────────────────────────────────────────────────────────────────
print("Loading users...")
users = pd.read_csv(DATA / "users_data.csv", low_memory=False)
for col in ["per_capita_income", "yearly_income", "total_debt"]:
    users[col] = users[col].astype(str).str.replace(r"[\$,]", "", regex=True).astype("float32")
users = users.rename(columns={"id": "client_id"})

# ── 4. Cards ─────────────────────────────────────────────────────────────────
print("Loading cards...")
cards = pd.read_csv(DATA / "cards_data.csv", low_memory=False)
cards["credit_limit"] = cards["credit_limit"].astype(str).str.replace(r"[\$,]", "", regex=True).astype("float32")
cards = cards.rename(columns={"id": "card_id"})

# ── 5. Merge ─────────────────────────────────────────────────────────────────
print("Merging...")
df = tx.merge(
    users[["client_id","current_age","gender","yearly_income","credit_score","num_credit_cards"]],
    on="client_id", how="left"
).merge(
    cards[["card_id","card_brand","card_type","has_chip","credit_limit","card_on_dark_web"]],
    on="card_id", how="left"
)

# ── 6. MCC labels ─────────────────────────────────────────────────────────────
with open(DATA / "mcc_codes.json") as f:
    mcc_map = json.load(f)
df["mcc_label"] = df["mcc"].astype(str).map(mcc_map).fillna("Other").astype("category")

# ── 7. Datetime features ──────────────────────────────────────────────────────
df["hour"]        = df["date"].dt.hour.astype("int8")
df["day_of_week"] = df["date"].dt.day_name().astype("category")
df["month"]       = df["date"].dt.month.astype("int8")
df["dow_num"]     = df["date"].dt.dayofweek.astype("int8")  # 0=Mon

# ── 8. Nulls ──────────────────────────────────────────────────────────────────
before = len(df)
df = df.dropna(subset=["amount", "is_fraud"])
print(f"  Dropped {before - len(df):,} rows with null amount/is_fraud")

# Fill categorical nulls
for col in df.select_dtypes("category").columns:
    df[col] = df[col].cat.add_categories("Unknown").fillna("Unknown")

# Age group
df["age_group"] = pd.cut(
    df["current_age"],
    bins=[0, 25, 35, 45, 55, 65, 120],
    labels=["<25", "25–34", "35–44", "45–54", "55–64", "65+"]
)

# Income bracket
df["income_bracket"] = pd.cut(
    df["yearly_income"],
    bins=[0, 30000, 60000, 100000, 150000, 1e9],
    labels=["<30k", "30–60k", "60–100k", "100–150k", "150k+"]
)

# ── 9. Save ───────────────────────────────────────────────────────────────────
out_path = OUT / "cleaned_transactions.parquet"
df.to_parquet(out_path, index=False)
print(f"\nSaved → {out_path}")
print(f"Final shape: {df.shape}")
print(f"Overall fraud rate: {df['is_fraud'].mean():.4%}")
print(f"Fraud count: {df['is_fraud'].sum():,}")
print(f"\nColumns: {list(df.columns)}")
