"""
Fraud Risk Intelligence Dashboard
Clean executive design — data visualization best practices (Tufte / Few / Knaflic).
Loads only pre-computed aggregates (~25KB CSVs) + 2MB stratified sample parquet.
"""
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Fraud Risk Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AGG = Path(__file__).parent / "aggregates"

# ── Design tokens ──────────────────────────────────────────────────────────────
BG       = "#F8FAFC"   # slate-50
CARD     = "#FFFFFF"
BORDER   = "#E2E8F0"   # slate-200
TXT_PRI  = "#0F172A"   # slate-900
TXT_SEC  = "#64748B"   # slate-500
TXT_TER  = "#94A3B8"   # slate-400
DANGER   = "#EF4444"   # red-500
WARNING  = "#F59E0B"   # amber-500
SAFE     = "#10B981"   # emerald-500
INFO     = "#3B82F6"   # blue-500
CAT      = ["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#EECA3B"]
AVG_RATE = 0.15        # dataset-wide fraud rate %

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', system-ui, sans-serif !important;
    background-color: #F8FAFC !important;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    max-width: 100% !important;
    padding-left: 2rem;
    padding-right: 2rem;
}
[data-testid="collapsedControl"] { display: none; }

/* Metric overrides */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: #64748B !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
}

/* Input / selectbox / number_input — keep light */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-baseweb="input"] input {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
[data-baseweb="select"] > div,
[data-baseweb="select"] [role="combobox"],
[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}
/* Dropdown menu list */
[data-baseweb="popover"] ul,
[data-baseweb="menu"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
[data-baseweb="menu"] li {
    color: #0F172A !important;
}
[data-baseweb="menu"] li:hover {
    background: #F1F5F9 !important;
}
/* Slider track */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: #3B82F6 !important;
    border-color: #3B82F6 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Layout helpers ─────────────────────────────────────────────────────────────
def section(label: str, description: str = ""):
    desc_html = (
        f"<span style='font-size:0.75rem;color:{TXT_TER};margin-left:12px;'>{description}</span>"
        if description else ""
    )
    st.markdown(f"""
    <div style="margin:32px 0 16px;border-top:1px solid {BORDER};padding-top:14px;">
      <span style="font-size:0.7rem;font-weight:600;text-transform:uppercase;
            letter-spacing:1.5px;color:{TXT_SEC};">{label}</span>{desc_html}
    </div>""", unsafe_allow_html=True)


def insight_row(finding: str, insight: str):
    st.markdown(f"""
    <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
      <div style="font-size:0.75rem;color:{TXT_SEC};border-left:3px solid {DANGER};
           padding:5px 10px;background:#FEF2F2;flex:1;min-width:200px;border-radius:0 4px 4px 0;">
        <strong style="color:{TXT_PRI};">Finding:</strong> {finding}
      </div>
      <div style="font-size:0.75rem;color:{TXT_SEC};border-left:3px solid {INFO};
           padding:5px 10px;background:#EFF6FF;flex:1;min-width:200px;border-radius:0 4px 4px 0;">
        <strong style="color:{TXT_PRI};">Insight:</strong> {insight}
      </div>
    </div>""", unsafe_allow_html=True)


# ── Plotly base helpers ────────────────────────────────────────────────────────
def chart_layout(**kw) -> dict:
    """Base layout dict — NO xaxis/yaxis keys (use update_xaxes/update_yaxes)."""
    base = dict(
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=TXT_PRI),
        margin=dict(l=10, r=10, t=52, b=10),
        showlegend=kw.pop("showlegend", False),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
            font=dict(size=11, color=TXT_SEC),
            orientation="h", yanchor="bottom", y=1.01,
        ),
        hoverlabel=dict(
            bgcolor=TXT_PRI, bordercolor=TXT_PRI,
            font=dict(size=11, color="white"),
        ),
    )
    base.update(kw)
    return base


def xax(**kw) -> dict:
    base = dict(
        showgrid=False, showline=True,
        linecolor=BORDER, linewidth=1,
        tickfont=dict(size=11, color=TXT_SEC),
        title_font=dict(size=11, color=TXT_SEC),
        zeroline=False,
    )
    base.update(kw)
    return base


