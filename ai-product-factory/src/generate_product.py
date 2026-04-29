import json, os, re, subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "signal-test-method-kdp-preview"
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

def lines(n=6):
    return "\n".join(["#line(length: 100%)" for _ in range(n)]) + "\n"

def box(title: str, body: str, notes: int = 0) -> str:
    content = esc(body)
    if notes:
        content += "\n\n#strong[Your notes]\n#v(3pt)\n" + lines(notes)
    return (
        '#block(inset: 8pt, radius: 4pt, stroke: 0.5pt, fill: rgb("FFFFFF"))['
        f'#strong[{esc(title)}]\n#v(3pt)\n{content}\n]\n\n'
    )

def scorecard_box() -> str:
    return (
        '#block(inset: 8pt, radius: 4pt, stroke: 0.5pt, fill: rgb("FFFFFF"))['
        '#strong[The 3-Signal Scorecard]\n#v(3pt)\n'
        'Problem strength (1-5): #line(length: 35%)\n\n'
        'Reachability (1-5): #line(length: 35%)\n\n'
        'Willingness to pay (1-5): #line(length: 35%)\n\n'
        'Total score: #line(length: 35%)\n\n'
        '#strong[Interpretation]\n'
        '3-7: Stop\n\n'
        '8-11: Pivot\n\n'
        '12-15: Continue\n'
        ']\n\n'
    )

def tracker_rows(n=24):
    rows = '  [Date], [Test], [Signal], [Next action],\n'
    for _ in range(n):
        rows += '  [], [], [], [],\n'
    return rows

def load_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

prompt = """
Create a sharp KDP workbook called The Signal Test Method.
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
  "case_study":{"title":"","idea":"","what_i_did":["",""],"what_happened":"","conclusion":"","what_to_do_differently":""},
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
- case study must be about a digital side hustle such as a template, audit, checklist, spreadsheet, or PDF mini-product
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
author = "The Modern Family Guide"

mini_tools = [
    ("The 10-Message Test", "Send 10 direct, personal messages before judging an idea. Do not count likes, compliments, or vague interest. Count replies that show pain or willingness to act."),
    ("The $10 Tiny Offer Test", "Turn your idea into one small thing someone could buy for around $10. If nobody wants the tiny version, do not build the big version yet."),
    ("The Polite Interest Trap", "People saying 'cool idea' is not demand. Demand looks like questions, urgency, payment, referrals, or asking when it is available."),
    ("The Silence Rule", "If people ignore the offer after multiple direct asks, treat silence as data. Do not argue with the market."),
]

typst = f"""
#set page(
  width: 6in,
  height: 9in,
  margin: (x: 0.62in, y: 0.68in),
  header: align(center)[#text(size: 8pt, fill: rgb("777777"))[The Signal Test Method]],
  footer: align(center)[#context text(size: 8pt, fill: rgb("777777"))[#counter(page).display()]]
)
#set text(size: 10pt)
#set heading(numbering: none)
#set par(justify: false)

#align(center)[
#v(120pt)
#text(size: 26pt, weight: "bold")[{esc(title)}]
#v(10pt)
#text(size: 12pt)[{esc(subtitle)}]
#v(44pt)
#text(size: 10pt)[By {esc(author)}]
]

#pagebreak()

#text(size: 8pt)[
Copyright © 2026\n\nThis workbook is for educational purposes only. It does not provide financial advice and does not guarantee income, business results, or sales. Your results depend on your skills, market, offer, effort, timing, and many other factors.
]

#pagebreak()

= Before You Build Anything

Most ideas do not fail because people are lazy.\n\nThey fail because nobody tested demand early enough.\n\nThis workbook forces you to do the opposite.\n\nIn the next 30 days, you will talk to real people, test a real problem, make a tiny offer, and ask for real money.\n\nIf nobody pays, you stop or pivot.\n\nIf someone pays, you continue.\n\nThat is the entire game.

#pagebreak()

= Your First Win (15 Minutes)

#block(inset: 10pt, radius: 4pt, stroke: 0.7pt, fill: rgb("FFFFFF"))[
#strong[Send this message to 1 person today]\n#v(4pt)
Hey, quick question — are you still struggling with \[problem\]?\n\nIf they reply, you have your first signal.\n\nDo not overthink it.
]

