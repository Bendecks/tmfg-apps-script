import json, subprocess, os
from pathlib import Path
import google.generativeai as genai

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "first-100-online-playbook"
PRODUCT_DIR = DIST / slug
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

# Gemini setup
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def esc(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace("$", "\\$").replace("#", "\\#")

def generate_day(day):
    prompt = f"Write a practical daily step for earning money online. Day {day}. Include action, example, and expected result."
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except:
        return "Take one real action that could lead to income."

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

This playbook is designed to get you from zero to your first \$100 online.

#pagebreak()
"""

for day in range(1,31):
    content = esc(generate_day(day))
    typst += f"\n== Day {day}\n\n{content}\n\n#pagebreak()\n"

source_file = PRODUCT_DIR / "book.typ"
source_file.write_text(typst, encoding="utf-8")

pdf_file = PRODUCT_DIR / "book.pdf"
subprocess.run(["typst", "compile", str(source_file), str(pdf_file)], check=True)

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text("A practical system to earn your first money online.", encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle, online income, make money", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({"engine":"typst_gemini_v1","product":title}, indent=2), encoding="utf-8")

print("AI PRODUCT BUILT:", pdf_file)