def yax(**kw) -> dict:
    base = dict(
        showgrid=True, gridcolor="#F1F5F9", gridwidth=1,
        showline=False,
        tickfont=dict(size=11, color=TXT_SEC),
        title_font=dict(size=11, color=TXT_SEC),
        zeroline=False,
    )
    base.update(kw)
    return base


def pchart(fig, height: int = 380):
    st.plotly_chart(
        fig,
        config={"displayModeBar": False},
        width="stretch",
    )


# ── Rate → semantic color ──────────────────────────────────────────────────────
def rate_color(rate_pct: float) -> str:
    if rate_pct >= 0.3:
        return DANGER
    if rate_pct >= 0.15:
        return WARNING
    return SAFE


# ── Data loaders ───────────────────────────────────────────────────────────────
@st.cache_data
def load_stats() -> dict:
    with open(AGG / "overall_stats.json") as f:
        return json.load(f)


@st.cache_data
def load_mcc() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_mcc.csv")


@st.cache_data
def load_histogram() -> pd.DataFrame:
    return pd.read_csv(AGG / "amount_histogram.csv")


@st.cache_data
def load_heatmap() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_heatmap.csv")


@st.cache_data
def load_monthly() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_month.csv")


@st.cache_data
def load_age() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_age.csv")


@st.cache_data
def load_income() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_income.csv")


@st.cache_data
def load_use_chip() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_use_chip.csv")


@st.cache_data
def load_card_type() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_card_type.csv")


@st.cache_data
def load_card_brand() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_card_brand.csv")


@st.cache_data
def load_has_chip() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_has_chip.csv")


@st.cache_data
def load_gender() -> pd.DataFrame:
    return pd.read_csv(AGG / "fraud_by_gender.csv")


@st.cache_data
def load_corr() -> pd.DataFrame:
    return pd.read_csv(AGG / "correlation_matrix.csv", index_col=0)


@st.cache_data
def load_sample() -> pd.DataFrame:
    return pd.read_parquet(AGG / "sample_transactions.parquet")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
stats   = load_stats()
sample  = load_sample()

total_tx    = stats.get("total_transactions", 0)
total_fraud = stats.get("fraud_count", 0)
fraud_rate  = stats.get("fraud_rate_pct", 0.0)
avg_legit   = stats.get("mean_legit_amount", 0.0)
avg_fraud   = stats.get("mean_fraud_amount", 0.0)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{CARD};border-bottom:1px solid {BORDER};
            padding:18px 32px 16px;margin:0 -2rem 24px -2rem;
            display:flex;align-items:center;justify-content:space-between;
            box-shadow:0 1px 3px rgba(0,0,0,0.06);">
  <div>
    <div style="font-size:1.15rem;font-weight:700;color:{TXT_PRI};letter-spacing:-0.3px;">
      Fraud Risk Intelligence
    </div>
    <div style="font-size:0.68rem;font-weight:500;color:{TXT_SEC};
                letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">
      Digital Banking — Transaction Analytics
    </div>
  </div>
  <div style="font-size:0.68rem;font-weight:500;color:{TXT_TER};
              letter-spacing:1px;text-transform:uppercase;">
    8.9M transactions &nbsp;|&nbsp; Kaggle 2024
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI strip ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total Transactions", f"{total_tx:,.0f}")
with k2:
    st.metric("Fraud Cases", f"{total_fraud:,.0f}")
with k3:
    st.metric("Fraud Rate", f"{fraud_rate:.3f}%")
with k4:
    st.metric("Avg Legit Tx", f"${avg_legit:,.2f}")
with k5:
    st.metric("Avg Fraud Tx", f"${avg_fraud:,.2f}")

