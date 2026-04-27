import os
import json
import csv
import textwrap
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / 'dist'
DIST.mkdir(exist_ok=True)
config = json.loads((BASE / 'config' / 'product.json').read_text())

PRODUCT_NAME = config.get('product_name', 'AI Digital Product')
BRAND = config.get('brand', 'Digital Product Studio')
AUDIENCE = config.get('audience', 'busy people who want practical results')


def gemini_generate(prompt: str) -> str:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return ''
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return (response.text or '').strip()
    except Exception as e:
        print(f'Gemini failed, using fallback. Error: {e}')
        return ''


def fallback_content() -> dict:
    return {
        'guide_title': PRODUCT_NAME,
        'guide_sections': [
            {
                'heading': 'Start Here',
                'body': 'This kit helps job seekers create stronger applications faster by using focused AI prompts, a simple tracker, and repeatable daily actions.'
            },
            {
                'heading': 'How To Use The Prompts',
                'body': 'Copy one prompt at a time into your AI tool. Add your real experience, the job description, and the tone you want. Never submit raw AI text without editing.'
            },
            {
                'heading': 'Daily Workflow',
                'body': 'Pick 3 roles, tailor your resume, draft a short cover letter, track each application, and schedule the next follow-up before moving on.'
            },
            {
                'heading': 'Quality Checklist',
                'body': 'Check that your application uses the role title, mirrors key requirements, includes measurable results, and sounds like a real person.'
            }
        ],
        'prompts': [
            'Rewrite my resume summary for this job description while keeping it honest and specific.',
            'Turn these bullet points into achievement-focused resume bullets with measurable impact.',
            'Write a concise cover letter that sounds natural and avoids corporate clichés.',
            'Create 10 interview questions likely for this role and give me strong answer outlines.',
            'Compare my resume against this job description and list the biggest gaps.'
        ],
        'gumroad_description': f'{PRODUCT_NAME}\n\nA practical digital toolkit for job seekers who want faster, sharper applications. Includes a quick-start guide, AI prompts, and a job application tracker.',
        'sales_page': 'Headline: Apply faster with better AI-assisted job materials.\n\nPromise: Build tailored resumes, cover letters, and interview prep in less time.\n\nIncludes: PDF guide, prompt pack, and tracker.',
        'promo_posts': [
            'Most job seekers waste hours starting from a blank page. This kit gives you prompts and a tracker so you can apply faster.',
            'Use AI for job applications without sounding fake. This kit helps you stay specific, honest, and organized.'
        ]
    }


def generate_content() -> dict:
    prompt = f'''
You are creating a sellable digital product for Gumroad.
Return ONLY valid JSON. No markdown.

Product name: {PRODUCT_NAME}
Brand: {BRAND}
Audience: {AUDIENCE}
Price target: ${config.get('price_usd', 9)}

Create content for a practical digital download that buyers can use immediately.
The tone must be concrete, useful, and not hypey.

JSON schema:
{{
  "guide_title": "string",
  "guide_sections": [{{"heading":"string", "body":"string"}}],
  "prompts": ["string"],
  "gumroad_description": "string",
  "sales_page": "string",
  "promo_posts": ["string"]
}}

Requirements:
- 6 guide sections
- 40 prompts
- Gumroad description must be persuasive but honest
- Sales page must include headline, promise, included files, who it is for, and who it is not for
- Promo posts must include 10 short posts for Pinterest, Reddit, X, or Facebook
'''
    raw = gemini_generate(prompt)
    if not raw:
        return fallback_content()
    try:
        raw = raw.strip()
        if raw.startswith('```'):
            raw = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except Exception as e:
        print(f'Could not parse Gemini JSON, using fallback. Error: {e}')
        return fallback_content()


def draw_wrapped(pdf, text, x, y, width_chars=88, line_height=14):
    for paragraph in text.split('\n'):
        wrapped = textwrap.wrap(paragraph, width=width_chars) or ['']
        for line in wrapped:
            if y < 60:
                pdf.showPage()
                pdf.setFont('Helvetica', 10)
                y = 800
            pdf.drawString(x, y, line)
            y -= line_height
        y -= 6
    return y


content = generate_content()

# PDF guide
pdf = canvas.Canvas(str(DIST / 'quick-start-guide.pdf'), pagesize=A4)
pdf.setTitle(content.get('guide_title', PRODUCT_NAME))
pdf.setFont('Helvetica-Bold', 18)
pdf.drawString(40, 800, content.get('guide_title', PRODUCT_NAME)[:70])
pdf.setFont('Helvetica', 10)
pdf.drawString(40, 780, f'By {BRAND}')
y = 745
for section in content.get('guide_sections', []):
    if y < 120:
        pdf.showPage()
        y = 800
    pdf.setFont('Helvetica-Bold', 13)
    pdf.drawString(40, y, section.get('heading', '')[:80])
    y -= 20
    pdf.setFont('Helvetica', 10)
    y = draw_wrapped(pdf, section.get('body', ''), 40, y)
    y -= 8
pdf.save()

# Prompt pack
with open(DIST / 'prompt-pack.txt', 'w', encoding='utf-8') as f:
    f.write(f'{PRODUCT_NAME} - Prompt Pack\n\n')
    for i, p in enumerate(content.get('prompts', []), 1):
        f.write(f'{i}. {p}\n\n')

# Tracker CSV
with open(DIST / 'job-tracker.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Company', 'Role', 'Job URL', 'Date Applied', 'Status', 'Follow-up Date', 'Notes'])

# Gumroad and promo assets
(DIST / 'gumroad-description.txt').write_text(content.get('gumroad_description', ''), encoding='utf-8')
(DIST / 'sales-page.txt').write_text(content.get('sales_page', ''), encoding='utf-8')
(DIST / 'promo-posts.txt').write_text('\n\n'.join(content.get('promo_posts', [])), encoding='utf-8')
(DIST / 'metadata.json').write_text(json.dumps({
    'product_name': PRODUCT_NAME,
    'brand': BRAND,
    'audience': AUDIENCE,
    'generated_with_gemini': bool(os.getenv('GEMINI_API_KEY')),
    'files': [p.name for p in DIST.iterdir()]
}, indent=2), encoding='utf-8')

print('Generated product files:')
for p in DIST.iterdir():
    print('-', p.name)
