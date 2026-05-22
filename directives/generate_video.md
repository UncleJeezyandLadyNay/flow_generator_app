# Directive: Google Flow — Video Generation Pipeline

## Purpose
Automate video (and image) generation through the Google Flow web UI (`labs.google/fx/tools/flow`) using Playwright browser automation, from prompt → rendered file → saved to `.tmp/`.

## Inputs
- **Prompt** — plain text description, or a Nano Banana 2 JSON prompt (12-field or 8-field schema)
- **Type** — `video` (default) or `image`
- **Timeout** — max seconds to wait for generation (default: 600 for video, 300 for image)
- **Output directory** — where to save the result (default: `.tmp/`)

## Tools / Scripts
| Task | Script |
|------|--------|
| One-time Google login (saves session) | `google-flow-generator/scripts/login.py` |
| Generate image or video | `google-flow-generator/scripts/generate.py` |
| Discover UI selectors (debugging) | `google-flow-generator/scripts/discover_selectors.py` |

> **Before writing new scripts**, check `google-flow-generator/scripts/` — use what exists, fix it if broken.

## Process
1. **Prerequisite — session must exist**: check for `.session/flow_auth.json`. If missing, run `login.py` first (opens a real browser window; user logs in manually once).
2. Run `generate.py` with `--prompt` (or `--json-prompt` for NB2 JSON) and `--type video`.
3. Script launches headless Chromium with the saved session, navigates to Flow, injects the prompt, triggers generation, and polls the DOM until a downloadable result appears.
4. Result is downloaded and saved to `.tmp/<timestamp>_<type>.<ext>`.
5. Script prints the absolute output path to stdout on success.

## Outputs
- `.tmp/<timestamp>_video.mp4` or `.tmp/<timestamp>_image.png/.jpg` — local intermediate file (disposable, always regenerable)

## Example Commands
```bash
# One-time login
.venv/bin/python google-flow-generator/scripts/login.py

# Generate a video
.venv/bin/python google-flow-generator/scripts/generate.py --prompt "A calm ocean at sunset" --type video

# Generate from a NB2 JSON file
.venv/bin/python google-flow-generator/scripts/generate.py --json-prompt .tmp/prompt.json --type video

# Generate an image from a spreadsheet row (row 1 = first data row after header)
.venv/bin/python google-flow-generator/scripts/generate.py --xlsx prompts.xlsx --row 3 --type image --out ./output/
```

## xlsx Spreadsheet Format
Required columns (case-insensitive):
| Column | Content |
|--------|---------|
| `Prompt` | Nano Banana 2 JSON string (same schema as `--json-prompt`) |
| `Filename` | Output filename stem — extension is added automatically |

- `--row` is 1-based: row 1 is the first data row after the header
- `--out` sets the output folder; defaults to `.tmp/` if omitted
- `--name` overrides the xlsx filename if both are provided
- `openpyxl` must be installed: `.venv/bin/pip install openpyxl`

## Edge Cases & Learnings
- Session expires occasionally — re-run `login.py` if generation fails with an auth error
- Video generation typically takes 2–10 minutes; script polls the DOM automatically
- Quota/rate-limit errors (pattern: "quota", "rate limit", error 253) are surfaced and should NOT be auto-retried
- If the UI selector changes (Flow UI updates), run `discover_selectors.py` to refresh and update `generate.py`

## Notes
- **Gallery navigation**: The "New project" button text is `add_2New project` (Material icon prefix). Use `has_text` partial match, not `get_by_role` accessible name — the accessible name doesn't always resolve correctly. Also wait up to 8s for the button since the gallery renders slowly with many existing projects.
- **Video mode setup (as of 2026-05-20)**: Image/Video tabs are INSIDE the settings panel (opened by clicking the toolbar model button), not separate UI elements. The correct sequence is: (1) click toolbar button → (2) click "Video" tab → (3) click model dropdown (button text contains "arrow_drop_down") → (4) select Veo model.
- **Variation count buttons**: Format is `1x`, `x2`, `x3`, `x4` — NOT `x1`. The `1x` button is directly visible in the settings panel (no sub-picker needed). Use regex `^x?{count}x?$` to match both formats.
- **Video generation time**: Typically 60–90 seconds for a single Veo 3.1 Lite generation.
- **Video URL detection (critical)**: Flow does NOT expose the video URL as a direct network response. Instead, `<video>` elements use `labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<uuid>` which initially redirects to `flow-content.google/image/<uuid>` (thumbnail). When the video finishes rendering, the same redirect URL switches to `flow-content.google/video/<uuid>` (mp4). The correct detection strategy is to poll `<video src="*media.getMediaUrlRedirect*">` DOM elements, follow their redirect via Playwright's request context, and return the URL when the content-type becomes `video/mp4`.
