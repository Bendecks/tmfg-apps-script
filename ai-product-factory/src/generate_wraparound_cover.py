import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

BASE = Path(__file__).resolve().parents[1]
PRODUCT_DIR = BASE / "dist" / "products" / "stop-building-ideas-nobody-wants"
BOOK_PDF = PRODUCT_DIR / "book.pdf"
QUALITY_REPORT = PRODUCT_DIR / "cover-quality-report.json"
DEFAULT_FRONT_COVER = PRODUCT_DIR / "cover-1.png"
SPEC_PATH = PRODUCT_DIR / "cover-spec.json"
META_PATH = PRODUCT_DIR / "metadata.json"

TITLE = "Stop Building Ideas Nobody Wants"
SUBTITLE = "The Signal Test Method: A 30-Day Side Hustle Workbook to Test Demand Before You Build"
AUTHOR = "The Modern Family Guide"
TRIM_W_IN = 6.0
TRIM_H_IN = 9.0
BLEED_IN = 0.125
DPI = 300
PAPER_TYPE = "black_white_white_paper"
SPINE_PER_PAGE_IN = 0.002252
MIN_SPINE_TEXT_IN = 0.25


def get_recommended_front_cover() -> Path:
    if QUALITY_REPORT.exists():
        try:
            report = json.loads(QUALITY_REPORT.read_text(encoding="utf-8"))
            recommended = report.get("recommended_front_cover")
            if recommended:
                candidate = PRODUCT_DIR / recommended
                if candidate.exists():
                    return candidate
        except Exception:
            pass
    return DEFAULT_FRONT_COVER


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_width):
    out, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=fnt)
        if bbox[2] - bbox[0] <= max_width:
            cur = test
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def draw_wrapped(draw, text, xy, fnt, max_width, fill, spacing=10):
    x, y = xy
    for line in wrap(draw, text, fnt, max_width):
        draw.text((x, y), line, fill=fill, font=fnt)
        bbox = draw.textbbox((0, 0), line, font=fnt)
        y += (bbox[3] - bbox[1]) + spacing
    return y


def get_page_count():
    if not BOOK_PDF.exists():
        raise RuntimeError(f"Missing interior PDF: {BOOK_PDF}")
    return len(PdfReader(str(BOOK_PDF)).pages)


