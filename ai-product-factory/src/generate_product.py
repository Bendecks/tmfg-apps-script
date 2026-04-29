from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]
TEMPLATES = BASE / 'templates'
OUTPUT = BASE / 'dist' / 'books' / 'premium-preview'
OUTPUT.mkdir(parents=True, exist_ok=True)

env = Environment(loader=FileSystemLoader(TEMPLATES))

pages = []

def render(name, **kwargs):
    return env.get_template(name).render(**kwargs)

pages.append(render('hero.html', title='First $100 Online Workbook', subtitle='A 30-Day Action System for Testing Simple Side Hustles'))
pages.append(render('phase.html', phase='Phase 1', title='Setup', description='Choose one idea, remove friction, and take the first useful action.'))
pages.append(render('day_premium.html', day=1, phase='SETUP', action='Pick one simple idea and define who might realistically pay for it.'))
pages.append(render('day_premium.html', day=7, phase='VALIDATION', action='Send 3 messages or make one public post to get real feedback.'))
pages.append(render('checklist.html', title='Idea Validation Checklist'))
pages.append(render('tracker_premium.html', title='Outreach Tracker'))
pages.append(render('money.html'))
pages.append(render('review.html', number=1))

html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><link rel="stylesheet" href="styles/premium.css"></head><body>' + ''.join(pages) + '</body></html>'

html_path = OUTPUT / 'preview.html'
pdf_path = OUTPUT / 'preview.pdf'
html_path.write_text(html, encoding='utf-8')
HTML(string=html, base_url=str(BASE)).write_pdf(pdf_path)

(OUTPUT / 'metadata.json').write_text(json.dumps({'engine':'premium_preview_v1','pages':len(pages),'purpose':'visual QA before scaling'}, indent=2), encoding='utf-8')
print('PREMIUM PREVIEW BUILT:', pdf_path)
