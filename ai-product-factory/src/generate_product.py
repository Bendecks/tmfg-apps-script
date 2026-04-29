from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]
TEMPLATES = BASE / 'templates'
OUTPUT = BASE / 'dist' / 'books' / 'premium-workbook'
OUTPUT.mkdir(parents=True, exist_ok=True)

env = Environment(loader=FileSystemLoader(TEMPLATES))

PRODUCT = 'First $100 Online Workbook'
SUBTITLE = 'A 30-Day System for Testing Simple Side Hustles'


def get_phase(day):
    if day <= 5:
        return 'PHASE 1 — SETUP'
    if day <= 15:
        return 'PHASE 2 — VALIDATION'
    if day <= 25:
        return 'PHASE 3 — REPEAT'
    return 'PHASE 4 — FIRST MONEY'


def get_action(day):
    if day <= 5:
        return 'Pick ONE simple idea and define who might realistically pay for it.'
    if day <= 15:
        return 'Send 3 messages or make 1 public post to get real-world feedback.'
    if day <= 25:
        return 'Repeat the action that created the clearest signal yesterday.'
    return 'Do one action today that could directly lead to your first payment.'


def render(template_name, **kwargs):
    return env.get_template(template_name).render(**kwargs)

pages = []

# Hook + commitment
pages.append(render('intro.html', title=PRODUCT, subtitle=SUBTITLE, note='This workbook is built for action, not endless planning.'))
pages.append(render('intro.html', title='Rules of the System', subtitle='One action per day. Real feedback. No pretending.', note='If you only fill pages but never act, nothing changes.'))
pages.append(render('commitment.html'))

# Idea selection
for i in range(1, 11):
    pages.append(render('idea.html', number=i))

# 30-day execution system
for day in range(1, 31):
    pages.append(render('day.html', day=day, phase=get_phase(day), action=get_action(day)))

# Tools and trackers
for i in range(1, 21):
    pages.append(render('tracker.html', title='Outreach Tracker', columns=['Date', 'Person / Platform', 'Message', 'Reply', 'Next step']))
for i in range(1, 11):
    pages.append(render('money.html'))
for i in range(1, 9):
    pages.append(render('review.html', number=i))

full_html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><link rel="stylesheet" href="styles/style.css"></head><body>' + ''.join(pages) + '</body></html>'

html_path = OUTPUT / 'premium-workbook.html'
pdf_path = OUTPUT / 'premium-workbook.pdf'
html_path.write_text(full_html, encoding='utf-8')
HTML(string=full_html, base_url=str(BASE)).write_pdf(pdf_path)

(OUTPUT / 'metadata.json').write_text(json.dumps({
    'product': PRODUCT,
    'subtitle': SUBTITLE,
    'engine': 'premium_workbook_v1',
    'pages': len(pages),
    'output_pdf': 'premium-workbook.pdf'
}, indent=2), encoding='utf-8')

(OUTPUT / 'title-subtitle.txt').write_text(PRODUCT + '\n' + SUBTITLE, encoding='utf-8')
(OUTPUT / 'description.txt').write_text(
    'A structured 30-day workbook for testing simple side hustle ideas, getting real feedback, tracking outreach, and building momentum toward a first online payment.',
    encoding='utf-8'
)

print('PREMIUM WORKBOOK BUILT:', pdf_path)
