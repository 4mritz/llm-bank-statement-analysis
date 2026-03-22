import time
from pathlib import Path
import re
import ollama

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MD_DIR = BASE_DIR / "data" / "markdown"
OUTPUT_DIR = BASE_DIR / "from_llm"
OUTPUT_DIR.mkdir(exist_ok=True)

PROMPT_FILE_PATH = BASE_DIR / "prompts" / "prompt4.txt"

SUMMARY_MD_PATH = MD_DIR / "canara_summary.md"
EMI_TXN_MD_PATH = MD_DIR / "canara_loan_emi_transactions.md"
EMI_PROVIDERS_MD_PATH = MD_DIR / "canara_loan_providers_summary.md"

FINAL_OUTPUT_PATH = OUTPUT_DIR / "corrected_final_analysis.html"

# ============================================================
# LOAD + SANITIZE MARKDOWN
# ============================================================

def load_md(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    return text


SUMMARY_MD = load_md(SUMMARY_MD_PATH)
EMI_TXN_MD = load_md(EMI_TXN_MD_PATH)
EMI_PROVIDERS_MD = load_md(EMI_PROVIDERS_MD_PATH)

# ============================================================
# LOAD PROMPTS FROM FILE
# ============================================================

def load_prompt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_prompt_block(full_text: str, name: str) -> str:
    pattern = rf"==================== {name} ====================\n(.*?)(?=\n====================|\Z)"
    match = re.search(pattern, full_text, re.S)
    if not match:
        raise RuntimeError(f"Prompt block '{name}' not found in prompt file")
    return match.group(1).strip()


def render_prompt(template: str, variables: dict) -> str:
    for k, v in variables.items():
        template = template.replace(f"{{{{{k}}}}}", v)
    return template


ALL_PROMPTS = load_prompt_file(PROMPT_FILE_PATH)

SUMMARY_PROMPT_TEMPLATE = extract_prompt_block(ALL_PROMPTS, "SUMMARY_PROMPT")
EMI_PROMPT_TEMPLATE = extract_prompt_block(ALL_PROMPTS, "EMI_PROMPT")
FINAL_PROMPT_TEMPLATE = extract_prompt_block(ALL_PROMPTS, "FINAL_PROMPT")

# ============================================================
# OLLAMA CONFIG
# ============================================================

MODEL = "llama3.1:8b-instruct-q4_K_M"

OLLAMA_OPTS = {
    "temperature": 0.0,
    "top_p": 1.0,
    "repeat_penalty": 1.0,
    "num_ctx": 4096,
    "seed": 42
}

# ============================================================
# PIPELINE (VALIDATION DISABLED)
# ============================================================

def run():

    start = time.time()

    summary_prompt = render_prompt(
        SUMMARY_PROMPT_TEMPLATE,
        {"SUMMARY_MD": SUMMARY_MD}
    )

    summary_html = ollama.generate(
        model=MODEL,
        prompt=summary_prompt,
        options=OLLAMA_OPTS
    )["response"].strip()

    emi_prompt = render_prompt(
        EMI_PROMPT_TEMPLATE,
        {
            "EMI_TXN_MD": EMI_TXN_MD,
            "EMI_PROVIDERS_MD": EMI_PROVIDERS_MD
        }
    )

    emi_html = ollama.generate(
        model=MODEL,
        prompt=emi_prompt,
        options=OLLAMA_OPTS
    )["response"].strip()

    final_prompt = render_prompt(
        FINAL_PROMPT_TEMPLATE,
        {
            "SUMMARY_HTML": summary_html,
            "EMI_HTML": emi_html
        }
    )

    final_html = ollama.generate(
        model=MODEL,
        prompt=final_prompt,
        options=OLLAMA_OPTS
    )["response"].strip()

    FINAL_OUTPUT_PATH.write_text(final_html, encoding="utf-8")

    print(f"Final analysis written to {FINAL_OUTPUT_PATH}")
    print(f"Completed in {round(time.time() - start, 2)} seconds")


# ============================================================
if __name__ == "__main__":
    run()
