import json, os, re, subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "signal-test-method-v3"
PRODUCT_DIR = DIST / slug
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "gemini-2.5-flash"
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

def esc(text: str) -> str:
    text = str(text)
    replacements = {"\\": "\\\\", "$": "\\$", "#": "\\#", "*": "\\*", "_": "\\_", "[": "\\[", "]": "\\]", "`": "\\`"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def box(title: str, body: str) -> str:
    return f'#box("{esc(title)}")[{esc(body)}]\n\n'

def load_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

prompt = """
Create a sharp KDP workbook called The Signal Test Method V3.
Subtitle: A 30-Day Side Hustle Workbook for Testing Real Demand Before You Build.

Use simple direct language. No fancy business jargon.
The method names MUST be exactly:
1. Find a real problem
2. Find someone who cares
3. Make a tiny offer
4. Ask directly
5. Try to get paid

Return ONLY valid JSON:
{
  "promise":"",
  "method_steps":[{"name":"","what_it_means":"","test":"","what_goes_wrong":"","stop_when":""}],
  "fast_wins":[{"title":"","action":""}],
  "scripts":[{"title":"","text":""}],
  "case_study":{"title":"","idea":"","what_i_did":["",""],"what_happened":"","conclusion":""},
  "days":[{"day":1,"title":"","action":"","reality":"","win_condition":""}]
}
Rules:
- exactly 5 method_steps
- exactly 3 fast_wins
- exactly 6 scripts
- exactly 30 days
- short plain text only
- no markdown
- no hype
- include low replies, awkwardness, and failure
"""

response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt,
    config=types.GenerateContentConfig(response_mime_type="application/json")
)
pack = load_json(response.text)

for key, expected in [("method_steps",5),("fast_wins",3),("scripts",6),("days",30)]:
    actual = len(pack.get(key, []))
    if actual != expected:
        raise RuntimeError(f"Expected {expected} {key}, got {actual}")

title = "The Signal Test Method"
subtitle = "A 30-Day Side Hustle Workbook for Testing Real Demand Before You Build"

typst = f"""
#set page(width: 6in, height: 9in, margin: (x: 0.62in, y: 0.68in))
#set text(size: 10pt)
#set heading(numbering: none)
#set par(justify: false)

#let box(t) = block.with(inset: 8pt, radius: 4pt, stroke: 0.5pt, fill: rgb("FFFFFF"))

#align(center)[
#v(50pt)
#text(size: 25pt, weight: "bold")[{esc(title)}]
#v(8pt)
#text(size: 11pt)[{esc(subtitle)}]
#v(28pt)
#box("Use this for")[{esc(pack.get('promise','Test small ideas before wasting time building the wrong thing.'))}]
]
#pagebreak()

= The Method

Do not build first. Look for signals first.

"""

for s in pack["method_steps"]:
    body = f"{s['what_it_means']}\n\nTest: {s['test']}\n\nWhat goes wrong: {s['what_goes_wrong']}\n\nStop when: {s['stop_when']}"
    typst += box(s["name"], body)

typst += "#pagebreak()\n= Start here: 15-minute tests\n\n"
for fw in pack["fast_wins"]:
    typst += box(fw["title"], fw["action"])

typst += "#pagebreak()\n= Copy/paste scripts\n\n"
for sc in pack["scripts"]:
    typst += box(sc["title"], sc["text"])

cs = pack["case_study"]
typst += f"#pagebreak()\n= {esc(cs['title'])}\n\n"
typst += box("Idea", cs["idea"])
typst += box("What I did", "\n".join(cs.get("what_i_did", [])))
typst += box("What happened", cs["what_happened"])
typst += box("Conclusion", cs["conclusion"])
typst += "#pagebreak()\n"

for d in pack["days"]:
    typst += f"= Day {d['day']}: {esc(d['title'])}\n\n"
    typst += box("Action", d["action"])
    typst += box("Reality", d["reality"])
    typst += box("Win condition", d["win_condition"])
    typst += "#pagebreak()\n"

typst += """
= Signal Tracker

#table(
  columns: (1fr, 1.6fr, 1.6fr, 1.3fr),
  inset: 7pt,
  stroke: 0.5pt,
  [Date], [Test], [Signal], [Next move],
)

#pagebreak()

= Final Decision

#box("Double down")[What created the strongest signal?]
#box("Stop")[What produced silence or weak signals?]
#box("Next test")[What is the smallest next action?]
"""

src = PRODUCT_DIR / "book.typ"
src.write_text(typst, encoding="utf-8")
subprocess.run(["typst", "compile", str(src), str(PRODUCT_DIR / "book.pdf")], check=True)

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text("A practical 30-day KDP workbook for testing real side hustle demand before building. Includes a simple 5-step method, fast tests, scripts, a case study, and daily action pages.", encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text("side hustle workbook, business idea validation, side hustle planner, online income beginner, product validation, demand testing, startup workbook", encoding="utf-8")
(PRODUCT_DIR / "cover-prompt.txt").write_text("Create a premium 6x9 KDP cover for The Signal Test Method. Clean modern workbook style. Subtitle: A 30-Day Side Hustle Workbook for Testing Real Demand Before You Build. Strong readable typography, warm neutral tones, subtle signal/radar motif, no people, not scammy.", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine":"signal_v3_fixed_box_rendering",
    "product": title,
    "days": len(pack["days"]),
    "scripts": len(pack["scripts"]),
    "method_steps": len(pack["method_steps"]),
    "fast_wins": len(pack["fast_wins"]),
    "model": MODEL_NAME,
    "kdp_only": True
}, indent=2), encoding="utf-8")

print("Signal Method V3 built")
