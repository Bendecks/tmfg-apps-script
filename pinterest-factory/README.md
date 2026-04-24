# TMFG Pinterest Factory

This folder is a standalone Pinterest production pipeline for The Modern Family Guide.

It is intentionally separate from the existing Apps Script engine.

## What v1 does

- Reads a small list of strong blog posts from `data/seed_posts.json`
- Creates multiple Pinterest pin variations per post
- Writes a ready-to-use queue to `output/pinterest_queue.csv`
- Writes a richer JSON queue to `output/pinterest_queue.json`
- Generates simple vertical SVG pin images in `output/pins/`
- Can run manually from GitHub Actions
- Can also run on a schedule

## Why SVG images?

SVG pins are generated without Canva and without paid image APIs. They are simple, readable, and usable as a first automation layer.

Later we can add Gemini/OpenAI image generation as a separate image mode.

## How to run in GitHub

Go to:

Actions → Pinterest Factory → Run workflow

Optional inputs:

- `pin_count`: how many pins to generate in one run
- `commit_output`: whether to commit generated output back to the repo

## Output

After the workflow runs, check:

- `pinterest-factory/output/pinterest_queue.csv`
- `pinterest-factory/output/pinterest_queue.json`
- `pinterest-factory/output/pins/`

## Status workflow

Use the `published_ok` column in the CSV/JSON.

- empty = not published
- OK = published/scheduled

## Next planned layers

1. Pull posts automatically from WordPress export/API
2. Write queue to Google Sheets
3. Generate PNG images via OpenAI or Gemini
4. Add iOS Shortcut helper for copy/paste/upload
5. Optional Tailwind/Pinterest scheduling integration if available
