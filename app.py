"""
Fraud Risk Intelligence — Executive Dashboard
Design: Tufte / Few / Knaflic principles · Loads pre-computed aggregates only.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from _theme import (
    BORDER, CARD, DANGER, INFO, SAFE, TXT_PRI, TXT_SEC, TXT_TER, WARNING,
    AVG_RATE, CAT,
    chart_layout, xax, yax, pchart,
    section, lollipop_chart, demographic_bar, rate_color, status_badge,
    load_stats, load_mcc, load_histogram, load_heatmap, load_monthly,
    load_age, load_income, load_use_chip, load_card_type,
    load_has_chip, load_gender, load_card_brand,
)

st.set_page_config(
    page_title="Fraud Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

[data-testid="stNumberInput"] input,
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
[data-baseweb="popover"] ul, [data-baseweb="menu"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
[data-baseweb="menu"] li { color: #0F172A !important; }
[data-baseweb="menu"] li:hover { background: #F1F5F9 !important; }
</style>
""", unsafe_allow_html=True)


# ── Data ───────────────────────────────────────────────────────────────────────
stats       = load_stats()
total_tx    = stats.get("total_transactions", 0)
total_fraud = stats.get("fraud_count", 0)
fraud_rate  = stats.get("fraud_rate_pct", 0.0)
avg_legit   = stats.get("mean_legit_amount", 0.0)
avg_fraud   = stats.get("mean_fraud_amount", 0.0)
date_min    = stats.get("date_min", "2010-01-01")
date_max    = stats.get("date_max", "2019-10-31")
mult        = avg_fraud / avg_legit if avg_legit > 0 else 1.0

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
    st.metric("Fraud Rate", f"{fraud_rate:.3f}%", delta="vs 0.10% threshold",
              delta_color="inverse")
with k4:
    st.metric("Avg Legit Tx", f"${avg_legit:,.2f}")
with k5:
    st.metric("Avg Fraud Tx", f"${avg_fraud:,.2f}",
              delta=f"{mult:.1f}× legit avg", delta_color="inverse")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: WHERE?
# ══════════════════════════════════════════════════════════════════════════════
section("WHERE?", "merchant category risk matrix · transaction amount distribution")

col_mcc, col_amt = st.columns([3, 2], gap="medium")

with col_mcc:
    st.markdown(
        f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:4px;'>"
        f"Fraud Risk Matrix — Merchant Category</p>"
        f"<p style='font-size:0.68rem;color:{TXT_TER};margin-bottom:8px;'>"
        f"X = fraud rate · Y = transaction volume · bubble size = fraud cases · color = risk level</p>",
        unsafe_allow_html=True,
    )
    min_vol = st.select_slider(
        "Min transaction volume",
        options=[200, 500, 1_000, 2_000, 5_000, 10_000],
        value=500,
        key="min_vol",
        label_visibility="collapsed",
    )
    mcc_df = load_mcc()
    rate_col  = next((c for c in mcc_df.columns if "rate" in c.lower()), mcc_df.columns[1])
    label_col = next((c for c in mcc_df.columns if "mcc" in c.lower() or "label" in c.lower()), mcc_df.columns[0])
    total_col = next((c for c in mcc_df.columns if "total" in c.lower()), None)
    fraud_cnt = next((c for c in mcc_df.columns if "fraud" in c.lower() and "count" in c.lower()), None)

    mcc_show = mcc_df[mcc_df[total_col] >= min_vol].copy() if total_col else mcc_df.copy()

    if len(mcc_show) > 0 and fraud_cnt and total_col:
        max_fc = mcc_show[fraud_cnt].max()
        bubble_sizes = [max(6, 6 + 44 * (v / max_fc) ** 0.5) for v in mcc_show[fraud_cnt]]
        colors_bub = [rate_color(r) for r in mcc_show[rate_col]]
        custom = np.stack([mcc_show[fraud_cnt].values, mcc_show[total_col].values], axis=-1)

        fig_mcc = go.Figure(go.Scatter(
            x=mcc_show[rate_col],
            y=mcc_show[total_col],
            mode="markers",
            marker=dict(size=bubble_sizes, color=colors_bub, opacity=0.75,
                        line=dict(color="white", width=1.5)),
            text=mcc_show[label_col],
            customdata=custom,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Fraud rate: %{x:.2f}%<br>"
                "Total transactions: %{customdata[1]:,.0f}<br>"
                "Fraud cases: %{customdata[0]:,.0f}"
                "<extra></extra>"
            ),
        ))
        fig_mcc.add_vline(
            x=AVG_RATE, line_width=1.5, line_dash="dash", line_color=TXT_SEC,
            annotation_text="Avg 0.15%",
            annotation_font=dict(size=10, color=TXT_SEC),
            annotation_position="top right",
        )
        top5 = mcc_show.nlargest(min(5, len(mcc_show)), fraud_cnt)
        for _, row in top5.iterrows():
            fig_mcc.add_annotation(
                x=row[rate_col], y=row[total_col],
                text=str(row[label_col])[:30],
                font=dict(size=8, color=TXT_PRI),
                showarrow=True, arrowhead=2, arrowsize=1,
                arrowwidth=1, arrowcolor=TXT_TER,
                ax=22, ay=-28,
                bgcolor=CARD, bordercolor=BORDER, borderwidth=1, borderpad=3,
            )
        x_high = mcc_show[rate_col].quantile(0.75)
        y_high = mcc_show[total_col].quantile(0.75)
        fig_mcc.add_annotation(
            x=x_high, y=y_high, xref="x", yref="y",
            text="HIGH PRIORITY",
            font=dict(size=9, color=DANGER),
            showarrow=False, bgcolor="#FEF2F2",
            bordercolor="#FECACA", borderwidth=1, borderpad=4,
        )
        fig_mcc.update_layout(**chart_layout(height=460))
        fig_mcc.update_xaxes(xax(title="Fraud rate (%)"))
        fig_mcc.update_yaxes(yax(title="Transaction volume (log scale)", type="log"))
        pchart(fig_mcc)
    else:
        st.info("No merchant categories match the selected volume threshold.")

