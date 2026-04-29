import json, os, re, subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "signal-test-method-v2"
PRODUCT_DIR = DIST / slug
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "gemini-2.5-flash"
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

def esc(text: str) -> str:
    text = str(text)
    replacements = {"\\": "\\\\", "$": "\\$", "#": "\\#", "*": "\\*", "_": "\\_"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def load_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

prompt = """
Create a KDP workbook: The Signal Test Method V2.
Focus on realism, friction, and failed attempts.

Return JSON:
{
  "promise": "",
  "method_steps": [
    {"name":"","meaning":"","test":"","what_goes_wrong":"","when_to_stop":""}
  ],
  "scripts": [
    {"title":"","text":""}
  ],
  "case_study": {
    "title":"",
    "steps": ["","",""],
    "result":""
  },
  "days": [
    {
      "day":1,
      "title":"",
      "signal_step":"",
      "specific_action":"",
      "reality_check":""
    }
  ]
}
Rules:
- 5 method_steps
- 6 scripts
- 1 case study
- 30 days
- include low responses, awkward outreach, failures
- no hype
"""

response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt,
    config=types.GenerateContentConfig(response_mime_type="application/json")
)

pack = load_json(response.text)

typst = """
#set page(width: 6in, height: 9in)
#set text(size: 10.5pt)
#set par(justify: true)
#let box(t,b)=block(inset:10pt,stroke:0.5pt,[t\n#v(4pt)b])
"""

# Method with realism
for s in pack["method_steps"]:
    typst += f"#box(\"{esc(s['name'])}\", [{esc(s['meaning'])}\nTest: {esc(s['test'])}\nWhat goes wrong: {esc(s['what_goes_wrong'])}\nWhen to stop: {esc(s['when_to_stop'])}])\n\n"

# Scripts
for sc in pack["scripts"]:
    typst += f"#box(\"{esc(sc['title'])}\", [{esc(sc['text'])}])\n\n"

# Case study
cs = pack["case_study"]
typst += f"= {esc(cs['title'])}\n"
for step in cs['steps']:
    typst += f"- {esc(step)}\n"
typst += f"Result: {esc(cs['result'])}\n\n#pagebreak()\n"

# Days with reality
for d in pack["days"]:
    typst += f"= Day {d['day']}: {esc(d['title'])}\n"
    typst += f"#box(\"Action\", [{esc(d['specific_action'])}])\n"
    typst += f"#box(\"Reality\", [{esc(d['reality_check'])}])\n#pagebreak()\n"

src = PRODUCT_DIR / "book.typ"
src.write_text(typst)

subprocess.run(["typst","compile",str(src),str(PRODUCT_DIR/"book.pdf")],check=True)

(PRODUCT_DIR/"metadata.json").write_text(json.dumps({
    "engine":"signal_v2",
    "days":len(pack.get("days",[])),
    "scripts":len(pack.get("scripts",[])),
    "method_steps":len(pack.get("method_steps",[]))
}, indent=2))

print("Signal Method V2 built")