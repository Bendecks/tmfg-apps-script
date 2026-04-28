import os, json, re, glob
from pathlib import Path
from datetime import datetime
import svgwrite
import cairosvg
from PIL import Image

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

WIDTH=816
HEIGHT=1056
MARGIN=60

def draw_box(dwg,x,y,w,h,label):
    dwg.add(dwg.rect(insert=(x,y),size=(w,h),rx=14,ry=14,fill="#fff",stroke="#111",stroke_width=2))
    dwg.add(dwg.text(label.upper(),insert=(x+14,y+26),font_size=16,font_family="Arial"))


def render_page(day):
    dwg=svgwrite.Drawing(str(PAGES/f"page_{day}.svg"),size=(WIDTH,HEIGHT))
    dwg.add(dwg.rect((0,0),(WIDTH,HEIGHT),fill="#f7f7f5"))

    dwg.add(dwg.text(f"Day {day}",insert=(MARGIN,70),font_size=34,font_weight="bold"))

    if day<=5:
        prompt="Start small. Remove friction."
    elif day<=15:
        prompt="Do something that creates feedback."
    elif day<=25:
        prompt="Repeat what worked."
    else:
        prompt="Focus on real results."

    dwg.add(dwg.text(prompt,insert=(MARGIN,120),font_size=18,fill="#333"))

    y=160
    sections=["Focus","Action","Result","Learning"]

    for s in sections:
        draw_box(dwg,MARGIN,y,WIDTH-2*MARGIN,140,s)
        y+=170

    if day%3==0:
        draw_box(dwg,MARGIN,y,WIDTH-2*MARGIN,120,"Make it easier tomorrow")

    dwg.save()

for d in range(1,31):
    render_page(d)

# convert SVG → PNG
for svg_file in glob.glob(str(PAGES/'*.svg')):
    cairosvg.svg2png(url=svg_file,write_to=svg_file.replace('.svg','.png'))

# combine PDF
images=[]
for i in range(1,31):
    img=Image.open(PAGES/f"page_{i}.png").convert("RGB")
    images.append(img)

images[0].save(BOOK/f"{slug}-interior.pdf",save_all=True,append_images=images[1:])

(BOOK/'metadata.json').write_text(json.dumps({'product':PRODUCT,'engine':'svg_design','pages':30},indent=2))
(BOOKS_ROOT/'LATEST_BOOK.txt').write_text(slug+'\n'+PRODUCT+'\n')

print("SVG DESIGN ENGINE COMPLETE",slug)