with col_amt:
    st.markdown(
        f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>"
        f"Amount Distribution — Fraud vs. Legitimate</p>",
        unsafe_allow_html=True,
    )
    hist_df = load_histogram()
    legit_col  = next((c for c in hist_df.columns if "legit" in c.lower()), None)
    fraud_col2 = next((c for c in hist_df.columns if "fraud" in c.lower()), None)
    bin_col    = hist_df.columns[0]
    bin_spacing = float(hist_df[bin_col].diff().median()) if len(hist_df) > 1 else 0.05

    if legit_col and fraud_col2:
        # Filter out sub-$3 bins to remove the $1 data-entry spike
        hist_plot = hist_df[hist_df[bin_col] > 0.5].copy()
        fig_amt = go.Figure()
        fig_amt.add_trace(go.Bar(
            x=hist_plot[bin_col], y=hist_plot[legit_col],
            name="Legitimate", marker_color="rgba(76,120,168,0.65)",
            marker_line_width=0, width=bin_spacing,
        ))
        fig_amt.add_trace(go.Bar(
            x=hist_plot[bin_col], y=hist_plot[fraud_col2],
            name="Fraud", marker_color="rgba(239,68,68,0.65)",
            marker_line_width=0, width=bin_spacing,
        ))
        fig_amt.update_layout(**chart_layout(
            showlegend=True, barmode="overlay", height=480,
            legend=dict(orientation="h", y=-0.18, yanchor="top",
                        bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
                        font=dict(size=11, color=TXT_SEC)),
        ))
        fig_amt.update_xaxes(xax(
            title="Amount (USD, log scale)",
            tickvals=[1, 2, 3, 4],
            ticktext=["$10", "$100", "$1K", "$10K"],
        ))
        fig_amt.update_yaxes(yax(title="Density"))
        pchart(fig_amt)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: WHEN?
# ══════════════════════════════════════════════════════════════════════════════
section("WHEN?", "time-of-day patterns · monthly trends")

col_heat, col_trend = st.columns([3, 2], gap="medium")

with col_heat:
    st.markdown(
        f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>"
        f"Fraud Rate — Hour × Day of Week</p>",
        unsafe_allow_html=True,
    )
    heat_df   = load_heatmap()
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
            [0.0, "#FFFFFF"],
            [0.33, "#FEF9C3"],
            [0.67, "#FDBA74"],
            [1.0, "#EF4444"],
        ],
        hovertemplate="Hour %{x} · %{y}<br>Fraud rate: %{z:.3f}%<extra></extra>",
        showscale=True,
        colorbar=dict(
            thickness=10, len=0.8,
            tickfont=dict(size=9, color=TXT_PRI),
            title=dict(text="Rate %", font=dict(size=10, color=TXT_PRI), side="right"),
        ),
    ))
    fig_heat.update_layout(**chart_layout(height=300))
    fig_heat.update_xaxes(xax(
        title="Hour of day", dtick=2,
        tickfont=dict(size=11, color=TXT_PRI),
        title_font=dict(size=11, color=TXT_PRI),
    ))
    fig_heat.update_yaxes(yax(
        title="", showgrid=False, autorange="reversed",
        tickfont=dict(size=11, color=TXT_PRI),
    ))
    pchart(fig_heat)

