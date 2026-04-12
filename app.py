"""
Fraud Risk Intelligence Dashboard
Executive-grade neobrutalism design.
Loads only pre-computed aggregates (~25KB) + 2MB sample parquet.
"""
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Fraud Risk Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AGG = Path(__file__).parent / "aggregates"

# ── Palette ───────────────────────────────────────────────────────────────────
BLACK   = "#0D0D0D"
WHITE   = "#FFFFFF"
OFFWHT  = "#FFFCF2"
YELLOW  = "#FFE600"
RED     = "#FF3B30"
GREEN   = "#00C853"
BLUE    = "#0057FF"
ORANGE  = "#FF6B35"
PURPLE  = "#8B5CF6"

# ── CSS injection ─────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Space Grotesk', 'Arial Black', Arial, sans-serif !important;
    background-color: {OFFWHT} !important;
}}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 0 !important; max-width: 100% !important; padding-left: 2rem; padding-right: 2rem; }}
[data-testid="collapsedControl"] {{ display: none; }}

/* ── Global scrollbar ── */
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: {OFFWHT}; }}
::-webkit-scrollbar-thumb {{ background: {BLACK}; border: 2px solid {OFFWHT}; }}

/* ── Top header bar ── */
.page-header {{
    background: {BLACK};
    padding: 20px 32px 18px;
    margin: 0 -2rem 28px -2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 4px solid {YELLOW};
}}
.page-header-left {{ display: flex; flex-direction: column; gap: 2px; }}
.page-title {{
    font-size: 1.5rem;
    font-weight: 800;
    color: {WHITE};
    letter-spacing: 1px;
    text-transform: uppercase;
    margin: 0;
}}
.page-subtitle {{
    font-size: 0.78rem;
    font-weight: 500;
    color: #888;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 0;
}}
.page-header-badge {{
    background: {YELLOW};
    color: {BLACK};
    font-size: 0.7rem;
    font-weight: 800;
    padding: 5px 14px;
    text-transform: uppercase;
    letter-spacing: 2px;
    border: 2px solid {WHITE};
}}

/* ── Alert banner ── */
.alert-banner {{
    background: {YELLOW};
    border: 3px solid {BLACK};
    box-shadow: 6px 6px 0 {BLACK};
    padding: 14px 22px;
    margin-bottom: 24px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}}
.alert-icon {{ font-size: 1.4rem; line-height: 1; margin-top: 2px; }}
.alert-body {{ flex: 1; }}
.alert-title {{
    font-weight: 800;
    font-size: 0.95rem;
    color: {BLACK};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}}
.alert-text {{ font-size: 0.82rem; font-weight: 500; color: #333; }}

/* ── KPI cards ── */
.kpi-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 28px; }}
.kpi-card {{
    background: {WHITE};
    border: 3px solid {BLACK};
    box-shadow: 5px 5px 0 {BLACK};
    padding: 18px 18px 14px;
    transition: box-shadow 0.1s, transform 0.1s;
}}
.kpi-card:hover {{ box-shadow: 8px 8px 0 {BLACK}; transform: translate(-2px, -2px); }}
.kpi-accent {{ width: 100%; height: 4px; margin-bottom: 12px; }}
.kpi-label {{
    font-size: 0.68rem;
    font-weight: 700;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
}}
.kpi-value {{
    font-size: 2rem;
    font-weight: 800;
    color: {BLACK};
    line-height: 1;
    margin-bottom: 4px;
}}
.kpi-delta {{
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 7px;
    border: 2px solid {BLACK};
    display: inline-block;
    margin-top: 6px;
}}
.kpi-delta-up {{ background: {RED}; color: {WHITE}; }}
.kpi-delta-neutral {{ background: {YELLOW}; color: {BLACK}; }}
.kpi-delta-good {{ background: {GREEN}; color: {WHITE}; }}

/* ── Section header ── */
.section-header {{
    display: flex;
    align-items: center;
    gap: 0;
    margin: 32px 0 16px;
}}
.section-header-bar {{
    background: {BLACK};
    color: {YELLOW};
    padding: 9px 20px;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 3px;
    white-space: nowrap;
}}
.section-header-line {{
    flex: 1;
    height: 3px;
    background: {BLACK};
}}

