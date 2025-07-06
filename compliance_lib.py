import requests, re, bs4, json, os
from functools import lru_cache
from datetime import datetime, timedelta

# ---- 1. simple web scraper --------------------------------------------------
HEADERS = {"User-Agent": "anupalankarta/1.0"}

@lru_cache(maxsize=128)
def fetch_text(url: str, ttl_hours: int = 12) -> str:
    """Download & cache plain-text from a URL for `ttl_hours`."""
    cache_path = f".cache_{re.sub(r'[^A-Za-z0-9]', '_', url)}.txt"
    if os.path.exists(cache_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.utcnow() - mtime < timedelta(hours=ttl_hours):
            return open(cache_path, encoding="utf-8").read()
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = bs4.BeautifulSoup(r.text, "html.parser")
    text = " ".join(t.get_text(" ", strip=True) for t in soup.find_all(["p", "li"]))
    open(cache_path, "w", encoding="utf-8").write(text)
    return text

# ---- 2. minimal rule base ---------------------------------------------------
RULES = {
    "GDPR": [
        ("Lawful basis documented", r"lawful\s+basis"),
        ("Data-subject rights process", r"right\s+to\s+access|erasure"),
        ("72-hour breach notice plan", r"72\s*hour"),
    ],
    "EU_AI_Act": [
        ("High-risk AI DPIA", r"risk\s+assessment"),
        ("Training data governance", r"data\s+governance"),
    ],
    "ISO_27001": [
        ("Annex A control list", r"annex\s*a"),
        ("Statement of Applicability", r"statement\s+of\s+applicability"),
    ],
    # extend as needed
}

def run_check(text: str) -> dict:
    """Return dict{framework: list[(item, pass_bool)]}."""
    results = {}
    for fw, tests in RULES.items():
        framework_res = []
        for label, pattern in tests:
            framework_res.append((label, bool(re.search(pattern, text, re.I))))
        results[fw] = framework_res
    return results

# ---- 3. Hugging Face model wrapper -----------------------------------------
from huggingface_hub import InferenceClient

HF_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

def generate_report(prompt: str, max_tokens=600) -> str:
    client = InferenceClient(model=HF_MODEL, token=os.environ.get("HF_TOKEN"))
    return client.text_generation(prompt, max_new_tokens=max_tokens,
                                  temperature=0.4, top_p=0.9)