#v(12pt)
#strong[Who will you message?]\n#v(4pt)
{lines(5)}

#pagebreak()

= Workbook Roadmap

The Method\n\nConversion Tools\n\nStart Here: 15-Minute Tests\n\nCopy/Paste Scripts\n\nDigital Side Hustle Case Study\n\n30-Day Signal Plan\n\nSignal Tracker\n\nStop / Pivot / Continue Decision\n
#pagebreak()

= How to Use This Workbook

This workbook is not for collecting ideas. It is for testing whether an idea deserves more time. Each day asks you to take one small action, face the realistic friction, and record what actually happened.

{box('Use this for', pack.get('promise','Test small ideas before wasting time building the wrong thing.'), 6)}

#pagebreak()

= The Method

Do not build first. Look for signals first.

"""

for s in pack["method_steps"]:
    body = f"{s['what_it_means']}\n\nTest: {s['test']}\n\nWhat goes wrong: {s['what_goes_wrong']}\n\nStop when: {s['stop_when']}"
    typst += box(s["name"], body, 4)

typst += "#pagebreak()\n= Conversion Tools\n\nThese tools help you avoid the most common beginner mistake: confusing polite interest with real demand.\n\n"
for name, desc in mini_tools:
    typst += box(name, desc, 3)
typst += scorecard_box()

typst += "#pagebreak()\n= Start Here: 15-Minute Tests\n\n"
for fw in pack["fast_wins"]:
    typst += box(fw["title"], fw["action"], 6)

typst += "#pagebreak()\n= Copy/Paste Scripts\n\nUse these as starting points. Rewrite them so they sound like you.\n\n"
for sc in pack["scripts"]:
    typst += box(sc["title"], sc["text"], 4)

cs = pack["case_study"]
typst += f"#pagebreak()\n= Digital Side Hustle Case Study: {esc(cs['title'])}\n\n"
typst += box("Idea", cs["idea"])
typst += box("What I did", "\n".join(cs.get("what_i_did", [])))
typst += box("What happened", cs["what_happened"])
typst += box("What I learned", cs["conclusion"])
typst += box("What I would do differently", cs.get("what_to_do_differently", "Use a smaller test, ask for money sooner, and stop faster if no one cares."), 6)
typst += "#pagebreak()\n= 30-Day Signal Plan\n\nEach day has one action, one reality check, and one win condition. Complete the action before reading ahead.\n\n#pagebreak()\n"

for d in pack["days"]:
    typst += f"= Day {d['day']}: {esc(d['title'])}\n\n"
    typst += box("Action", d["action"])
    typst += box("Reality", d["reality"])
    typst += box("Win condition", d["win_condition"])
    typst += box("Daily notes", "What happened today? What signal did you see? What is the next smallest action?", 11)
    typst += "#pagebreak()\n"

typst += f"""
= Signal Tracker

#table(
  columns: (1fr, 1.6fr, 1.6fr, 1.3fr),
  inset: 7pt,
  stroke: 0.5pt,
{tracker_rows(24)})

#pagebreak()

= Stop / Pivot / Continue

{box('Continue', 'What created a real signal: payment, specific request, repeated problem, urgency, or a direct yes?', 8)}
{box('Pivot', 'What part seemed promising, but needs a different audience, offer, price, or message?', 8)}
{box('Stop', 'What produced silence, vague compliments, weak signals, or polite interest without action?', 8)}
{box('Next $10 Test', 'What is the smallest paid test you will run next?', 8)}
"""

src = PRODUCT_DIR / "book.typ"
src.write_text(typst, encoding="utf-8")
subprocess.run(["typst", "compile", str(src), str(PRODUCT_DIR / "book.pdf")], check=True)

sales_description = """Most side hustle ideas fail because people build before they test.

The Signal Test Method is a practical 30-day workbook for testing real demand before you waste time building the wrong thing.

Inside, you get a simple 5-step method, conversion tools like The 10-Message Test and The $10 Tiny Offer Test, a real 3-Signal Scorecard, 15-minute tests, copy/paste scripts, a digital side hustle case study, daily action pages, notes space, a signal tracker, and Stop / Pivot / Continue worksheets.

This workbook is designed for beginners who want a realistic way to test side hustle ideas without hype, expensive tools, or fake income promises.

No guru hype. No build-first nonsense. No guarantees.

