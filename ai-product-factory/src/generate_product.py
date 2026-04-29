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
        "\\": "\\\\", "$": "\\$", "#": "\\#", "*": "\\*", "_": "\\_",
        "`": "\\`", "[": "\\[", "]": "\\]", "@": "\\@"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def load_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

def generate_pack():
    prompt = """
Create a complete practical product called First $100 Online Playbook.
Audience: beginners who want to test simple side hustles without fake guru advice.
Return ONLY valid JSON in this exact shape:
{
  "promise": "one sentence, no guarantees",
  "who_it_is_for": ["item", "item", "item"],
  "rules": ["item", "item", "item", "item"],
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
- No markdown formatting, no bullet symbols, no asterisks.
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
    if len(data.get("days", [])) != 30:
        raise RuntimeError(f"Expected 30 days from Gemini, got {len(data.get('days', []))}")
    return data

def list_items(items):
    return "\n".join([f"- {esc(x)}" for x in items])

title = "First $100 Online Playbook"
subtitle = "A practical 30-day system for testing simple side hustles"
pack = generate_pack()
days = pack["days"]

typst = f"""
#set page(width: 6in, height: 9in, margin: (x: 0.65in, y: 0.72in))
#set text(font: "Liberation Serif", size: 10.5pt, leading: 0.62em)
#set heading(numbering: none)
#set par(justify: true)

#let rule() = line(length: 100%, stroke: 0.5pt + rgb("D7D2CA"))
#let label(t) = text(size: 8pt, weight: "bold", fill: rgb("6B6258"), upper(t))
#let box(title, body) = block(
  width: 100%,
  inset: 10pt,
  radius: 6pt,
  stroke: 0.7pt + rgb("D7D2CA"),
  fill: rgb("FBFAF7"),
  [#label(title)\n#v(5pt)#body]
)

#align(center)[
  #v(45pt)
  #text(size: 25pt, weight: "bold")[{esc(title)}]
  #v(8pt)
  #text(size: 12pt, fill: rgb("6B6258"))[{esc(subtitle)}]
  #v(32pt)
  #box("Core promise", [{esc(pack.get('promise', 'A practical system for testing simple side hustle ideas without overbuilding.'))}])
]

#pagebreak()

= How to Use This Playbook

This playbook is designed to help you test simple online income ideas through practical daily action. It does not promise guaranteed income. It gives you a structure for learning, testing, and improving quickly.

== Who this is for
{list_items(pack.get('who_it_is_for', []))}

== Rules
{list_items(pack.get('rules', []))}

#pagebreak()

= 30-Day Execution Plan

Each day has one objective, one specific action, one example, one expected result, and one reflection question. Do the action first. Fill the notes after.

#pagebreak()
"""

for item in days:
    day = int(item.get("day"))
    day_title = esc(item.get("title", f"Day {day}"))
    typst += f"\n= Day {day}: {day_title}\n\n"
    typst += f"#box(\"Objective\", [{esc(item.get('objective', ''))}])\n\n"
    typst += f"#box(\"Specific action\", [{esc(item.get('specific_action', ''))}])\n\n"
    typst += f"#box(\"Example\", [{esc(item.get('example', ''))}])\n\n"
    typst += f"#box(\"Expected result\", [{esc(item.get('expected_result', ''))}])\n\n"
    typst += f"#box(\"Reflection\", [{esc(item.get('reflection_question', ''))}])\n\n"
    typst += "#pagebreak()\n"

typst += """
= Outreach Tracker

#table(
  columns: (1fr, 2fr, 2fr, 1.5fr),
  inset: 7pt,
  stroke: 0.5pt + rgb("D7D2CA"),
  [Date], [Person / platform], [Message sent], [Next step],
)

#pagebreak()

= Next 30 Days

#box("Double down", [What action created the clearest signal?])
#box("Cut", [What felt busy but did not create useful feedback?])
#box("Next offer", [What will you test next?])
"""

source_file = PRODUCT_DIR / "book.typ"
source_file.write_text(typst, encoding="utf-8")

pdf_file = PRODUCT_DIR / "book.pdf"
subprocess.run(["typst", "compile", str(source_file), str(pdf_file)], check=True)

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text("A practical 30-day playbook for testing simple side hustle ideas, taking real action, and learning what could lead to a first online payment.", encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle, online income, make money online, first online income, beginner side hustle, action playbook", encoding="utf-8")
(PRODUCT_DIR / "cover-prompt.txt").write_text("Create a clean premium 6x9 book cover for 'First $100 Online Playbook'. Minimal modern business style, strong readable title, warm neutral background, subtle money/progress motif, no fake luxury, no people, high readability as Amazon thumbnail.", encoding="utf-8")
(PRODUCT_DIR / "upload-checklist.txt").write_text("1. Open book.pdf and inspect 5 random pages.\n2. Check title/subtitle.\n3. Generate cover from cover-prompt.txt.\n4. Use description.txt and keywords.txt for listing.\n5. Do not publish before checking no income guarantees are stated.\n", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine": "typst_gemini_sales_layout_v4",
    "product": title,
    "gemini_used": True,
    "model": MODEL_NAME,
    "days_generated": len(days),
    "fallback_allowed": False,
    "typst_sanitized": True,
    "layout": "6x9_sales_playbook"
}, indent=2), encoding="utf-8")

print("AI PRODUCT BUILT:", pdf_file)
print("Gemini model:", MODEL_NAME)
