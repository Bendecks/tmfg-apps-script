import json, os, re, subprocess
from pathlib import Path
from google import genai
from google.genai import types

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist" / "products"
DIST.mkdir(parents=True, exist_ok=True)

slug = "stop-building-ideas-nobody-wants"
PRODUCT_DIR = DIST / slug
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "gemini-2.5-flash"
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing.")

client = genai.Client(api_key=api_key)

# KDP-facing title optimized for search + click-through.
title = "Stop Building Ideas Nobody Wants"
subtitle = "The Signal Test Method: A 30-Day Side Hustle Workbook to Test Demand Before You Build"
author = "The Modern Family Guide"
internal_method_name = "The Signal Test Method"

def esc(text: str) -> str:
    text = str(text)
    replacements = {"\\": "\\\\", "$": "\\$", "#": "\\#", "*": "\\*", "_": "\\_", "[": "\\[", "]": "\\]", "`": "\\`"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def humanize(text: str) -> str:
    text = str(text)
    replacements = {
        "You will": "You’ll",
        "you will": "you’ll",
        "Do not": "Don’t",
        "do not": "don’t",
        "It is": "It’s",
        "it is": "it’s",
        "You are": "You’re",
        "you are": "you’re",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def lines(n=6):
    return "\n".join(["#line(length: 100%)" for _ in range(n)]) + "\n"

def box_primary(title_text: str, body: str, notes: int = 0) -> str:
    content = esc(humanize(body))
    if notes:
        content += "\n\n#strong[Your notes]\n#v(4pt)\n" + lines(notes)
    return '#block(inset: 10pt, radius: 6pt, stroke: 0.8pt, fill: rgb("F8F8F8"))[' + f'#strong[{esc(title_text)}]\n#v(4pt)\n{content}\n]\n\n'

def box_secondary(title_text: str, body: str, notes: int = 0) -> str:
    content = esc(humanize(body))
    if notes:
        content += "\n\n#emph[Notes]\n#v(3pt)\n" + lines(notes)
    return '#block(inset: 8pt, radius: 4pt, stroke: 0.4pt)[' + f'#emph[{esc(title_text)}]\n#v(3pt)\n{content}\n]\n\n'

def box_highlight(text: str) -> str:
    return '#block(inset: 12pt, radius: 0pt, stroke: none)[' + f'#text(size: 12pt, weight: "bold")[{esc(humanize(text))}]' + ']\n\n'

def scorecard_box() -> str:
    return (
        '#block(inset: 10pt, radius: 6pt, stroke: 0.8pt, fill: rgb("F8F8F8"))['
        '#strong[The 3-Signal Scorecard]\n#v(4pt)\n'
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
Create a sharp KDP workbook system called The Signal Test Method.
The public book title is Stop Building Ideas Nobody Wants.
Subtitle: The Signal Test Method: A 30-Day Side Hustle Workbook to Test Demand Before You Build.

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

for key, expected in [("method_steps", 5), ("fast_wins", 3), ("scripts", 6), ("days", 30)]:
    actual = len(pack.get(key, []))
    if actual != expected:
        raise RuntimeError(f"Expected {expected} {key}, got {actual}")

mini_tools = [
    ("The 10-Message Test", "Send 10 direct, personal messages before judging an idea. Don’t count likes, compliments, or vague interest. Count replies that show pain or willingness to act."),
    ("The $10 Tiny Offer Test", "Turn your idea into one small thing someone could buy for around $10. If nobody wants the tiny version, don’t build the big version yet."),
    ("The Polite Interest Trap", "People saying 'cool idea' is not demand. Demand looks like questions, urgency, payment, referrals, or asking when it is available."),
    ("The Silence Rule", "If people ignore the offer after multiple direct asks, treat silence as data. Don’t argue with the market."),
]

typst = f"""
#set page(
  width: 6in,
  height: 9in,
  margin: (x: 0.62in, y: 0.68in),
  header: align(center)[#text(size: 8pt, fill: rgb("777777"))[{esc(title)}]],
  footer: align(center)[#context text(size: 8pt, fill: rgb("777777"))[#counter(page).display()]]
)
#set text(size: 10pt)
#set heading(numbering: none)
#set par(justify: false)

#align(center)[
#v(105pt)
#text(size: 25pt, weight: "bold")[{esc(title)}]
#v(10pt)
#text(size: 11pt)[{esc(subtitle)}]
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

#align(center)[
#v(140pt)
#text(size: 22pt, weight: "bold")[Most people don’t fail because they’re lazy.]
#v(12pt)
#text(size: 14pt)[They fail because they never ask anyone if the idea is worth paying for.]
#v(24pt)
#text(size: 12pt)[This workbook forces you to ask.]
]

#pagebreak()

= Your First Win (15 Minutes)

#block(inset: 10pt, radius: 6pt, stroke: 0.8pt, fill: rgb("F8F8F8"))[
#strong[Send this message to 1 person today]\n#v(4pt)
Hey, quick question — are you still struggling with \[problem\]?\n\nIf they reply, you have your first signal.\n\nDon’t overthink it.
]

#v(12pt)
#strong[Who will you message?]\n#v(4pt)
{lines(5)}

#pagebreak()

= What Counts as a Real Signal?

#block(inset: 10pt, radius: 6pt, stroke: 0.8pt, fill: rgb("F8F8F8"))[
#strong[Real signals]\n#v(4pt)
- Someone asks a follow-up question\n
- Someone shares a real problem\n
- Someone asks for the price\n
- Someone says “can you do this for me?”
]

#block(inset: 8pt, radius: 4pt, stroke: 0.4pt)[
#emph[Not real signals]\n#v(3pt)
- “Cool idea”\n
- “Nice”\n
- Likes\n
- Silence
]

#v(10pt)
#text(size: 11pt)[If you cannot tell the difference, you will waste months building the wrong thing.]

#pagebreak()

= Workbook Roadmap

The Method\n\nConversion Tools\n\nStart Here: 15-Minute Tests\n\nCopy/Paste Scripts\n\nDigital Side Hustle Case Study\n\n30-Day Signal Plan\n\nSignal Tracker\n\nStop / Pivot / Continue Decision\n
#pagebreak()

= How to Use This Workbook

This workbook is not for collecting ideas. It is for testing whether an idea deserves more time. Each day asks you to take one small action, face the realistic friction, and record what actually happened.

{box_primary('Use this for', pack.get('promise','Test small ideas before wasting time building the wrong thing.'), 6)}

#pagebreak()

= The Method

Do not build first. Look for signals first.

"""

for s in pack["method_steps"]:
    body = f"{s['what_it_means']}\n\nTest: {s['test']}\n\nWhat goes wrong: {s['what_goes_wrong']}\n\nStop when: {s['stop_when']}"
    typst += box_primary(s["name"], body, 4)

typst += "#pagebreak()\n= Conversion Tools\n\nThese tools help you avoid the most common beginner mistake: confusing polite interest with real demand.\n\n"
for name, desc in mini_tools:
    typst += box_secondary(name, desc, 3)
typst += scorecard_box()

typst += "#pagebreak()\n= Start Here: 15-Minute Tests\n\n"
for fw in pack["fast_wins"]:
    typst += box_primary(fw["title"], fw["action"], 6)

typst += "#pagebreak()\n= Copy/Paste Scripts\n\nUse these as starting points. Rewrite them so they sound like you.\n\n"
for sc in pack["scripts"]:
    typst += box_secondary(sc["title"], sc["text"], 4)

cs = pack["case_study"]
typst += f"#pagebreak()\n= Digital Side Hustle Case Study: {esc(cs['title'])}\n\n"
typst += box_primary("Idea", cs["idea"])
typst += box_secondary("What I did", "\n".join(cs.get("what_i_did", [])))
typst += box_secondary("What happened", cs["what_happened"])
typst += box_primary("What I learned", cs["conclusion"])
typst += box_highlight("Nobody bought the first version. That was the signal. Not failure.")
typst += box_primary("What I would do differently", cs.get("what_to_do_differently", "Use a smaller test, ask for money sooner, and stop faster if no one cares."), 6)
typst += "#pagebreak()\n= 30-Day Signal Plan\n\nEach day has one action, one reality check, and one win condition. Complete the action before reading ahead.\n\n#pagebreak()\n"

for d in pack["days"]:
    typst += f"= Day {d['day']}: {esc(d['title'])}\n\n"
    typst += box_primary("Action", d["action"])
    typst += box_secondary("Reality", d["reality"])
    typst += box_primary("Win condition", d["win_condition"])
    if int(d["day"]) % 5 == 0:
        typst += box_highlight("You are not looking for motivation. You are looking for proof.")
    typst += box_secondary("Daily notes", "What happened today? What signal did you see? What is the next smallest action?", 11)
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

{box_primary('Continue', 'What created a real signal: payment, specific request, repeated problem, urgency, or a direct yes?', 8)}
{box_secondary('Pivot', 'What part seemed promising, but needs a different audience, offer, price, or message?', 8)}
{box_secondary('Stop', 'What produced silence, vague compliments, weak signals, or polite interest without action?', 8)}
{box_primary('Next $10 Test', 'What is the smallest paid test you will run next?', 8)}
"""

src = PRODUCT_DIR / "book.typ"
src.write_text(typst, encoding="utf-8")
subprocess.run(["typst", "compile", str(src), str(PRODUCT_DIR / "book.pdf")], check=True)

sales_description = """Most side hustle ideas fail because people build before they test.

Stop Building Ideas Nobody Wants is a practical 30-day side hustle workbook that helps you test real demand before you waste time building the wrong thing.

Inside, you’ll use The Signal Test Method: a simple 5-step process for finding a real problem, finding someone who cares, making a tiny offer, asking directly, and trying to get paid.

You also get conversion tools like The 10-Message Test, The $10 Tiny Offer Test, The Polite Interest Trap, The Silence Rule, and a real 3-Signal Scorecard.

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
        "test business idea",
        "product validation workbook",
        "side hustle planner",
        "startup workbook",
        "online income beginner"
    ],
    "title_variants_for_future_tests": [
        "Stop Building Ideas Nobody Wants",
        "Test Before You Build",
        "Side Hustle Idea Validation Workbook",
        "The Signal Test Method",
        "Will Anyone Pay For This?"
    ],
    "recommended_positioning": "Lead with the fear of wasting time building the wrong idea. Sell the workbook as a practical validation system, not an income promise.",
    "pricing_note": "Start with a low royalty-positive paperback price for traction. Raise only after reviews, proof of conversion, or a stronger cover."
}

cover_spec = {
    "format": "KDP paperback cover concept",
    "trim_size": "6x9",
    "title": title,
    "subtitle": subtitle,
    "thumbnail_rule": "Title must be readable when reduced to Amazon search-result thumbnail size.",
    "avoid": ["money rain", "laptop luxury lifestyle", "fake guru look", "crowded illustrations", "tiny subtitle", "generic planner cover"],
    "recommended_concept": "bold typography first, minimal signal/checkmark motif second, warm neutral background, business-workbook credibility",
    "front_cover_prompt": "Create a premium 6x9 KDP paperback front cover for 'Stop Building Ideas Nobody Wants'. Subtitle: 'The Signal Test Method: A 30-Day Side Hustle Workbook to Test Demand Before You Build'. The cover must be high-contrast and readable as a small Amazon thumbnail. Use bold modern typography, warm neutral tones, and a subtle signal/checkmark/radar motif. Make it look like a credible business workbook, not a scammy make-money-online product. No people, no money rain, no luxury laptop scene, no fake guru style, no clutter.",
    "concepts": [
        {
            "name": "Bold Text / Proof Motif",
            "prompt": "Minimal warm-neutral cover. Huge bold title. Small radar/checkmark icon. Professional business workbook style. Strong contrast."
        },
        {
            "name": "Stop Sign / Idea Filter",
            "prompt": "Clean cover with abstract stop/filter symbol and checklist marks. Strong title hierarchy. Not playful. Credible and practical."
        },
        {
            "name": "Signal Dashboard",
            "prompt": "Minimal dashboard-like cover with simple signal bars and checkmarks. Premium workbook feel. No charts that look like stock investing."
        }
    ],
    "back_cover_blurb": "Stop building ideas nobody asked for. This workbook helps you test demand first with small actions, direct asks, tiny paid offers, and clear Stop / Pivot / Continue decisions.",
    "spine_text": title
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
(PRODUCT_DIR / "upload-checklist.txt").write_text("1. Open book.pdf and inspect first 10 pages, real/fake signal page, conversion tools, scorecard, 3 daily pages, tracker, and Stop / Pivot / Continue page.\n2. Check that no income guarantees are stated.\n3. Generate 3 cover concepts using cover-spec.json.\n4. Test thumbnail readability before upload.\n5. Use kdp-listing.json and kdp-upload-fields.txt for KDP metadata.\n6. Upload interior PDF to KDP and preview before publishing.\n", encoding="utf-8")
(PRODUCT_DIR / "metadata.json").write_text(json.dumps({
    "engine": "kdp_sales_optimization_v1",
    "product": title,
    "method_name": internal_method_name,
    "days": len(pack["days"]),
    "scripts": len(pack["scripts"]),
    "method_steps": len(pack["method_steps"]),
    "fast_wins": len(pack["fast_wins"]),
    "conversion_tools": len(mini_tools) + 1,
    "model": MODEL_NAME,
    "kdp_only": True,
    "sales_title_optimized": True,
    "searchable_subtitle": True,
    "cover_positioning_assets": True,
    "cover_concepts": 3,
    "thumbnail_rule": True,
    "scroll_stop_page": True,
    "real_signal_page": True,
    "box_styles": 3,
    "daily_highlights": True,
    "humanize_tone": True,
    "humanize_have_contraction_removed": True,
    "headers_footers": True,
    "worksheets": True,
    "tracker_rows": 24,
    "listing_assets": True,
    "cover_assets": True
}, indent=2), encoding="utf-8")

print("KDP Sales Optimization Build created")