# ── Gauge ──────────────────────────────────────────────────────────────────────
section("FRAUD RATE GAUGE", "threshold zones: green < 0.10% · amber 0.10–0.30% · red > 0.30%")

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=fraud_rate,
    number=dict(suffix="%", font=dict(size=32, color=TXT_PRI, family="Inter, system-ui")),
    gauge=dict(
        axis=dict(range=[0, 0.5], ticksuffix="%",
                  tickfont=dict(size=10, color=TXT_SEC)),
        bar=dict(color=rate_color(fraud_rate), thickness=0.25),
        bgcolor=CARD,
        borderwidth=0,
        steps=[
            dict(range=[0, 0.10],  color="#D1FAE5"),
            dict(range=[0.10, 0.30], color="#FEF3C7"),
            dict(range=[0.30, 0.5],  color="#FEE2E2"),
        ],
        threshold=dict(
            line=dict(color=TXT_SEC, width=2),
            thickness=0.75,
            value=0.15,
        ),
    ),
    title=dict(text="Overall Fraud Rate", font=dict(size=13, color=TXT_SEC,
                                                     family="Inter, system-ui")),
))
fig_gauge.update_layout(**chart_layout(height=220))
pchart(fig_gauge, height=220)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: WHERE?
# ══════════════════════════════════════════════════════════════════════════════
section("WHERE?", "merchant category & transaction amount")

col_mcc, col_amt = st.columns([3, 2], gap="medium")

with col_mcc:
    st.markdown(f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
                f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>Fraud Rate by Merchant Category</p>",
                unsafe_allow_html=True)
    n_mcc = st.number_input("Top N merchants", min_value=5, max_value=50, value=15, step=1,
                            key="n_mcc", label_visibility="collapsed")
    mcc_df = load_mcc()
    # expect columns: mcc_desc (or mcc), fraud_rate_pct, total_transactions
    rate_col  = next((c for c in mcc_df.columns if "rate" in c.lower()), mcc_df.columns[1])
    label_col = next((c for c in mcc_df.columns if "desc" in c.lower() or "name" in c.lower()
                      or "mcc" in c.lower()), mcc_df.columns[0])
    mcc_top = (mcc_df.nlargest(int(n_mcc), rate_col)
                     .sort_values(rate_col, ascending=True))

    colors_mcc = [
        f"rgba(239,68,68,{0.3 + 0.7 * (v / mcc_top[rate_col].max())})"
        for v in mcc_top[rate_col]
    ]

    fig_mcc = go.Figure()
    fig_mcc.add_trace(go.Bar(
        x=mcc_top[rate_col],
        y=mcc_top[label_col].str[:40],
        orientation="h",
        marker=dict(color=colors_mcc, line_width=0),
        text=[f"{v:.2f}%" for v in mcc_top[rate_col]],
        textposition="outside",
        textfont=dict(size=10, color=TXT_SEC),
        hovertemplate="%{y}<br>Fraud rate: %{x:.3f}%<extra></extra>",
    ))
    # average reference line
    fig_mcc.add_vline(
        x=AVG_RATE, line_width=1.5, line_dash="dash", line_color=TXT_SEC,
        annotation_text="Avg 0.15%",
        annotation_font=dict(size=10, color=TXT_SEC),
        annotation_position="top right",
    )
    fig_mcc.update_layout(**chart_layout(height=420))
    fig_mcc.update_xaxes(xax(title="Fraud rate (%)"))
    fig_mcc.update_yaxes(yax(title="", showgrid=False))
    pchart(fig_mcc, height=420)

