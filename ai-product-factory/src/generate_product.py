import os, json, re, textwrap
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / 'dist'
DIST.mkdir(exist_ok=True)
config = json.loads((BASE/'config'/'product.json').read_text())
rotation = config.get('rotation', [])
seed = int(datetime.utcnow().strftime('%Y%m%d'))
selected = rotation[seed % len(rotation)] if rotation else {}
PRODUCT = selected.get('product_name','Kids Activity Book')
AUDIENCE = selected.get('audience','parents')
NICHE = selected.get('niche','kids activities')
TRIM = config.get('trim_size','8.5x11')
PAGES = int(config.get('page_target',110))

def slugify(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
slug = slugify(PRODUCT)
BOOK = DIST / slug
BOOK.mkdir(exist_ok=True)

def gemini(prompt):
 key=os.getenv('GEMINI_API_KEY')
 if not key: return ''
 try:
  import google.generativeai as genai
  genai.configure(api_key=key)
  r=genai.GenerativeModel('gemini-2.0-flash').generate_content(prompt)
  return (r.text or '').strip()
 except: return ''

raw=gemini(f'Return only JSON with title,subtitle,description,keywords,categories,cover_hook for {PRODUCT} in niche {NICHE}')
try:
 import json as j
 if raw.startswith('```'): raw=raw.replace('```json','').replace('```','').strip()
 data=j.loads(raw)
except:
 data={'title':PRODUCT,'subtitle':'Fun screen-free activities for children','description':f'{PRODUCT} gives families fun low-mess activities.','keywords':['kids activity book','quiet activities','screen free kids'],'categories':['Juvenile Nonfiction','Activity Books'],'cover_hook':'Bright playful cover with happy kids icons'}

# 8.5x11 inches = 612x792 points
w,h=(612,792)
pdf=canvas.Canvas(str(BOOK/f'{slug}-interior.pdf'), pagesize=(w,h))
# title page
pdf.setFont('Helvetica-Bold',24); pdf.drawCentredString(w/2,700,data['title'][:50])
pdf.setFont('Helvetica',14); pdf.drawCentredString(w/2,670,data['subtitle'][:70])
pdf.showPage()
for i in range(1,PAGES+1):
 pdf.setFont('Helvetica-Bold',16)
 pdf.drawString(40,760,f'Activity Page {i}')
 pdf.setFont('Helvetica',12)
 y=720
 blocks=[
 'Draw your favorite animal.',
 'Circle 5 things you can see today.',
 'Write 3 kind words.',
 'Maze path: Start to Finish.',
 'Color something blue, red, and green.',
 'Tell a grown-up your best idea.'
 ]
 for b in blocks:
  for line in textwrap.wrap(b,60):
   pdf.drawString(40,y,line); y-=22
  pdf.rect(40,y-120,520,100)
  y-=150
  if y<120: break
 pdf.showPage()
pdf.save()

(BOOK/'title-subtitle.txt').write_text(data['title']+'\n'+data['subtitle'],encoding='utf-8')
(BOOK/'description.txt').write_text(data['description'],encoding='utf-8')
(BOOK/'keywords.txt').write_text('\n'.join(data['keywords']),encoding='utf-8')
(BOOK/'categories.txt').write_text('\n'.join(data['categories']),encoding='utf-8')
(BOOK/'cover-brief.txt').write_text(f"Title: {data['title']}\nSubtitle: {data['subtitle']}\nHook: {data['cover_hook']}\nTrim: {TRIM}\nAudience: {AUDIENCE}",encoding='utf-8')
(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'slug':slug,'trim_size':TRIM,'pages':PAGES,'generated_with_gemini':bool(os.getenv('GEMINI_API_KEY'))},indent=2),encoding='utf-8')
print('Kids KDP book generated:', slug)
