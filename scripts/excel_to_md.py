import pandas as pd
from pathlib import Path

def convert_excel_to_md(input_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    xls = pd.ExcelFile(input_path)
    md_paths = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        md_path = output_dir / f"{sheet.lower()}.md"
        df.to_markdown(md_path, index=False)
        md_paths[sheet] = md_path

    return md_paths