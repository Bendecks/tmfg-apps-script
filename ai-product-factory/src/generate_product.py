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

prompt=f'''Premium Amazon KDP kids activity book cover, vertical 3:4 ratio. Title text: {PRODUCT}. Subtitle text: {subtitle}. Bold readable typography, bright playful modern colors, clean white space, bestselling thumbnail style, cheerful icons like crayons stars puzzle pieces, no clutter, no watermark, highly readable on mobile, polished commercial design, no people.'''
(BOOK/'gemini-cover-prompt.txt').write_text(prompt,encoding='utf-8')

cover_created=False
try:
    from google import genai
    from google.genai import types
    client=genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    resp=client.models.generate_images(
        model='imagen-4.0-generate-001',
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=3, aspect_ratio='3:4')
    )
    names=['cover-front.png','cover-variant-a.png','cover-variant-b.png']
    for i,img in enumerate(resp.generated_images[:3]):
        img.image.save(BOOK/f'{slug}-{names[i]}')
    cover_created=True
except Exception as e:
    # fallback placeholder
    size=(1600,2560)
    img=Image.new('RGB',size,(255,255,255))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle((70,70,1530,2490),radius=30,outline=(20,20,20),width=8)
    d.text((140,180),PRODUCT[:34],fill=(0,0,0))
    d.text((140,280),subtitle[:46],fill=(70,70,70))
    img.save(BOOK/f'{slug}-cover-front.png')
    img.save(BOOK/f'{slug}-cover-variant-a.png')
    img.save(BOOK/f'{slug}-cover-variant-b.png')

base=Image.open(BOOK/f'{slug}-cover-front.png')
thumb=base.copy(); thumb.thumbnail((300,480)); thumb.save(BOOK/'thumbnail-preview.png')
mobile=base.copy(); mobile.thumbnail((220,352)); mobile.save(BOOK/'amazon-mobile-preview.png')

(BOOK/'canva-cover-brief.txt').write_text('Optional: refine generated cover in Canva if needed.',encoding='utf-8')
(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\n'+subtitle,encoding='utf-8')
(BOOK/'description.txt').write_text(PRODUCT+' gives families ready-to-use quiet activities for travel, home, restaurants, and rainy days.',encoding='utf-8')
(BOOK/'keywords.txt').write_text('kids activity book\nquiet activities for kids\ntravel activity book\nrainy day kids book\nscreen free activities\nrestaurant kids activities\nindoor activity book',encoding='utf-8')
(BOOK/'quality-check-report.txt').write_text('DIRECT IMAGE GENERATION MODE\n\nCheck:\n- title readable on thumbnail\n- no spelling mistakes\n- looks premium\n- compare variants\n',encoding='utf-8')
(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'folder':f'generated-output/books/{slug}','ai_cover_ready':True,'cover_generated_in_code':cover_created},indent=2),encoding='utf-8')
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n',encoding='utf-8')
print('Direct image cover package generated:',slug)
