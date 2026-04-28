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
PRODUCT=selected.get('product_name','Planner')
AUDIENCE=selected.get('audience','people')
slug=re.sub(r'[^a-z0-9]+','-',PRODUCT.lower()).strip('-')
BOOK=BOOKS_ROOT/slug
BOOK.mkdir(parents=True,exist_ok=True)
for f in BOOK.glob('*'):
    if f.is_file(): f.unlink()
subtitle='A Simple System to Take Action and See Progress'

# interior PDF
w,h=(432,648)
pdf=canvas.Canvas(str(BOOK/f'{slug}-interior.pdf'),pagesize=(w,h))
pdf.setFont('Helvetica-Bold',18)
pdf.drawCentredString(w/2,500,PRODUCT[:40])
pdf.setFont('Helvetica',11)
pdf.drawCentredString(w/2,470,subtitle)
pdf.showPage()

for i in range(1,121):
    t=i%4
    pdf.setFont('Helvetica-Bold',12)
    pdf.drawString(36,620,f'Page {i}')
    pdf.setFont('Helvetica',10)
    if t==0:
        pdf.drawString(36,580,'Today\'s Goal:'); pdf.line(36,560,396,560)
        pdf.drawString(36,520,'1 Action:'); pdf.line(36,500,396,500)
        pdf.drawString(36,460,'Result:'); pdf.line(36,440,396,440)
    elif t==1:
        pdf.drawString(36,580,'Idea:'); pdf.line(36,560,396,560)
        pdf.drawString(36,520,'Effort:'); pdf.line(36,500,396,500)
    elif t==2:
        pdf.drawString(36,580,'Action Taken:'); pdf.line(36,560,396,560)
        pdf.drawString(36,520,'Outcome:'); pdf.line(36,500,396,500)
    else:
        pdf.drawString(36,580,'Weekly Reflection:'); pdf.line(36,560,396,560)
    pdf.showPage()
pdf.save()

# cover generation (AI)
prompt=f'Amazon KDP book cover, minimal clean modern design, bold typography, title {PRODUCT}, subtitle {subtitle}, professional look'
cover_created=False
try:
    from google import genai
    from google.genai import types
    client=genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    resp=client.models.generate_images(model='imagen-4.0-generate-001',prompt=prompt,config=types.GenerateImagesConfig(number_of_images=1,aspect_ratio='3:4'))
    resp.generated_images[0].image.save(BOOK/f'{slug}-cover-front.png')
    cover_created=True
except:
    img=Image.new('RGB',(1600,2560),(255,255,255))
    d=ImageDraw.Draw(img)
    d.text((200,400),PRODUCT,fill=(0,0,0))
    img.save(BOOK/f'{slug}-cover-front.png')

# metadata
(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\n'+subtitle,encoding='utf-8')
(BOOK/'description.txt').write_text(f'{PRODUCT} helps {AUDIENCE} take action and make progress.',encoding='utf-8')
(BOOK/'keywords.txt').write_text('planner\ntracker\nproductivity\nmoney\nside hustle\ndaily planner\ngoals',encoding='utf-8')
(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'type':'money_kdp','cover_generated':cover_created},indent=2),encoding='utf-8')
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n',encoding='utf-8')
print('Money generator ready:',slug)