Just small tests, real signals, and clearer next steps.
"""

kdp_listing = {
    "title": title,
    "subtitle": subtitle,
    "author": author,
    "description": sales_description,
    "categories_to_try": [
        "Business & Money > Small Business & Entrepreneurship",
        "Business & Money > Entrepreneurship",
        "Business & Money > Skills > Personal Success"
    ],
    "backend_keywords": [
        "side hustle workbook",
        "business idea validation",
        "product validation workbook",
        "test business idea",
        "online income beginner",
        "startup workbook",
        "side hustle planner"
    ],
    "pricing_note": "Start low for early traction. For paperback, test the lowest viable royalty-positive price, then raise only after reviews or proof of demand.",
    "positioning_note": "Position as a practical validation workbook, not a make-money promise."
}

cover_spec = {
    "format": "KDP paperback cover concept",
    "trim_size": "6x9",
    "title": title,
    "subtitle": subtitle,
    "style": "high-contrast premium workbook, credible business guide, warm neutral tones, bold readable typography, subtle signal/radar/checklist motif, no people, no fake luxury, not scammy",
    "front_cover_prompt": "Create a premium 6x9 KDP paperback front cover for 'The Signal Test Method'. Subtitle: 'A 30-Day Side Hustle Workbook for Testing Real Demand Before You Build'. High-contrast clean modern business workbook style. Title must be readable as a small Amazon thumbnail. Use warm neutral tones, strong typography, and a subtle signal/radar/checklist motif. No people. No fake luxury. No money rain. Credible, practical, not make-money-online spam.",
    "back_cover_blurb": "Stop building ideas nobody asked for. The Signal Test Method helps you test demand first with small actions, direct asks, tiny paid offers, and clear Stop / Pivot / Continue decisions.",
    "spine_text": "The Signal Test Method"
}

upload_fields = (
    f"TITLE\n{title}\n\n"
    f"SUBTITLE\n{subtitle}\n\n"
    f"AUTHOR\n{author}\n\n"
    f"DESCRIPTION\n{sales_description}\n\n"
    f"KEYWORDS\n{', '.join(kdp_listing['backend_keywords'])}\n\n"
    "CATEGORIES TO TRY\n"
    + "\n".join(kdp_listing["categories_to_try"])
    + "\n"
)

(PRODUCT_DIR / "title.txt").write_text(title + "\n" + subtitle, encoding="utf-8")
(PRODUCT_DIR / "description.txt").write_text(sales_description, encoding="utf-8")
(PRODUCT_DIR / "keywords.txt").write_text(", ".join(kdp_listing["backend_keywords"]), encoding="utf-8")
(PRODUCT_DIR / "kdp-listing.json").write_text(json.dumps(kdp_listing, indent=2), encoding="utf-8")
(PRODUCT_DIR / "cover-spec.json").write_text(json.dumps(cover_spec, indent=2), encoding="utf-8")
(PRODUCT_DIR / "cover-prompt.txt").write_text(cover_spec["front_cover_prompt"], encoding="utf-8")
(PRODUCT_DIR / "kdp-upload-fields.txt").write_text(upload_fields, encoding="utf-8")
(PRODUCT_DIR / "upload-checklist.txt").write_text("1. Open book.pdf and inspect first 8 pages, conversion tools, scorecard, 3 daily pages, tracker, and Stop / Pivot / Continue page.\n2. Check that no income guarantees are stated.\n3. Generate KDP cover using cover-spec.json or cover-prompt.txt.\n4. Use kdp-listing.json and kdp-upload-fields.txt for KDP metadata.\n5. Upload interior PDF to KDP and preview before publishing.\n", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine":"kdp_preview_optimization_v1_fixed_page_counter",
    "product": title,
    "days": len(pack["days"]),
    "scripts": len(pack["scripts"]),
    "method_steps": len(pack["method_steps"]),
    "fast_wins": len(pack["fast_wins"]),
    "conversion_tools": len(mini_tools) + 1,
    "model": MODEL_NAME,
    "kdp_only": True,
    "frontmatter": True,
    "preview_intro": True,
    "fast_win_page": True,
    "headers_footers": True,
    "worksheets": True,
    "tracker_rows": 24,
    "listing_assets": True,
    "cover_assets": True
}, indent=2), encoding="utf-8")

print("KDP Preview Optimization Build created")
