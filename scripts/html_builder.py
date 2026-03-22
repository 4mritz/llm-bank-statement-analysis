from bs4 import BeautifulSoup
from pathlib import Path

def extract(path: Path):
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    return soup.body.decode_contents() if soup.body else html

def build(pivot_html: Path, llm_html: Path, template: Path, output: Path):
    pivot = extract(pivot_html)
    llm = extract(llm_html)

    base = template.read_text(encoding="utf-8")
    final = base.replace("{{PIVOT}}", pivot).replace("{{LLM}}", llm)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final, encoding="utf-8")

    return output