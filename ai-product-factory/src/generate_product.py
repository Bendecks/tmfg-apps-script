import json, re, glob
from pathlib import Path
from datetime import datetime
import svgwrite
import cairosvg

BASE=Path(__file__).resolve().parents[1]
DIST=BASE/'dist'
BOOKS_ROOT=DIST/'books'
BOOKS_ROOT.mkdir(parents=True,exist_ok=True)
config=json.loads((BASE/'config'/'product.json').read_text())
rotation=config.get('rotation',[])
seed=int(datetime.utcnow().strftime('%Y%m%d'))
selected=rotation[seed % len(rotation)] if rotation else {}
PRODUCT=selected.get('product_name','Planner')
slug=re.sub(r'[^a-z0-9]+','-',PRODUCT.lower()).strip('-')
BOOK=BOOKS_ROOT/slug
BOOK.mkdir(parents=True,exist_ok=True)
PAGES=BOOK/'pages'
PAGES.mkdir(parents=True,exist_ok=True)

# clean generated files for this book
for f in BOOK.glob('*'):
    if f.is_file(): f.unlink()
for f in PAGES.glob('*'):
    if f.is_file(): f.unlink()

WIDTH=816
HEIGHT=1056
MARGIN=60

def draw_box(dwg,x,y,w,h,label):
    dwg.add(dwg.rect(insert=(x,y),size=(w,h),rx=14,ry=14,fill='#ffffff',stroke='#111111',stroke_width=2))
    dwg.add(dwg.text(label.upper(),insert=(x+14,y+28),font_size=16,font_family='Arial',font_weight='bold',fill='#111111'))

def render_page(day):
    path=PAGES/f'page_{day:02d}.svg'
    dwg=svgwrite.Drawing(str(path),size=(WIDTH,HEIGHT),profile='tiny')
    dwg.add(dwg.rect(insert=(0,0),size=(WIDTH,HEIGHT),fill='#f7f7f5'))
    dwg.add(dwg.text(f'Day {day}',insert=(MARGIN,72),font_size=34,font_family='Arial',font_weight='bold',fill='#111111'))
    if day<=5:
        prompt='Start small. Remove friction.'
    elif day<=15:
        prompt='Do something that creates feedback.'
    elif day<=25:
        prompt='Repeat what worked.'
    else:
        prompt='Focus on real results.'
    dwg.add(dwg.text(prompt,insert=(MARGIN,122),font_size=18,font_family='Arial',fill='#333333'))
    y=165
    for section in ['Focus','Action','Result','Learning']:
        draw_box(dwg,MARGIN,y,WIDTH-2*MARGIN,140,section)
        y+=170
    if day%3==0:
        draw_box(dwg,MARGIN,y,WIDTH-2*MARGIN,115,'Make it easier tomorrow')
    dwg.save()
    return path

svg_files=[render_page(d) for d in range(1,31)]

# SVG to PNG preview files
for svg_file in svg_files:
    cairosvg.svg2png(url=str(svg_file),write_to=str(svg_file).replace('.svg','.png'),output_width=WIDTH,output_height=HEIGHT)

# SVG pages directly to PDF, then merge with PyPDF-free CairoSVG approach via ReportLab fallback avoided.
# CairoSVG can write one PDF per page; concatenate by rendering all pages as PNG and saving PDF with Pillow can fail on some runners.
# Instead create a single PDF with ReportLab embedding the PNG previews.
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
pdf_path=BOOK/f'{slug}-interior.pdf'
pdf=canvas.Canvas(str(pdf_path),pagesize=(WIDTH,HEIGHT))
for i in range(1,31):
    png=PAGES/f'page_{i:02d}.png'
    pdf.drawImage(ImageReader(str(png)),0,0,width=WIDTH,height=HEIGHT)
    pdf.showPage()
pdf.save()

(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'engine':'svg_design','pages':30,'pdf_export':'reportlab_embed_png'},indent=2),encoding='utf-8')
(BOOK/'title-subtitle.txt').write_text(PRODUCT+'\nA 30-Day Action System',encoding='utf-8')
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n',encoding='utf-8')
print('SVG DESIGN ENGINE COMPLETE',slug)
