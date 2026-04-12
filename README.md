# Transaction Patterns and Fraud Risk Indicators in Digital Banking

## Live Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/WetCatto/data-analysis/main/app.py)

## Overview

Interactive fraud analysis dashboard built on the [Financial Transactions Dataset: Analytics](https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets) (Kaggle, Oct 2024).

- **8,914,963** labelled transactions
- **13,332** fraud cases (0.15% fraud rate)
- Five chart sections: Merchant & Amount, Time Patterns, Demographics, Card Analysis, Interactive Explorer

## Repository Structure

```
app.py                          # Streamlit dashboard (runs on free tier)
requirements.txt                # Python dependencies
aggregates/                     # Pre-computed summaries (~25KB total, committed to git)
  overall_stats.json
  fraud_by_mcc.csv
  amount_histogram.csv
  fraud_heatmap.csv
  fraud_by_age.csv
  fraud_by_income.csv
  fraud_by_use_chip.csv
  fraud_by_card_type.csv
  fraud_by_card_brand.csv
  fraud_by_has_chip.csv
  fraud_by_gender.csv
  correlation_matrix.csv
  fraud_by_month.csv
  sample_transactions.parquet   # 93K stratified sample (2MB, committed to git)
figures/                        # Static PNG charts (300 DPI) for the written report
01_load_and_clean.py            # Generates cleaned_transactions.parquet from raw CSVs
02_eda_and_visualizations.py    # Generates figures/
03_build_report.py              # Builds Transaction_Fraud_Analysis_Report.docx
03_build_report_humanized.py    # Humanized version of the report
04_precompute_aggregates.py     # Generates aggregates/ from the parquet
```

## Local Setup

1. Download the raw dataset from Kaggle into a `data/` folder:
   - `transactions_data.csv` (~1.2 GB)
   - `users_data.csv`
   - `cards_data.csv`
   - `train_fraud_labels.json`
   - `mcc_codes.json`

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install python-docx pyarrow tqdm
   ```

3. Run the pipeline:
   ```bash
   python 01_load_and_clean.py       # ~3 min — produces cleaned_transactions.parquet
   python 02_eda_and_visualizations.py
   python 03_build_report_humanized.py
   python 04_precompute_aggregates.py  # re-run if you modify the cleaned parquet
   ```

4. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```

## Note on large files

The raw CSVs and full `cleaned_transactions.parquet` (245MB) are gitignored. The dashboard on Streamlit Community Cloud loads only the `aggregates/` folder (~25KB of CSVs + a 2MB sample parquet).

## References

1. computingvictor, "Financial Transactions Dataset: Analytics," Kaggle, Oct. 2024.
2. T. Hastie, R. Tibshirani, J. Friedman, *The Elements of Statistical Learning*, 2nd ed. Springer, 2009.
3. A. Dal Pozzolo et al., "Calibrating probability with undersampling for unbalanced classification," IEEE CIDM, 2015.
