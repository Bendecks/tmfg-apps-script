# AI Product Factory

A lightweight GitHub-based system for generating sellable digital products with the Gemini API.

## First product line

**AI Job Search Kit**

This repo/folder is designed to generate a complete digital download package containing:

- PDF guide
- Prompt pack
- Job application tracker
- Gumroad sales copy
- Social promo copy
- Product metadata

## Why this niche

The first product targets job seekers because it has clear buying intent, evergreen demand, and can be packaged as useful digital templates rather than a vague ebook.

## How it works

1. Edit `config/product.json`
2. Add your `GEMINI_API_KEY` as a GitHub Actions secret
3. Run the workflow manually from GitHub Actions
4. Download the generated artifact
5. Upload the ZIP/PDF manually to Gumroad

## Local setup

```bash
cd ai-product-factory
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
python src/generate_product.py
```

Generated files will appear in `dist/`.

## Current limitation

Gumroad product creation/upload is not fully automated here because Gumroad does not currently expose a simple official public product-upload API suitable for this workflow. The repo therefore automates production, packaging, metadata, and sales copy, while Gumroad upload remains manual.
