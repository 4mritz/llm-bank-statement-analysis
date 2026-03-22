import argparse
from pathlib import Path

from src.excel_to_md import convert_excel_to_md
from src.llm_analysis import run_llm
from src.pivot_analysis import run_pivot
from src.html_builder import build

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="llama3.1:8b-instruct-q4_K_M")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent

    md_dir = base / "data" / "markdown"
    llm_out = base / "outputs" / "from_llm" / "analysis.html"
    pivot_out = base / "outputs" / "pivot_table" / "pivot.html"
    final_out = base / "outputs" / "final_report.html"

    md_paths = convert_excel_to_md(Path(args.input), md_dir)

    llm_html = run_llm(
        md_paths,
        base / "prompts" / "financial_analysis_prompts.txt",
        llm_out,
        args.model
    )

    pivot_html = run_pivot(md_paths, pivot_out)

    build(
        pivot_html,
        llm_html,
        base / "templates" / "base.html",
        final_out
    )

    print(final_out)

if __name__ == "__main__":
    main()