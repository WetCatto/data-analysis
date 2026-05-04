# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (dashboard only)
pip install -r requirements.txt

# Install full pipeline dependencies (needed for scripts 01–04)
pip install -r requirements.txt python-docx pyarrow tqdm

# Run the full local pipeline (requires raw Kaggle CSVs in data/)
python 01_load_and_clean.py          # ~3 min → cleaned_transactions.parquet (245MB, gitignored)
python 02_eda_and_visualizations.py  # → figures/ static PNGs for the Word report
python 03_build_report_humanized.py  # → Transaction_Fraud_Analysis_Report.docx
python 04_precompute_aggregates.py   # → aggregates/ CSVs + sample_transactions.parquet

# Launch the dashboard
streamlit run app.py
```

Raw Kaggle CSVs (`transactions_data.csv`, `users_data.csv`, `cards_data.csv`, `train_fraud_labels.json`, `mcc_codes.json`) go in `data/` and are gitignored along with `cleaned_transactions.parquet`.

## Architecture

The project has two independent parts: a **local data pipeline** and a **Streamlit dashboard**.

### Local pipeline (scripts 01–04)

Numbered scripts run sequentially and are only needed when re-generating outputs from the raw data:

- `01_load_and_clean.py` — merges raw CSVs, labels fraud, engineers features (age_group, income_bracket, hour, day_of_week, mcc_label, etc.) → `cleaned_transactions.parquet`
- `02_eda_and_visualizations.py` — generates `figures/fig{1-6}_*.png` at 300 DPI. Has a graceful fallback: if `cleaned_transactions.parquet` is absent it reads from `aggregates/` CSVs instead, so it runs without the full parquet.
- `03_build_report_humanized.py` / `03_build_report.py` — generates the Word report from `figures/` and hardcoded findings.
- `04_precompute_aggregates.py` — reads the full parquet and writes all `aggregates/` files (CSVs + stratified sample parquet). Re-run this whenever `cleaned_transactions.parquet` changes.

### Dashboard (`app.py`)

Deployed to Streamlit Community Cloud free tier. It loads **only** from `aggregates/` (committed to git: ~25KB of CSVs + a 2MB stratified sample parquet). It never reads the full parquet.

**Design system** (all defined at the top of `app.py`):
- Design tokens: `BG`, `CARD`, `BORDER`, `TXT_PRI/SEC/TER`, `DANGER`, `WARNING`, `SAFE`, `INFO`, `CAT`, `AVG_RATE`
- Layout helpers: `section(label, description)`, `insight_row(finding, insight)`
- Plotly helpers: `chart_layout(**kw)`, `xax(**kw)`, `yax(**kw)`, `pchart(fig, height)`
- Chart helpers: `lollipop_chart(...)`, `demographic_bar(...)`
- All data loaders decorated with `@st.cache_data`; one loader per aggregate file

**Dashboard sections** (in order): Fraud Rate Gauge → WHERE (MCC + amount distribution) → WHEN (hour×day heatmap + monthly trend) → HOW (payment channel, card type, chip status) → WHO (age, income, correlation matrix) → Risk Factor Summary table.

The `figures/` PNGs and `aggregates/` CSVs are committed to git so the dashboard and report work without re-running the pipeline.
