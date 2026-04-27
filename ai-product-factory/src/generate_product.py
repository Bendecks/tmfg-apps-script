import os, json, csv, textwrap, zipfile, re
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / 'dist'
DIST.mkdir(exist_ok=True)
for old in DIST.glob('*'):
    old.unlink()

config = json.loads((BASE / 'config' / 'product.json').read_text())
BRAND = config.get('brand', 'Digital Product Studio')
selected = config.get('rotation', [])[0]
PRODUCT_NAME = selected['product_name']
AUDIENCE = selected['audience']
NICHE = selected['niche']
PRICE = config.get('price_usd', 9)

def slugify(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

SLUG = slugify(PRODUCT_NAME)
PRODUCT_DIR = DIST / SLUG
PRODUCT_DIR.mkdir(exist_ok=True)


def gemini(prompt:str):
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        return ''
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        r = model.generate_content(prompt)
        return (r.text or '').strip()
    except Exception as e:
        print(e)
        return ''

prompt = f'''Return ONLY valid JSON. Build a Gumroad-ready digital product package.
Product: {PRODUCT_NAME}
Niche: {NICHE}
Audience: {AUDIENCE}
Price: ${PRICE}

The buyer must feel they are getting a complete usable kit, not loose text files.

JSON schema:
{{
 "title":"string",
 "subtitle":"string",
 "guide_sections":[{{"heading":"string","body":"string"}}],
 "checklist_items":["string"],
 "action_plan_days":[{{"day":"Day 1","task":"string","details":"string"}}],
 "prompts":[{{"title":"string","prompt":"string","how_to_use":"string"}}],
 "templates":[{{"name":"string","content":"string"}}],
 "gumroad_description":"string",
 "sales_page":"string",
 "promo_posts":["string"]
}}

Requirements:
- 8 practical guide sections
- 14 day action plan
- 50 AI prompts with titles
- 5 copy/paste templates
- 20 checklist items
- concrete, honest, immediately usable
- no income guarantees
'''
raw = gemini(prompt)
try:
    if raw.startswith('```'):
        raw = raw.replace('```json','').replace('```','').strip()
    data = json.loads(raw)
except Exception:
    data = {
      'title': PRODUCT_NAME,
      'subtitle': f'A practical starter kit for {AUDIENCE}',
      'guide_sections':[{'heading':'Start Here','body':f'This kit helps {AUDIENCE} take practical first steps in {NICHE} without unrealistic promises.'}],
      'checklist_items':['Choose one simple idea','Set a 7 day test window','Track each action'],
      'action_plan_days':[{'day':'Day 1','task':'Choose your first idea','details':'Pick one idea you can test quickly.'}],
      'prompts':[{'title':'Idea finder','prompt':f'Give me 10 realistic ideas in {NICHE}.','how_to_use':'Paste into your AI tool and add your situation.'}],
      'templates':[{'name':'Simple offer template','content':'I help [audience] get [result] without [pain].'}],
      'gumroad_description':f'{PRODUCT_NAME}\n\nA practical starter kit for {AUDIENCE}.',
      'sales_page':f'{PRODUCT_NAME}\n\nA practical kit for {NICHE}.',
      'promo_posts':[f'{PRODUCT_NAME} is a practical starter kit for {NICHE}.']
    }


def draw_wrapped(pdf, text, x, y, width=88, line_height=14):
    for para in str(text).split('\n'):
        for line in textwrap.wrap(para, width) or ['']:
            if y < 60:
                pdf.showPage(); pdf.setFont('Helvetica',10); y = 800
            pdf.drawString(x, y, line[:110]); y -= line_height
        y -= 5
    return y

# Main buyer PDF
pdf_path = PRODUCT_DIR / f'{SLUG}-buyer-guide.pdf'
pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
pdf.setTitle(data.get('title', PRODUCT_NAME))
pdf.setFont('Helvetica-Bold',20)
pdf.drawString(40,800,data.get('title', PRODUCT_NAME)[:65])
pdf.setFont('Helvetica',11)
pdf.drawString(40,775,data.get('subtitle','')[:90])
y=735
for s in data.get('guide_sections',[]):
    pdf.setFont('Helvetica-Bold',13)
    pdf.drawString(40,y,s.get('heading','')[:80]); y-=18
    pdf.setFont('Helvetica',10)
    y = draw_wrapped(pdf, s.get('body',''), 40, y)
    y-=8
pdf.showPage()
pdf.setFont('Helvetica-Bold',16); pdf.drawString(40,800,'14 Day Action Plan')
y=765
pdf.setFont('Helvetica',10)
for d in data.get('action_plan_days',[]):
    y = draw_wrapped(pdf, f"{d.get('day','')}: {d.get('task','')} - {d.get('details','')}", 40, y)
pdf.showPage()
pdf.setFont('Helvetica-Bold',16); pdf.drawString(40,800,'Checklist')
y=765
pdf.setFont('Helvetica',10)
for item in data.get('checklist_items',[]):
    y = draw_wrapped(pdf, f'[ ] {item}', 40, y)
pdf.save()

# Prompt pack PDF
prompt_pdf_path = PRODUCT_DIR / f'{SLUG}-prompt-pack.pdf'
pdf = canvas.Canvas(str(prompt_pdf_path), pagesize=A4)
pdf.setTitle(f'{PRODUCT_NAME} Prompt Pack')
pdf.setFont('Helvetica-Bold',18); pdf.drawString(40,800,f'{PRODUCT_NAME} Prompt Pack'[:70])
y=760
for i,p in enumerate(data.get('prompts',[]),1):
    pdf.setFont('Helvetica-Bold',11); pdf.drawString(40,y,f"{i}. {p.get('title','Prompt')}"[:90]); y-=16
    pdf.setFont('Helvetica',9); y=draw_wrapped(pdf,p.get('prompt',''),40,y,95,12)
    y=draw_wrapped(pdf,'How to use: '+p.get('how_to_use',''),40,y,95,12); y-=8
pdf.save()

# Templates text
(PRODUCT_DIR / f'{SLUG}-templates.txt').write_text('\n\n---\n\n'.join([t.get('name','Template')+'\n\n'+t.get('content','') for t in data.get('templates',[])]),encoding='utf-8')

# Tracker CSV
with open(PRODUCT_DIR / f'{SLUG}-tracker.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['Idea/Lead','Platform','Action','Status','Next Step','Notes'])

# README for buyer
(PRODUCT_DIR / 'READ-ME-FIRST.txt').write_text(f'''{PRODUCT_NAME}

Start here:
1. Open the buyer guide PDF.
2. Follow the 14 day action plan.
3. Use the prompt pack when you need ideas, copy, or decisions.
4. Use the tracker CSV to track actions.
5. Copy templates from the templates file.

Important: This kit does not guarantee income or results. It is a practical planning and action toolkit.
''',encoding='utf-8')

# Seller assets kept outside buyer package
(DIST/'gumroad-description.txt').write_text(data.get('gumroad_description',''),encoding='utf-8')
(DIST/'sales-page.txt').write_text(data.get('sales_page',''),encoding='utf-8')
(DIST/'promo-posts.txt').write_text('\n\n'.join(data.get('promo_posts',[])),encoding='utf-8')
(DIST/'metadata.json').write_text(json.dumps({'product_name':PRODUCT_NAME,'niche':NICHE,'audience':AUDIENCE,'price_usd':PRICE,'generated_with_gemini':bool(os.getenv('GEMINI_API_KEY')),'buyer_package':f'{SLUG}.zip'},indent=2),encoding='utf-8')

zip_path = DIST / f'{SLUG}.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for file in PRODUCT_DIR.iterdir():
        z.write(file, arcname=file.name)

print(f'Gumroad-ready package: {zip_path.name}')
