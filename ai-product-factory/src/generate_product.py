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

w,h=(432,648)  # 6x9 KDP interior
M=36
RIGHT=w-M

def header(pdf,title,page=None):
    pdf.setFont('Helvetica-Bold',14)
    pdf.drawString(M,610,title.upper()[:36])
    pdf.setLineWidth(1)
    pdf.line(M,598,RIGHT,598)
    if page:
        pdf.setFont('Helvetica',8)
        pdf.drawRightString(RIGHT,615,str(page))

def box(pdf,x,y,width,height,label):
    pdf.setLineWidth(1)
    pdf.roundRect(x,y,width,height,6,stroke=1,fill=0)
    pdf.setFont('Helvetica-Bold',8)
    pdf.drawString(x+8,y+height-14,label.upper())

def lined_box(pdf,x,y,width,height,label,lines=3):
    box(pdf,x,y,width,height,label)
    gap=(height-28)/max(lines,1)
    yy=y+height-28
    pdf.setLineWidth(.5)
    for _ in range(lines):
        pdf.line(x+8,yy,x+width-8,yy)
        yy-=gap

def daily_page(pdf,n):
    header(pdf,'Daily Action Page',n)
    lined_box(pdf,M,500,360,75,"Today's Focus",2)
    lined_box(pdf,M,400,170,75,'Main Action',2)
    lined_box(pdf,M+190,400,170,75,'Time / Energy',2)
    lined_box(pdf,M,285,360,90,'Result / Proof of Progress',3)
    lined_box(pdf,M,185,170,75,'Obstacle',2)
    lined_box(pdf,M+190,185,170,75,'Next Step',2)
    pdf.setFont('Helvetica',8)
    pdf.drawString(M,150,'Tiny rule: one useful action beats ten vague plans.')

def idea_page(pdf,n):
    header(pdf,'Idea Validation',n)
    lined_box(pdf,M,510,360,70,'Idea',2)
    lined_box(pdf,M,420,110,65,'Effort',2)
    lined_box(pdf,M+125,420,110,65,'Money Potential',2)
    lined_box(pdf,M+250,420,110,65,'Fastest Test',2)
    lined_box(pdf,M,290,360,100,'Who would pay for this and why?',4)
    lined_box(pdf,M,185,360,75,'First 24-hour action',3)

def tracker_page(pdf,n):
    header(pdf,'Action Tracker',n)
    pdf.setFont('Helvetica-Bold',8)
    cols=[M,92,190,280,350]
    labels=['Date','Action','Platform','Outcome','Next']
    for x,l in zip(cols,labels): pdf.drawString(x,565,l)
    pdf.setLineWidth(.8)
    y=550
    for _ in range(12):
        pdf.line(M,y,RIGHT,y)
        y-=32
    for x in [86,184,274,344]:
        pdf.line(x,570,x,166)

def weekly_page(pdf,n):
    header(pdf,'Weekly Review',n)
    lined_box(pdf,M,505,360,70,'Biggest win',2)
    lined_box(pdf,M,405,360,75,'What worked?',3)
    lined_box(pdf,M,305,360,75,"What did not work?",3)
    lined_box(pdf,M,205,170,70,'Double down on',2)
    lined_box(pdf,M+190,205,170,70,'Stop doing',2)
    lined_box(pdf,M,125,360,55,'Next week focus',2)

def money_snapshot(pdf,n):
    header(pdf,'Money Snapshot',n)
    fields=[('Income idea',505),('Expected first small win',445),('Cost to test',385),('How I will find buyers/readers/users',325),('What I learned',240)]
    for label,y in fields:
        lined_box(pdf,M,y,360,50,label,1)
    pdf.setFont('Helvetica-Bold',10)
    pdf.drawString(M,180,'Score this idea')
    for i,label in enumerate(['Easy','Fast','Useful','Worth repeating']):
        pdf.rect(M+i*90,145,18,18)
        pdf.setFont('Helvetica',8); pdf.drawString(M+24+i*90,149,label)

