import os, json, re, textwrap, random
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / 'dist'
BOOKS_ROOT = DIST / 'books'
BOOKS_ROOT.mkdir(parents=True, exist_ok=True)

config = json.loads((BASE / 'config' / 'product.json').read_text())
rotation = config.get('rotation', [])
seed = int(datetime.utcnow().strftime('%Y%m%d'))
selected = rotation[seed % len(rotation)] if rotation else {}

PRODUCT = selected.get('product_name', 'Kids Activity Book')
AUDIENCE = selected.get('audience', 'parents')
NICHE = selected.get('niche', 'kids activities')
TRIM = config.get('trim_size', '8.5x11')
PAGES = int(config.get('page_target', 110))


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

slug = slugify(PRODUCT)
BOOK = BOOKS_ROOT / slug
BOOK.mkdir(parents=True, exist_ok=True)

# clean current book folder only
for old in BOOK.glob('*'):
    if old.is_file():
        old.unlink()


def gemini(prompt):
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        return ''
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        r = genai.GenerativeModel('gemini-2.0-flash').generate_content(prompt)
        return (r.text or '').strip()
    except Exception as e:
        print('Gemini error:', e)
        return ''

listing_prompt = f'''
Return ONLY valid JSON. No markdown.
Create Amazon KDP listing assets for a children's activity book.
Product concept: {PRODUCT}
Niche: {NICHE}
Audience: {AUDIENCE}
Trim size: {TRIM}
Pages: {PAGES}

Schema:
{{
  "title":"string",
  "subtitle":"string",
  "description":"string, 900-1400 characters, HTML-free but with short paragraphs",
  "keywords":["exactly 7 keyword phrases for Amazon KDP keyword boxes"],
  "categories":["3 relevant Amazon categories"],
  "cover_hook":"string",
  "cover_brief":"string, concrete visual brief for a KDP cover designer or AI image tool",
  "activity_themes":["20 varied activity page ideas"]
}}

Rules:
- No promise that the child will learn faster or become smarter.
- Make the buyer clearly understand what is inside.
- Emphasize screen-free, low-prep, calm, travel, rainy day, restaurant, waiting room usefulness where relevant.
- Keywords must not repeat the title exactly in all slots.
'''
raw = gemini(listing_prompt)
try:
    if raw.startswith('```'):
        raw = raw.replace('```json', '').replace('```', '').strip()
    data = json.loads(raw)
except Exception:
    data = {
        'title': PRODUCT,
        'subtitle': 'Screen-Free Activities for Home, Travel, Restaurants, and Rainy Days',
        'description': f'{PRODUCT} is a simple screen-free activity book for families who need calm, low-prep ideas for children.\n\nInside, kids get a mix of drawing prompts, observation games, simple puzzles, imagination starters, coloring spaces, and reflection pages. The activities are designed to be easy to understand, low mess, and useful at home, on trips, in restaurants, in waiting rooms, or during rainy afternoons.\n\nThis book is for parents, grandparents, and caregivers who want a ready-to-use activity book without complicated materials or setup. Children can use many pages independently, while younger children may enjoy doing them with an adult nearby.',
        'keywords': ['screen free activities for kids', 'kids activity book ages 3 8', 'quiet activities for children', 'rainy day activities for kids', 'travel activity book for kids', 'restaurant activities for kids', 'low prep kids activities'],
        'categories': ['Juvenile Nonfiction / Activity Books', 'Juvenile Nonfiction / Games & Activities', 'Family & Relationships / Activities'],
        'cover_hook': 'Screen-free calm activities for busy families',
        'cover_brief': 'Bright, clean, kid-friendly cover. Large readable title. Soft playful icons: crayons, clouds, car, puzzle pieces, smiling kids, simple shapes. White or light background. Designed for parents browsing Amazon on mobile.',
        'activity_themes': ['Draw a cozy room', 'Spot five shapes', 'Simple maze', 'Color by mood', 'Design a silly animal', 'Finish the pattern', 'Restaurant waiting game', 'Rain cloud drawing', 'Road trip bingo', 'Kind words page', 'Find and count', 'Make a tiny map', 'Complete the face', 'Trace simple lines', 'Story starter', 'Draw your snack', 'Calm breathing page', 'Design a toy', 'Weather watcher', 'Quiet challenge']
    }

# Normalize listing fields
keywords = list(data.get('keywords', []))[:7]
while len(keywords) < 7:
    keywords.append(['screen free kids activities','kids activity workbook','quiet activity book','indoor activities for kids','travel games for children','rainy day activity book','preschool activity book'][len(keywords)])

activity_themes = list(data.get('activity_themes', []))
if len(activity_themes) < 20:
    activity_themes += ['Draw and color', 'Find and count', 'Finish the picture', 'Simple maze', 'Pattern practice', 'Story starter', 'Observation game', 'Quiet challenge']

# 8.5x11 inches = 612x792 points
w, h = (612, 792)
interior = BOOK / f'{slug}-interior.pdf'
pdf = canvas.Canvas(str(interior), pagesize=(w, h))
pdf.setTitle(data.get('title', PRODUCT))

# Title page
pdf.setFont('Helvetica-Bold', 24)
pdf.drawCentredString(w / 2, 700, data.get('title', PRODUCT)[:55])
pdf.setFont('Helvetica', 14)
pdf.drawCentredString(w / 2, 665, data.get('subtitle', '')[:75])
pdf.setFont('Helvetica', 10)
pdf.drawCentredString(w / 2, 90, 'Interior generated for Amazon KDP review and manual quality check')
pdf.showPage()

