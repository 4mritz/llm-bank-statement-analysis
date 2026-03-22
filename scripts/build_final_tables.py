import pandas as pd
from pathlib import Path

from sympy import re

# =========================
# CONFIG
# =========================
MIN_BALANCE_THRESHOLD = 1000

BASE_DIR = Path(__file__).resolve().parent.parent
MD_DIR = BASE_DIR / "data" / "markdown"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(exist_ok=True)

SUMMARY_MD = MD_DIR / "canara_summary.md"
EMI_MD = MD_DIR / "canara_loan_providers_summary.md"


# =========================
# UTILITIES
# =========================
def safe(v):
    if v is None:
        return "Not mentioned"
    if isinstance(v, float) and pd.isna(v):
        return "Not mentioned"
    return v


def clean_num(x):
    if pd.isna(x):
        return None
    try:
        return float(str(x).replace(",", "").strip())
    except Exception:
        return None


# =========================
# MARKDOWN TABLE PARSER
# =========================
def read_md_table(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if all(set(p) <= {"-"} for p in parts):
                continue
            rows.append(parts)

    if len(rows) < 2:
        raise ValueError(f"No valid table found in {path.name}")

    return pd.DataFrame(rows[1:], columns=rows[0])


# =========================
# SUMMARY PROCESSING
# =========================
def process_summary():
    df = read_md_table(SUMMARY_MD)

    desc_idx = df.index[df.iloc[:, 0] == "Description"][0]

    banking_df = df.iloc[:desc_idx]
    metrics_df = df.iloc[desc_idx + 1:].reset_index(drop=True)
    metrics_df.columns = df.iloc[desc_idx]

    # ---- Banking Information ----
    banking_info = {}
    for _, row in banking_df.iterrows():
        k = row.iloc[0]
        v = row.iloc[1]

        if pd.isna(k) or pd.isna(v):
            continue

        k = str(k).strip()
        v = str(v).strip()

        if not k or not v:
            continue
        if k.startswith(":") or v.startswith(":"):
            continue
        if k.lower() == "nan" or v.lower() == "nan":
            continue
        if "Unnamed" in k:
            continue

        banking_info[k] = v

    # ---- Metrics ----
    month_cols = [c for c in metrics_df.columns if str(c).startswith("202")]
    months_analysed = len(month_cols)

    def row(name):
        r = metrics_df[metrics_df["Description"] == name]
        return None if r.empty else r.iloc[0]

    closing = row("Closing Balance")
    penalties = row("Penalty Charges")

    salary = clean_num(row("Salary Income")["Overall"]) if row("Salary Income") is not None else None
    total_debit = clean_num(row("Total Debit")["Overall"]) if row("Total Debit") is not None else None

    summary = {
        "Loan Repayment to Annual Income (%)": None,
        "EMI to Monthly Income (%)": None,
        "Net Cashflow (Monthly Average)": clean_num(row("Net Cashflow")["Average"]),
        "Expense to Income (%)": round((total_debit / salary) * 100, 2) if salary and salary != 0 else None,
        "Average Balance": clean_num(row("Monthly Average Balance")["Average"]),
        "Minimum Balance": clean_num(row("Min Balance")["Overall"]),
        "Maximum Balance": clean_num(row("Max Balance")["Overall"]),
        "Monthly Balance Volatility (%)": clean_num(row("Monthly Balance Change %")["Average"]),
        "Statement Period (Months)": months_analysed,
        "% Months with Negative Closing Balance": round(
            (closing[month_cols].astype(float) < 0).sum() / months_analysed * 100, 2
        ) if closing is not None else None,
        "% Months with Low Closing Balance": round(
            (closing[month_cols].astype(float) < MIN_BALANCE_THRESHOLD).sum()
            / months_analysed * 100, 2
        ) if closing is not None else None,
        "Penalty Occurrence (Months) and Total Amount": (
            f"{(penalties[month_cols].astype(float) > 0).sum()} months, ₹{clean_num(penalties['Overall'])}"
            if penalties is not None else None
        ),
    }

    return banking_info, summary, salary


# =========================
# EMI PROCESSING
# =========================
def process_emi(salary):
    df = read_md_table(EMI_MD)

    df["Total EMI Paid"] = df["Total EMI Paid"].apply(clean_num)
    df["Total EMI Amount"] = df["Total EMI Amount"].apply(clean_num)

    # distinct EMI months
    emi_months = set()
    import re
    
    month_pattern = re.compile(r"^\d{4}-\d{2}$")

    for val in df["Months Paid"]:
        if pd.isna(val):
            continue
        for m in str(val).split(","):
            m = m.strip()
            if month_pattern.match(m):
                emi_months.add(m)

    months_paid = len(emi_months)

    # condensed payment period
    if emi_months:
        start_month = min(emi_months)
        end_month = max(emi_months)
        payment_period = f"{start_month} to {end_month}"
    else:
        payment_period = None

    total_emi_amount = df["Total EMI Amount"].sum()
    total_emi_paid = df["Total EMI Paid"].sum()

    emi = {
        "Total EMI Transactions": total_emi_paid,
        "Total EMI Amount": total_emi_amount,
        "Distinct EMI Months Paid": months_paid,
        "Missed EMI Months": None,
        "EMI Payment Period": payment_period,
    }

    emi_to_income = round((total_emi_amount / salary) * 100, 2) if salary and salary != 0 else None
    loan_to_income = round((total_emi_amount / (salary * 12)) * 100, 2) if salary and salary != 0 else None

    return emi, emi_to_income, loan_to_income


# =========================
# HTML RENDERING
# =========================
def table_html(title, rows):
    body = "\n".join(f"<tr><td>{k}</td><td>{safe(v)}</td></tr>" for k, v in rows)
    return f"""
<h3>{title}</h3>
<table>
<tr><th>Metric</th><th>Value</th></tr>
{body}
</table>
"""


def wrap_html(content):
    return f"""
<html>
<head>
<style>
body {{ font-family: Arial; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 25px; }}
th, td {{ border: 1px solid #ccc; padding: 8px; }}
th {{ background-color: #2f8fa3; color: white; }}
</style>
</head>
<body>
{content}
</body>
</html>
"""


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    banking, summary, salary = process_summary()
    emi, emi_to_income, loan_to_income = process_emi(salary)

    summary["EMI to Monthly Income (%)"] = emi_to_income
    summary["Loan Repayment to Annual Income (%)"] = loan_to_income

    SUMMARY_ORDER = [
        "Loan Repayment to Annual Income (%)",
        "EMI to Monthly Income (%)",
        "Net Cashflow (Monthly Average)",
        "Expense to Income (%)",
        "Average Balance",
        "Minimum Balance",
        "Maximum Balance",
        "Monthly Balance Volatility (%)",
        "Statement Period (Months)",
        "% Months with Negative Closing Balance",
        "% Months with Low Closing Balance",
        "Penalty Occurrence (Months) and Total Amount",
    ]

    EMI_ORDER = [
        "Total EMI Transactions",
        "Total EMI Amount",
        "Distinct EMI Months Paid",
        "Missed EMI Months",
        "EMI Payment Period",
    ]

    html = ""
    html += table_html("Banking Information", banking.items())
    html += table_html("Summary Analysis", [(k, summary.get(k)) for k in SUMMARY_ORDER])
    html += table_html("EMI Analysis", [(k, emi.get(k)) for k in EMI_ORDER])

    (OUT_DIR / "05_canara_final_report.html").write_text(wrap_html(html), encoding="utf-8")

    print("✔ Final HTML report generated successfully")
