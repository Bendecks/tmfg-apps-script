import os, json, re
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas

BASE=Path(__file__).resolve().parents[1]
DIST=BASE/'dist'
BOOKS_ROOT=DIST/'books'
BOOKS_ROOT.mkdir(parents=True,exist_ok=True)
config=json.loads((BASE/'config'/'product.json').read_text())
rotation=config.get('rotation',[])
seed=int(datetime.utcnow().strftime('%Y%m%d'))
selected=rotation[seed % len(rotation)] if rotation else {}
PRODUCT=selected.get('product_name','Planner')
AUDIENCE=selected.get('audience','people')
slug=re.sub(r'[^a-z0-9]+','-',PRODUCT.lower()).strip('-')
BOOK=BOOKS_ROOT/slug
BOOK.mkdir(parents=True,exist_ok=True)
for f in BOOK.glob('*'):
    if f.is_file(): f.unlink()

subtitle='A 30-Day Action System (Not Just a Planner)'

w,h=(432,648)
pdf=canvas.Canvas(str(BOOK/f'{slug}-interior.pdf'),pagesize=(w,h))

# ===== HOOK PAGES =====
pdf.setFont('Helvetica-Bold',18)
pdf.drawCentredString(w/2,500,PRODUCT[:40])
pdf.setFont('Helvetica',11)
pdf.drawCentredString(w/2,470,subtitle)
pdf.showPage()

pdf.setFont('Helvetica-Bold',16)
pdf.drawString(36,560,'This Only Works If You Do This')
pdf.setFont('Helvetica',10)
rules=[
 'You commit to ONE action daily.',
 'You stop planning and start executing.',
 'You track real actions, not ideas.',
 'You accept imperfect progress.',
 'You do not skip days.'
]
y=520
for r in rules:
    pdf.drawString(36,y,'• '+r); y-=24
pdf.showPage()

pdf.setFont('Helvetica-Bold',16)
pdf.drawString(36,560,'Your Commitment')
pdf.setFont('Helvetica',10)
pdf.drawString(36,520,'If you follow this for 30 days, your situation WILL change.')
pdf.line(36,480,396,480)
pdf.drawString(36,460,'Signature:')
pdf.line(36,440,200,440)
pdf.drawString(36,400,'Start Date:')
pdf.line(36,380,200,380)
pdf.showPage()

# ===== SYSTEM WITH VISUAL STRUCTURE =====
for day in range(1,31):
    pdf.setFont('Helvetica-Bold',14)
    pdf.drawString(36,600,f'Day {day}')

    pdf.setLineWidth(1)
    pdf.rect(36,520,360,60)
    pdf.setFont('Helvetica-Bold',10)
    pdf.drawString(42,565,'FOCUS')

    pdf.setFont('Helvetica',10)
    if day <= 5:
        prompt='Small action. Remove friction.'
    elif day <= 15:
        prompt='Action that creates feedback.'
    elif day <= 25:
        prompt='Repeat what worked.'
    else:
        prompt='Focus on results.'

    pdf.drawString(42,540,prompt)

    # Action box
    pdf.rect(36,430,360,60)
    pdf.drawString(42,470,'Your action:')

    # Result box
    pdf.rect(36,340,360,60)
    pdf.drawString(42,380,'Result:')

    # Learning box
    pdf.rect(36,250,360,60)
    pdf.drawString(42,290,'What did you learn?')

    # Variation every 3rd day
    if day % 3 == 0:
        pdf.rect(36,170,360,50)
        pdf.drawString(42,200,'What would make this easier tomorrow?')

    pdf.showPage()

# ===== WEEKLY RESET WITH MORE FEEL =====
for w_i in range(1,5):
    pdf.setFont('Helvetica-Bold',14)
    pdf.drawString(36,600,f'Weekly Reset {w_i}')

    sections=[
        'Biggest win',
        'What actually worked',
        'What wasted time',
        'What to repeat',
        'What to eliminate'
    ]

    y=550
    for s in sections:
        pdf.rect(36,y,360,50)
        pdf.drawString(42,y+30,s)
        y-=70

    pdf.showPage()

pdf.save()

# SALES FILES
(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\n'+subtitle)

(BOOK/'description.txt').write_text(
 f"{PRODUCT} is a 30-day execution system for {AUDIENCE}.\n\nThis is not a passive planner. It forces action.\n\nEach page is designed to remove overthinking, guide decisions, and build momentum fast.\n\nIf you want progress instead of planning, this is for you.")

(BOOK/'keywords.txt').write_text(
 'execution planner\naction system\n30 day planner\nproductivity system\nside hustle planner\nfocus journal\nmomentum system'
)

(BOOK/'metadata.json').write_text(json.dumps({
 'product':PRODUCT,
 'engine':'product_feel_v1',
 'system':True
},indent=2))

(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n')

print('Product Feel Engine LIVE:',slug)
