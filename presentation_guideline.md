# Presentation Guideline
## Transaction Patterns and Fraud Risk Indicators in Digital Banking
**Course:** CSDS 327 – Data Visualization | University of Southeastern Philippines  
**Dataset:** 8,914,963 transactions · 13,332 fraud cases · 0.15% fraud rate · 2010–2019

---

## How to use this document

Each slide below contains:
- **Headline** — the big text on screen (one sentence, one idea)
- **Visual** — which chart or layout to show
- **Key numbers** — data points to highlight or annotate
- **Speaker notes** — what to say (can be shortened for a 5-minute presentation)
- **Transition** — how to link to the next slide

---

## Slide 1 — Title

**Headline:**
> Transaction Patterns and Fraud Risk Indicators in Digital Banking

**Subtitle:**
> 8.9 Million Transactions · 10-Year Dataset · What the Data Reveals

**Visual:**
Three large number cards side by side:
- `8,914,963` — Total Transactions
- `13,332` — Fraud Cases
- `0.150%` — Overall Fraud Rate

Below the cards, add team names, course name, institution, and date.

**Speaker notes:**
"Good [morning/afternoon]. Today we're presenting our analysis of a real-world financial transactions dataset from Kaggle — nearly nine million transactions spanning a decade of digital banking activity. We identified 13,332 fraudulent transactions out of those nine million. That sounds small, but fraud is never random. Our goal was to find the patterns that explain where, when, and how fraud happens — and what banks can actually do about it."

**Transition:** "Let's start with the big picture."

---

## Slide 2 — The Scale of the Problem

**Headline:**
> 1 in 668 transactions is fraudulent — but fraud is not random

**Visual:**
Two-column layout:
- Left: Large fraud rate number (`0.150%`) in red/amber, with a context sentence below it
- Right: Two stat cards stacked:
  - `$120.71` — Average fraud transaction (labeled "Avg Fraud Amount")
  - `$47.93` — Average legitimate transaction (labeled "Avg Legit Amount")
  - Add note: "Fraud transactions are 2.5× higher in value on average"

**Key numbers to call out:**
- 0.150% fraud rate
- $120.71 vs $47.93 (2.5× difference)
- 2010–2019 date range

**Speaker notes:**
"One in 668 transactions in this dataset is fraudulent. That's a very low rate — but when you're processing millions of transactions, even 0.15% means thousands of fraud cases and significant financial loss. One early signal: fraudulent transactions are consistently higher in value — averaging $120 versus $48 for legitimate ones. This tells us fraud isn't random noise. It clusters. And finding those clusters is exactly what the rest of this presentation is about."

**Transition:** "Let's start with WHERE fraud happens."

---

## Slide 3 — WHERE: High-Value Goods Are 60–72× Riskier

**Headline:**
> Computer stores, electronics shops, and jewelers see fraud at 60 to 72 times the baseline rate

