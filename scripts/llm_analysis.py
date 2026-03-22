import re
from pathlib import Path
import ollama

def load_md(path: Path):
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\n{3,}", "\n\n", text.strip())

def load_prompt_blocks(path: Path):
    text = path.read_text(encoding="utf-8")
    blocks = {}
    matches = re.findall(r"=+\s*(.*?)\s*=+\n(.*?)(?=\n=+|\Z)", text, re.S)
    for name, content in matches:
        blocks[name.strip()] = content.strip()
    return blocks

def render(template: str, vars: dict):
    for k, v in vars.items():
        template = template.replace(f"{{{{{k}}}}}", v)
    return template

def generate(prompt, model):
    return ollama.generate(
        model=model,
        prompt=prompt,
        options={"temperature": 0.0}
    )["response"].strip()

def run_llm(md_paths: dict, prompt_file: Path, output_path: Path, model: str):
    blocks = load_prompt_blocks(prompt_file)

    summary = generate(
        render(blocks["SUMMARY_PROMPT"], {"SUMMARY_MD": load_md(md_paths["Summary"])}),
        model
    )

    emi = generate(
        render(
            blocks["EMI_PROMPT"],
            {
                "EMI_TXN_MD": load_md(md_paths.get("Loan_EMI_Transactions")),
                "EMI_PROVIDERS_MD": load_md(md_paths.get("Loan_Providers_Summary"))
            }
        ),
        model
    )

    final = generate(
        render(
            blocks["FINAL_PROMPT"],
            {"SUMMARY_HTML": summary, "EMI_HTML": emi}
        ),
        model
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final, encoding="utf-8")

    return output_path