def make_back_cover(draw, x0, y0, w, h, bg, ink, accent):
    title_font = font(58, True)
    body_font = font(38, False)
    small_font = font(30, False)
    bold_small = font(32, True)

    margin = int(0.48 * DPI)
    x = x0 + margin
    y = y0 + margin
    max_width = w - margin * 2

    draw.text((x, y), "Stop building before you test.", fill=ink, font=title_font)
    y += 95
    blurb = (
        "Most side hustle ideas do not fail because people are lazy. "
        "They fail because nobody tested demand early enough.\n\n"
        "This workbook gives you a simple 30-day system for finding real problems, "
        "asking real people, making tiny offers, and deciding whether to stop, pivot, or continue."
    )
    for para in blurb.split("\n\n"):
        y = draw_wrapped(draw, para, (x, y), body_font, max_width, ink, spacing=9)
        y += 28

    y += 15
    draw.rounded_rectangle((x, y, x + max_width, y + 360), radius=20, outline=accent, width=5)
    y2 = y + 35
    draw.text((x + 35, y2), "Inside:", fill=ink, font=bold_small)
    y2 += 56
    bullets = [
        "The 10-Message Test",
        "The $10 Tiny Offer Test",
        "The Polite Interest Trap",
        "The 3-Signal Scorecard",
        "30 days of direct action pages",
    ]
    for b in bullets:
        draw.text((x + 45, y2), f"• {b}", fill=ink, font=small_font)
        y2 += 48

    footer = "No guru hype. No income guarantees. Just small tests, real signals, and clearer next steps."
    draw_wrapped(draw, footer, (x, y0 + h - margin - 145), small_font, max_width, accent, spacing=7)

    safe_w = int(2.0 * DPI)
    safe_h = int(1.2 * DPI)
    bx = x0 + w - margin - safe_w
    by = y0 + h - margin - safe_h
    draw.rectangle((bx, by, bx + safe_w, by + safe_h), outline=(190, 190, 190), width=3)
    draw.text((bx + 35, by + safe_h // 2 - 18), "Barcode area", fill=(150, 150, 150), font=small_font)


def make_wraparound():
    front_cover = get_recommended_front_cover()
    page_count = get_page_count()
    spine_in = max(page_count * SPINE_PER_PAGE_IN, 0.0)

    trim_w = int(TRIM_W_IN * DPI)
    trim_h = int(TRIM_H_IN * DPI)
    bleed = int(BLEED_IN * DPI)
    spine_px = int(round(spine_in * DPI))

    full_w = trim_w * 2 + spine_px + bleed * 2
    full_h = trim_h + bleed * 2

    bg = (244, 239, 229)
    ink = (34, 36, 40)
    accent = (98, 91, 74)
    img = Image.new("RGB", (full_w, full_h), bg)
    draw = ImageDraw.Draw(img)

    back_x = bleed
    front_x = bleed + trim_w + spine_px
    panel_y = bleed

    make_back_cover(draw, back_x, panel_y, trim_w, trim_h, bg, ink, accent)

    spine_x = bleed + trim_w
    draw.rectangle((spine_x, 0, spine_x + spine_px, full_h), fill=(235, 230, 219))
    if spine_in >= MIN_SPINE_TEXT_IN:
        spine_font = font(max(22, min(42, int(spine_px * 0.32))), True)
        spine_text = f"{TITLE}    {AUTHOR}"
        tmp = Image.new("RGBA", (trim_h, max(spine_px, 80)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        bbox = td.textbbox((0, 0), spine_text, font=spine_font)
        tx = (trim_h - (bbox[2] - bbox[0])) // 2
        ty = (max(spine_px, 80) - (bbox[3] - bbox[1])) // 2
        td.text((tx, ty), spine_text, fill=ink, font=spine_font)
        tmp = tmp.rotate(90, expand=True)
        img.paste(tmp, (spine_x + (spine_px - tmp.width) // 2, bleed + (trim_h - tmp.height) // 2), tmp)

    if not front_cover.exists():
        raise RuntimeError(f"Missing front cover: {front_cover}")
    front = Image.open(front_cover).convert("RGB").resize((trim_w + bleed, trim_h + bleed * 2))
    img.paste(front, (front_x, 0))

    guide = (210, 210, 210)
    draw.rectangle((bleed, bleed, full_w - bleed, full_h - bleed), outline=guide, width=1)
    draw.line((spine_x, bleed, spine_x, full_h - bleed), fill=guide, width=1)
    draw.line((spine_x + spine_px, bleed, spine_x + spine_px, full_h - bleed), fill=guide, width=1)

    png_path = PRODUCT_DIR / "kdp-wraparound-cover.png"
    pdf_path = PRODUCT_DIR / "kdp-wraparound-cover.pdf"
    img.save(png_path, format="PNG", dpi=(DPI, DPI))
    img.save(pdf_path, "PDF", resolution=DPI)

    data = {
        "trim_size": f"{TRIM_W_IN}x{TRIM_H_IN}",
        "dpi": DPI,
        "bleed_in": BLEED_IN,
        "paper_type": PAPER_TYPE,
        "interior_page_count": page_count,
        "spine_width_in": round(spine_in, 4),
        "spine_width_px": spine_px,
        "full_cover_width_in": round(full_w / DPI, 4),
        "full_cover_height_in": round(full_h / DPI, 4),
        "front_cover_source": front_cover.name,
        "front_cover_selection": "cover-quality-report recommended_front_cover if available; fallback cover-1.png",
        "wraparound_png": png_path.name,
        "wraparound_pdf": pdf_path.name,
        "spine_text_included": spine_in >= MIN_SPINE_TEXT_IN,
        "note": "This is an automated KDP paperback wraparound draft. Verify dimensions in KDP Print Previewer before publishing."
    }
    (PRODUCT_DIR / "kdp-wraparound-cover.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    meta = json.loads(META_PATH.read_text(encoding="utf-8")) if META_PATH.exists() else {}
    meta.update({
        "kdp_wraparound_cover": True,
        "kdp_wraparound_pdf": pdf_path.name,
        "kdp_wraparound_png": png_path.name,
        "kdp_wraparound_metadata": "kdp-wraparound-cover.json",
        "kdp_wraparound_uses_recommended_front_cover": True,
        "kdp_wraparound_front_cover_source": front_cover.name,
        "interior_page_count": page_count,
        "spine_width_in": round(spine_in, 4),
    })
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    checklist = PRODUCT_DIR / "upload-checklist.txt"
    existing = checklist.read_text(encoding="utf-8") if checklist.exists() else ""
    checklist.write_text(
        existing
        + "\nKDP WRAPAROUND COVER\n"
        + "8. Open kdp-wraparound-cover.pdf and kdp-wraparound-cover.png.\n"
        + f"9. Confirm the wraparound uses the recommended front cover: {front_cover.name}.\n"
        + "10. Upload kdp-wraparound-cover.pdf in KDP paperback cover step.\n"
        + "11. Verify trim, bleed, barcode area, and spine alignment in KDP Print Previewer.\n",
        encoding="utf-8",
    )
    print("KDP wraparound cover generated")


if __name__ == "__main__":
    make_wraparound()