/* ── Chart panel ── */
.chart-panel {{
    background: {WHITE};
    border: 3px solid {BLACK};
    box-shadow: 5px 5px 0 {BLACK};
    padding: 20px;
    height: 100%;
}}
.chart-panel-title {{
    font-size: 0.78rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: {BLACK};
    margin-bottom: 14px;
    border-bottom: 2px solid {BLACK};
    padding-bottom: 8px;
}}

/* ── Finding / Insight chips ── */
.fi-row {{ display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }}
.fi-chip {{
    font-size: 0.75rem;
    font-weight: 600;
    padding: 6px 12px;
    border: 2px solid {BLACK};
    line-height: 1.3;
    flex: 1;
    min-width: 200px;
}}
.fi-chip-find {{ background: #FFF0EE; border-left: 5px solid {RED}; }}
.fi-chip-insight {{ background: #EEF3FF; border-left: 5px solid {BLUE}; }}

/* ── Risk badge ── */
.risk-high {{
    background: {RED}; color: {WHITE};
    font-size: 0.62rem; font-weight: 800;
    padding: 2px 8px; text-transform: uppercase;
    letter-spacing: 1px; border: 2px solid {BLACK};
    display: inline-block;
}}
.risk-med {{
    background: {YELLOW}; color: {BLACK};
    font-size: 0.62rem; font-weight: 800;
    padding: 2px 8px; text-transform: uppercase;
    letter-spacing: 1px; border: 2px solid {BLACK};
    display: inline-block;
}}
.risk-low {{
    background: {GREEN}; color: {WHITE};
    font-size: 0.62rem; font-weight: 800;
    padding: 2px 8px; text-transform: uppercase;
    letter-spacing: 1px; border: 2px solid {BLACK};
    display: inline-block;
}}

/* ── Explorer filters ── */
.filter-bar {{
    background: {BLACK};
    padding: 16px 20px;
    margin-bottom: 16px;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: flex-end;
}}

/* ── Override Streamlit widget styles ── */
div[data-testid="stMetric"] {{
    background: {WHITE};
    border: 3px solid {BLACK};
    box-shadow: 4px 4px 0 {BLACK};
    padding: 16px !important;
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 3px solid {BLACK};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    background: {WHITE};
    border: 3px solid {BLACK};
    border-bottom: none;
    border-radius: 0 !important;
    font-weight: 700;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 10px 20px;
    margin-right: 4px;
    color: {BLACK};
}}
.stTabs [aria-selected="true"] {{
    background: {YELLOW} !important;
    color: {BLACK} !important;
}}
div[data-testid="stSelectbox"] > div,
div[data-testid="stMultiSelect"] > div {{
    border: 2px solid {BLACK} !important;
    border-radius: 0 !important;
    box-shadow: 3px 3px 0 {BLACK} !important;
}}
.stSlider [data-testid="stThumbValue"] {{
    background: {BLACK};
    color: {WHITE};
    font-weight: 700;
    border-radius: 0 !important;
}}
div[data-testid="stDataFrame"] {{
    border: 3px solid {BLACK};
    box-shadow: 4px 4px 0 {BLACK};
}}
div[data-testid="stExpander"] {{
    border: 3px solid {BLACK} !important;
    border-radius: 0 !important;
    box-shadow: 4px 4px 0 {BLACK};
}}

/* ── Divider ── */
hr {{ border: none; border-top: 3px solid {BLACK}; margin: 28px 0; }}
</style>
""", unsafe_allow_html=True)


# ── Data loaders ──────────────────────────────────────────────────────────────
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


# ── Plotly base layout ────────────────────────────────────────────────────────
def neo_layout(**overrides):
    base = dict(
        paper_bgcolor=WHITE,
        plot_bgcolor=OFFWHT,
        font=dict(family="Space Grotesk, Arial Black, Arial", color=BLACK, size=11),
        title_font=dict(size=12, color=BLACK, family="Space Grotesk, Arial Black, Arial"),
        xaxis=dict(
            showgrid=True, gridcolor="#E8E4D9", gridwidth=1,
            linecolor=BLACK, linewidth=2,
            tickfont=dict(size=10), title_font=dict(size=10),
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#E8E4D9", gridwidth=1,
            linecolor=BLACK, linewidth=2,
            tickfont=dict(size=10), title_font=dict(size=10),
            zeroline=False,
        ),
        margin=dict(l=8, r=8, t=16, b=8),
        showlegend=True,
        legend=dict(
            bgcolor=WHITE, bordercolor=BLACK, borderwidth=2,
            font=dict(size=10), orientation="h",
            yanchor="bottom", y=1.02, xanchor="left", x=0,
        ),
    )
    base.update(overrides)
    return base


# ── HTML helpers ──────────────────────────────────────────────────────────────
def section(label):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-header-bar">{label}</div>
        <div class="section-header-line"></div>
    </div>""", unsafe_allow_html=True)


def panel_title(text, badge=None):
    badge_html = f' &nbsp;<span class="risk-{badge[0]}">{badge[1]}</span>' if badge else ""
    st.markdown(f'<div class="chart-panel-title">{text}{badge_html}</div>', unsafe_allow_html=True)


def fi(finding, insight):
    st.markdown(f"""
    <div class="fi-row">
        <div class="fi-chip fi-chip-find">📊 <strong>Finding:</strong> {finding}</div>
        <div class="fi-chip fi-chip-insight">💡 <strong>Insight:</strong> {insight}</div>
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ═════════════════════════════════════════════════════════════════════════════
stats = load_stats()

st.markdown(f"""
<div class="page-header">
    <div class="page-header-left">
        <div class="page-title">⚡ Fraud Risk Intelligence</div>
        <div class="page-subtitle">Digital Banking Analytics &nbsp;·&nbsp; {stats['date_min']} — {stats['date_max']}</div>
    </div>
    <div class="page-header-badge">Fraud Risk Intelligence</div>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# CRITICAL ALERT
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="alert-banner">
    <div class="alert-icon">⚠️</div>
    <div class="alert-body">
        <div class="alert-title">Critical Risk Signal Identified</div>
        <div class="alert-text">
            Online transactions carry a <strong>0.84% fraud rate — 28× higher</strong> than in-store swipe (0.03%).
            Computer &amp; electronics retailers hit <strong>10.83%</strong> fraud rate, over 70× the dataset average.
            Both signals combine: an online purchase at an electronics merchant is the highest-risk scenario in this dataset.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# KPI STRIP
# ═════════════════════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)

kpi_data = [
    (k1, BLUE,   "Total transactions",    f"{stats['total_transactions']:,}",    None, None),
    (k2, RED,    "Confirmed fraud",        f"{stats['fraud_count']:,}",           "HIGH RISK", "up"),
    (k3, ORANGE, "Fraud rate",             f"{stats['fraud_rate_pct']:.3f}%",     "0.15% AVG", "neutral"),
    (k4, GREEN,  "Median legit amount",   f"${stats['median_legit_amount']:.2f}", None, None),
    (k5, RED,    "Median fraud amount",   f"${stats['median_fraud_amount']:.2f}",
        f"+${stats['median_fraud_amount']-stats['median_legit_amount']:.2f} vs legit", "up"),
]

for col, accent, label, value, delta_text, delta_type in kpi_data:
    with col:
        delta_html = ""
        if delta_text:
            delta_html = f'<div class="kpi-delta kpi-delta-{delta_type}">{delta_text}</div>'
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-accent" style="background:{accent};"></div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — FRAUD CONCENTRATION
# ═════════════════════════════════════════════════════════════════════════════
section("01 — Where Fraud Happens: Merchant & Amount")

col_mcc, col_amt = st.columns([1.2, 1], gap="large")

with col_mcc:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title("Fraud rate by merchant category", badge=("high", "HIGH RISK"))

    mcc = load_csv("fraud_by_mcc.csv")
    top_n = st.select_slider("Top N merchants", options=[5,10,15,20,30], value=15, key="mcc_n",
                             label_visibility="collapsed")
    mcc_plot = mcc.nlargest(top_n, "fraud_rate_pct").sort_values("fraud_rate_pct")

    bar_colors = []
    for v in mcc_plot["fraud_rate_pct"]:
        if v > 5: bar_colors.append(RED)
        elif v > 1: bar_colors.append(ORANGE)
        else: bar_colors.append(YELLOW)

    fig_mcc = go.Figure(go.Bar(
        x=mcc_plot["fraud_rate_pct"],
        y=mcc_plot["mcc_label"],
        orientation="h",
        marker_color=bar_colors,
        marker_line_color=BLACK,
        marker_line_width=2,
        text=[f"{v:.2f}%" for v in mcc_plot["fraud_rate_pct"]],
        textposition="outside",
        textfont=dict(size=10, color=BLACK, family="Space Grotesk, Arial Black"),
        hovertemplate="<b>%{y}</b><br>Fraud rate: %{x:.3f}%<br>Volume: %{customdata:,}<extra></extra>",
        customdata=mcc_plot["total_count"],
    ))
    fig_mcc.update_layout(
        **neo_layout(showlegend=False),
        height=420,
        xaxis=dict(title="Fraud rate (%)", showgrid=True, gridcolor="#E8E4D9",
                   linecolor=BLACK, linewidth=2, tickfont=dict(size=10)),
        yaxis=dict(title="", showgrid=False, linecolor=BLACK, linewidth=2,
                   tickfont=dict(size=10)),
        xaxis_range=[0, mcc_plot["fraud_rate_pct"].max() * 1.3],
    )
    st.plotly_chart(fig_mcc, use_container_width=True, config={"displayModeBar": False})
    fi(
        "Computer equipment retailers hit 10.83% fraud — 70× the 0.15% average. "
        "Electronics stores follow at 8.57%.",
        "MCC code is the single strongest fraud signal. "
        "Tiered limits for MCC codes 5045 and 5065 alone would cover the bulk of high-rate exposure."
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_amt:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title("Transaction amount distribution", badge=("med", "SIGNAL"))

    hist = load_csv("amount_histogram.csv")
    fig_amt = go.Figure()
    fig_amt.add_trace(go.Bar(
        x=hist["log10_amount"], y=hist["legit_density"],
        name="Legitimate",
        marker_color=GREEN, marker_line_color=BLACK, marker_line_width=1,
        opacity=0.85,
    ))
    fig_amt.add_trace(go.Bar(
        x=hist["log10_amount"], y=hist["fraud_density"],
        name="Fraud",
        marker_color=RED, marker_line_color=BLACK, marker_line_width=1,
        opacity=0.85,
    ))
    tick_vals = [0, 1, 2, 3, 4]
    tick_text = ["$1", "$10", "$100", "$1K", "$10K"]
    fig_amt.update_layout(
        **neo_layout(),
        barmode="overlay",
        height=220,
        xaxis=dict(title="Amount (log scale)", tickvals=tick_vals, ticktext=tick_text,
                   linecolor=BLACK, linewidth=2, showgrid=True, gridcolor="#E8E4D9"),
        yaxis=dict(title="Density", linecolor=BLACK, linewidth=2,
                   showgrid=True, gridcolor="#E8E4D9"),
    )
    st.plotly_chart(fig_amt, use_container_width=True, config={"displayModeBar": False})

    # Amount stat callouts
    a1, a2 = st.columns(2)
    a1.markdown(f"""
    <div style="border:3px solid {BLACK}; background:{GREEN}; padding:12px; text-align:center; box-shadow:3px 3px 0 {BLACK};">
        <div style="font-size:0.65rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{BLACK};">Median Legit</div>
        <div style="font-size:1.6rem;font-weight:900;color:{BLACK};">${stats['median_legit_amount']:.2f}</div>
    </div>""", unsafe_allow_html=True)
    a2.markdown(f"""
    <div style="border:3px solid {BLACK}; background:{RED}; padding:12px; text-align:center; box-shadow:3px 3px 0 {BLACK};">
        <div style="font-size:0.65rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{WHITE};">Median Fraud</div>
        <div style="font-size:1.6rem;font-weight:900;color:{WHITE};">${stats['median_fraud_amount']:.2f}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    fi(
        f"Fraud median is ${stats['median_fraud_amount']:.2f} vs ${stats['median_legit_amount']:.2f} "
        "for legitimate. A second fraud peak appears in the $500–$2,000 range.",
        "Amount alone is too weak to trigger on. But transactions above $200 in high-MCC-risk "
        "categories warrant automatic step-up."
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — CHANNEL & CARD RISK
# ═════════════════════════════════════════════════════════════════════════════
section("02 — How Fraud Travels: Channel & Card")

c1, c2, c3 = st.columns(3, gap="large")

def small_bar(df, x_col, y_col, title, colors, badge=None):
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title(title, badge=badge)
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col],
        marker_color=colors[:len(df)],
        marker_line_color=BLACK, marker_line_width=2,
        text=[f"{v:.3f}%" for v in df[y_col]],
        textposition="outside",
        textfont=dict(size=11, color=BLACK),
    ))
    fig.update_layout(
        **neo_layout(showlegend=False),
        height=260,
        yaxis=dict(title="Fraud rate (%)", linecolor=BLACK, linewidth=2,
                   showgrid=True, gridcolor="#E8E4D9", tickfont=dict(size=10)),
        xaxis=dict(linecolor=BLACK, linewidth=2, showgrid=False, tickfont=dict(size=10)),
        yaxis_range=[0, df[y_col].max() * 1.3],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with c1:
    chip_df = load_csv("fraud_by_use_chip.csv")
    chip_df = chip_df[chip_df["use_chip"] != "Unknown"].sort_values("fraud_rate_pct", ascending=False)
    small_bar(chip_df, "use_chip", "fraud_rate_pct",
              "By transaction method", [RED, ORANGE, GREEN], badge=("high", "HIGH RISK"))
    fi(
        "Online: 0.84% fraud rate — 28× swipe (0.03%).",
        "Card-not-present is the primary attack surface. 3DS 2.0 is the clearest fix."
    )

with c2:
    ctype = load_csv("fraud_by_card_type.csv").sort_values("fraud_rate_pct", ascending=False)
    small_bar(ctype, "card_type", "fraud_rate_pct",
              "By card type", [RED, ORANGE, GREEN], badge=("med", "ELEVATED"))
    fi(
        "Prepaid debit: 0.22% fraud — 1.65× standard debit.",
        "Prepaid card issuance needs tighter KYC. Credit is mid-range, not the worst offender."
    )

with c3:
    chip_yn = load_csv("fraud_by_has_chip.csv").sort_values("fraud_rate_pct", ascending=False)
    small_bar(chip_yn, "has_chip", "fraud_rate_pct",
              "Chip card vs. no chip", [RED, GREEN], badge=("low", "ACTIONABLE"))
    fi(
        "Non-chip cards have markedly higher fraud rates.",
        "Replacing remaining magnetic-stripe cards directly reduces counterfeit fraud. Cheap fix."
    )

st.markdown("<br>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — TEMPORAL PATTERNS
# ═════════════════════════════════════════════════════════════════════════════
section("03 — When Fraud Strikes: Temporal Patterns")

col_heat, col_trend = st.columns([1.4, 1], gap="large")

with col_heat:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title("Fraud rate heatmap — hour of day × day of week", badge=("med", "PATTERN"))

    heatmap_df = load_heatmap()
    fig_heat = px.imshow(
        heatmap_df,
        labels=dict(x="Hour of day (0–23)", y="", color="Fraud %"),
        color_continuous_scale=[
            [0.0, WHITE],
            [0.2, "#FFE6E4"],
            [0.5, ORANGE],
            [0.8, RED],
            [1.0, "#8B0000"],
        ],
        aspect="auto",
        text_auto=".2f",
    )
    fig_heat.update_traces(textfont=dict(size=8, color=BLACK))
    fig_heat.update_layout(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(family="Space Grotesk, Arial", color=BLACK, size=10),
        coloraxis_colorbar=dict(
            title="Fraud %",
            tickfont=dict(size=9),
            title_font=dict(size=10),
            thickness=14,
            len=0.8,
        ),
        margin=dict(l=8, r=8, t=10, b=8),
        height=290,
        xaxis=dict(linecolor=BLACK, linewidth=2, tickfont=dict(size=10)),
        yaxis=dict(linecolor=BLACK, linewidth=2, tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
    fi(
        "Midnight–5 AM on weekends shows the highest fraud concentration across all days.",
        "Time-of-day is a free feature. Flag late-night transactions with soft challenges, "
        "not hard declines, to protect real late-night shoppers."
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_trend:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title("Fraud rate vs. transaction volume over time")

    trend = load_csv("fraud_by_month.csv")
    fig_tr = make_subplots(specs=[[{"secondary_y": True}]])
    fig_tr.add_trace(go.Bar(
        x=trend["year_month"], y=trend["total_count"],
        name="Transaction volume",
        marker_color=BLUE, marker_line_color=BLACK, marker_line_width=1,
        opacity=0.35,
    ), secondary_y=True)
    fig_tr.add_trace(go.Scatter(
        x=trend["year_month"], y=trend["fraud_rate_pct"],
        name="Fraud rate (%)",
        line=dict(color=RED, width=3),
        mode="lines",
    ), secondary_y=False)
    fig_tr.update_layout(
        paper_bgcolor=WHITE,
        plot_bgcolor=OFFWHT,
        font=dict(family="Space Grotesk, Arial", color=BLACK, size=10),
        legend=dict(bgcolor=WHITE, bordercolor=BLACK, borderwidth=2, font=dict(size=9),
                    orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=8, r=8, t=30, b=8),
        height=290,
        xaxis=dict(linecolor=BLACK, linewidth=2, showgrid=False,
                   tickfont=dict(size=8), nticks=8),
    )
    fig_tr.update_yaxes(
        title_text="Fraud rate (%)", secondary_y=False,
        linecolor=BLACK, linewidth=2, gridcolor="#E8E4D9",
        title_font=dict(size=10), tickfont=dict(size=9),
    )
    fig_tr.update_yaxes(
        title_text="Volume", secondary_y=True,
        linecolor=BLACK, linewidth=2, showgrid=False,
        title_font=dict(size=10), tickfont=dict(size=9),
    )
    st.plotly_chart(fig_tr, use_container_width=True, config={"displayModeBar": False})
    fi(
        "Fraud rate fluctuates over time independently of transaction volume.",
        "Seasonal anomalies in the fraud rate signal external events (campaigns, compromised batches) "
        "worth investigating with the fraud team."
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — CUSTOMER RISK PROFILE
# ═════════════════════════════════════════════════════════════════════════════
section("04 — Who Is Targeted: Customer Risk Profile")

col_age, col_inc, col_corr = st.columns([1, 1, 1.2], gap="large")

with col_age:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title("Fraud rate by age group")
    age = load_csv("fraud_by_age.csv")
    age_colors = []
    for v in age["fraud_rate_pct"]:
        if v == age["fraud_rate_pct"].max(): age_colors.append(RED)
        elif v > age["fraud_rate_pct"].median(): age_colors.append(ORANGE)
        else: age_colors.append(YELLOW)
    fig_age = go.Figure(go.Bar(
        x=age["age_group"].astype(str), y=age["fraud_rate_pct"],
        marker_color=age_colors, marker_line_color=BLACK, marker_line_width=2,
        text=[f"{v:.3f}%" for v in age["fraud_rate_pct"]],
        textposition="outside", textfont=dict(size=10, color=BLACK),
    ))
    fig_age.update_layout(
        **neo_layout(showlegend=False), height=280,
        yaxis=dict(title="Fraud rate (%)", linecolor=BLACK, linewidth=2,
                   showgrid=True, gridcolor="#E8E4D9", tickfont=dict(size=10)),
        xaxis=dict(linecolor=BLACK, linewidth=2, showgrid=False, tickfont=dict(size=10)),
        yaxis_range=[0, age["fraud_rate_pct"].max() * 1.35],
    )
    st.plotly_chart(fig_age, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_inc:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title("Fraud rate by income bracket")
    income = load_csv("fraud_by_income.csv")
    inc_colors = []
    for v in income["fraud_rate_pct"]:
        if v == income["fraud_rate_pct"].max(): inc_colors.append(RED)
        elif v > income["fraud_rate_pct"].median(): inc_colors.append(ORANGE)
        else: inc_colors.append(YELLOW)
    fig_inc = go.Figure(go.Bar(
        x=income["income_bracket"].astype(str), y=income["fraud_rate_pct"],
        marker_color=inc_colors, marker_line_color=BLACK, marker_line_width=2,
        text=[f"{v:.3f}%" for v in income["fraud_rate_pct"]],
        textposition="outside", textfont=dict(size=10, color=BLACK),
    ))
    fig_inc.update_layout(
        **neo_layout(showlegend=False), height=280,
        yaxis=dict(title="Fraud rate (%)", linecolor=BLACK, linewidth=2,
                   showgrid=True, gridcolor="#E8E4D9", tickfont=dict(size=10)),
        xaxis=dict(linecolor=BLACK, linewidth=2, showgrid=False,
                   tickfont=dict(size=10), tickangle=-15),
        yaxis_range=[0, income["fraud_rate_pct"].max() * 1.35],
    )
    st.plotly_chart(fig_inc, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_corr:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title("Feature correlation matrix", badge=("low", "MULTI-SIGNAL"))
    corr = load_corr()
    mask = np.tril(np.ones_like(corr, dtype=bool))
    corr_masked = corr.where(mask)

    fig_corr = px.imshow(
        corr_masked,
        color_continuous_scale=[
            [0.0, BLUE], [0.35, "#EEF3FF"],
            [0.5, WHITE],
            [0.65, "#FFEEEE"], [1.0, RED],
        ],
        color_continuous_midpoint=0,
        zmin=-0.35, zmax=0.35,
        text_auto=".2f",
        aspect="auto",
    )
    fig_corr.update_traces(textfont=dict(size=8))
    fig_corr.update_layout(
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        font=dict(family="Space Grotesk, Arial", color=BLACK, size=9),
        coloraxis_colorbar=dict(thickness=12, len=0.7,
                                title="r", title_font=dict(size=9), tickfont=dict(size=8)),
        margin=dict(l=8, r=8, t=10, b=8),
        height=280,
        xaxis=dict(linecolor=BLACK, linewidth=1, tickfont=dict(size=8), tickangle=-30),
        yaxis=dict(linecolor=BLACK, linewidth=1, tickfont=dict(size=8)),
    )
    st.plotly_chart(fig_corr, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# Combined finding for demographics section
fi(
    "Under-25s have the highest fraud victimization by age. "
    "Sub-$30K income bracket leads across income. No single feature correlates strongly with fraud (max r = 0.04).",
    "No threshold rule catches this. Fraud requires combining MCC + channel + time + demographics in a scoring model. "
    "Target fraud awareness campaigns at younger, lower-income segments."
)
st.markdown("<br>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — TRANSACTION INTELLIGENCE EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
section("05 — Transaction Intelligence Explorer")

st.markdown(f"""
<div style="background:{BLACK}; color:{WHITE}; padding:8px 16px; font-size:0.75rem;
     font-weight:600; margin-bottom:16px; border-bottom:3px solid {YELLOW};">
    Sample: all 13,332 fraud transactions + 80,000 random legitimate transactions
    from the full 8.9M-row dataset &nbsp;·&nbsp; Use filters below to explore patterns
</div>""", unsafe_allow_html=True)

sample = load_sample()

# Filter row
f1, f2, f3, f4 = st.columns([1.2, 1.2, 1.2, 1])
with f1:
    tx_method = st.multiselect("Transaction method",
        options=sorted(sample["use_chip"].unique()),
        default=sorted(sample["use_chip"].unique()),
        key="ex_method")
with f2:
    card_types = st.multiselect("Card type",
        options=sorted(sample["card_type"].unique()),
        default=sorted(sample["card_type"].unique()),
        key="ex_card")
with f3:
    fraud_filter = st.radio("Transactions to show",
        ["All", "Fraud only", "Legitimate only"], horizontal=True, key="ex_fraud")
with f4:
    amount_range = st.slider("Amount ($)", 0, 5000, (0, 5000), key="ex_amt")

# Apply filters
mask = (
    sample["use_chip"].isin(tx_method) &
    sample["card_type"].isin(card_types) &
    sample["amount"].between(amount_range[0], amount_range[1])
)
if fraud_filter == "Fraud only":    mask &= sample["is_fraud"] == 1
elif fraud_filter == "Legitimate only": mask &= sample["is_fraud"] == 0
filtered = sample[mask]

# Filtered KPIs
fk1, fk2, fk3, fk4 = st.columns(4)
frate = filtered["is_fraud"].mean() * 100 if len(filtered) else 0
med_amt = filtered["amount"].median() if len(filtered) else 0
for col, accent, label, value in [
    (fk1, BLUE,  "Transactions",  f"{len(filtered):,}"),
    (fk2, RED,   "Fraud cases",   f"{filtered['is_fraud'].sum():,}"),
    (fk3, ORANGE,"Fraud rate",    f"{frate:.3f}%"),
    (fk4, GREEN, "Median amount", f"${med_amt:.2f}"),
]:
    col.markdown(f"""
    <div style="background:{WHITE};border:3px solid {BLACK};box-shadow:4px 4px 0 {BLACK};
         padding:14px 16px;margin-bottom:12px;">
        <div style="width:100%;height:3px;background:{accent};margin-bottom:8px;"></div>
        <div style="font-size:0.65rem;font-weight:800;text-transform:uppercase;
             letter-spacing:2px;color:#777;">{label}</div>
        <div style="font-size:1.7rem;font-weight:900;color:{BLACK};">{value}</div>
    </div>""", unsafe_allow_html=True)

if len(filtered) > 0:
    ex_left, ex_right = st.columns(2, gap="large")

    with ex_left:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        panel_title("Amount distribution — filtered selection")
        samp_plot = filtered.sample(min(len(filtered), 5000), random_state=42)
        color_map = samp_plot["is_fraud"].map({1: "Fraud", 0: "Legitimate"})
        fig_ex_amt = px.histogram(
            samp_plot, x="amount", color=color_map,
            nbins=50, log_x=True, barmode="overlay",
            color_discrete_map={"Fraud": RED, "Legitimate": GREEN},
            labels={"amount": "Amount ($)", "color": ""},
            opacity=0.8,
        )
        fig_ex_amt.update_traces(marker_line_color=BLACK, marker_line_width=1)
        fig_ex_amt.update_layout(**neo_layout(), height=280)
        st.plotly_chart(fig_ex_amt, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with ex_right:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        panel_title("Top fraud merchants — filtered selection")
        mcc_f = (
            filtered.groupby("mcc_label")
            .agg(fraud_rate=("is_fraud", lambda x: x.mean() * 100),
                 count=("is_fraud", "count"))
            .query("count >= 5")
            .nlargest(10, "fraud_rate")
            .sort_values("fraud_rate")
            .reset_index()
        )
        if len(mcc_f):
            fig_ex_mcc = go.Figure(go.Bar(
                x=mcc_f["fraud_rate"], y=mcc_f["mcc_label"],
                orientation="h",
                marker_color=RED, marker_line_color=BLACK, marker_line_width=2,
                text=[f"{v:.2f}%" for v in mcc_f["fraud_rate"]],
                textposition="outside", textfont=dict(size=10, color=BLACK),
            ))
            fig_ex_mcc.update_layout(
                **neo_layout(showlegend=False), height=280,
                xaxis=dict(title="Fraud rate (%)", linecolor=BLACK, linewidth=2,
                           showgrid=True, gridcolor="#E8E4D9"),
                yaxis=dict(title="", linecolor=BLACK, linewidth=2, showgrid=False,
                           tickfont=dict(size=10)),
                xaxis_range=[0, mcc_f["fraud_rate"].max() * 1.3],
            )
            st.plotly_chart(fig_ex_mcc, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Not enough data in this filter to show merchant breakdown.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Data table
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    panel_title(f"Transaction records — showing first 500 of {len(filtered):,} filtered rows")
    display = (
        filtered[["date","amount","use_chip","mcc_label","is_fraud",
                  "card_type","age_group","income_bracket","has_chip"]]
        .rename(columns={
            "use_chip": "method", "mcc_label": "merchant_category",
            "is_fraud": "fraud", "age_group": "age", "income_bracket": "income",
            "has_chip": "chip",
        })
        .head(500)
    )
    st.dataframe(display, use_container_width=True, hide_index=True, height=280)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown(f"""
    <div style="background:{YELLOW};border:3px solid {BLACK};box-shadow:5px 5px 0 {BLACK};
         padding:20px;text-align:center;font-weight:800;font-size:1rem;">
        No transactions match the current filters.
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<hr>
<div style="display:flex;justify-content:space-between;align-items:center;
     padding:8px 0;font-size:0.72rem;color:#888;font-weight:500;">
    <div>
        <strong style="color:{BLACK};">Data:</strong>
        computingvictor · Financial Transactions Dataset: Analytics · Kaggle · Oct 2024
    </div>
    <div>April 2026</div>
</div>
""", unsafe_allow_html=True)
