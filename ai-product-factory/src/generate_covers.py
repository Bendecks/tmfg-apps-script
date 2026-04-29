import base64
import json
import os
from io import BytesIO
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont, ImageStat

BASE = Path(__file__).resolve().parents[1]
PRODUCT_DIR = BASE / "dist" / "products" / "stop-building-ideas-nobody-wants"
SPEC_PATH = PRODUCT_DIR / "cover-spec.json"

TITLE = "Stop Building Ideas Nobody Wants"
SUBTITLE = "The Signal Test Method: A 30-Day Side Hustle Workbook to Test Demand Before You Build"
AUTHOR = "The Modern Family Guide"

IMAGE_MODEL_CANDIDATES = [
    os.environ.get("GEMINI_IMAGE_MODEL", "").strip(),
    "gemini-2.5-flash-image-preview",
    "gemini-3.1-flash-image-preview",
]
IMAGE_MODEL_CANDIDATES = [m for m in IMAGE_MODEL_CANDIDATES if m]


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
    y = draw_center(draw, SUBTITLE, subtitle_font, y, 1320, ink, 12)
    draw.line((260, 1850, 1540, 1850), fill=accent, width=12)
    for i, h in enumerate([150, 270, 420, 580]):
        x0 = 1130 + i * 95
        draw.rounded_rectangle((x0, 1770 - h, x0 + 48, 1770), radius=18, fill=accent)
    draw.ellipse((250, 1540, 520, 1810), outline=accent, width=12)
    draw.ellipse((325, 1615, 445, 1735), outline=accent, width=9)
    draw.line((520, 1675, 820, 1675), fill=accent, width=10)
    draw_center(draw, "A 30-day workbook to test demand before you waste time building.", font(44, False), 2020, 1200, accent, 10)
    draw.text((1800 // 2 - draw.textlength(AUTHOR, font=author_font) // 2, 2380), AUTHOR, fill=ink, font=author_font)
    img.save(out_path, format="PNG", dpi=(300, 300))


def make_fallback_cover(out_path: Path, concept_name: str, index: int):
    palettes = [
        ((244, 239, 229), (35, 38, 43), (111, 88, 65)),
        ((238, 235, 226), (28, 34, 38), (79, 112, 99)),
        ((242, 238, 232), (38, 34, 31), (135, 85, 63)),
    ]
    bg, ink, accent = palettes[index % len(palettes)]
    img = Image.new("RGB", (1800, 2700), bg)
    draw = ImageDraw.Draw(img)

    title_font = font(150, True)
    subtitle_font = font(52, False)
    author_font = font(42, True)
    small_font = font(34, False)

    draw.rectangle((120, 120, 1680, 2580), outline=ink, width=8)
    draw.line((220, 2060, 1580, 2060), fill=accent, width=10)

    for i, h in enumerate([120, 220, 350, 500]):
        x0 = 1180 + i * 90
        draw.rounded_rectangle((x0, 1900 - h, x0 + 46, 1900), radius=18, fill=accent)

    draw.ellipse((250, 1710, 470, 1930), outline=accent, width=10)
    draw.ellipse((305, 1765, 415, 1875), outline=accent, width=8)
    draw.line((470, 1820, 720, 1820), fill=accent, width=8)

    y = 360
    y = draw_center(draw, TITLE, title_font, y, 1400, ink, 18)
    y += 75
    y = draw_center(draw, SUBTITLE, subtitle_font, y, 1320, ink, 12)
    y += 90
    draw_center(draw, "A practical workbook for testing demand before you waste time building.", small_font, y, 1120, accent, 10)
    draw.text((1800 // 2 - draw.textlength(AUTHOR, font=author_font) // 2, 2380), AUTHOR, fill=ink, font=author_font)
    draw.text((1800 // 2 - draw.textlength(concept_name, font=small_font) // 2, 2460), concept_name, fill=accent, font=small_font)
    img.save(out_path, format="PNG", dpi=(300, 300))


def extract_image_bytes(response):
    if not getattr(response, "candidates", None):
        return None
    parts = getattr(response.candidates[0].content, "parts", []) or []
    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline and getattr(inline, "data", None):
            data = inline.data
            if isinstance(data, bytes):
                return data
            if isinstance(data, str):
                return base64.b64decode(data)
    return None


def generate_ai_cover(client, prompt_text: str, out_path: Path):
    last_error = None
    for model in IMAGE_MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt_text,
                config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
            img_bytes = extract_image_bytes(response)
            if img_bytes:
                img = Image.open(BytesIO(img_bytes)).convert("RGB")
                img = img.resize((1800, 2700))
                img.save(out_path, format="PNG", dpi=(300, 300))
                return {"ok": True, "model": model, "error": None}
        except Exception as exc:
            last_error = str(exc)
    return {"ok": False, "model": None, "error": last_error or "No image data returned"}


def make_contact_sheet(image_paths, out_path: Path, thumb_w=420, thumb_h=630):
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
    if contrast >= 45:
        score += 40
    elif contrast >= 35:
        score += 30
    else:
        score += 15
    if 70 <= brightness <= 220:
        score += 25
    else:
        score += 10
    if img.size == (1800, 2700):
        score += 20
    score += 15 if index == 4 else 5  # controlled typographic cover gets reliability bonus
    return {
        "file": path.name,
        "thumbnail_contrast_stddev": contrast,
        "thumbnail_brightness": brightness,
        "dimensions": list(img.size),
        "quality_score": score,
        "notes": "Automated heuristic only. Human visual check still required."
    }


def main():
    if not SPEC_PATH.exists():
        raise RuntimeError(f"Missing cover spec: {SPEC_PATH}")

    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    results, paths = [], []
    for idx, concept in enumerate(spec.get("concepts", []), start=1):
        out_path = PRODUCT_DIR / f"cover-{idx}.png"
        prompt = (
            spec["front_cover_prompt"]
            + "\n\nSpecific concept: "
            + concept["name"]
            + ". "
            + concept["prompt"]
            + "\n\nGenerate only the front cover, portrait 6:9, no mockup, no book shadow, no extra border outside the cover."
        )
        if client:
            result = generate_ai_cover(client, prompt, out_path)
        else:
            result = {"ok": False, "model": None, "error": "GEMINI_API_KEY missing"}
        if not result["ok"]:
            make_fallback_cover(out_path, concept["name"], idx - 1)
            result["fallback_used"] = True
        else:
            result["fallback_used"] = False
        result.update({"file": out_path.name, "concept": concept["name"]})
        results.append(result)
        paths.append(out_path)

    control_path = PRODUCT_DIR / "cover-4-typographic-control.png"
    make_typographic_control_cover(control_path)
    results.append({"ok": True, "model": "deterministic-pillow", "error": None, "fallback_used": False, "file": control_path.name, "concept": "Typographic Control Cover"})
    paths.append(control_path)

    make_contact_sheet(paths, PRODUCT_DIR / "cover-contact-sheet.png")
    make_contact_sheet(paths, PRODUCT_DIR / "thumbnail-test-contact-sheet.png", thumb_w=150, thumb_h=225)

    quality = [analyze_cover(p, idx + 1) for idx, p in enumerate(paths)]
    recommended = max(quality, key=lambda q: q["quality_score"])
    (PRODUCT_DIR / "cover-quality-report.json").write_text(json.dumps({"recommended_front_cover": recommended["file"], "covers": quality}, indent=2), encoding="utf-8")
    (PRODUCT_DIR / "cover-generation.json").write_text(json.dumps({"covers": results}, indent=2), encoding="utf-8")

    meta_path = PRODUCT_DIR / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta.update({
        "engine": "kdp_value_cover_quality_v1",
        "auto_front_covers": True,
        "front_cover_pngs": [p.name for p in paths],
        "typographic_control_cover": control_path.name,
        "cover_contact_sheet": "cover-contact-sheet.png",
        "thumbnail_test_contact_sheet": "thumbnail-test-contact-sheet.png",
        "cover_quality_report": "cover-quality-report.json",
        "recommended_front_cover": recommended["file"],
        "cover_generation_metadata": "cover-generation.json",
        "image_models_tried": IMAGE_MODEL_CANDIDATES,
    })
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    checklist = PRODUCT_DIR / "upload-checklist.txt"
    checklist.write_text(
        "1. Open book.pdf and inspect first 10 pages, real/fake signal page, conversion tools, scorecard, 3 daily pages, tracker, and Stop / Pivot / Continue page.\n"
        "2. Check the value pages: signal test logs, extra scorecards, weekly reviews, and price-test pages.\n"
        "3. Open cover-contact-sheet.png and thumbnail-test-contact-sheet.png.\n"
        "4. Read cover-quality-report.json and start with the recommended front cover.\n"
        "5. Check cover-generation.json to see whether AI image generation or deterministic cover generation was used.\n"
        "6. Check that no income guarantees are stated.\n"
        "7. Use kdp-listing.json and kdp-upload-fields.txt for KDP metadata.\n"
        "8. Upload interior PDF and wraparound cover PDF to KDP Print Previewer.\n",
        encoding="utf-8",
    )
    print("KDP cover candidates and quality report generated")


if __name__ == "__main__":
    main()
