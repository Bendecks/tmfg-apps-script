import json, re
from pathlib import Path
import svgwrite, cairosvg
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

BASE=Path(__file__).resolve().parents[1]
DIST=BASE/'dist'
BOOKS_ROOT=DIST/'books'
BOOKS_ROOT.mkdir(parents=True,exist_ok=True)

PRODUCT="First $100 Online Planner"
slug="first-100-online-planner"
BOOK=BOOKS_ROOT/slug
BOOK.mkdir(parents=True,exist_ok=True)
PAGES=BOOK/'pages'
PAGES.mkdir(parents=True,exist_ok=True)

# clean
for f in BOOK.glob('*'):
    if f.is_file(): f.unlink()
for f in PAGES.glob('*'):
    if f.is_file(): f.unlink()

WIDTH,HEIGHT,MARGIN=816,1056,60

def draw_box(dwg,x,y,w,h,label):
    dwg.add(dwg.rect(insert=(x,y),size=(w,h),rx=14,ry=14,fill='#fff',stroke='#111',stroke_width=2))
    dwg.add(dwg.text(label,insert=(x+14,y+30),font_size=18,font_weight='bold'))

# intro pages
svg_files=[]
for i in range(1,6):
    p=PAGES/f'page_{i:03d}.svg'
    dwg=svgwrite.Drawing(str(p),size=(WIDTH,HEIGHT))
    dwg.add(dwg.rect((0,0),(WIDTH,HEIGHT),fill='#f7f7f5'))
    dwg.add(dwg.text(PRODUCT,insert=(MARGIN,200),font_size=40,font_weight='bold'))
    dwg.add(dwg.text("Get your first $100 online",insert=(MARGIN,260),font_size=24))
    dwg.save()
    svg_files.append(p)

# 30 day system
for day in range(1,31):
    p=PAGES/f'page_{(day+5):03d}.svg'
    dwg=svgwrite.Drawing(str(p),size=(WIDTH,HEIGHT))
    dwg.add(dwg.rect((0,0),(WIDTH,HEIGHT),fill='#f7f7f5'))
    dwg.add(dwg.text(f'Day {day}',insert=(MARGIN,70),font_size=34,font_weight='bold'))

    if day<=5:
        prompt="Pick simple idea"
    elif day<=15:
        prompt="Get feedback"
    elif day<=25:
        prompt="Repeat what works"
    else:
        prompt="Focus on earning"

    dwg.add(dwg.text(prompt,insert=(MARGIN,120),font_size=20))

    y=170
    for s in ["Focus","Action","Result","Learning"]:
        draw_box(dwg,MARGIN,y,WIDTH-2*MARGIN,140,s)
        y+=170

    dwg.save()
    svg_files.append(p)

# trackers
for i in range(36,121):
    p=PAGES/f'page_{i:03d}.svg'
    dwg=svgwrite.Drawing(str(p),size=(WIDTH,HEIGHT))
    dwg.add(dwg.rect((0,0),(WIDTH,HEIGHT),fill='#fff'))
    dwg.add(dwg.text("ACTION TRACKER",insert=(MARGIN,70),font_size=32,font_weight='bold'))
    y=140
    for _ in range(12):
        dwg.add(dwg.line((MARGIN,y),(WIDTH-MARGIN,y),stroke='#111'))
        y+=60
    dwg.save()
    svg_files.append(p)

# convert + pdf
for svg in svg_files:
    cairosvg.svg2png(url=str(svg),write_to=str(svg).replace('.svg','.png'))

pdf=canvas.Canvas(str(BOOK/f"{slug}-interior.pdf"),pagesize=(WIDTH,HEIGHT))
for svg in svg_files:
    png=str(svg).replace('.svg','.png')
    pdf.drawImage(ImageReader(png),0,0,width=WIDTH,height=HEIGHT)
    pdf.showPage()
pdf.save()

(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'pages':len(svg_files),'engine':'first100_v1'},indent=2))
(BOOK/'title-subtitle.txt').write_text(PRODUCT+"\n30 Day System")
(BOOK/'description.txt').write_text("Get your first $100 online with structured action.")
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+"\n"+PRODUCT)

print("FIRST 100 BUILT")
