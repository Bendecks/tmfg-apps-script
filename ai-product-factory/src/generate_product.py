import json, os, re, subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "first-100-side-hustle-test-kit"
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
Create a complete practical product called First $100 Side Hustle Test Kit.
Subtitle: A 30-Day Action System for Testing Real Online Income Ideas Without Fake Guru Advice.
Audience: beginners who want to test simple side hustles without hype, expensive tools, or unrealistic promises.
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
- Avoid survey sites as the core strategy. Focus on testing simple services, offers, outreach, content, and digital products.
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

title = "First $100 Side Hustle Test Kit"
subtitle = "A 30-Day Action System for Testing Real Online Income Ideas Without Fake Guru Advice"
pack = generate_pack()
days = pack["days"]

typst = f"""
#set page(width: 6in, height: 9in, margin: (x: 0.65in, y: 0.72in))
#set text(font: "Liberation Serif", size: 10.5pt)
#set heading(numbering: none)
#set par(justify: true, leading: 0.62em)

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
  #text(size: 23pt, weight: "bold")[{esc(title)}]
  #v(8pt)
  #text(size: 11pt, fill: rgb("6B6258"))[{esc(subtitle)}]
  #v(32pt)
  #box("What this actually helps you do", [{esc(pack.get('promise', 'Test simple side hustle ideas through real actions, feedback, and small experiments without pretending income is guaranteed.'))}])
]

#pagebreak()

= How to Use This Test Kit

This is not a motivational side hustle book. It is a practical testing system. The goal is to stop collecting ideas and start running small, realistic experiments that create feedback.

== Who this is for
{list_items(pack.get('who_it_is_for', []))}

== Rules
{list_items(pack.get('rules', []))}

#pagebreak()

= 30-Day Action Plan

Each day gives you one objective, one specific action, one example, one expected result, and one reflection question. Do the action first. Judge the result after.

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

sales_description = """Most people do not need another side hustle idea.

They need a way to test what actually works.

First $100 Side Hustle Test Kit is a practical 30-day action system for beginners who want to explore simple online income ideas without fake guru promises, expensive tools, or endless planning.

Inside, you get daily actions, simple idea tests, outreach prompts, reflection questions, and a built-in tracker to help you move from thinking to testing.

No fake promises. No expensive tools. No build-a-brand-first nonsense.

Just action, feedback, and progress.
"""

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text(sales_description, encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle test kit, make money online beginner, first online income, realistic side hustle, online income for beginners, action plan side hustle, 30 day challenge money", encoding="utf-8")
(PRODUCT_DIR / "cover-prompt.txt").write_text("""Create a premium 6x9 book cover.

Title: First $100 Side Hustle Test Kit
Subtitle: A 30-Day Action System for Testing Real Online Income Ideas

Style:
- Clean, modern, minimal
- Strong typography, readable as an Amazon thumbnail
- Warm neutral tones
- Subtle progress or money motif
- No people
- No fake luxury visuals
- Credible and practical, not make-money-online spam
""", encoding="utf-8")
(PRODUCT_DIR / "upload-checklist.txt").write_text("1. Open book.pdf and inspect 5 random pages.\n2. Check title/subtitle.\n3. Generate cover from cover-prompt.txt.\n4. Use description.txt and keywords.txt for listing.\n5. Do not publish before checking no income guarantees are stated.\n", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine": "typst_gemini_sales_positioned_v5",
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
