import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat

BASE = Path(__file__).resolve().parents[1]
PRODUCT_DIR = BASE / "dist" / "products" / "stop-building-ideas-nobody-wants"
OLD_AUTHOR = "The Modern Family Guide"
NEW_AUTHOR = "Daniel Brooks"
TITLE = "Stop Building Ideas Nobody Wants"
SUBTITLE = "The Signal Test Method: A 30-Day Side Hustle Workbook to Test Demand Before You Build"


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


def draw_center(draw, text, fnt, y, max_width, fill, line_spacing=12):
    for line in wrap(draw, text, fnt, max_width):
        bbox = draw.textbbox((0, 0), line, font=fnt)
        x = (1800 - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=fill, font=fnt)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def replace_author_in_text_files():
    for path in PRODUCT_DIR.glob("*"):
        if path.suffix.lower() not in {".txt", ".json", ".typ"}:
            continue
        text = path.read_text(encoding="utf-8")
        updated = text.replace(OLD_AUTHOR, NEW_AUTHOR)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def patch_json_files():
    for name in ["kdp-listing.json", "metadata.json"]:
        path = PRODUCT_DIR / name
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        data["author"] = NEW_AUTHOR
        data["author_pseudonym"] = NEW_AUTHOR
        data["author_pseudonym_applied"] = True
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def recompile_book():
    typ = PRODUCT_DIR / "book.typ"
    pdf = PRODUCT_DIR / "book.pdf"
    if typ.exists():
        subprocess.run(["typst", "compile", str(typ), str(pdf)], check=True)


def make_typographic_control_cover(out_path: Path):
    bg = (244, 239, 229)
    ink = (29, 32, 36)
    accent = (98, 91, 74)
    img = Image.new("RGB", (1800, 2700), bg)
    draw = ImageDraw.Draw(img)
    title_font = font(156, True)
    subtitle_font = font(50, False)
    author_font = font(42, True)
    label_font = font(34, True)

    draw.rectangle((120, 120, 1680, 2580), outline=ink, width=10)
    draw.rectangle((120, 120, 1680, 315), fill=ink)
    draw.text((190, 205), "THE SIGNAL TEST METHOD", fill=bg, font=label_font)
    y = 430
    y = draw_center(draw, TITLE, title_font, y, 1400, ink, 18)
    y += 85
    draw_center(draw, SUBTITLE, subtitle_font, y, 1320, ink, 12)
    draw.line((260, 1850, 1540, 1850), fill=accent, width=12)
    for i, h in enumerate([150, 270, 420, 580]):
        x0 = 1130 + i * 95
        draw.rounded_rectangle((x0, 1770 - h, x0 + 48, 1770), radius=18, fill=accent)
    draw.ellipse((250, 1540, 520, 1810), outline=accent, width=12)
    draw.ellipse((325, 1615, 445, 1735), outline=accent, width=9)
    draw.line((520, 1675, 820, 1675), fill=accent, width=10)
    draw_center(draw, "A 30-day workbook to test demand before you waste time building.", font(44, False), 2020, 1200, accent, 10)
    draw.text((1800 // 2 - draw.textlength(NEW_AUTHOR, font=author_font) // 2, 2380), NEW_AUTHOR, fill=ink, font=author_font)
    img.save(out_path, format="PNG", dpi=(300, 300))


def make_contact_sheet(image_paths, out_path: Path, thumb_w=420, thumb_h=630):
    if not image_paths:
        return
    label_h, margin = 70, 30
    sheet = Image.new("RGB", (len(image_paths) * (thumb_w + margin) + margin, thumb_h + label_h + margin * 2), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    label_font = font(24, True)
    for idx, path in enumerate(image_paths):
        img = Image.open(path).convert("RGB").resize((thumb_w, thumb_h))
        x = margin + idx * (thumb_w + margin)
        sheet.paste(img, (x, margin))
        draw.text((x, margin + thumb_h + 15), f"Cover {idx + 1}", fill=(35, 35, 35), font=label_font)
    sheet.save(out_path, format="PNG")


def analyze_cover(path: Path, index: int):
    img = Image.open(path).convert("RGB")
    small = img.resize((120, 180))
    gray = small.convert("L")
    stat = ImageStat.Stat(gray)
    contrast = round(stat.stddev[0], 2)
    brightness = round(stat.mean[0], 2)
    score = 0
    score += 40 if contrast >= 45 else 30 if contrast >= 35 else 15
    score += 25 if 70 <= brightness <= 220 else 10
    score += 20 if img.size == (1800, 2700) else 0
    score += 15 if path.name == "cover-4-typographic-control.png" else 5
    return {
        "file": path.name,
        "thumbnail_contrast_stddev": contrast,
        "thumbnail_brightness": brightness,
        "dimensions": list(img.size),
        "quality_score": score,
        "notes": "Automated heuristic only. Human visual check still required."
    }


def refresh_cover_quality_assets():
    # Only run after covers exist.
    existing = [PRODUCT_DIR / f"cover-{i}.png" for i in range(1, 4)]
    existing = [p for p in existing if p.exists()]
    if not existing:
        return

    control = PRODUCT_DIR / "cover-4-typographic-control.png"
    make_typographic_control_cover(control)
    paths = existing + [control]
    make_contact_sheet(paths, PRODUCT_DIR / "cover-contact-sheet.png")
    make_contact_sheet(paths, PRODUCT_DIR / "thumbnail-test-contact-sheet.png", thumb_w=150, thumb_h=225)
    quality = [analyze_cover(p, idx + 1) for idx, p in enumerate(paths)]
    recommended = max(quality, key=lambda q: q["quality_score"])
    (PRODUCT_DIR / "cover-quality-report.json").write_text(json.dumps({"recommended_front_cover": recommended["file"], "covers": quality}, indent=2), encoding="utf-8")

    generation = PRODUCT_DIR / "cover-generation.json"
    if generation.exists():
        data = json.loads(generation.read_text(encoding="utf-8"))
    else:
        data = {"covers": []}
    if not any(c.get("file") == control.name for c in data.get("covers", [])):
        data.setdefault("covers", []).append({"ok": True, "model": "deterministic-pillow", "error": None, "fallback_used": False, "file": control.name, "concept": "Typographic Control Cover"})
    generation.write_text(json.dumps(data, indent=2), encoding="utf-8")

    meta_path = PRODUCT_DIR / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta.update({
        "author": NEW_AUTHOR,
        "author_pseudonym": NEW_AUTHOR,
        "author_pseudonym_applied": True,
        "typographic_control_cover": control.name,
        "cover_quality_report": "cover-quality-report.json",
        "thumbnail_test_contact_sheet": "thumbnail-test-contact-sheet.png",
        "recommended_front_cover": recommended["file"],
        "front_cover_pngs": [p.name for p in paths],
    })
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main():
    if not PRODUCT_DIR.exists():
        raise RuntimeError(f"Missing product dir: {PRODUCT_DIR}")
    replace_author_in_text_files()
    patch_json_files()
    recompile_book()
    refresh_cover_quality_assets()
    print(f"Author pseudonym applied: {NEW_AUTHOR}")


if __name__ == "__main__":
    main()
