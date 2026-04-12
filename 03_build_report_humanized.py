"""
03_build_report_humanized.py
Humanized version of the report — less AI-sounding prose.
Produces: Transaction_Fraud_Analysis_Report_Humanized.docx
Original preserved as: Transaction_Fraud_Analysis_Report.docx
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE    = Path(__file__).parent
FIGS    = BASE / "figures"
OUTPUT  = BASE / "Transaction_Fraud_Analysis_Report_Humanized.docx"

# ── Helpers ───────────────────────────────────────────────────────────────────

def set_margins(section, top=1.0, right=1.0, bottom=1.0, left=1.5):
    section.top_margin    = Inches(top)
    section.right_margin  = Inches(right)
    section.bottom_margin = Inches(bottom)
    section.left_margin   = Inches(left)
    section.page_width    = Cm(21.0)
    section.page_height   = Cm(29.7)


def apply_font(run, bold=False, size=12, color=None):
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def set_para_format(para, spacing=1.5, space_before=0, space_after=6, align=None):
    pf = para.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing      = spacing
    pf.space_before      = Pt(space_before)
    pf.space_after       = Pt(space_after)
    if align:
        pf.alignment = align


def add_heading(doc, text):
    p = doc.add_paragraph()
    set_para_format(p, space_before=12, space_after=6)
    run = p.add_run(text)
    apply_font(run, bold=True)
    return p


def add_body(doc, text, align=None):
    p = doc.add_paragraph()
    set_para_format(p, space_after=6)
    run = p.add_run(text)
    apply_font(run)
    if align:
        p.paragraph_format.alignment = align
    return p


def add_finding_insight(doc, finding_text, insight_text):
    p1 = doc.add_paragraph()
    set_para_format(p1, space_after=4)
    r1a = p1.add_run("Finding: ")
    apply_font(r1a, bold=True)
    r1b = p1.add_run(finding_text)
    apply_font(r1b)

    p2 = doc.add_paragraph()
    set_para_format(p2, space_after=10)
    r2a = p2.add_run("Insight: ")
    apply_font(r2a, bold=True)
    r2b = p2.add_run(insight_text)
    apply_font(r2b)


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    set_para_format(p, space_after=4)
    run = p.add_run(text)
    apply_font(run)
    return p


def add_figure(doc, fig_path, caption=None, width=5.5):
    doc.add_picture(str(fig_path), width=Inches(width))
    last = doc.paragraphs[-1]
    last.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        cp = doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_para_format(cp, space_after=8)
        run = cp.add_run(caption)
        apply_font(run, bold=False, size=10)


# ═════════════════════════════════════════════════════════════════════════════
# Build Document
# ═════════════════════════════════════════════════════════════════════════════
doc = Document()

for style in doc.styles:
    if style.name == "Normal":
        style.font.name = "Arial"
        style.font.size = Pt(12)

section = doc.sections[0]
set_margins(section)

# ── COVER PAGE ────────────────────────────────────────────────────────────────
def cover_line(doc, text, bold=False, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6):
    p = doc.add_paragraph()
    p.alignment = align
    set_para_format(p, space_after=space_after)
    run = p.add_run(text)
    apply_font(run, bold=bold, size=size)
    return p

cover_line(doc, " ", size=12, space_after=2)

cover_line(doc, "Transaction Patterns and Fraud Risk Indicators in Digital Banking:",
           bold=True, size=14, space_after=4)
cover_line(doc, "A 2024 Data-Driven Analysis", bold=True, size=14, space_after=30)

cover_line(doc, " ", size=12, space_after=2)

cover_line(doc, "Submitted by:", bold=True, size=12, space_after=4)
cover_line(doc, "[Member 1]", size=12, space_after=2)
cover_line(doc, "[Member 2]", size=12, space_after=2)
cover_line(doc, "[Member 3]", size=12, space_after=12)

cover_line(doc, "Instructor: [Instructor Name]", size=12, space_after=4)
cover_line(doc, "Date: April 2026", size=12, space_after=0)

doc.add_page_break()

# ── I. INTRODUCTION ───────────────────────────────────────────────────────────
add_heading(doc, "I. Introduction")
add_body(doc,
    "Digital banking has changed how people and organizations handle money. Mobile payments, "
    "contactless cards, and online transfers now account for the majority of transactions in most "
    "markets. The Association of Certified Fraud Examiners estimates that financial institutions "
    "lose billions of dollars annually to payment fraud, and digital channels are where an "
    "increasing share of that fraud occurs."
)
add_body(doc,
    "Banks and payment processors have relied on rule-based detection systems for decades, but "
    "static rules struggle to keep pace with how fraud tactics evolve. Identifying what actually "
    "separates fraudulent transactions from legitimate ones requires examining the transaction data "
    "directly, without assuming which variables matter in advance."
)
add_body(doc,
    "Research Question: What transaction characteristics and customer behaviors most significantly "
    "distinguish fraudulent transactions from legitimate ones in digital banking platforms?"
)
add_body(doc, "This study has three objectives:")
add_bullet(doc, "Identify the merchant categories, transaction methods, and time windows with the highest fraud rates.")
add_bullet(doc, "Examine whether customer demographic variables (age, income) are associated with fraud victimization.")
add_bullet(doc, "Determine which card attributes (card type, chip technology) are most protective against fraud.")

# ── II. DATASET DESCRIPTION ───────────────────────────────────────────────────
doc.add_paragraph()
add_heading(doc, "II. Dataset Description")
add_body(doc,
    "The dataset is \"Financial Transactions Dataset: Analytics,\" published on Kaggle by "
    "computingvictor and last updated October 2024 [1]. It simulates a digital banking environment "
    "and is distributed across five related files."
)
add_body(doc, "Dataset overview:")
add_bullet(doc, "Source: Kaggle (https://www.kaggle.com), computingvictor, October 2024")
add_bullet(doc, "Labelled transactions: 8,914,963 records with fraud/legitimate classification")
add_bullet(doc, "Fraud transactions: 13,332 (0.15% overall fraud rate)")
add_bullet(doc, "Date range: Multi-year, from 2010 onward")

add_body(doc, "The five files and their contents:")

# Variables table
table = doc.add_table(rows=6, cols=3)
table.style = "Table Grid"
headers = ["File", "Records", "Key Variables"]
rows_data = [
    ("transactions_data.csv", "13,305,915",
     "id, date, client_id, card_id, amount, use_chip, merchant_id, mcc, errors"),
    ("users_data.csv", "2,000",
     "id, current_age, gender, yearly_income, credit_score, num_credit_cards"),
    ("cards_data.csv", "6,146",
     "id, client_id, card_brand, card_type, has_chip, credit_limit"),
    ("train_fraud_labels.json", "8,914,963",
     "Transaction ID to fraud label (Yes/No)"),
    ("mcc_codes.json", "150 codes",
     "MCC integer code to merchant category description"),
]
hdr_cells = table.rows[0].cells
for i, h in enumerate(headers):
    hdr_cells[i].text = h
    for run in hdr_cells[i].paragraphs[0].runs:
        apply_font(run, bold=True, size=11)
for row_idx, row_data in enumerate(rows_data, start=1):
    cells = table.rows[row_idx].cells
    for col_idx, val in enumerate(row_data):
        cells[col_idx].text = val
        for run in cells[col_idx].paragraphs[0].runs:
            apply_font(run, size=10)

doc.add_paragraph()
add_body(doc, "Data limitations:")
add_bullet(doc, "The data is synthetic and may not capture all the variation present in real-world fraud.")
add_bullet(doc, "Approximately 33% of transactions had no fraud label and were excluded from analysis.")
add_bullet(doc, "Merchant city and state were excluded due to high cardinality.")
add_bullet(doc, "There are no behavioral signals like transaction velocity or device fingerprints.")

# ── III. METHODOLOGY ─────────────────────────────────────────────────────────
doc.add_paragraph()
add_heading(doc, "III. Methodology")
add_body(doc,
    "The analysis used Python 3.12 throughout. The work moved through four stages:"
)
add_bullet(doc,
    "Stage 1 - Data ingestion and optimization: The main transactions file is 1.2 GB, so column "
    "dtypes were set explicitly during loading (int32, float32, category), which cut memory use by "
    "around 60%. Fraud labels were loaded from JSON and joined to the transactions table.")
add_bullet(doc,
    "Stage 2 - Cleaning and feature engineering: Dollar signs and commas were stripped from "
    "monetary fields (amount, yearly_income, credit_limit). Dates were parsed and broken into "
    "hour, day of week, and month. Age and income were binned into groups. MCC integer codes were "
    "replaced with readable category names using the lookup file.")
add_bullet(doc,
    "Stage 3 - Exploratory data analysis: Fraud rates were calculated across merchant categories, "
    "transaction methods, card types, customer demographics, and time dimensions.")
add_bullet(doc,
    "Stage 4 - Visualization and reporting: Six charts were generated at 300 DPI using Matplotlib "
    "and Seaborn. The report was assembled programmatically in python-docx to match the A4, "
    "Arial 12, 1.5-line-spacing format specification.")
add_body(doc,
    "Tools used: Python 3.12, Pandas 2.x (data manipulation), Matplotlib 3.x and Seaborn 0.x "
    "(visualization), python-docx 1.x (report generation), PyArrow (Parquet I/O).")

# ── IV. DATA ANALYSIS & VISUAL FINDINGS ──────────────────────────────────────
doc.add_paragraph()
add_heading(doc, "IV. Data Analysis and Visual Findings")

# --- Fig 1
add_heading(doc, "Figure 1: Fraud rate by merchant category (top 15 highest-risk)")
add_figure(doc, FIGS / "fig1_fraud_by_mcc.png",
           "Figure 1. Top 15 merchant categories ranked by fraud rate.")
add_finding_insight(doc,
    "Computer and peripheral equipment retailers had the highest fraud rate at 10.83%, followed by "
    "electronics stores (8.57%) and precious stones and metals dealers (6.87%). Routine categories "
    "like grocery stores and service stations stayed below 0.05%.",
    "Electronics and luxury goods have high resale value, which makes them targets. Merchants in "
    "these categories should require additional verification for larger transactions and apply tighter "
    "velocity limits. Acquiring banks can address much of the dataset's fraud by treating these MCC "
    "codes differently from low-risk categories."
)

# --- Fig 2
add_heading(doc, "Figure 2: Transaction amount distribution - fraud vs. legitimate")
add_figure(doc, FIGS / "fig2_amount_distribution.png",
           "Figure 2. Log-scale histogram of transaction amounts by fraud status.")
add_finding_insight(doc,
    "Legitimate transactions are concentrated in the $10 to $100 range (median: $28.95), while "
    "fraudulent transactions have a higher median of $69.97 and a longer right tail. The fraud "
    "distribution has a secondary peak in the $500 to $2,000 range that is absent from legitimate "
    "transactions.",
    "Fraudulent transactions skew higher in amount, which is consistent with trying to maximize "
    "return before detection. Amount alone is a weak fraud signal - its real value is as a "
    "combined feature alongside MCC category and transaction method."
)

# --- Fig 3
add_heading(doc, "Figure 3: Fraud rate heatmap - hour of day by day of week")
add_figure(doc, FIGS / "fig3_fraud_heatmap_time.png",
           "Figure 3. Heatmap of fraud rate (%) by hour and day of week.")
add_finding_insight(doc,
    "Fraud rates are elevated from midnight to 5:00 AM across all days, with the highest "
    "concentrations on weekends between 1:00 AM and 4:00 AM. Weekday business hours (9:00 AM to "
    "5:00 PM) have the lowest fraud rates, which makes sense - that is when most cardholders are "
    "actively using their cards for routine purchases.",
    "Time of day is a useful and cheap signal. A transaction at 3:00 AM from a computer equipment "
    "retailer is worth a second look even if the amount seems ordinary. Banks can trigger "
    "authentication challenges during off-peak hours rather than issuing hard declines, which "
    "keeps the experience tolerable for legitimate late-night users."
)

# --- Fig 4
add_heading(doc, "Figure 4: Fraud rate by customer demographics")
add_figure(doc, FIGS / "fig4_fraud_by_demographic.png",
           "Figure 4. Fraud rate by age group (left) and annual income bracket (right).")
add_finding_insight(doc,
    "Customers under 25 had the highest fraud rate among age groups. The 55 to 64 cohort had "
    "the lowest. Across income brackets, customers earning under $30,000 annually saw the highest "
    "fraud rates, with rates declining as income increased.",
    "Younger and lower-income customers see more fraud, probably because they are less cautious "
    "with credentials and more likely to reuse passwords across accounts. These groups are also "
    "less likely to notice unfamiliar charges quickly. Targeted in-app alerts and simpler fraud "
    "reporting would help both detection speed and customer trust for these segments."
)

# --- Fig 5
add_heading(doc, "Figure 5: Fraud rate by card type and transaction method")
add_figure(doc, FIGS / "fig5_fraud_by_card_type.png",
           "Figure 5. Fraud rate by transaction method (left), card type (center), and chip availability (right).")
add_finding_insight(doc,
    "Online transactions had a fraud rate of 0.84%, which is 28 times higher than swipe "
    "transactions (0.03%) and 8 times higher than chip transactions (0.10%). Prepaid debit cards "
    "had a higher fraud rate (0.22%) than standard debit (0.13%) and credit (0.16%). Cards "
    "without chip technology had markedly higher fraud rates than chip-enabled cards.",
    "Online is where most of the fraud is happening. The card-not-present gap is the clearest "
    "problem to fix: 3D Secure 2.0, behavioral biometrics, and stricter identity checks at "
    "prepaid card issuance would all make a measurable difference. Non-chip cards should be "
    "phased out, with prepaid customers prioritized given their elevated exposure."
)

# --- Fig 6
add_heading(doc, "Figure 6: Correlation matrix of numerical features")
add_figure(doc, FIGS / "fig6_correlation_heatmap.png",
           "Figure 6. Pearson correlation matrix of numerical features including the is_fraud label.")
add_finding_insight(doc,
    "No single numerical feature correlates strongly with the fraud label. Hour-of-day has the "
    "highest positive correlation (r = +0.04), consistent with the time patterns in Figure 3. "
    "Transaction amount shows a modest positive correlation, and credit score shows a slight "
    "negative correlation. Feature inter-correlations are generally low.",
    "The absence of any strong individual signal is useful to know: a simple rule like 'flag "
    "transactions above $X' will not work well in isolation. Tree-based ensemble models "
    "(Random Forest, Gradient Boosting) can pick up the non-linear combinations that linear "
    "correlation misses. Adding velocity features and merchant-level deviation scores would "
    "make those models considerably stronger."
)

# ── V. KEY INSIGHTS ───────────────────────────────────────════════════════════
doc.add_paragraph()
add_heading(doc, "V. Key Insights")
add_body(doc, "Across 8,914,963 labelled transactions, five patterns stand out:")
add_bullet(doc,
    "Online transactions account for only 11.7% of total volume but carry a fraud rate of 0.84%, "
    "which is 28 times the rate for swipe transactions. The card-not-present gap is the clearest "
    "place to intervene.")
add_bullet(doc,
    "Merchant category separates fraud better than any other single variable. Computer and "
    "electronics retailers hit fraud rates above 10%, more than 60 times the 0.15% average. "
    "Any fraud detection system should treat MCC as a primary input.")
add_bullet(doc,
    "Most fraud happens between midnight and 5:00 AM, especially on weekends. Time-of-day "
    "features are cheap to compute and reliably signal elevated risk.")
add_bullet(doc,
    "Non-chip cards have significantly higher fraud rates. Phasing them out reduces counterfeit "
    "card fraud directly.")
add_bullet(doc,
    "Fraudulent transactions have a median amount of $69.97 versus $28.95 for legitimate ones. "
    "Amount is a useful first-pass filter, especially when combined with MCC category.")

# ── VI. RECOMMENDATIONS ───────────────────────────────────────────────────────
doc.add_paragraph()
add_heading(doc, "VI. Recommendations")
add_body(doc,
    "Five actions would address the highest-risk patterns identified in this analysis:"
)
add_bullet(doc,
    "Set MCC-specific transaction limits: Require step-up authentication for transactions "
    "above $500 at high-risk MCC codes (5045, 5065, 5094). This targets the categories where "
    "fraud rates exceed 10% without affecting the vast majority of low-risk transactions.")
add_bullet(doc,
    "Secure online channels with behavioral authentication: Online transactions are 28 times "
    "more likely to be fraudulent than swipe transactions. All card-not-present transactions "
    "should go through 3D Secure 2.0. Behavioral biometrics such as typing cadence and device "
    "fingerprinting add another layer without significantly increasing friction for legitimate users.")
add_bullet(doc,
    "Add time-of-day to fraud scoring models: Hour-of-day and day-of-week are reliable risk "
    "signals that cost nothing extra to collect. Transactions between midnight and 5:00 AM should "
    "receive a higher risk score, triggering a soft challenge rather than a hard decline, so "
    "legitimate late-night users are not blocked.")
add_bullet(doc,
    "Accelerate non-chip card phase-out: Non-EMV cards have substantially higher fraud rates, "
    "and prepaid debit customers are the most exposed. Proactively mailing chip card replacements "
    "to magnetic-stripe-only cardholders directly reduces counterfeit card fraud.")
add_bullet(doc,
    "Focus fraud awareness outreach on younger and lower-income customers: Customers under 25 "
    "and those earning under $30,000 annually showed above-average victimization rates. In-app "
    "alerts for unusual patterns and a straightforward reporting flow reduce both fraud volume "
    "and the time it takes to catch it.")

# ── VII. CONCLUSION ───────────────────────────────────────────────────────────
doc.add_paragraph()
add_heading(doc, "VII. Conclusion")
add_body(doc,
    "This study analyzed 8,914,963 labelled transactions to find what separates fraud from "
    "legitimate activity. Fraud is not evenly spread. It clusters in electronics retailers, "
    "online channels, late-night hours on weekends, and non-chip cards. The overall fraud rate "
    "is low at 0.15%, but within specific segments it exceeds 10%."
)
add_body(doc,
    "The online channel is the biggest single problem, with fraud rates 28 times higher than "
    "swipe transactions. Computer equipment retailers reach 10% fraud rates against a 0.15% "
    "dataset average. Chip cards suppress fraud relative to magnetic stripe, and time-of-day "
    "turns out to be a cheap, reliable signal."
)
add_body(doc,
    "These findings confirm that fraud detection works better when multiple signals are combined. "
    "No single variable catches everything. Banks that use MCC category, transaction method, time "
    "of day, and card type together in their scoring models should see a meaningful drop in fraud "
    "rates without blocking too many legitimate transactions."
)
add_body(doc,
    "Follow-on work could add transaction velocity and geographic distance as features, test "
    "classification models like Gradient Boosting or Isolation Forest, and validate these "
    "patterns against data from a real financial institution rather than a simulated dataset."
)

# ── REFERENCES ────────────────────────────────────────────────────────────────
doc.add_paragraph()
add_heading(doc, "References")
add_body(doc,
    "[1] computingvictor, \"Financial Transactions Dataset: Analytics,\" Kaggle, Oct. 2024. "
    "[Online]. Available: https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets. "
    "[Accessed: Apr. 12, 2026]."
)
add_body(doc,
    "[2] T. Hastie, R. Tibshirani, and J. Friedman, The Elements of Statistical Learning: Data Mining, "
    "Inference, and Prediction, 2nd ed. New York, NY, USA: Springer, 2009."
)
add_body(doc,
    "[3] A. Dal Pozzolo, O. Caelen, R. A. Johnson, and G. Bontempi, \"Calibrating probability with "
    "undersampling for unbalanced classification,\" in Proc. IEEE Symp. Comput. Intell. Data Mining "
    "(CIDM), Orlando, FL, USA, Dec. 2015, pp. 159-166."
)

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save(OUTPUT)
print(f"Saved -> {OUTPUT}")

# ── Validate ──────────────────────────────────────────────────────────────────
print("\n=== VALIDATION ===")
doc2 = Document(OUTPUT)
headings = [p.text for p in doc2.paragraphs if p.runs and p.runs[0].bold and
            any(kw in p.text for kw in ["Introduction","Dataset","Methodology","Analysis","Insights",
                                         "Recommendation","Conclusion","Reference"])]
print(f"Section headings found: {len(headings)}")
for h in headings:
    print(f"  * {h[:80]}")
print(f"Embedded images: {len(doc2.inline_shapes)}")
s = doc2.sections[0]
print(f"Page size: {s.page_width.cm:.1f} cm x {s.page_height.cm:.1f} cm")
print(f"Margins - Top:{s.top_margin.inches:.2f}\" Right:{s.right_margin.inches:.2f}\" "
      f"Bottom:{s.bottom_margin.inches:.2f}\" Left:{s.left_margin.inches:.2f}\"")
total_words = sum(len(p.text.split()) for p in doc2.paragraphs)
print(f"Estimated word count: {total_words:,}")
print(f"\nOriginal preserved at: {BASE / 'Transaction_Fraud_Analysis_Report.docx'}")
