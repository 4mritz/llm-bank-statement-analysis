import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "data" / "excel" / "Canara.xlsx"
MD_DIR = BASE_DIR / "data" / "markdown"

MD_DIR.mkdir(parents=True, exist_ok=True)

# Sheet name → output md file
SHEETS = {
    "Summary": "canara_summary.md",
    "Loan_EMI_Transactions": "canara_loan_emi_transactions.md",
    "Loan_Providers_Summary": "canara_loan_providers_summary.md",
}

def df_to_markdown(df):
    return df.to_markdown(index=False)

def main():
    for sheet, md_file in SHEETS.items():
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
        md_content = df_to_markdown(df)

        md_path = MD_DIR / md_file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"Created {md_file}")

if __name__ == "__main__":
    main()
