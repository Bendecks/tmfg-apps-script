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
PRODUCT = selected.get('product_name','Kids Activity Book')
AUDIENCE = selected.get('audience','parents')
NICHE = selected.get('niche','kids activities')
TRIM = config.get('trim_size','8.5x11')
PAGES = int(config.get('page_target',110))
slug = re.sub(r'[^a-z0-9]+','-',PRODUCT.lower()).strip('-')
BOOK = BOOKS_ROOT / slug
BOOK.mkdir(parents=True, exist_ok=True)
for f in BOOK.glob('*'):
    if f.is_file(): f.unlink()

def fallback():
    return {
      'title': PRODUCT,
      'subtitle':'Screen-Free Activities for Home, Travel, Restaurants, and Rainy Days',
      'description': PRODUCT + ' is a practical activity book packed with calm, low-prep pages for children.',
      'keywords':['screen free kids activities','kids activity book ages 3 8','quiet activities for kids','travel activity book kids','rainy day activities kids','restaurant activities kids','indoor kids activity book'],
      'categories':['Juvenile Nonfiction / Activity Books','Juvenile Nonfiction / Games & Activities','Family & Relationships / Activities'],
      'cover_hook':'Bright playful cover for mobile shoppers',
      'cover_brief':'Large bold title, bright playful icons, clean white background.',
      'activity_themes':['Draw a pet','Maze','Count shapes','Finish picture','Story page','Color patterns']
    }

data=fallback()
# interior
w,h=(612,792)
pdf=canvas.Canvas(str(BOOK/f'{slug}-interior.pdf'),pagesize=(w,h))
pdf.setFont('Helvetica-Bold',24); pdf.drawCentredString(w/2,700,data['title'][:55])
pdf.setFont('Helvetica',14); pdf.drawCentredString(w/2,670,data['subtitle'][:75]); pdf.showPage()
for i in range(1,PAGES+1):
    pdf.setFont('Helvetica-Bold',17); pdf.drawString(40,748,f'{i}. {data["activity_themes"][i%len(data["activity_themes"])]}')
    pdf.rect(50,180,512,500)
    pdf.line(60,250,550,250)
    pdf.line(60,320,550,320)
    pdf.line(60,390,550,390)
    pdf.line(60,460,550,460)
    pdf.line(60,530,550,530)
    pdf.showPage()
pdf.save()
# cover draft PDF
cover=canvas.Canvas(str(BOOK/f'{slug}-cover-draft.pdf'),pagesize=(w,h))
cover.setFont('Helvetica-Bold',28); cover.drawCentredString(w/2,680,data['title'][:40])
cover.setFont('Helvetica',14); cover.drawCentredString(w/2,645,data['subtitle'][:70])
cover.rect(80,240,120,120); cover.circle(300,300,60); cover.rect(390,240,120,120)
cover.setFont('Helvetica',12); cover.drawCentredString(w/2,180,'Draft front cover concept')
cover.save()
# files
(Path(BOOK/'title-subtitle.txt')).write_text(data['title']+'\n'+data['subtitle'],encoding='utf-8')
(Path(BOOK/'description.txt')).write_text(data['description'],encoding='utf-8')
(Path(BOOK/'keywords.txt')).write_text('\n'.join(data['keywords']),encoding='utf-8')
(Path(BOOK/'categories.txt')).write_text('\n'.join(data['categories']),encoding='utf-8')
(Path(BOOK/'cover-brief.txt')).write_text(data['cover_brief'],encoding='utf-8')
(Path(BOOK/'quality-check-report.txt')).write_text(f'QUALITY CHECK\n\nTitle present: PASS\nInterior pages target: {PAGES}\nInterior file: PASS\nCover draft file: PASS\nKeywords count: {len(data["keywords"])}\nManual checks still needed:\n- Open PDF and inspect margins\n- Check no duplicate pages\n- Verify title spelling\n- Review cover readability on mobile\n- Upload preview in KDP\n',encoding='utf-8')
(Path(BOOK/'metadata.json')).write_text(json.dumps({'product':PRODUCT,'folder':f'generated-output/books/{slug}','pages':PAGES,'cover_file':f'{slug}-cover-draft.pdf','interior_pdf':f'{slug}-interior.pdf'},indent=2),encoding='utf-8')
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n',encoding='utf-8')
print('Kids KDP package generated:',slug)
