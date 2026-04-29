import json, os, re, subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "signal-test-method-side-hustle-playbook"
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
Create a complete KDP workbook using a named method called The Signal Test Method.
Product title: The Signal Test Method
Subtitle: A 30-Day Side Hustle Playbook for Testing Real Demand Before You Waste Time
Audience: beginners who want to test simple side hustle ideas without fake guru advice.

The method has 5 steps:
1. Problem Signal: find a real pain point people mention.
2. Buyer Signal: identify who might pay to solve it.
3. Offer Signal: write one tiny paid offer.
4. Response Signal: send low-pressure outreach and measure replies.
5. Money Signal: ask for a small payment, deposit, or booked test.

Return ONLY valid JSON in this exact shape:
{
  "promise": "one sentence, no guarantees",
  "who_it_is_for": ["item", "item", "item"],
  "rules": ["item", "item", "item", "item"],
  "method_steps": [
    {"name":"Problem Signal", "meaning":"plain text", "test":"plain text"}
  ],
  "scripts": [
    {"title":"DM feedback script", "text":"plain text"}
  ],
  "days": [
    {
      "day": 1,
      "title": "short title",
      "signal_step": "one of the 5 method steps",
      "objective": "plain text, no markdown",
      "specific_action": "plain text, no markdown",
      "example": "plain text, no markdown",
      "expected_result": "plain text, no markdown",
      "reflection_question": "plain text, no markdown"
    }
  ]
}
Rules:
- Exactly 5 method_steps.
- Exactly 6 scripts: feedback request, first outreach, follow-up, small paid offer, rejection reply, testimonial request.
- Exactly 30 days.
- No markdown formatting, no bullet symbols, no asterisks.
- Do not promise guaranteed income.
- Avoid survey sites as the core strategy.
- Focus on simple services, tiny offers, outreach, content tests, and digital product tests.
- Make every day different and concrete.
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    data = load_json(response.text)
    if len(data.get("days", [])) != 30:
        raise RuntimeError(f"Expected 30 days from Gemini, got {len(data.get('days', []))}")
    if len(data.get("method_steps", [])) != 5:
        raise RuntimeError(f"Expected 5 method steps, got {len(data.get('method_steps', []))}")
    if len(data.get("scripts", [])) != 6:
        raise RuntimeError(f"Expected 6 scripts, got {len(data.get('scripts', []))}")
    return data

def list_items(items):
    return "\n".join([f"- {esc(x)}" for x in items])

title = "The Signal Test Method"
subtitle = "A 30-Day Side Hustle Playbook for Testing Real Demand Before You Waste Time"
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
  #text(size: 25pt, weight: "bold")[{esc(title)}]
  #v(8pt)
  #text(size: 11pt, fill: rgb("6B6258"))[{esc(subtitle)}]
  #v(32pt)
  #box("What this actually helps you do", [{esc(pack.get('promise', 'Test side hustle ideas through small demand signals before wasting time building the wrong thing.'))}])
]

#pagebreak()

= How to Use This Book

This is a KDP workbook for testing demand, not a promise of income. The goal is to stop collecting side hustle ideas and start looking for real signals: pain, interest, replies, willingness to pay, and proof that a small offer deserves more time.

== Who this is for
{list_items(pack.get('who_it_is_for', []))}

== Rules
{list_items(pack.get('rules', []))}

#pagebreak()

= The Signal Test Method

The method is simple: do not build first. Test for signals first.