with col_amt:
    st.markdown(f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
                f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>Amount Distribution — Fraud vs Legitimate</p>",
                unsafe_allow_html=True)
    hist_df = load_histogram()
    # expect columns: bin_start, legit_density, fraud_density (or similar)
    # fallback: use sample
    # CSV x-axis is log10(amount) — plot on linear scale with dollar tick labels
    legit_col  = next((c for c in hist_df.columns if "legit" in c.lower()), None)
    fraud_col2 = next((c for c in hist_df.columns if "fraud" in c.lower() and "rate" not in c.lower()), None)
    bin_col    = hist_df.columns[0]  # log10_amount is always first column
    bin_spacing = float(hist_df[bin_col].diff().median()) if len(hist_df) > 1 else 0.05

    if legit_col and fraud_col2:
        fig_amt = go.Figure()
        fig_amt.add_trace(go.Bar(
            x=hist_df[bin_col], y=hist_df[legit_col],
            name="Legitimate", marker_color="rgba(76,120,168,0.65)",
            marker_line_width=0, width=bin_spacing,
        ))
        fig_amt.add_trace(go.Bar(
            x=hist_df[bin_col], y=hist_df[fraud_col2],
            name="Fraud", marker_color="rgba(239,68,68,0.65)",
            marker_line_width=0, width=bin_spacing,
        ))
        fig_amt.update_layout(**chart_layout(showlegend=True, barmode="overlay", height=468,
                              legend=dict(orientation="h", y=-0.18, yanchor="top",
                                          bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
                                          font=dict(size=11, color=TXT_SEC))))
        # x is already log10(amount) — show dollar labels at integer log10 ticks
        fig_amt.update_xaxes(xax(
            title="Amount (USD, log scale)",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["$1", "$10", "$100", "$1K", "$10K"],
        ))
        fig_amt.update_yaxes(yax(title="Density", rangemode="tozero"))
    else:
        # fallback: build from sample
        legit_s = sample.loc[sample["is_fraud"] == 0, "amount"].clip(lower=0.01, upper=10000)
        fraud_s = sample.loc[sample["is_fraud"] == 1, "amount"].clip(lower=0.01, upper=10000)
        fig_amt = go.Figure()
        fig_amt.add_trace(go.Histogram(
            x=np.log10(legit_s), histnorm="probability density", name="Legitimate",
            marker_color="rgba(76,120,168,0.65)", marker_line_width=0, opacity=0.7,
            xbins=dict(size=0.1),
        ))
        fig_amt.add_trace(go.Histogram(
            x=np.log10(fraud_s), histnorm="probability density", name="Fraud",
            marker_color="rgba(239,68,68,0.65)", marker_line_width=0, opacity=0.7,
            xbins=dict(size=0.1),
        ))
        med_legit = float(np.log10(legit_s.median()))
        med_fraud = float(np.log10(fraud_s.median()))
        fig_amt.add_vline(x=med_legit, line_dash="dash", line_color="#4C78A8", line_width=1.5,
                          annotation_text=f"Med ${legit_s.median():.0f}",
                          annotation_font=dict(size=9, color="#4C78A8"))
        fig_amt.add_vline(x=med_fraud, line_dash="dash", line_color=DANGER, line_width=1.5,
                          annotation_text=f"Med ${fraud_s.median():.0f}",
                          annotation_font=dict(size=9, color=DANGER))
        fig_amt.update_layout(**chart_layout(showlegend=True, barmode="overlay", height=468,
                              legend=dict(orientation="h", y=-0.18, yanchor="top",
                                          bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
                                          font=dict(size=11, color=TXT_SEC))))
        fig_amt.update_xaxes(xax(
            title="Amount (USD, log scale)",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["$1", "$10", "$100", "$1K", "$10K"],
        ))
        fig_amt.update_yaxes(yax(title="Density", rangemode="tozero"))
    pchart(fig_amt, height=468)

insight_row(
    "High-risk MCC categories show fraud rates 5–10× above the 0.15% dataset average, "
    "concentrated in digital goods, fuel, and telecom merchants.",
    "Fraudsters exploit low-friction, high-liquidity merchant categories. "
    "Enhanced velocity checks for these MCCs would catch a disproportionate share of fraud.",
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: WHEN?
# ══════════════════════════════════════════════════════════════════════════════
section("WHEN?", "time-of-day patterns & monthly trends")

col_heat, col_trend = st.columns([3, 2], gap="medium")

with col_heat:
    st.markdown(f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
                f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>Fraud Rate — Hour × Day of Week</p>",
                unsafe_allow_html=True)
    heat_df = load_heatmap()
    # CSV is already pivoted: first col = day_of_week, remaining cols = hours 0-23
    heat_pivot = heat_df.set_index(heat_df.columns[0])
    heat_pivot.columns = [str(c) for c in heat_pivot.columns]
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    existing  = [d for d in day_order if d in heat_pivot.index]
    if existing:
        heat_pivot = heat_pivot.reindex(existing)

    fig_heat = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=[str(h) for h in heat_pivot.columns],
        y=list(heat_pivot.index),
        colorscale=[
            [0.0,  "#FFFFFF"],
            [0.3,  "#DBEAFE"],
            [0.7,  "#3B82F6"],
            [1.0,  "#EF4444"],
        ],
        text=[[f"{v:.2f}%" if not np.isnan(v) else "" for v in row] for row in heat_pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=8, color=TXT_PRI),
        hovertemplate="Hour %{x} · %{y}<br>Fraud rate: %{z:.3f}%<extra></extra>",
        showscale=True,
        colorbar=dict(
            thickness=10, len=0.8,
            tickfont=dict(size=9, color=TXT_SEC),
            title=dict(text="Rate %", font=dict(size=10, color=TXT_SEC), side="right"),
        ),
    ))
    fig_heat.update_layout(**chart_layout(height=300))
    fig_heat.update_xaxes(xax(title="Hour of day", dtick=2))
    fig_heat.update_yaxes(yax(title="", showgrid=False, autorange="reversed"))
    pchart(fig_heat, height=300)

