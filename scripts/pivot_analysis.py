import pandas as pd
import re
from pathlib import Path

def read_md_table(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if all(set(p) <= {"-"} for p in parts):
            continue
        rows.append(parts)
    return pd.DataFrame(rows[1:], columns=rows[0])

def clean_num(x):
    try:
        return float(str(x).replace(",", ""))
    except:
        return None

def process(md_summary, md_emi):
    df = read_md_table(md_summary)
    salary = clean_num(df.iloc[-1].iloc[-1])

    emi_df = read_md_table(md_emi)
    emi_df["Total EMI Amount"] = emi_df["Total EMI Amount"].apply(clean_num)

    total_emi = emi_df["Total EMI Amount"].sum()
    emi_ratio = (total_emi / salary) * 100 if salary else None

    return {
        "salary": salary,
        "total_emi": total_emi,
        "emi_to_income": emi_ratio
    }

def build_html(data):
    return f"""
    <h2>Pivot Analysis</h2>
    <table>
    <tr><td>Salary</td><td>{data['salary']}</td></tr>
    <tr><td>Total EMI</td><td>{data['total_emi']}</td></tr>
    <tr><td>EMI %</td><td>{data['emi_to_income']}</td></tr>
    </table>
    """

def run_pivot(md_paths, output_path):
    data = process(
        md_paths["Summary"],
        md_paths["Loan_Providers_Summary"]
    )

    html = build_html(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    return output_path