with col_trend:
    st.markdown(
        f"<p style='font-size:0.72rem;font-weight:600;text-transform:uppercase;"
        f"letter-spacing:1px;color:{TXT_PRI};margin-bottom:8px;'>"
        f"Monthly Fraud Rate Trend</p>",
        unsafe_allow_html=True,
    )
    month_df = load_monthly()
    rate_m   = next((c for c in month_df.columns if "rate" in c.lower()), month_df.columns[-1])
    cnt_m    = next((c for c in month_df.columns if "count" in c.lower() or "total" in c.lower()), None)
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
    pchart(fig_trend)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: HOW?
# ══════════════════════════════════════════════════════════════════════════════
section("HOW?", "payment channel · card type · chip status")

col_ch, col_ct, col_chip = st.columns(3, gap="medium")

with col_ch:
    uc_df   = load_use_chip()
    lbl_uc  = next((c for c in uc_df.columns if "chip" in c.lower() or "use" in c.lower()), uc_df.columns[0])
    rate_uc = next((c for c in uc_df.columns if "rate" in c.lower()), uc_df.columns[-1])
    pchart(lollipop_chart(uc_df, lbl_uc, rate_uc, "Payment Channel"))

with col_ct:
    ct_df   = load_card_type()
    lbl_ct  = next((c for c in ct_df.columns if "type" in c.lower()), ct_df.columns[0])
    rate_ct = next((c for c in ct_df.columns if "rate" in c.lower()), ct_df.columns[-1])
    pchart(lollipop_chart(ct_df, lbl_ct, rate_ct, "Card Type"))

with col_chip:
    hc_df   = load_has_chip()
    lbl_hc  = next((c for c in hc_df.columns if "chip" in c.lower()), hc_df.columns[0])
    rate_hc = next((c for c in hc_df.columns if "rate" in c.lower()), hc_df.columns[-1])
    pchart(lollipop_chart(hc_df, lbl_hc, rate_hc, "Chip Status"))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: WHO?
# ══════════════════════════════════════════════════════════════════════════════
section("WHO?", "demographics · model implications")

col_age, col_inc, col_model = st.columns([1, 1, 2], gap="medium")

with col_age:
    age_df   = load_age()
    lbl_age  = next((c for c in age_df.columns if "age" in c.lower()), age_df.columns[0])
    rate_age = next((c for c in age_df.columns if "rate" in c.lower()), age_df.columns[-1])
    pchart(demographic_bar(age_df, lbl_age, rate_age, "Fraud Rate by Age Group", height=400))

with col_inc:
    inc_df   = load_income()
    lbl_inc  = next((c for c in inc_df.columns if "income" in c.lower()), inc_df.columns[0])
    rate_inc = next((c for c in inc_df.columns if "rate" in c.lower()), inc_df.columns[-1])
    pchart(demographic_bar(inc_df, lbl_inc, rate_inc, "Fraud Rate by Income", height=400))

