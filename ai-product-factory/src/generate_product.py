import os, json, re
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

BASE=Path(__file__).resolve().parents[1]
DIST=BASE/'dist'; BOOKS_ROOT=DIST/'books'; BOOKS_ROOT.mkdir(parents=True,exist_ok=True)
config=json.loads((BASE/'config'/'product.json').read_text())
rotation=config.get('rotation',[])
seed=int(datetime.utcnow().strftime('%Y%m%d'))
selected=rotation[seed % len(rotation)] if rotation else {}
PRODUCT=selected.get('product_name','Kids Activity Book')
slug=re.sub(r'[^a-z0-9]+','-',PRODUCT.lower()).strip('-')
BOOK=BOOKS_ROOT/slug; BOOK.mkdir(parents=True,exist_ok=True)
for f in BOOK.glob('*'):
    if f.is_file(): f.unlink()
subtitle='Screen-Free Activities for Home, Travel, and Rainy Days'
# basic interior placeholder
w,h=(612,792)
pdf=canvas.Canvas(str(BOOK/f'{slug}-interior.pdf'),pagesize=(w,h))
pdf.setFont('Helvetica-Bold',24); pdf.drawCentredString(w/2,700,PRODUCT[:50]); pdf.showPage(); pdf.save()
# cover pdf draft
cover=canvas.Canvas(str(BOOK/f'{slug}-cover-draft.pdf'),pagesize=(w,h))
cover.setFont('Helvetica-Bold',28); cover.drawCentredString(w/2,690,PRODUCT[:38]); cover.setFont('Helvetica',14); cover.drawCentredString(w/2,650,subtitle[:70]); cover.save()
# png covers
size=(1600,2560)
for idx,name in enumerate(['cover-front','cover-variant-a','cover-variant-b']):
    img=Image.new('RGB',size,(255,255,255) if idx==0 else ((245,250,255) if idx==1 else (255,248,240)))
    d=ImageDraw.Draw(img)
    d.rectangle((80,80,1520,2480), outline=(0,0,0), width=6)
    d.ellipse((120,1700,420,2000), outline=(0,0,0), width=5)
    d.rectangle((620,1700,980,2050), outline=(0,0,0), width=5)
    d.polygon([(1200,2000),(1320,1700),(1440,2000)], outline=(0,0,0))
    d.text((120,180), PRODUCT[:32], fill=(0,0,0))
    d.text((120,260), subtitle[:44], fill=(0,0,0))
    d.text((120,2350), 'Ages 3-8', fill=(0,0,0))
    img.save(BOOK/f'{slug}-{name}.png')
# thumbnails
thumb=Image.open(BOOK/f'{slug}-cover-front.png'); thumb.thumbnail((300,480)); thumb.save(BOOK/'thumbnail-preview.png')
mobile=Image.open(BOOK/f'{slug}-cover-front.png'); mobile.thumbnail((220,352)); mobile.save(BOOK/'amazon-mobile-preview.png')
# text files
(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\n'+subtitle,encoding='utf-8')
(BOOK/'description.txt').write_text(PRODUCT+' gives families ready-to-use quiet activities for travel, home, restaurants, and rainy days.',encoding='utf-8')
(BOOK/'keywords.txt').write_text('kids activity book\nquiet activities for kids\ntravel activity book\nrainy day kids book\nscreen free activities\nrestaurant kids activities\nindoor activity book',encoding='utf-8')
(BOOK/'quality-check-report.txt').write_text('COVER DOMINATION MODE\n\nFiles created:\n- cover-front.png\n- cover-variant-a.png\n- cover-variant-b.png\n- thumbnail-preview.png\n- amazon-mobile-preview.png\n\nManual checks:\n- Is title readable as thumbnail?\n- Is subtitle too small?\n- Does cover stand out vs competitors?\n',encoding='utf-8')
(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'folder':f'generated-output/books/{slug}','cover_assets':5,'interior_pdf':f'{slug}-interior.pdf'},indent=2),encoding='utf-8')
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n',encoding='utf-8')
print('Cover Domination package generated:',slug)