# Copyright / use note page
pdf.setFont('Helvetica-Bold', 16)
pdf.drawString(50, 720, 'How to Use This Book')
pdf.setFont('Helvetica', 11)
y = 690
intro_lines = [
    'Choose any page. There is no wrong order.',
    'Use crayons, pencils, or markers depending on the page.',
    'Younger children may enjoy doing the pages with an adult nearby.',
    'Many pages are designed for quiet, low-prep moments at home or away.'
]
for line in intro_lines:
    pdf.drawString(60, y, u'• ' + line)
    y -= 28
pdf.showPage()

# Activity pages with varied layouts
random.seed(seed)
for i in range(1, PAGES + 1):
    theme = activity_themes[(i - 1) % len(activity_themes)]
    page_type = i % 6
    pdf.setFont('Helvetica-Bold', 17)
    pdf.drawString(40, 748, f'{i}. {theme}'[:65])
    pdf.setFont('Helvetica', 11)

    if page_type == 0:
        pdf.drawString(40, 710, 'Draw your idea in the big box. Add as many details as you can.')
        pdf.rect(50, 160, 512, 520)
    elif page_type == 1:
        pdf.drawString(40, 710, 'Find, count, or imagine. Write or draw your answers below.')
        labels = ['I found:', 'I counted:', 'My favorite part:', 'One more idea:']
        y = 660
        for label in labels:
            pdf.drawString(55, y, label)
            pdf.line(165, y - 3, 560, y - 3)
            y -= 80
    elif page_type == 2:
        pdf.drawString(40, 710, 'Finish the picture. Add colors, details, and a background.')
        pdf.circle(170, 520, 55)
        pdf.rect(320, 465, 120, 110)
        pdf.line(70, 300, 540, 300)
        pdf.rect(50, 160, 512, 520)
    elif page_type == 3:
        pdf.drawString(40, 710, 'Make a path from START to FINISH. Then decorate the page.')
        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(70, 650, 'START')
        pdf.drawString(470, 190, 'FINISH')
        pdf.setFont('Helvetica', 10)
        x, y = 80, 620
        for step in range(12):
            pdf.rect(x, y, 70, 35)
            x += 80 if step % 2 == 0 else -50
            y -= 38
        pdf.rect(50, 150, 512, 520)
    elif page_type == 4:
        pdf.drawString(40, 710, 'Color the shapes. Add your own pattern in the empty spaces.')
        y = 630
        for row in range(4):
            x = 80
            for col in range(5):
                if (row + col) % 3 == 0:
                    pdf.circle(x, y, 24)
                elif (row + col) % 3 == 1:
                    pdf.rect(x - 22, y - 22, 44, 44)
                else:
                    pdf.line(x - 24, y - 24, x + 24, y + 24)
                    pdf.line(x + 24, y - 24, x - 24, y + 24)
                x += 95
            y -= 105
    else:
        pdf.drawString(40, 710, 'Tell a tiny story. Draw the beginning, middle, and end.')
        sections = [('Beginning', 600), ('Middle', 410), ('End', 220)]
        for label, yy in sections:
            pdf.setFont('Helvetica-Bold', 12)
            pdf.drawString(55, yy + 130, label)
            pdf.rect(55, yy, 500, 120)
            pdf.setFont('Helvetica', 10)

    pdf.showPage()

pdf.save()

# Files per book
(BOOK / 'title-subtitle.txt').write_text(data.get('title', PRODUCT) + '\n' + data.get('subtitle', ''), encoding='utf-8')
(BOOK / 'description.txt').write_text(data.get('description', ''), encoding='utf-8')
(BOOK / 'keywords.txt').write_text('\n'.join(keywords), encoding='utf-8')
(BOOK / 'categories.txt').write_text('\n'.join(data.get('categories', [])), encoding='utf-8')
(BOOK / 'cover-brief.txt').write_text(
    f"Title: {data.get('title', PRODUCT)}\nSubtitle: {data.get('subtitle', '')}\nHook: {data.get('cover_hook', '')}\nTrim: {TRIM}\nAudience: {AUDIENCE}\n\nVisual brief:\n{data.get('cover_brief', '')}\n", encoding='utf-8'
)
(BOOK / 'kdp-upload-checklist.txt').write_text(
    'KDP upload checklist\n\n'
    '1. Review the interior PDF manually before upload.\n'
    '2. Create or upload a cover using the cover brief.\n'
    '3. Use title-subtitle.txt for title fields.\n'
    '4. Use description.txt for Amazon description.\n'
    '5. Use keywords.txt as the 7 KDP keyword boxes.\n'
    '6. Choose the closest available KDP categories.\n'
    '7. Order/preview proof before publishing.\n', encoding='utf-8'
)
(BOOK / 'metadata.json').write_text(json.dumps({
    'product': PRODUCT,
    'slug': slug,
    'folder': f'generated-output/books/{slug}',
    'trim_size': TRIM,
    'pages': PAGES,
    'generated_with_gemini': bool(os.getenv('GEMINI_API_KEY')),
    'interior_pdf': f'{slug}-interior.pdf'
}, indent=2), encoding='utf-8')

# Index file in books root
(BOOKS_ROOT / 'LATEST_BOOK.txt').write_text(f'{slug}\n{PRODUCT}\n', encoding='utf-8')
print('Kids KDP book generated:', f'books/{slug}')
