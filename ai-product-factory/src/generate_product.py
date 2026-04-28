import os, json, re
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw

BASE=Path(__file__).resolve().parents[1]
DIST=BASE/'dist'
BOOKS_ROOT=DIST/'books'
BOOKS_ROOT.mkdir(parents=True,exist_ok=True)
config=json.loads((BASE/'config'/'product.json').read_text())
rotation=config.get('rotation',[])
seed=int(datetime.utcnow().strftime('%Y%m%d'))
selected=rotation[seed % len(rotation)] if rotation else {}
PRODUCT=selected.get('product_name','Kids Activity Book')
slug=re.sub(r'[^a-z0-9]+','-',PRODUCT.lower()).strip('-')
BOOK=BOOKS_ROOT/slug
BOOK.mkdir(parents=True,exist_ok=True)
for f in BOOK.glob('*'):
    if f.is_file(): f.unlink()
subtitle='Screen-Free Activities for Home, Travel, and Rainy Days'
# interior placeholder
w,h=(612,792)
pdf=canvas.Canvas(str(BOOK/f'{slug}-interior.pdf'),pagesize=(w,h))
pdf.setFont('Helvetica-Bold',24)
pdf.drawCentredString(w/2,700,PRODUCT[:50])
pdf.showPage()
pdf.save()
# cleaner placeholder cover png
size=(1600,2560)
img=Image.new('RGB',size,(255,255,255))
d=ImageDraw.Draw(img)
d.rounded_rectangle((70,70,1530,2490),radius=30,outline=(20,20,20),width=8)
d.rounded_rectangle((120,1500,1480,2200),radius=40,outline=(80,80,80),width=4)
d.text((140,180),PRODUCT[:34],fill=(0,0,0))
d.text((140,280),subtitle[:46],fill=(70,70,70))
d.text((140,2340),'Ages 3-8',fill=(0,0,0))
img.save(BOOK/f'{slug}-cover-front.png')
thumb=img.copy(); thumb.thumbnail((300,480)); thumb.save(BOOK/'thumbnail-preview.png')
mobile=img.copy(); mobile.thumbnail((220,352)); mobile.save(BOOK/'amazon-mobile-preview.png')
# AI prompt assets
prompt=f'''Create a premium Amazon KDP kids activity book cover. Vertical 8.5x11 ratio. Title: {PRODUCT}. Subtitle: {subtitle}. Audience: parents buying for ages 3-8. Style: bold readable typography, bright modern playful colors, clean white space, cheerful kid-friendly icons, professional bestselling Amazon thumbnail look, highly readable on mobile, no clutter, no watermark. Include subtle activity elements like puzzle pieces, crayons, stars, road trip / rainy day hints if relevant.'''
(BOOK/'gemini-cover-prompt.txt').write_text(prompt,encoding='utf-8')
(BOOK/'canva-cover-brief.txt').write_text('Use Kids Book Cover template. Large bold title top third. Subtitle smaller. Bright accent colors. Clean background. Add 3 playful icons. Ensure thumbnail readability.',encoding='utf-8')
(BOOK/'cover-variants.txt').write_text('Variant A: Blue + yellow\nVariant B: Orange + teal\nVariant C: Rainbow minimal',encoding='utf-8')
# listing files
(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\n'+subtitle,encoding='utf-8')
(BOOK/'description.txt').write_text(PRODUCT+' gives families ready-to-use quiet activities for travel, home, restaurants, and rainy days.',encoding='utf-8')
(BOOK/'keywords.txt').write_text('kids activity book\nquiet activities for kids\ntravel activity book\nrainy day kids book\nscreen free activities\nrestaurant kids activities\nindoor activity book',encoding='utf-8')
(BOOK/'quality-check-report.txt').write_text('AI COVER MODE\n\nFiles created:\n- cover-front.png\n- thumbnail-preview.png\n- amazon-mobile-preview.png\n- gemini-cover-prompt.txt\n- canva-cover-brief.txt\n\nBest practice:\nGenerate final cover in Gemini/Canva using prompt file.\n',encoding='utf-8')
(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'folder':f'generated-output/books/{slug}','cover_assets':5,'ai_cover_ready':True},indent=2),encoding='utf-8')
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n',encoding='utf-8')
print('AI cover package generated:',slug)
