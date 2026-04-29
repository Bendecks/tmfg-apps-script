import os, json, subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "first-100-online-playbook"
PRODUCT_DIR = DIST / slug
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

# CONTENT
title = "First $100 Online Playbook"
subtitle = "A practical 30-day system for testing simple side hustles"

sections = [
    "Why most people never make their first dollar online",
    "The rule: action over thinking",
    "How to pick one idea fast",
    "How to test without overbuilding",
    "How to get real feedback"
]

# BUILD TYPST FILE
typst = f"""
#set page(margin: 2cm)
#set text(font: "Liberation Serif", size: 11pt)

= {title}
{subtitle}

#pagebreak()

== Introduction

This playbook is designed to get you from zero to your first $100 online.

#pagebreak()
"""

for s in sections:
    typst += f"\n== {s}\n\nTake one real action here.\n\n#pagebreak()\n"

for day in range(1,31):
    typst += f"\n== Day {day}\n\nAction: Do one thing that moves you closer to earning.\n\nResult:\n\nNext step:\n\n#pagebreak()\n"

source_file = PRODUCT_DIR / "book.typ"
source_file.write_text(typst, encoding="utf-8")

pdf_file = PRODUCT_DIR / "book.pdf"
subprocess.run(["typst", "compile", str(source_file), str(pdf_file)], check=True)

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle)
(PRODUCT_DIR / "description.txt").write_text("A no-nonsense system to get your first online income.")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle, online income, first money")

print("PRODUCT BUILT:", pdf_file)
