# Flow Generator App

Automate image and video generation through [Google Flow](https://labs.google/fx/tools/flow) (powered by Veo 3.1) using Playwright browser automation. Accepts prompts from a spreadsheet, generates media, and saves the result locally.

---

## Features

- Generate **images** (Nano Banana 2) or **videos** (Veo 3.1 Lite) from Google Flow
- Pull prompts and filenames from an **Excel spreadsheet** (`.xlsx`)
- Supports plain-text prompts or structured **Nano Banana 2 JSON** prompts
- Simple **GUI app** to kick off generations without touching the terminal
- Headless by default — runs silently in the background

---

## Requirements

- macOS (tested on Sonoma)
- Python 3.14+
- Google account with access to [Google Flow](https://labs.google/fx/tools/flow)
- Google Chrome installed

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/UncleJeezyandLadyNay/flow_generator_app.git
cd flow_generator_app

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Install dependencies
.venv/bin/pip install playwright openpyxl

# 4. Install Playwright's browser driver
.venv/bin/playwright install chromium

# 5. (macOS only) Install tkinter for the GUI
brew install python-tk@3.14
```

---

## Setup — One-Time Login

The app needs a saved Google session to run headlessly. Do this once:

```bash
.venv/bin/python google-flow-generator/scripts/login.py
```

A Chrome window opens. Sign in with your Google account, confirm you can see the Flow editor, then press **Enter** in the terminal. Your session is saved to `.session/flow_auth.json` (excluded from git).

> **Re-run login.py if you ever get an auth error during generation.**

---

## Usage

### GUI (recommended)

```bash
.venv/bin/python execution/generate_ui.py
```

Fill in the fields and click **Generate**. The log streams live output.

### Command Line

**From a spreadsheet row:**
```bash
.venv/bin/python google-flow-generator/scripts/generate.py \
  --xlsx /path/to/prompts.xlsx \
  --row 1 \
  --type image \
  --out ./output/
```

**From a plain-text prompt:**
```bash
.venv/bin/python google-flow-generator/scripts/generate.py \
  --prompt "A calm ocean at sunset, golden hour, cinematic wide shot" \
  --type video \
  --out ./output/
```

**Key flags:**

| Flag | Description | Default |
|------|-------------|---------|
| `--xlsx` | Path to `.xlsx` spreadsheet | — |
| `--row` | Row number (1 = first data row) | — |
| `--prompt` | Plain-text prompt | — |
| `--type` | `image` or `video` | `video` |
| `--out` | Output folder | `.tmp/` |
| `--timeout` | Max seconds to wait for generation | 600 (video), 300 (image) |
| `--no-headless` | Show the browser window | — |

---

## Spreadsheet Format

Your `.xlsx` file needs at minimum these two columns (names are case-insensitive):

| `Filename` | `Prompt` |
|-----------|---------|
| `rainy_city_night` | `Medium shot. A man walking through a rainy city street...` |
| `coffee_shop` | `{"goal": "cozy coffee shop", "style": "photorealistic", ...}` |

- **Filename** — output file stem (extension added automatically)
- **Prompt** — plain text or a [Nano Banana 2 JSON](https://labs.google/fx/tools/flow) object

The script handles:
- Outer-quoted JSON (`"{ ... }"`) — stripped automatically
- Missing closing `}` — auto-repaired with a warning

---

## Project Structure

```
flow_generator_app/
├── google-flow-generator/
│   └── scripts/
│       ├── login.py              # One-time Google auth
│       ├── generate.py           # Core generation script
│       └── discover_selectors.py # Debug helper for UI changes
├── execution/
│   ├── generate_ui.py            # GUI app
│   └── utils.py
├── directives/
│   └── generate_video.md         # SOP / learnings doc
├── AGENTS.md                     # AI agent instructions
├── .env.example                  # Environment variable template
└── .gitignore
```

---

## Notes

- **Video generation** takes ~60–90 seconds with Veo 3.1 Lite
- **Quota errors** (error 253) are detected and surfaced — do not auto-retry, wait and try again
- If the Flow UI changes and selectors break, run `discover_selectors.py` to debug
- The session file (`.session/flow_auth.json`) contains auth cookies — never commit it

---

## License

MIT
