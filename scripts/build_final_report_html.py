from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parents[1]

PIVOT_HTML = BASE_DIR / "outputs/pivot_table/05_canara_final_report.html"
ANALYSIS_HTML = BASE_DIR / "outputs/from_llm/final_analysis.html"
OUTPUT_HTML = BASE_DIR / "wrapper/final.html"


def extract_body(html_path: Path) -> str:
    html_text = html_path.read_text(encoding="utf-8").strip()
    soup = BeautifulSoup(html_text, "html.parser")

    # Case 1: Full HTML document
    if soup.body:
        return soup.body.decode_contents().strip()

    # Case 2: HTML fragment (no <body>)
    return html_text



def build_final_html(pivot_body: str, analysis_body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Bank Statement Analysis</title>

<style>
body {{
  font-family: Arial;
  margin: 40px;
}}

table {{
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 25px;
}}

th, td {{
  border: 1px solid #ccc;
  padding: 8px;
}}

th {{
  background-color: #2f8fa3;
  color: white;
}}

.page-break {{
  page-break-before: always;
}}
</style>
</head>

<body>

<!-- ===================== -->
<!-- PIVOT TABLE SECTION -->
<!-- ===================== -->
{pivot_body}

<div class="page-break"></div>

<!-- ===================== -->
<!-- LLM ANALYSIS SECTION -->
<!-- ===================== -->
{analysis_body}

</body>
</html>
"""


def main():
    pivot_body = extract_body(PIVOT_HTML)
    analysis_body = extract_body(ANALYSIS_HTML)

    final_html = build_final_html(pivot_body, analysis_body)
    OUTPUT_HTML.write_text(final_html, encoding="utf-8")

    print(f"Final report generated → {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
