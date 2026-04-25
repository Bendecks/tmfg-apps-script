import os, json, csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / 'dist'
DIST.mkdir(exist_ok=True)
config = json.loads((BASE/'config'/'product.json').read_text())

# Simple fallback content (Gemini can be added later)
name = config['product_name']

pdf = canvas.Canvas(str(DIST/'quick-start-guide.pdf'), pagesize=A4)
pdf.setFont('Helvetica-Bold',18)
pdf.drawString(40,800,name)
pdf.setFont('Helvetica',11)
lines = [
'Use AI to tailor resumes quickly.',
'Use prompts to draft cover letters.',
'Practice interviews daily.',
'Track applications consistently.',
'Ship more applications with less stress.'
]
y=760
for line in lines:
    pdf.drawString(40,y,line)
    y-=22
pdf.save()

with open(DIST/'job-tracker.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['Company','Role','Date Applied','Status','Next Step'])

(DIST/'gumroad-description.txt').write_text(
    f'{name}\n\nA practical digital toolkit for job seekers who want faster, better applications. Includes prompts, tracker, and quick-start guide.'
)

print('Generated files in dist/')