pdf=canvas.Canvas(str(BOOK/f'{slug}-interior.pdf'),pagesize=(w,h))
pdf.setTitle(PRODUCT)
pdf.setFont('Helvetica-Bold',20); pdf.drawCentredString(w/2,505,PRODUCT[:40])
pdf.setFont('Helvetica',11); pdf.drawCentredString(w/2,475,subtitle)
pdf.setFont('Helvetica',9); pdf.drawCentredString(w/2,90,'A simple planner for focused action and visible progress')
pdf.showPage()

pdf.setFont('Helvetica-Bold',16); pdf.drawString(M,560,'How to use this planner')
pdf.setFont('Helvetica',10)
intro=['Pick one goal for the week.','Use daily pages for one clear action.','Track real actions, not wishes.','Review what worked every week.','Repeat the simplest thing that creates progress.']
y=520
for item in intro:
    pdf.drawString(M,y,'• '+item); y-=28
pdf.showPage()

for i in range(1,121):
    t=i%5
    if t==0: daily_page(pdf,i)
    elif t==1: idea_page(pdf,i)
    elif t==2: tracker_page(pdf,i)
    elif t==3: weekly_page(pdf,i)
    else: money_snapshot(pdf,i)
    pdf.showPage()
pdf.save()

prompt=f'Amazon KDP book cover, minimal premium productivity planner design, bold typography, title {PRODUCT}, subtitle {subtitle}, clean modern, high perceived value, professional, no clutter'
cover_created=False
try:
    from google import genai
    from google.genai import types
    client=genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    resp=client.models.generate_images(model='imagen-4.0-generate-001',prompt=prompt,config=types.GenerateImagesConfig(number_of_images=1,aspect_ratio='3:4'))
    resp.generated_images[0].image.save(BOOK/f'{slug}-cover-front.png')
    cover_created=True
except Exception:
    img=Image.new('RGB',(1600,2560),(250,250,247))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle((120,120,1480,2440),radius=40,outline=(20,20,20),width=8)
    d.text((180,360),PRODUCT[:30],fill=(0,0,0))
    d.text((180,470),subtitle[:44],fill=(70,70,70))
    d.line((180,650,1420,650),fill=(0,0,0),width=4)
    img.save(BOOK/f'{slug}-cover-front.png')

base=Image.open(BOOK/f'{slug}-cover-front.png')
thumb=base.copy(); thumb.thumbnail((300,480)); thumb.save(BOOK/'thumbnail-preview.png')
mobile=base.copy(); mobile.thumbnail((220,352)); mobile.save(BOOK/'amazon-mobile-preview.png')

(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\n'+subtitle,encoding='utf-8')
(BOOK/'description.txt').write_text(f'{PRODUCT} helps {AUDIENCE} turn vague goals into simple daily actions. Inside are structured pages for daily focus, idea validation, action tracking, money snapshots, and weekly reviews. The layout is intentionally simple so you can see what matters, act quickly, and build momentum without overwhelm.',encoding='utf-8')
(BOOK/'keywords.txt').write_text('side hustle planner\nmake money planner\nproductivity planner\naction tracker\nonline income planner\nweekly review journal\nfreelance logbook',encoding='utf-8')
(BOOK/'categories.txt').write_text('Business & Money / Entrepreneurship\nSelf-Help / Personal Transformation\nBusiness & Money / Personal Finance',encoding='utf-8')
(BOOK/'quality-check-report.txt').write_text('LAYOUT ENGINE V1\n\nInterior upgraded with structured boxes, tracker tables, review pages, idea validation pages and money snapshots.\n\nManual checks:\n- Open interior PDF.\n- Check margins in KDP previewer.\n- Check cover title spelling.\n- Confirm page count and trim size.\n',encoding='utf-8')
(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'type':'money_kdp','layout_engine':'v1','pages':122,'cover_generated':cover_created,'folder':f'generated-output/books/{slug}'},indent=2),encoding='utf-8')
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n',encoding='utf-8')
print('Money Layout Engine V1 generated:',slug)