**Visual:**
Fraud Risk Matrix — Bubble Chart  
(Use the 'Fraud Risk Matrix' chart from the dashboard's WHERE section)
- X-axis: Fraud rate (%)
- Y-axis: Transaction volume (log scale)
- Bubble size: Absolute fraud case count
- Color: Red = high risk, amber = elevated, green = low
- Label the top 5 bubbles (Electronics, Computer Equipment, Precious Metals, etc.)
- Dashed vertical line at 0.15% baseline

**Key numbers to call out:**
- Computer equipment: **10.83%** (72× baseline)
- Electronics stores: **8.57%** (57× baseline)
- Precious metals: **6.87%** (46× baseline)
- Cruise Lines: **59.78%** (but only 276 transactions — a statistical outlier, not an operational priority)

**Speaker notes:**
"When we mapped fraud rates by merchant category, the pattern was stark. Merchants selling laptops, televisions, and jewelry see fraud at rates 46 to 72 times higher than the dataset average. These aren't coincidences — high-value, easily resalable goods are exactly what fraudsters target. The risk matrix we're showing here reveals two types of threats: niche categories with wild fraud rates but tiny transaction volumes — like cruise lines at 60%, which is alarming but represents barely 300 transactions — and high-volume, high-rate categories like electronics and computers. That second group is where the real operational priority lies."

**Transition:** "Now let's look at WHEN fraud is most likely to occur."

---

## Slide 4 — WHEN: Sunday Morning Is the Riskiest Window

**Headline:**
> Fraud peaks on Sunday at 10–11 AM — not at 3 AM as commonly assumed

**Visual:**
Hour × Day Heatmap  
(Use the heatmap from the dashboard's WHEN section)
- Color scale: White → Yellow → Orange → Red
- X-axis: Hours 0–23 (dark text, readable)
- Y-axis: Days of week (dark text, readable)
- Add a callout annotation: **"Sunday 10–11 AM: 0.44% — peak fraud window"** pointing at the Sunday mid-morning cells
- Optionally, annotate a second callout for weekday mid-morning cluster (Tue–Fri, 10–11 AM)

**Key numbers to call out:**
- Sunday 10 AM: **0.44%** fraud rate (3× the baseline)
- Sunday 11 AM: **0.41%**
- Tuesday 10 AM: **0.34%**
- Thursday 11 AM: **0.30%**
- Safe window: Late evening (8–10 PM), most weekdays

**Speaker notes:**
"One of our more surprising findings: fraud doesn't primarily happen at 3 in the morning. The highest fraud rates in the entire dataset occur on Sunday late-morning — 10 AM to 1 PM — with Sunday 10 AM hitting 0.44%, nearly three times the dataset average. Weekday mid-mornings (10–11 AM, Tuesday through Friday) are also elevated. This pattern likely reflects online shopping fraud happening when people are active but fraud monitoring teams may be understaffed on weekends."

**Transition:** "The timing tells us when. The next question is HOW fraud happens — which transaction methods are most vulnerable."

---

## Slide 5 — HOW: Online Transactions Are 28× Riskier Than Chip

**Headline:**
> The gap between online and in-store fraud is the most important number in this dataset

**Visual:**
Three Lollipop Charts side by side (use the HOW section from the dashboard):
1. **Payment Channel** — Online (0.84%), Chip (0.10%), Swipe (0.03%)
2. **Card Type** — Prepaid (0.22%), Credit (0.16%), Debit (0.13%)
3. **Chip Status** — No chip (higher), Has chip (lower)

Make the "Online" dot visually distinct — annotate it with "28× higher than swipe" or highlight in red.

**Key numbers to call out:**
- Online: **0.84%** (28× swipe, 8× chip)
- Chip swipe: **0.03%** (lowest of all channels)
- Prepaid debit: **0.22%** (highest card type)
- The chip-vs-no-chip gap is visually striking

**Speaker notes:**
"The payment channel is the single clearest predictor of fraud risk. An online transaction is 28 times more likely to be fraudulent than an in-person chip swipe. That's not a small effect — it's the dominant fraud vector in this entire dataset. The card type adds another layer: prepaid debit cards carry higher risk than standard debit or credit. And cards without chip technology are consistently more vulnerable than chip-enabled ones. Together, these three charts tell a story about card-not-present fraud being the industry's biggest unsolved problem."

**Transition:** "We've covered where, when, and how. Now — who is most at risk?"

---

## Slide 6 — WHO: Younger and Lower-Income Cardholders Face the Highest Exposure

**Headline:**
> Under-25 cardholders and those earning under $30K are the most fraud-exposed demographic segments

**Visual:**
Two bar charts side by side (use the WHO section from the dashboard):
1. **Fraud Rate by Age Group** — bars for: <25, 25–34, 35–44, 45–54, 55–64, 65+
2. **Fraud Rate by Income Bracket** — bars for: <$30K, $30–60K, $60–100K, $100–150K, $150K+

Color bars using the same RAG scheme (red/amber/green). Add a dashed average line at 0.15%.

Add a note below or beside the charts:
> "Maximum Pearson correlation with fraud: r = 0.04. Demographics alone are weak predictors."

**Key numbers to call out:**
- Under-25 fraud rate (highest age cohort)
- Under-$30K income bracket rate (highest income cohort)
- r = 0.04 — almost no linear relationship

**Speaker notes:**
"Younger cardholders and lower-income earners face the highest fraud exposure in the dataset. This likely reflects higher online transaction frequency and lower adoption of security features like two-factor authentication. But there's an important caveat: the correlation between any demographic variable and fraud is almost flat — maxing out at 0.04 on the Pearson scale. Demographics tell us where fraud awareness programs should focus, not where fraud detection algorithms should profile people."

**Transition:** "So what does all of this mean? What should a bank actually do?"

---

## Slide 7 — Recommendations: Five Evidence-Based Actions

**Headline:**
> Five targeted actions, each directly supported by the data

**Visual:**
A clean numbered list or table. Use a simple two-column layout or card-per-action design.

| # | Action | Why | Priority |
|---|--------|-----|----------|
| 1 | **MCC-specific step-up auth** — require OTP for purchases over $500 at computer (5045), electronics (5065), and precious metals (5094) merchants | These categories are 45–72× riskier than baseline | HIGH |
| 2 | **3D Secure 2.0 for all online transactions** — add biometric/behavioral verification for card-not-present purchases | Online channel runs 28× the fraud rate of chip swipe | HIGH |
| 3 | **Time-aware soft authentication** — OTP prompt (not hard decline) during Sunday 10 AM–1 PM and weekday 10–11 AM peak windows | Targets the highest-risk hours without blocking legitimate users | MEDIUM |
| 4 | **Accelerate chip card rollout** — proactively issue chip cards to all magnetic-stripe holders; prioritize prepaid accounts | Chip cards dramatically reduce in-person counterfeit fraud | MEDIUM |
| 5 | **In-app fraud education for under-25 and under-$30K cardholders** — phishing awareness, 2FA setup prompts | Low-cost, high-dignity way to reduce victimization in highest-risk segments | LOW |

**Speaker notes:**
"Each recommendation maps directly to a finding. MCC controls target the WHERE. 3D Secure targets the HOW. Time-aware authentication targets the WHEN. Chip rollout addresses card technology risk. And education targets the WHO. None of these are speculative — they're direct translations of the data patterns we found. The highest-priority actions are online channel hardening and MCC-specific controls, because those segments carry the most absolute fraud risk."

**Transition:** "Let's close with what all of this adds up to."

---

## Slide 8 — Conclusion: Fraud Is Predictable. Prevention Is Achievable.

**Headline:**
> No single feature is sufficient — but five combined signals make fraud detectable

**Visual:**
Five insight cards in a 2-column grid (or horizontal strip):

| Dimension | Finding |
|-----------|---------|
| **WHERE** | Computer stores and electronics see 45–72× the baseline fraud rate |
| **WHEN** | Sunday 10–11 AM is the peak fraud window — 3× the average |
| **HOW** | Online transactions are 28× riskier than chip swipe |
| **WHO** | Under-25 and under-$30K segments are most exposed |
| **HOW MUCH** | Fraud transactions average 2.5× the legitimate transaction value |

Below the cards, add a final callout box:
> "No single variable reliably predicts fraud (max r = 0.04). A gradient-boosted ensemble model combining merchant category, payment channel, hour of day, card type, and amount would dramatically outperform any single rule — catching more fraud with far less friction for honest customers."

**Speaker notes:**
"To close: fraud in this dataset is not random noise. It clusters clearly across five dimensions — where people spend, when they transact, how they pay, who they are, and how much they spend. But here's the key insight: no single dimension is strong enough on its own. The correlations are near zero. What that tells us is that the bank's best tool isn't a simple rule — it's a machine learning model that combines all five signals simultaneously. The data is telling us exactly which signals matter and which windows to focus on. Acting on that is a choice."

**Final line (optional closing statement):**
"Thank you. We're happy to take questions."

---

## Chart Reference

| Slide | Chart Name | Dashboard Section | Notes |
|-------|-----------|-------------------|-------|
| 2 | KPI cards | Header strip | Use the 5-metric layout |
| 3 | Risk Matrix (Bubble chart) | WHERE — left panel | Filter: min vol 500 |
| 4 | Heatmap (Hour × Day) | WHEN — left panel | Annotate Sunday 10–11 AM |
| 5 | Lollipop charts × 3 | HOW | All three columns |
| 6 | Demographic bar charts × 2 | WHO | Age + income side by side |
| 7 | Table / card layout | — | Design manually in slide tool |
| 8 | Summary card grid | — | Design manually in slide tool |

---

## Data Accuracy Notes

- Fraud rate: **0.150%** (not 0.15 — the trailing zero matters for precision)
- Peak fraud window: **Sunday 10 AM (0.44%)**, NOT 3 AM — verified from raw heatmap data
- Online vs. swipe lift: **28×** (0.84% / 0.03%)
- Computer equipment MCC fraud rate: **10.83%** (72× baseline)
- Fraud transaction median: **$69.97** vs. legitimate median **$28.95** (2.4× ratio)
- Dataset range: **2010-01-01 to 2019-10-31** (approximately 10 years)

---

*Generated from: Financial Transactions Dataset, computingvictor (Kaggle, Oct 2024)*  
*Analysis: Python 3.12 · Pandas · Plotly · Streamlit*