"""

for step in pack.get("method_steps", []):
    typst += f"#box(\"{esc(step.get('name','Signal'))}\", [{esc(step.get('meaning',''))}\n\nTest: {esc(step.get('test',''))}])\n\n"

typst += "#pagebreak()\n\n= Script Bank\n\nUse these scripts as starting points. Rewrite them so they sound like you.\n\n"
for script in pack.get("scripts", []):
    typst += f"#box(\"{esc(script.get('title','Script'))}\", [{esc(script.get('text',''))}])\n\n"

typst += "#pagebreak()\n\n= 30-Day Signal Plan\n\nEach day tests one signal. Do the action first. Judge the result after.\n\n#pagebreak()\n"

for item in days:
    day = int(item.get("day"))
    day_title = esc(item.get("title", f"Day {day}"))
    typst += f"\n= Day {day}: {day_title}\n\n"
    typst += f"#box(\"Signal step\", [{esc(item.get('signal_step', ''))}])\n\n"
    typst += f"#box(\"Objective\", [{esc(item.get('objective', ''))}])\n\n"
    typst += f"#box(\"Specific action\", [{esc(item.get('specific_action', ''))}])\n\n"
    typst += f"#box(\"Example\", [{esc(item.get('example', ''))}])\n\n"
    typst += f"#box(\"Expected signal\", [{esc(item.get('expected_result', ''))}])\n\n"
    typst += f"#box(\"Reflection\", [{esc(item.get('reflection_question', ''))}])\n\n"
    typst += "#pagebreak()\n"

typst += """
= Signal Tracker

#table(
  columns: (1fr, 1.6fr, 1.6fr, 1.3fr),
  inset: 7pt,
  stroke: 0.5pt + rgb("D7D2CA"),
  [Date], [Test], [Signal seen], [Next action],
)

#pagebreak()

= Next 30 Days

#box("Double down", [What test created the strongest signal?])
#box("Cut", [What felt busy but produced weak or no signal?])
#box("Next offer", [What tiny paid offer will you test next?])
"""

source_file = PRODUCT_DIR / "book.typ"
source_file.write_text(typst, encoding="utf-8")

pdf_file = PRODUCT_DIR / "book.pdf"
subprocess.run(["typst", "compile", str(source_file), str(pdf_file)], check=True)

sales_description = """Most side hustle ideas fail because people build before they test.

The Signal Test Method gives beginners a practical 30-day system for testing real demand before wasting time on the wrong idea.

Instead of collecting more ideas, you will look for signals: real pain points, likely buyers, simple offers, replies, feedback, and early willingness to pay.

Inside, you get a named 5-step method, daily action pages, outreach scripts, follow-up scripts, offer prompts, reflection questions, and a signal tracker.

No fake promises. No expensive tools. No guru hype.

Just small tests, real feedback, and clearer next steps.
"""

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text(sales_description, encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle workbook, side hustle planner, business idea validation, online income beginner, make money online realistic, offer testing, side hustle test kit", encoding="utf-8")
(PRODUCT_DIR / "cover-prompt.txt").write_text("""Create a premium 6x9 KDP book cover.

Title: The Signal Test Method
Subtitle: A 30-Day Side Hustle Playbook for Testing Real Demand Before You Waste Time

Style:
- Clean, modern, credible business workbook
- Strong typography, readable as an Amazon thumbnail
- Warm neutral tones
- Subtle signal/radar/progress motif
- No people
- No fake luxury visuals
- Practical, serious, not make-money-online spam
""", encoding="utf-8")
(PRODUCT_DIR / "upload-checklist.txt").write_text("1. Open book.pdf and inspect 5 random pages.\n2. Check title/subtitle.\n3. Generate cover from cover-prompt.txt.\n4. Use description.txt and keywords.txt for KDP listing.\n5. Do not publish before checking no income guarantees are stated.\n", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine": "signal_test_method_v1",
    "product": title,
    "kdp_only": True,
    "gemini_used": True,
    "model": MODEL_NAME,
    "days_generated": len(days),
    "scripts_generated": len(pack.get("scripts", [])),
    "method_steps": len(pack.get("method_steps", [])),
    "fallback_allowed": False,
    "typst_sanitized": True,
    "layout": "6x9_kdp_workbook"
}, indent=2), encoding="utf-8")

print("AI PRODUCT BUILT:", pdf_file)
print("Gemini model:", MODEL_NAME)
