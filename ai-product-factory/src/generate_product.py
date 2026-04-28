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

# STRONG INTRO
pdf.setFont('Helvetica-Bold',18)
pdf.drawCentredString(w/2,500,PRODUCT[:40])
pdf.setFont('Helvetica',11)
pdf.drawCentredString(w/2,470,subtitle)
pdf.showPage()

pdf.setFont('Helvetica-Bold',14)
pdf.drawString(36,580,'Stop Planning. Start Moving.')
pdf.setFont('Helvetica',10)
intro=[
 'This is not a planner full of empty pages.',
 'This is a system designed to force progress.',
 'You only need ONE action per day.',
 'Small actions → momentum → results.',
 'Do not skip. Do not overthink. Just act.'
]
y=540
for i in intro:
    pdf.drawString(36,y,'- '+i)
    y-=25
pdf.showPage()

# 30 DAY STRUCTURE WITH PROGRESSION
for day in range(1,31):
    pdf.setFont('Helvetica-Bold',14)
    pdf.drawString(36,600,f'Day {day}')

    pdf.setFont('Helvetica-Bold',10)
    pdf.drawString(36,560,'YOUR FOCUS')

    pdf.setFont('Helvetica',10)

    if day <= 5:
        prompt='Do something small. Remove friction. What is the easiest possible useful action?'
    elif day <= 15:
        prompt='Now push slightly harder. What action creates real-world feedback?'
    elif day <= 25:
        prompt='Focus on repetition. What can you do again that already worked?'
    else:
        prompt='Focus on results. What action directly leads to money or output?'

    pdf.drawString(36,540,prompt)

    pdf.drawString(36,500,'Your action:')
    pdf.line(36,480,396,480)

    pdf.drawString(36,450,'Result (what actually happened?):')
    pdf.line(36,430,396,430)

    pdf.drawString(36,400,'What did you learn?')
    pdf.line(36,380,396,380)

    pdf.drawString(36,350,'Next step (tomorrow):')
    pdf.line(36,330,396,330)

    pdf.showPage()

# WEEKLY REVIEWS WITH DEPTH
for w_i in range(1,5):
    pdf.setFont('Helvetica-Bold',14)
    pdf.drawString(36,600,f'Weekly Reset {w_i}')
    pdf.setFont('Helvetica',10)

    pdf.drawString(36,560,'What actually worked? (not what felt productive)')
    pdf.line(36,540,396,540)

    pdf.drawString(36,500,'What wasted time?')
    pdf.line(36,480,396,480)

    pdf.drawString(36,440,'What should you repeat next week?')
    pdf.line(36,420,396,420)

    pdf.drawString(36,380,'What will you cut completely?')
    pdf.line(36,360,396,360)

    pdf.showPage()

pdf.save()

# BETTER SALES TEXT
(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\n'+subtitle)

(BOOK/'description.txt').write_text(
 f"{PRODUCT} is not just another planner. It is a 30-day execution system designed for {AUDIENCE} who are tired of overthinking and want real progress.\n\nInstead of empty pages, you get guided daily prompts that force action, weekly resets that eliminate wasted effort, and a simple structure that builds momentum fast.\n\nIf you struggle to follow through, this system fixes that.")

(BOOK/'keywords.txt').write_text(
 '30 day planner\nmake money planner\nexecution system\naction planner\nside hustle system\nfocus journal\nproductivity system'
)

(BOOK/'metadata.json').write_text(json.dumps({
 'product':PRODUCT,
 'engine':'system_v2',
 'days':30,
 'progression':True
},indent=2))

(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n')

print('System Engine V2 LIVE:',slug)
