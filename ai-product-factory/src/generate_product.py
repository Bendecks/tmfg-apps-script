from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
TEMPLATES=BASE/'templates'
OUTPUT=BASE/'dist'/'books'/'first-100-html'
OUTPUT.mkdir(parents=True,exist_ok=True)

env=Environment(loader=FileSystemLoader(TEMPLATES))

def get_phase(day):
    if day<=5: return 'SETUP'
    if day<=15: return 'VALIDATION'
    if day<=25: return 'REPEAT'
    return 'FIRST MONEY'

def get_prompt(day):
    if day<=5:
        return 'Start small. Do the easiest useful action.'
    elif day<=15:
        return 'Do something that creates real-world feedback.'
    elif day<=25:
        return 'Repeat what worked.'
    return 'Do something that could lead to money today.'

template=env.get_template('day.html')
pages=[]

for day in range(1,31):
    html=template.render(
        day=day,
        phase=get_phase(day),
        prompt=get_prompt(day),
        extra='Make it easier tomorrow' if day%3==0 else None
    )
    pages.append(html)

full_html='<html><body>'+''.join(pages)+'</body></html>'

pdf_path=OUTPUT/'first-100-planner.pdf'
HTML(string=full_html,base_url=str(BASE)).write_pdf(pdf_path)

print('HTML DESIGN PDF CREATED:',pdf_path)