with col_trend:
    st.markdown(f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
                f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>Monthly Fraud Rate Trend</p>",
                unsafe_allow_html=True)
    month_df = load_monthly()
    rate_m   = next((c for c in month_df.columns if "rate" in c.lower()), month_df.columns[-1])
    cnt_m    = next((c for c in month_df.columns if "count" in c.lower() or "total" in c.lower()
                     or "tx" in c.lower()), None)
    date_m   = next((c for c in month_df.columns if "month" in c.lower() or "date" in c.lower()
                     or "period" in c.lower()), month_df.columns[0])

    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    if cnt_m:
        fig_trend.add_trace(go.Bar(
            x=month_df[date_m], y=month_df[cnt_m],
            name="Volume", marker_color="rgba(59,130,246,0.12)", marker_line_width=0,
        ), secondary_y=True)
    fig_trend.add_trace(go.Scatter(
        x=month_df[date_m], y=month_df[rate_m],
        mode="lines", name="Fraud rate %",
        line=dict(color=DANGER, width=2),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.06)",
        hovertemplate="%{x}<br>Fraud rate: %{y:.3f}%<extra></extra>",
    ), secondary_y=False)
    fig_trend.add_hline(y=AVG_RATE, line_dash="dash", line_color=TXT_TER, line_width=1,
                        annotation_text="Avg", annotation_font=dict(size=9, color=TXT_TER))
    fig_trend.update_layout(**chart_layout(showlegend=False, height=300))
    fig_trend.update_xaxes(xax(title=""))
    fig_trend.update_yaxes(yax(title="Fraud rate (%)"), secondary_y=False)
    if cnt_m:
        fig_trend.update_yaxes(yax(title="Volume", showgrid=False), secondary_y=True)
    pchart(fig_trend, height=300)