with col_model:
    st.markdown(f"""
    <div style="background:#F8FAFC;border:1px solid {BORDER};border-left:4px solid {INFO};
                border-radius:8px;padding:28px 24px;height:380px;
                display:flex;flex-direction:column;justify-content:center;gap:20px;">
      <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;
                  letter-spacing:1.5px;color:{INFO};">Model Implication</div>
      <div style="font-size:1.35rem;font-weight:700;color:{TXT_PRI};line-height:1.3;">
        No single feature reliably<br>predicts fraud
      </div>
      <div style="font-size:0.85rem;color:{TXT_SEC};line-height:1.7;">
        Maximum Pearson correlation with <code>is_fraud</code>:<br>
        <strong style="color:{TXT_PRI};font-size:1rem;">r = 0.04</strong>
        &nbsp;(hour of day)<br><br>
        All features — amount, age, income, credit score,<br>
        card type, hour — are near-independent of fraud status.<br><br>
        <strong>Effective detection requires multivariate ensemble<br>
        models</strong> (gradient boosting, random forests) that combine<br>
        merchant risk, channel, time, and card signals together.
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: RISK EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
section("RISK EXPLORER", "filterable merchant category fraud rate chart")

ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 1], gap="medium")
with ctrl1:
    ex_min_rate = st.slider("Minimum fraud rate (%)", 0.0, 5.0, 0.15, step=0.01, key="ex_rate")
with ctrl2:
    ex_min_vol = st.slider("Minimum transaction volume", 200, 10_000, 500, step=100, key="ex_vol")
with ctrl3:
    ex_sort = st.selectbox("Sort by", ["Fraud Rate ↓", "Transaction Volume ↓", "Fraud Cases ↓"], key="ex_sort")

mcc_ex    = load_mcc()
rc_ex     = next((c for c in mcc_ex.columns if "rate"  in c.lower()), mcc_ex.columns[1])
lc_ex     = next((c for c in mcc_ex.columns if "label" in c.lower() or "mcc" in c.lower()), mcc_ex.columns[0])
tc_ex     = next((c for c in mcc_ex.columns if "total" in c.lower()), None)
fc_ex     = next((c for c in mcc_ex.columns if "fraud" in c.lower() and "count" in c.lower()), None)

mcc_filt = mcc_ex.copy()
if tc_ex:
    mcc_filt = mcc_filt[mcc_filt[tc_ex] >= ex_min_vol]
mcc_filt = mcc_filt[mcc_filt[rc_ex] >= ex_min_rate]

sort_map = {"Fraud Rate ↓": rc_ex, "Transaction Volume ↓": tc_ex or rc_ex, "Fraud Cases ↓": fc_ex or rc_ex}
mcc_filt = mcc_filt.sort_values(sort_map[ex_sort], ascending=False).reset_index(drop=True)

s1, s2, s3 = st.columns(3)
with s1:
    st.metric("Categories Flagged", len(mcc_filt))
with s2:
    fc_sum = int(mcc_filt[fc_ex].sum()) if fc_ex else 0
    st.metric("Fraud Cases in View", f"{fc_sum:,.0f}")
with s3:
    pct_fraud = fc_sum / total_fraud * 100 if total_fraud > 0 and fc_ex else 0
    st.metric("Share of All Fraud", f"{pct_fraud:.1f}%")

if len(mcc_filt) == 0:
    st.info("No categories match the selected filters.")
else:
    # Sort ascending so highest value is at the top of the horizontal bar chart
    chart_df = mcc_filt.sort_values(sort_map[ex_sort], ascending=True).reset_index(drop=True)
    lift_vals = (chart_df[rc_ex] / AVG_RATE).round(1)
    bar_colors = [rate_color(r) for r in chart_df[rc_ex]]
    bar_text   = [f"{r:.2f}%  ({l}× avg)" for r, l in zip(chart_df[rc_ex], lift_vals)]

    hover_parts = ["<b>%{y}</b>", "Fraud rate: %{x:.2f}%"]
    custom_cols = []
    if tc_ex and fc_ex:
        custom_cols = chart_df[[tc_ex, fc_ex]].values
        hover_parts += ["Transactions: %{customdata[0]:,}", "Fraud cases: %{customdata[1]:,}"]
    hover_tmpl = "<br>".join(hover_parts) + "<extra></extra>"

    chart_height = max(340, len(chart_df) * 28)
    fig_ex = go.Figure(go.Bar(
        x=chart_df[rc_ex],
        y=chart_df[lc_ex],
        orientation="h",
        marker=dict(color=bar_colors, line_width=0, opacity=0.85),
        text=bar_text,
        textposition="outside",
        textfont=dict(size=10, color=TXT_SEC),
        customdata=custom_cols if len(custom_cols) > 0 else None,
        hovertemplate=hover_tmpl,
    ))
    fig_ex.add_vline(
        x=AVG_RATE, line_width=1.5, line_dash="dash", line_color=TXT_SEC,
        annotation_text="Baseline 0.15%",
        annotation_font=dict(size=10, color=TXT_SEC),
        annotation_position="top right",
    )
    fig_ex.update_layout(**chart_layout(
        height=chart_height,
        margin=dict(l=10, r=180, t=40, b=10),
    ))
    fig_ex.update_xaxes(xax(title="Fraud rate (%)"))
    fig_ex.update_yaxes(yax(title="", showgrid=False, tickfont=dict(size=10, color=TXT_PRI)))
    pchart(fig_ex)
