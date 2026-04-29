import json, os, re, subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "first-100-online-playbook"
PRODUCT_DIR = DIST / slug
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "gemini-2.5-flash"
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing. Add it as a GitHub Actions repository secret.")

client = genai.Client(api_key=api_key)

def esc(text: str) -> str:
    text = str(text)
    replacements = {
        "\\": "\\\\",
        "$": "\\$",
        "#": "\\#",
        "*": "\\*",
        "_": "\\_",
        "`": "\\`",
        "[": "\\[",
        "]": "\\]",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def load_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

def generate_days():
    prompt = """
Create a complete 30-day practical playbook called First $100 Online Playbook.
Audience: beginners who want to test simple side hustles without fake guru advice.

Return ONLY valid JSON in this exact shape:
{
  "days": [
    {
      "day": 1,
      "title": "short title",
      "objective": "plain text, no markdown",
      "specific_action": "plain text, no markdown",
      "example": "plain text, no markdown",
      "expected_result": "plain text, no markdown",
      "reflection_question": "plain text, no markdown"
    }
  ]
}

Rules:
- Exactly 30 days.
- No markdown formatting.
- No bullet symbols.
- No asterisks.
- Do not promise guaranteed income.
- Make every day different and concrete.
- Keep each field concise but useful.
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    data = load_json(response.text)
    days = data.get("days", [])
    if len(days) != 30:
        raise RuntimeError(f"Expected 30 days from Gemini, got {len(days)}")
    return days

title = "First $100 Online Playbook"
subtitle = "A practical 30-day system for testing simple side hustles"
days = generate_days()

typst = f"""
#set page(margin: 2cm)
#set text(font: "Liberation Serif", size: 11pt)

= {esc(title)}
{esc(subtitle)}

#pagebreak()

== Introduction

This playbook is designed to help you test simple online income ideas through practical daily action. It does not promise guaranteed income. It gives you a structure for learning, testing, and improving quickly.

#pagebreak()
"""

for item in days:
    day = int(item.get("day"))
    day_title = esc(item.get("title", f"Day {day}"))
    typst += f"\n== Day {day}: {day_title}\n\n"
    typst += f"Objective: {esc(item.get('objective', ''))}\n\n"
    typst += f"Specific action: {esc(item.get('specific_action', ''))}\n\n"
    typst += f"Example: {esc(item.get('example', ''))}\n\n"
    typst += f"Expected result: {esc(item.get('expected_result', ''))}\n\n"
    typst += f"Reflection question: {esc(item.get('reflection_question', ''))}\n\n"
    typst += "#pagebreak()\n"

source_file = PRODUCT_DIR / "book.typ"
source_file.write_text(typst, encoding="utf-8")

pdf_file = PRODUCT_DIR / "book.pdf"
subprocess.run(["typst", "compile", str(source_file), str(pdf_file)], check=True)

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text("A practical 30-day playbook for testing simple side hustle ideas, taking real action, and learning what could lead to a first online payment.", encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle, online income, make money online, first online income, beginner side hustle, action playbook", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine": "typst_gemini_json_v3",
    "product": title,
    "gemini_used": True,
    "model": MODEL_NAME,
    "days_generated": len(days),
    "fallback_allowed": False,
    "typst_sanitized": True
}, indent=2), encoding="utf-8")

print("AI PRODUCT BUILT:", pdf_file)
print("Gemini model:", MODEL_NAME)