insight_row(
    "Late-night hours (00:00–04:00) and weekends show elevated fraud rates, "
    "particularly Saturday and Sunday overnight.",
    "Fraudsters exploit reduced monitoring windows. Time-based risk scoring "
    "(higher scrutiny for off-hours transactions) can reduce false negatives.",
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: HOW?
# ══════════════════════════════════════════════════════════════════════════════
section("HOW?", "payment channel, card type & chip status")

col_ch, col_ct, col_chip = st.columns(3, gap="medium")


def lollipop_chart(df: pd.DataFrame, label_col: str, rate_col: str,
                   title: str, height: int = 320) -> go.Figure:
    df_s = df.sort_values(rate_col, ascending=True)
    colors = [rate_color(r) for r in df_s[rate_col]]
    fig = go.Figure()
    for i, (_, row) in enumerate(df_s.iterrows()):
        fig.add_trace(go.Scatter(
            x=[0, row[rate_col]], y=[row[label_col], row[label_col]],
            mode="lines",
            line=dict(color=BORDER, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter(
        x=df_s[rate_col],
        y=df_s[label_col],
        mode="markers+text",
        marker=dict(color=colors, size=12, line=dict(color="white", width=1.5)),
        text=[f"{v:.2f}%" for v in df_s[rate_col]],
        textposition="middle right",
        textfont=dict(size=10, color=TXT_SEC),
        showlegend=False,
        hovertemplate="%{y}<br>Fraud rate: %{x:.3f}%<extra></extra>",
    ))
    fig.add_vline(x=AVG_RATE, line_dash="dash", line_color=TXT_TER, line_width=1)
    fig.update_layout(**chart_layout(title_text=title,
                                      title_font=dict(size=11, color=TXT_PRI),
                                      height=height))
    fig.update_xaxes(xax(title="Fraud rate (%)"))
    fig.update_yaxes(yax(title="", showgrid=False))
    return fig


with col_ch:
    uc_df   = load_use_chip()
    lbl_uc  = next((c for c in uc_df.columns if "chip" in c.lower() or "method" in c.lower()
                    or "use" in c.lower()), uc_df.columns[0])
    rate_uc = next((c for c in uc_df.columns if "rate" in c.lower()), uc_df.columns[-1])
    fig_uc  = lollipop_chart(uc_df, lbl_uc, rate_uc, "Payment Channel")
    pchart(fig_uc, height=320)

with col_ct:
    ct_df   = load_card_type()
    lbl_ct  = next((c for c in ct_df.columns if "type" in c.lower() or "card" in c.lower()),
                   ct_df.columns[0])
    rate_ct = next((c for c in ct_df.columns if "rate" in c.lower()), ct_df.columns[-1])
    fig_ct  = lollipop_chart(ct_df, lbl_ct, rate_ct, "Card Type")
    pchart(fig_ct, height=320)

with col_chip:
    hc_df   = load_has_chip()
    lbl_hc  = next((c for c in hc_df.columns if "chip" in c.lower() or "has" in c.lower()),
                   hc_df.columns[0])
    rate_hc = next((c for c in hc_df.columns if "rate" in c.lower()), hc_df.columns[-1])
    fig_hc  = lollipop_chart(hc_df, lbl_hc, rate_hc, "Chip Status")
    pchart(fig_hc, height=320)

insight_row(
    "Online / card-not-present transactions show fraud rates 3–6× higher than chip-authenticated "
    "in-person transactions.",
    "Chip EMV adoption has reduced counterfeit card fraud at POS terminals; "
    "investment should shift toward step-up authentication for digital channels.",
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: WHO?
# ══════════════════════════════════════════════════════════════════════════════
section("WHO?", "demographics & feature correlations")

col_age, col_inc, col_corr = st.columns([1, 1, 2], gap="medium")


def demographic_bar(df: pd.DataFrame, label_col: str, rate_col: str,
                    title: str, height: int = 320) -> go.Figure:
    df_s = df  # preserve CSV row order (age/income brackets already ordered correctly)
    colors = [rate_color(r) for r in df_s[rate_col]]
    fig = go.Figure(go.Bar(
        x=df_s[label_col],
        y=df_s[rate_col],
        marker=dict(color=colors, line_width=0),
        text=[f"{v:.2f}%" for v in df_s[rate_col]],
        textposition="outside",
        textfont=dict(size=10, color=TXT_SEC),
        hovertemplate="%{x}<br>Fraud rate: %{y:.3f}%<extra></extra>",
    ))
    fig.add_hline(y=AVG_RATE, line_dash="dash", line_color=TXT_TER, line_width=1,
                  annotation_text="Avg", annotation_font=dict(size=9, color=TXT_TER),
                  annotation_position="top right")
    fig.update_layout(**chart_layout(title_text=title,
                                      title_font=dict(size=11, color=TXT_PRI),
                                      height=height))
    fig.update_xaxes(xax(title=""))
    fig.update_yaxes(yax(title="Fraud rate (%)"))
    return fig


with col_age:
    age_df   = load_age()
    lbl_age  = next((c for c in age_df.columns if "age" in c.lower() or "group" in c.lower()),
                    age_df.columns[0])
    rate_age = next((c for c in age_df.columns if "rate" in c.lower()), age_df.columns[-1])
    fig_age  = demographic_bar(age_df, lbl_age, rate_age, "Fraud Rate by Age Group", height=400)
    pchart(fig_age, height=400)

with col_inc:
    inc_df   = load_income()
    lbl_inc  = next((c for c in inc_df.columns if "income" in c.lower() or "bracket" in c.lower()),
                    inc_df.columns[0])
    rate_inc = next((c for c in inc_df.columns if "rate" in c.lower()), inc_df.columns[-1])
    fig_inc  = demographic_bar(inc_df, lbl_inc, rate_inc, "Fraud Rate by Income", height=400)
    pchart(fig_inc, height=400)

with col_corr:
    st.markdown(f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
                f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>Feature Correlation Matrix</p>",
                unsafe_allow_html=True)
    corr_df = load_corr()
    mask    = np.triu(np.ones(corr_df.shape, dtype=bool), k=1)
    z_vals  = corr_df.values.astype(float)
    z_vals[mask] = np.nan
    text_vals = [[f"{v:.2f}" if not np.isnan(v) else "" for v in row] for row in z_vals]

    fig_corr = go.Figure(go.Heatmap(
        z=z_vals,
        x=corr_df.columns.tolist(),
        y=corr_df.index.tolist(),
        zmin=-1, zmax=1,
        colorscale=[
            [0.0, "#2563EB"],
            [0.5, "#FFFFFF"],
            [1.0, "#DC2626"],
        ],
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(size=9, color=TXT_PRI),
        hovertemplate="%{x} × %{y}<br>r = %{z:.3f}<extra></extra>",
        showscale=True,
        colorbar=dict(
            thickness=10, len=0.8,
            tickfont=dict(size=9, color=TXT_SEC),
            title=dict(text="r", font=dict(size=10, color=TXT_SEC), side="right"),
        ),
    ))
    fig_corr.update_layout(**chart_layout(height=400))
    fig_corr.update_xaxes(xax(title="", tickangle=30, showline=False))
    fig_corr.update_yaxes(yax(title="", showgrid=False, autorange="reversed"))
    pchart(fig_corr, height=400)

insight_row(
    "Younger cardholders (18–30) and lower-income brackets show slightly elevated fraud exposure, "
    "likely due to weaker security practices and higher online transaction frequency.",
    "Demographics alone are weak fraud predictors (low r values). "
    "Combine demographic signals with behavioral features for effective detection models.",
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
section("EXPLORER", "interactive slice of the 93K stratified sample")

st.markdown(f"<p style='font-size:0.75rem;color:{TXT_SEC};margin-bottom:12px;'>"
            "Filters apply to the stratified sample (all 13,332 fraud + 80K random legitimate). "
            "Not a replacement for full-dataset analysis.</p>", unsafe_allow_html=True)

f1, f2, f3 = st.columns([1, 1, 2], gap="medium")

with f1:
    amt_min, amt_max = float(sample["amount"].min()), float(sample["amount"].max())
    lo, hi = st.slider(
        "Amount range ($)",
        min_value=0.0, max_value=min(amt_max, 5000.0),
        value=(0.0, min(amt_max, 5000.0)),
        step=10.0,
        key="explorer_amt",
    )

with f2:
    fraud_filter = st.selectbox(
        "Transaction type",
        ["All", "Fraud only", "Legitimate only"],
        key="explorer_fraud",
    )

with f3:
    if "use_chip" in sample.columns:
        channels = ["All"] + sorted(sample["use_chip"].dropna().unique().tolist())
        channel_sel = st.selectbox("Channel", channels, key="explorer_channel")
    else:
        channel_sel = "All"

# Apply filters
df_ex = sample.copy()
df_ex = df_ex[(df_ex["amount"] >= lo) & (df_ex["amount"] <= hi)]
if fraud_filter == "Fraud only":
    df_ex = df_ex[df_ex["is_fraud"] == 1]
elif fraud_filter == "Legitimate only":
    df_ex = df_ex[df_ex["is_fraud"] == 0]
if channel_sel != "All" and "use_chip" in df_ex.columns:
    df_ex = df_ex[df_ex["use_chip"] == channel_sel]

n_total = len(df_ex)
n_fraud = int(df_ex["is_fraud"].sum()) if "is_fraud" in df_ex.columns else 0
r_fraud = n_fraud / n_total * 100 if n_total > 0 else 0.0

st.markdown(
    f"<p style='font-size:0.75rem;color:{TXT_SEC};'>"
    f"Showing <strong style='color:{TXT_PRI};'>{n_total:,}</strong> transactions &nbsp;|&nbsp; "
    f"Fraud: <strong style='color:{DANGER};'>{n_fraud:,}</strong> "
    f"(<strong style='color:{DANGER};'>{r_fraud:.2f}%</strong>)</p>",
    unsafe_allow_html=True,
)

ex_c1, ex_c2 = st.columns(2, gap="medium")

with ex_c1:
    fig_ex_hist = go.Figure()
    for label, mask_val, color in [("Legitimate", 0, "rgba(76,120,168,0.6)"),
                                    ("Fraud",       1, "rgba(239,68,68,0.6)")]:
        sub = df_ex[df_ex["is_fraud"] == mask_val]["amount"] if "is_fraud" in df_ex.columns else df_ex["amount"]
        if len(sub) > 0:
            fig_ex_hist.add_trace(go.Histogram(
                x=sub, histnorm="probability density", name=label,
                marker_color=color, marker_line_width=0, opacity=0.7,
            ))
    fig_ex_hist.update_layout(**chart_layout(showlegend=True, barmode="overlay",
                                              title_text="Amount distribution",
                                              title_font=dict(size=11, color=TXT_PRI),
                                              height=300))
    fig_ex_hist.update_xaxes(xax(title="Amount (USD)", type="log"))
    fig_ex_hist.update_yaxes(yax(title="Density", rangemode="tozero"))
    pchart(fig_ex_hist, height=300)

with ex_c2:
    if "mcc_desc" in df_ex.columns or "mcc" in df_ex.columns:
        mcc_col_ex = "mcc_desc" if "mcc_desc" in df_ex.columns else "mcc"
        mcc_ex = (df_ex[df_ex["is_fraud"] == 1][mcc_col_ex].value_counts().head(10)
                  if "is_fraud" in df_ex.columns else
                  df_ex[mcc_col_ex].value_counts().head(10))
        fig_ex_mcc = go.Figure(go.Bar(
            y=mcc_ex.index.str[:35],
            x=mcc_ex.values,
            orientation="h",
            marker=dict(color=DANGER, opacity=0.7, line_width=0),
            hovertemplate="%{y}<br>Count: %{x}<extra></extra>",
        ))
        fig_ex_mcc.update_layout(**chart_layout(title_text="Top fraud MCCs (filtered)",
                                                  title_font=dict(size=11, color=TXT_PRI),
                                                  height=300))
        fig_ex_mcc.update_xaxes(xax(title="Fraud count"))
        fig_ex_mcc.update_yaxes(yax(title="", showgrid=False))
        pchart(fig_ex_mcc, height=300)
    else:
        # mcc_desc not in sample — show fraud rate by channel instead
        ch_col = next((c for c in ["use_chip", "card_type", "card_brand"] if c in df_ex.columns), None)
        if ch_col and "is_fraud" in df_ex.columns and len(df_ex) > 0:
            ch_rates = (df_ex.groupby(ch_col)["is_fraud"]
                        .agg(fraud_count="sum", total="count")
                        .assign(rate=lambda d: d["fraud_count"] / d["total"] * 100)
                        .sort_values("rate", ascending=True)
                        .reset_index())
            fig_ch_ex = go.Figure(go.Bar(
                x=ch_rates["rate"], y=ch_rates[ch_col],
                orientation="h",
                marker=dict(color=[rate_color(r) for r in ch_rates["rate"]],
                            opacity=0.8, line_width=0),
                text=[f"{r:.2f}%" for r in ch_rates["rate"]],
                textposition="outside",
                textfont=dict(size=10, color=TXT_SEC),
                hovertemplate="%{y}<br>Fraud rate: %{x:.2f}%<extra></extra>",
            ))
            fig_ch_ex.update_layout(**chart_layout(title_text="Fraud rate by channel (filtered)",
                                                    title_font=dict(size=11, color=TXT_PRI),
                                                    height=300))
            fig_ch_ex.update_xaxes(xax(title="Fraud rate (%)"))
            fig_ch_ex.update_yaxes(yax(title="", showgrid=False))
            pchart(fig_ch_ex, height=300)

# Transaction table
show_cols = [c for c in ["transaction_id", "amount", "is_fraud", "use_chip", "mcc_desc",
                          "merchant_city", "date"] if c in df_ex.columns]
if not show_cols:
    show_cols = df_ex.columns[:6].tolist()
display = df_ex[show_cols].head(200)
if "is_fraud" in display.columns:
    display = display.rename(columns={"is_fraud": "fraud"})
st.dataframe(display, hide_index=True, height=240, width="stretch")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid {BORDER};
            font-size:0.68rem;color:{TXT_TER};text-align:center;letter-spacing:0.5px;">
  Data: computingvictor — Financial Transactions Dataset (Kaggle, Oct 2024) &nbsp;|&nbsp;
  8,914,963 transactions &nbsp;|&nbsp; Dashboard loads aggregates only (&lt;25KB + 2MB sample)
</div>
""", unsafe_allow_html=True)
