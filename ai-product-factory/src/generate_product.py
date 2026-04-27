import os, json, csv, textwrap, hashlib
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / 'dist'
DIST.mkdir(exist_ok=True)
config = json.loads((BASE / 'config' / 'product.json').read_text())
BRAND = config.get('brand', 'Digital Product Studio')

rotation = config.get('rotation', [])
if rotation:
    day_seed = int(datetime.utcnow().strftime('%Y%m%d'))
    selected = rotation[day_seed % len(rotation)]
else:
    selected = {
        'product_name': config.get('product_name', 'AI Digital Product'),
        'audience': config.get('audience', 'buyers'),
        'niche': 'general'
    }

PRODUCT_NAME = selected['product_name']
AUDIENCE = selected['audience']
NICHE = selected['niche']
PRICE = config.get('price_usd', 9)


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

prompt = f'''Return ONLY valid JSON. Create a high-converting Gumroad digital product in niche: {NICHE}. Product: {PRODUCT_NAME}. Audience: {AUDIENCE}. Price: ${PRICE}. JSON schema: {{"guide_sections":[{{"heading":"x","body":"x"}}],"prompts":["x"],"gumroad_description":"x","sales_page":"x","promo_posts":["x"]}} Requirements: 6 guide sections, 40 prompts, 10 promo posts, persuasive but honest copy.'''
raw = gemini(prompt)

fallback = {
 'guide_sections':[{'heading':'Start Here','body':f'{PRODUCT_NAME} helps {AUDIENCE} get faster results in {NICHE}.'}],
 'prompts':[f'Give me a step by step plan for success in {NICHE}.'],
 'gumroad_description':f'{PRODUCT_NAME}\n\nA practical toolkit for {AUDIENCE}.',
 'sales_page':f'Headline: {PRODUCT_NAME}\nPromise: Faster progress in {NICHE}.',
 'promo_posts':[f'{PRODUCT_NAME}: practical help for {NICHE}.']
}

try:
    if raw.startswith('```'):
        raw = raw.replace('```json','').replace('```','').strip()
    content = json.loads(raw) if raw else fallback
except:
    content = fallback

pdf = canvas.Canvas(str(DIST/'quick-start-guide.pdf'), pagesize=A4)
pdf.setFont('Helvetica-Bold',18)
pdf.drawString(40,800,PRODUCT_NAME[:70])
pdf.setFont('Helvetica',10)
pdf.drawString(40,780,f'{NICHE} | {BRAND}')
y=745
for s in content['guide_sections']:
    pdf.setFont('Helvetica-Bold',13)
    pdf.drawString(40,y,s['heading'][:80]); y-=18
    pdf.setFont('Helvetica',10)
    for line in textwrap.wrap(s['body'],88):
        pdf.drawString(40,y,line); y-=14
        if y<60:
            pdf.showPage(); y=800
    y-=8
pdf.save()

(DIST/'prompt-pack.txt').write_text('\n\n'.join(content['prompts']),encoding='utf-8')
(DIST/'gumroad-description.txt').write_text(content['gumroad_description'],encoding='utf-8')
(DIST/'sales-page.txt').write_text(content['sales_page'],encoding='utf-8')
(DIST/'promo-posts.txt').write_text('\n\n'.join(content['promo_posts']),encoding='utf-8')
with open(DIST/'job-tracker.csv','w',newline='',encoding='utf-8') as f:
    csv.writer(f).writerow(['Lead','Source','Status','Next Step'])
(DIST/'metadata.json').write_text(json.dumps({'product_name':PRODUCT_NAME,'niche':NICHE,'audience':AUDIENCE,'generated_with_gemini':bool(os.getenv('GEMINI_API_KEY'))},indent=2),encoding='utf-8')
print(PRODUCT_NAME)
