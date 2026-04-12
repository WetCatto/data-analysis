"""
Fraud Analysis Dashboard — CSDS 327
Interactive Streamlit app using pre-computed aggregates.
The raw 1GB CSV and full parquet are NOT deployed — only the tiny
aggregate files (total ~25KB) + a 2MB stratified sample are loaded.

Run locally:  streamlit run app.py
Deploy:       Streamlit Community Cloud (free tier)
"""
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Digital Banking Fraud Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

AGG = Path(__file__).parent / "aggregates"

# ── Color palette ─────────────────────────────────────────────────────────────
FRAUD_COLOR = "#e74c3c"
LEGIT_COLOR = "#2ecc71"
NEUTRAL     = "#3498db"

# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data
def load_stats():
    with open(AGG / "overall_stats.json") as f:
        return json.load(f)

@st.cache_data
def load_csv(name):
    return pd.read_csv(AGG / name)

@st.cache_data
def load_sample():
    df = pd.read_parquet(AGG / "sample_transactions.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data
def load_heatmap():
    df = pd.read_csv(AGG / "fraud_heatmap.csv", index_col=0)
    df.columns = df.columns.astype(int)
    return df

@st.cache_data
def load_corr():
    return pd.read_csv(AGG / "correlation_matrix.csv", index_col=0)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Fraud Analysis")
    st.markdown("**CSDS 327 — Data Visualization**")
    st.markdown("University of Southeastern Philippines")
    st.divider()
    st.markdown(
        "**Dataset:** Financial Transactions Dataset: Analytics  \n"
        "**Source:** Kaggle (computingvictor, Oct 2024)  \n"
        "**Full dataset:** 8,914,963 transactions  \n"
        "**Dashboard sample:** 93,332 transactions"
    )
    st.divider()
    st.markdown("**Note:** Charts on the Overview, Time, Demographics, and Cards tabs use "
                "pre-computed aggregates from the full 8.9M-row dataset. "
                "The Explorer tab uses a 93K stratified sample.")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Transaction Patterns and Fraud Risk Indicators in Digital Banking")
st.caption("A 2024 Data-Driven Analysis | CSDS 327")

# ── KPI row ───────────────────────────────────────────────────────────────────
stats = load_stats()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Transactions", f"{stats['total_transactions']:,}")
col2.metric("Fraud Cases", f"{stats['fraud_count']:,}")
col3.metric("Overall Fraud Rate", f"{stats['fraud_rate_pct']:.3f}%")
col4.metric("Median Legit Amount", f"${stats['median_legit_amount']:.2f}")
col5.metric("Median Fraud Amount", f"${stats['median_fraud_amount']:.2f}",
            delta=f"+${stats['median_fraud_amount'] - stats['median_legit_amount']:.2f}",
            delta_color="inverse")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Merchant & Amount",
    "Time Patterns",
    "Demographics",
    "Card Analysis",
    "Transaction Explorer",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Merchant & Amount
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Fraud rate by merchant category")

        mcc = load_csv("fraud_by_mcc.csv")
        top_n = st.slider("Show top N categories", min_value=5, max_value=50, value=15, key="mcc_n")
        sort_by = st.radio("Sort by", ["Fraud rate", "Transaction volume"], horizontal=True, key="mcc_sort")

        if sort_by == "Fraud rate":
            mcc_plot = mcc.nlargest(top_n, "fraud_rate_pct").sort_values("fraud_rate_pct")
        else:
            mcc_plot = mcc.nlargest(top_n, "total_count").sort_values("fraud_rate_pct")

        fig_mcc = px.bar(
            mcc_plot, x="fraud_rate_pct", y="mcc_label",
            orientation="h",
            labels={"fraud_rate_pct": "Fraud rate (%)", "mcc_label": ""},
            color="fraud_rate_pct",
            color_continuous_scale=["#f9f3f3", FRAUD_COLOR],
            text=mcc_plot["fraud_rate_pct"].apply(lambda x: f"{x:.2f}%"),
        )
        fig_mcc.update_traces(textposition="outside")
        fig_mcc.update_layout(
            coloraxis_showscale=False,
            margin=dict(l=0, r=40, t=10, b=10),
            height=420,
        )
        st.plotly_chart(fig_mcc, use_container_width=True)

        st.caption(
            "**Finding:** Computer/peripheral equipment retailers hit 10.83% fraud — over 70x the "
            "dataset average of 0.15%.  \n"
            "**Insight:** High-value, easily resalable goods attract fraud. "
            "These MCC codes need tighter per-transaction limits."
        )

    with col_right:
        st.subheader("Transaction amount: fraud vs. legitimate")

        hist = load_csv("amount_histogram.csv")
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(
            x=hist["log10_amount"], y=hist["legit_density"],
            name="Legitimate", marker_color=LEGIT_COLOR, opacity=0.7,
        ))
        fig_hist.add_trace(go.Bar(
            x=hist["log10_amount"], y=hist["fraud_density"],
            name="Fraudulent", marker_color=FRAUD_COLOR, opacity=0.85,
        ))
        tick_vals = [0, 1, 2, 3, 4]
        tick_text = ["$1", "$10", "$100", "$1K", "$10K"]
        fig_hist.update_layout(
            barmode="overlay",
            xaxis=dict(title="Transaction amount (log scale)", tickvals=tick_vals, ticktext=tick_text),
            yaxis=dict(title="Density"),
            legend=dict(orientation="h", yanchor="top", y=1.12),
            margin=dict(l=0, r=0, t=30, b=10),
            height=420,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        st.caption(
            f"**Finding:** Median fraud amount is ${stats['median_fraud_amount']:.2f} vs. "
            f"${stats['median_legit_amount']:.2f} for legitimate transactions. "
            "Fraud has a secondary peak in the $500-$2,000 range.  \n"
            "**Insight:** Amount is a weak standalone signal but a strong combined feature "
            "with MCC and transaction method."
        )

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Time Patterns
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Fraud rate heatmap: hour of day x day of week")
    heatmap = load_heatmap()

    fig_heat = px.imshow(
        heatmap,
        labels=dict(x="Hour of day", y="", color="Fraud rate (%)"),
        color_continuous_scale="YlOrRd",
        aspect="auto",
        text_auto=".2f",
    )
    fig_heat.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        coloraxis_colorbar=dict(title="Fraud %"),
        font=dict(size=10),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.caption(
        "**Finding:** Fraud clusters between midnight and 5:00 AM, especially on weekends.  \n"
        "**Insight:** Adding hour-of-day to fraud scoring is cheap and reliably flags elevated risk. "
        "Use soft authentication challenges at night rather than hard declines."
    )

    st.divider()
    st.subheader("Fraud rate trend over time")

    trend = load_csv("fraud_by_month.csv")
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Scatter(
            x=trend["year_month"], y=trend["fraud_rate_pct"],
            name="Fraud rate (%)", line=dict(color=FRAUD_COLOR, width=2),
            mode="lines",
        ),
        secondary_y=False,
    )
    fig_trend.add_trace(
        go.Bar(
            x=trend["year_month"], y=trend["total_count"],
            name="Total transactions", marker_color=NEUTRAL, opacity=0.3,
        ),
        secondary_y=True,
    )
    fig_trend.update_layout(
        xaxis_title="Month",
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=0, r=0, t=30, b=10),
        height=340,
    )
    fig_trend.update_yaxes(title_text="Fraud rate (%)", secondary_y=False)
    fig_trend.update_yaxes(title_text="Transaction volume", secondary_y=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Demographics
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("By age group")
        age = load_csv("fraud_by_age.csv")
        fig_age = px.bar(
            age, x="age_group", y="fraud_rate_pct",
            color="fraud_rate_pct", color_continuous_scale=["#fff0f0", FRAUD_COLOR],
            labels={"age_group": "Age group", "fraud_rate_pct": "Fraud rate (%)"},
            text=age["fraud_rate_pct"].apply(lambda x: f"{x:.3f}%"),
        )
        fig_age.update_traces(textposition="outside")
        fig_age.update_layout(coloraxis_showscale=False, height=340,
                              margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_age, use_container_width=True)

    with c2:
        st.subheader("By income bracket")
        income = load_csv("fraud_by_income.csv")
        fig_inc = px.bar(
            income, x="income_bracket", y="fraud_rate_pct",
            color="fraud_rate_pct", color_continuous_scale=["#fff0f0", "#e67e22"],
            labels={"income_bracket": "Annual income", "fraud_rate_pct": "Fraud rate (%)"},
            text=income["fraud_rate_pct"].apply(lambda x: f"{x:.3f}%"),
        )
        fig_inc.update_traces(textposition="outside")
        fig_inc.update_layout(coloraxis_showscale=False, height=340,
                              margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_inc, use_container_width=True)

    with c3:
        st.subheader("By gender")
        gender = load_csv("fraud_by_gender.csv")
        fig_gen = px.pie(
            gender, values="total_count", names="gender",
            hole=0.4,
            color_discrete_sequence=[NEUTRAL, "#9b59b6", "#95a5a6"],
        )
        fig_gen.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_gen, use_container_width=True)

        gender["fraud_rate_pct_str"] = gender["fraud_rate_pct"].apply(lambda x: f"{x:.3f}%")
        st.dataframe(
            gender[["gender", "fraud_rate_pct_str", "fraud_count"]]
            .rename(columns={"gender": "Gender", "fraud_rate_pct_str": "Fraud rate",
                             "fraud_count": "Fraud cases"}),
            hide_index=True, use_container_width=True,
        )

    st.caption(
        "**Finding:** Customers under 25 have the highest fraud rate. Lower-income brackets "
        "(<$30K) show above-average fraud victimization.  \n"
        "**Insight:** Target in-app fraud alerts and awareness content at younger and "
        "lower-income customers — they see more fraud and are slower to notice unusual charges."
    )

    st.divider()
    st.subheader("Correlation matrix")
    corr = load_corr()
    mask = np.tril(np.ones_like(corr, dtype=bool))
    corr_masked = corr.where(mask)

    fig_corr = px.imshow(
        corr_masked,
        color_continuous_scale="RdBu_r", color_continuous_midpoint=0,
        zmin=-0.3, zmax=0.3,
        text_auto=".3f",
        labels=dict(color="Pearson r"),
        aspect="auto",
    )
    fig_corr.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=10))
    st.plotly_chart(fig_corr, use_container_width=True)
    st.caption(
        "**Finding:** No feature correlates strongly with the fraud label individually "
        "(max r = +0.04 for hour-of-day).  \n"
        "**Insight:** Simple threshold rules will not work. "
        "Non-linear ensemble models (Random Forest, Gradient Boosting) are needed to capture "
        "the interaction effects."
    )

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — Card Analysis
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("By transaction method")
        chip = load_csv("fraud_by_use_chip.csv")
        chip = chip[chip["use_chip"] != "Unknown"].sort_values("fraud_rate_pct", ascending=False)
        fig_chip = px.bar(
            chip, x="use_chip", y="fraud_rate_pct",
            color="fraud_rate_pct", color_continuous_scale=["#fff0f0", FRAUD_COLOR],
            labels={"use_chip": "", "fraud_rate_pct": "Fraud rate (%)"},
            text=chip["fraud_rate_pct"].apply(lambda x: f"{x:.3f}%"),
        )
        fig_chip.update_traces(textposition="outside")
        fig_chip.update_layout(coloraxis_showscale=False, height=350,
                               margin=dict(l=0, r=0, t=10, b=10),
                               xaxis_tickangle=-10)
        st.plotly_chart(fig_chip, use_container_width=True)

    with c2:
        st.subheader("By card type")
        ctype = load_csv("fraud_by_card_type.csv").sort_values("fraud_rate_pct", ascending=False)
        fig_ctype = px.bar(
            ctype, x="card_type", y="fraud_rate_pct",
            color="fraud_rate_pct", color_continuous_scale=["#fff0f0", "#e67e22"],
            labels={"card_type": "", "fraud_rate_pct": "Fraud rate (%)"},
            text=ctype["fraud_rate_pct"].apply(lambda x: f"{x:.3f}%"),
        )
        fig_ctype.update_traces(textposition="outside")
        fig_ctype.update_layout(coloraxis_showscale=False, height=350,
                                margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_ctype, use_container_width=True)

    with c3:
        st.subheader("Chip-enabled vs. no chip")
        chip_yn = load_csv("fraud_by_has_chip.csv").sort_values("fraud_rate_pct", ascending=False)
        fig_yn = px.bar(
            chip_yn, x="has_chip", y="fraud_rate_pct",
            color="has_chip",
            color_discrete_map={"YES": LEGIT_COLOR, "NO": FRAUD_COLOR},
            labels={"has_chip": "Has chip", "fraud_rate_pct": "Fraud rate (%)"},
            text=chip_yn["fraud_rate_pct"].apply(lambda x: f"{x:.3f}%"),
        )
        fig_yn.update_traces(textposition="outside")
        fig_yn.update_layout(showlegend=False, height=350,
                             margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_yn, use_container_width=True)

    st.caption(
        "**Finding:** Online transactions have a 0.84% fraud rate, 28x higher than swipe (0.03%). "
        "Non-chip cards have markedly higher fraud rates than chip-enabled cards.  \n"
        "**Insight:** Online is the biggest exposure. 3D Secure 2.0 and behavioral biometrics "
        "for card-not-present transactions, plus accelerating non-chip card replacement, "
        "would directly reduce fraud."
    )

    st.divider()
    st.subheader("By card brand")
    brand = load_csv("fraud_by_card_brand.csv").sort_values("fraud_rate_pct", ascending=False)
    fig_brand = px.bar(
        brand, x="card_brand", y="fraud_rate_pct",
        color="fraud_rate_pct", color_continuous_scale=["#fff0f0", FRAUD_COLOR],
        labels={"card_brand": "Card brand", "fraud_rate_pct": "Fraud rate (%)"},
        text=brand["fraud_rate_pct"].apply(lambda x: f"{x:.3f}%"),
        width=500,
    )
    fig_brand.update_traces(textposition="outside")
    fig_brand.update_layout(coloraxis_showscale=False, height=320,
                            margin=dict(l=0, r=0, t=10, b=10))
    col_brand, _ = st.columns([1, 2])
    with col_brand:
        st.plotly_chart(fig_brand, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — Transaction Explorer (uses 93K sample)
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Interactive transaction explorer")
    st.caption(
        "Uses a stratified sample: all 13,332 fraud transactions + 80,000 random legitimate "
        "transactions from the full 8.9M-row dataset."
    )

    sample = load_sample()

    # Filters
    with st.expander("Filters", expanded=True):
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            tx_method = st.multiselect(
                "Transaction method",
                options=sorted(sample["use_chip"].unique()),
                default=sorted(sample["use_chip"].unique()),
            )
        with f2:
            card_types = st.multiselect(
                "Card type",
                options=sorted(sample["card_type"].unique()),
                default=sorted(sample["card_type"].unique()),
            )
        with f3:
            fraud_filter = st.radio(
                "Show", ["All", "Fraud only", "Legitimate only"],
                horizontal=True,
            )
        with f4:
            amount_range = st.slider(
                "Amount range ($)",
                min_value=0, max_value=5000, value=(0, 5000),
            )

    # Apply filters
    mask = (
        sample["use_chip"].isin(tx_method) &
        sample["card_type"].isin(card_types) &
        sample["amount"].between(amount_range[0], amount_range[1])
    )
    if fraud_filter == "Fraud only":
        mask &= sample["is_fraud"] == 1
    elif fraud_filter == "Legitimate only":
        mask &= sample["is_fraud"] == 0

    filtered = sample[mask]

    # Summary row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Transactions (filtered)", f"{len(filtered):,}")
    fraud_in_filtered = filtered["is_fraud"].sum()
    m2.metric("Fraud cases", f"{fraud_in_filtered:,}")
    frate = filtered["is_fraud"].mean() * 100 if len(filtered) > 0 else 0
    m3.metric("Fraud rate", f"{frate:.3f}%")
    m4.metric("Median amount", f"${filtered['amount'].median():.2f}" if len(filtered) > 0 else "—")

    # Scatter amount vs MCC fraud rate
    if len(filtered) > 0:
        c_left, c_right = st.columns(2)

        with c_left:
            st.markdown("**Amount distribution in filtered selection**")
            fig_scatter = px.histogram(
                filtered.sample(min(len(filtered), 5000), random_state=42),
                x="amount", color=filtered.sample(min(len(filtered), 5000), random_state=42)["is_fraud"].map({1: "Fraud", 0: "Legitimate"}),
                nbins=60, log_x=True,
                color_discrete_map={"Fraud": FRAUD_COLOR, "Legitimate": LEGIT_COLOR},
                labels={"amount": "Amount ($)", "color": ""},
                barmode="overlay", opacity=0.75,
            )
            fig_scatter.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=10),
                                      legend_title="")
            st.plotly_chart(fig_scatter, use_container_width=True)

        with c_right:
            st.markdown("**Fraud rate by merchant category (filtered selection)**")
            mcc_filtered = (
                filtered.groupby("mcc_label")
                .agg(fraud_rate=("is_fraud", lambda x: x.mean() * 100),
                     count=("is_fraud", "count"))
                .query("count >= 5")
                .nlargest(12, "fraud_rate")
                .sort_values("fraud_rate")
                .reset_index()
            )
            if len(mcc_filtered) > 0:
                fig_mf = px.bar(
                    mcc_filtered, x="fraud_rate", y="mcc_label",
                    orientation="h",
                    color="fraud_rate",
                    color_continuous_scale=["#fff0f0", FRAUD_COLOR],
                    labels={"fraud_rate": "Fraud rate (%)", "mcc_label": ""},
                )
                fig_mf.update_layout(coloraxis_showscale=False, height=320,
                                     margin=dict(l=0, r=0, t=10, b=10))
                st.plotly_chart(fig_mf, use_container_width=True)
            else:
                st.info("Not enough data in the filtered selection to show MCC breakdown.")

        # Raw data table
        st.markdown("**Sample rows**")
        display_cols = ["date","amount","use_chip","mcc_label","is_fraud",
                        "card_type","age_group","income_bracket"]
        st.dataframe(
            filtered[display_cols]
            .rename(columns={"is_fraud": "fraud", "use_chip": "method",
                             "mcc_label": "merchant_category", "age_group": "age",
                             "income_bracket": "income"})
            .head(500),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No transactions match the current filters.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data: computingvictor, *Financial Transactions Dataset: Analytics*, Kaggle, Oct. 2024 | "
    "CSDS 327 — Data Visualization | University of Southeastern Philippines"
)
