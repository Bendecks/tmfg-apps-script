import json, subprocess, os
from pathlib import Path
import google.generativeai as genai

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

# Gemini setup
genai.configure(api_key=api_key)
model = genai.GenerativeModel(MODEL_NAME)

def esc(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("$", "\\$").replace("#", "\\#")

def generate_day(day):
    prompt = f"""
Write Day {day} of a practical playbook called First $100 Online Playbook.
Audience: beginners who want to test simple side hustles without fake guru advice.

Return useful content with these sections:
- Today's objective
- Specific action
- Example
- Expected result
- Reflection question

Rules:
- Be concrete, not motivational fluff.
- Do not promise guaranteed income.
- Keep it concise enough to fit on 1-2 pages.
"""
    try:
        res = model.generate_content(prompt)
        text = (res.text or "").strip()
        if len(text) < 80:
            raise RuntimeError(f"Gemini returned too little text on day {day}: {repr(text)}")
        return text
    except Exception as e:
        raise RuntimeError(f"Gemini generation failed on day {day} using {MODEL_NAME}: {e}")

# CONTENT
title = "First $100 Online Playbook"
subtitle = "A practical 30-day system for testing simple side hustles"

# BUILD TYPST FILE
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

for day in range(1, 31):
    content = esc(generate_day(day))
    typst += f"\n== Day {day}\n\n{content}\n\n#pagebreak()\n"

source_file = PRODUCT_DIR / "book.typ"
source_file.write_text(typst, encoding="utf-8")

pdf_file = PRODUCT_DIR / "book.pdf"
subprocess.run(["typst", "compile", str(source_file), str(pdf_file)], check=True)

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text("A practical 30-day playbook for testing simple side hustle ideas, taking real action, and learning what could lead to a first online payment.", encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle, online income, make money online, first online income, beginner side hustle, action playbook", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine": "typst_gemini_v2",
    "product": title,
    "gemini_used": True,
    "model": MODEL_NAME,
    "days_generated": 30,
    "fallback_allowed": False
}, indent=2), encoding="utf-8")

print("AI PRODUCT BUILT:", pdf_file)
print("Gemini model:", MODEL_NAME)
