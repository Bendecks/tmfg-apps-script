import os, json, textwrap, re
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / 'dist'
DIST.mkdir(exist_ok=True)
for p in DIST.glob('*'):
    if p.is_file(): p.unlink()

config = json.loads((BASE/'config'/'product.json').read_text())
rotation = config.get('rotation', [])
seed = int(datetime.utcnow().strftime('%Y%m%d'))
selected = rotation[seed % len(rotation)] if rotation else {'product_name':'Notebook','audience':'buyers','niche':'general'}
PRODUCT = selected['product_name']
AUDIENCE = selected['audience']
NICHE = selected['niche']
TRIM = config.get('trim_size','6x9')
PAGES = int(config.get('page_target',120))

slug = re.sub(r'[^a-z0-9]+','-',PRODUCT.lower()).strip('-')

def gemini(prompt):
    key=os.getenv('GEMINI_API_KEY')
    if not key: return ''
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model=genai.GenerativeModel('gemini-2.0-flash')
        r=model.generate_content(prompt)
        return (r.text or '').strip()
    except:
        return ''

prompt=f'''Return ONLY valid JSON. Create Amazon KDP listing assets for a low-content/high-value workbook. Product: {PRODUCT}. Audience: {AUDIENCE}. Niche: {NICHE}. Schema: {{"title":"x","subtitle":"x","description":"x","keywords":["x"],"categories":["x"],"chapters":["x"],"cover_hook":"x"}}'''
raw=gemini(prompt)
try:
    if raw.startswith('```'): raw=raw.replace('```json','').replace('```','').strip()
    data=json.loads(raw)
except:
    data={
      'title':PRODUCT,
      'subtitle':f'A practical workbook for {AUDIENCE}',
      'description':f'{PRODUCT} helps {AUDIENCE} take consistent action in {NICHE}.',
      'keywords':[PRODUCT.lower(), NICHE, 'workbook'],
      'categories':['Self-Help','Business'],
      'chapters':['Introduction','Goals','Daily Plan','Weekly Review'],
      'cover_hook':'Simple practical workbook'
    }

# Interior PDF (6x9 approx 432x648 points)
width,height=(432,648)
pdf=canvas.Canvas(str(DIST/f'{slug}-interior.pdf'), pagesize=(width,height))
# Front matter
pdf.setFont('Helvetica-Bold',18); pdf.drawCentredString(width/2,500,data['title'][:45])
pdf.setFont('Helvetica',11); pdf.drawCentredString(width/2,470,data['subtitle'][:60])
pdf.showPage()

# Generate workbook pages
for i in range(1,PAGES+1):
    pdf.setFont('Helvetica-Bold',12)
    pdf.drawString(36,620,f'{data["title"][:30]} | Page {i}')
    pdf.setFont('Helvetica',10)
    y=590
    prompts=[
      'Today I will focus on:',
      'One action that moves me forward:',
      'Biggest obstacle today:',
      'How I will respond:',
      'Wins today:',
      'Next step tomorrow:'
    ]
    for t in prompts:
        pdf.drawString(36,y,t)
        y-=22
        pdf.line(36,y,396,y)
        y-=24
    if i % 10 == 0:
        pdf.showPage(); pdf.setFont('Helvetica-Bold',16); pdf.drawString(36,620,'Weekly Review')
        y=580
        for _ in range(8):
            pdf.line(36,y,396,y); y-=28
    pdf.showPage()
pdf.save()

# Metadata files
(DIST/'title-subtitle.txt').write_text(data['title']+'\n'+data['subtitle'],encoding='utf-8')
(DIST/'description.txt').write_text(data['description'],encoding='utf-8')
(DIST/'keywords.txt').write_text('\n'.join(data['keywords']),encoding='utf-8')
(DIST/'categories.txt').write_text('\n'.join(data['categories']),encoding='utf-8')
(DIST/'cover-brief.txt').write_text(f"Title: {data['title']}\nSubtitle: {data['subtitle']}\nHook: {data['cover_hook']}\nTrim: {TRIM}\nAudience: {AUDIENCE}",encoding='utf-8')
(DIST/'metadata.json').write_text(json.dumps({'product':PRODUCT,'niche':NICHE,'audience':AUDIENCE,'trim_size':TRIM,'page_target':PAGES,'generated_with_gemini':bool(os.getenv('GEMINI_API_KEY'))},indent=2),encoding='utf-8')
print('KDP package generated')
