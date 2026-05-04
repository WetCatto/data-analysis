"""
_theme.py — shared design tokens, Plotly helpers, and cached data loaders.
Imported by app.py (executive dashboard) and pages/presentation.py (storytelling).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

AGG = Path(__file__).parent / "aggregates"

# ── Design tokens ──────────────────────────────────────────────────────────────
BG      = "#F8FAFC"
CARD    = "#FFFFFF"
BORDER  = "#E2E8F0"
TXT_PRI = "#0F172A"
TXT_SEC = "#64748B"
TXT_TER = "#94A3B8"
DANGER  = "#EF4444"
WARNING = "#F59E0B"
SAFE    = "#10B981"
INFO    = "#3B82F6"
CAT     = ["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#EECA3B"]
AVG_RATE = 0.15


def rate_color(rate_pct: float) -> str:
    if rate_pct >= 0.3:
        return DANGER
    if rate_pct >= 0.15:
        return WARNING
    return SAFE


def status_badge(rate: float) -> tuple[str, str, str, str]:
    """Returns (label, badge_color, band_bg, band_border)."""
    if rate >= 0.3:
        return "CRITICAL", DANGER, "#FEF2F2", "#FECACA"
    if rate >= 0.10:
        return "ELEVATED", WARNING, "#FFFBEB", "#FDE68A"
    return "NORMAL", SAFE, "#F0FDF4", "#BBF7D0"


# ── Plotly base helpers ────────────────────────────────────────────────────────
def chart_layout(**kw) -> dict:
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


def pchart(fig):
    st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)


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


# ── Reusable chart builders ────────────────────────────────────────────────────
def lollipop_chart(df: pd.DataFrame, label_col: str, rate_col: str,
                   title: str, height: int = 320) -> go.Figure:
    df_s = df.sort_values(rate_col, ascending=True)
    colors = [rate_color(r) for r in df_s[rate_col]]
    fig = go.Figure()
    for _, row in df_s.iterrows():
        fig.add_trace(go.Scatter(
            x=[0, row[rate_col]], y=[row[label_col], row[label_col]],
            mode="lines", line=dict(color=BORDER, width=2),
            showlegend=False, hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter(
        x=df_s[rate_col], y=df_s[label_col],
        mode="markers+text",
        marker=dict(color=colors, size=12, line=dict(color="white", width=1.5)),
        text=[f"{v:.2f}%" for v in df_s[rate_col]],
        textposition="middle right",
        textfont=dict(size=10, color=TXT_SEC),
        showlegend=False,
        hovertemplate="%{y}<br>Fraud rate: %{x:.3f}%<extra></extra>",
    ))
    fig.add_vline(x=AVG_RATE, line_dash="dash", line_color=TXT_TER, line_width=1)
    fig.update_layout(**chart_layout(
        title_text=title, title_font=dict(size=11, color=TXT_PRI), height=height,
    ))
    fig.update_xaxes(xax(title="Fraud rate (%)"))
    fig.update_yaxes(yax(title="", showgrid=False))
    return fig


def demographic_bar(df: pd.DataFrame, label_col: str, rate_col: str,
                    title: str, height: int = 320) -> go.Figure:
    colors = [rate_color(r) for r in df[rate_col]]
    fig = go.Figure(go.Bar(
        x=df[label_col], y=df[rate_col],
        marker=dict(color=colors, line_width=0),
        text=[f"{v:.2f}%" for v in df[rate_col]],
        textposition="outside",
        textfont=dict(size=10, color=TXT_SEC),
        hovertemplate="%{x}<br>Fraud rate: %{y:.3f}%<extra></extra>",
    ))
    fig.add_hline(y=AVG_RATE, line_dash="dash", line_color=TXT_TER, line_width=1,
                  annotation_text="Avg", annotation_font=dict(size=9, color=TXT_TER),
                  annotation_position="top right")
    fig.update_layout(**chart_layout(
        title_text=title, title_font=dict(size=11, color=TXT_PRI), height=height,
    ))
    fig.update_xaxes(xax(title=""))
    fig.update_yaxes(yax(title="Fraud rate (%)"))
    return fig


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
def load_sample() -> pd.DataFrame:
    return pd.read_parquet(AGG / "sample_transactions.parquet")
