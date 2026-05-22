---
name: google-flow-generator
description: Automate image and video generation using the Google Flow web interface (labs.google/flow). Use this skill whenever the user wants to generate an image or video with a text prompt, wants to use Google Flow, Veo, or Imagen to create media, or says something like "generate a video of...", "create an image of...", "use Google Flow to make...", or "make a clip of...". Always invoke this skill for any media generation request that should go through Google Flow.
---

# Google Flow Generator

Automates the Google Flow web UI (labs.google/flow) to generate images and videos from text prompts using Playwright browser automation.

## Quick Start

```
# One-time login (opens a real browser window — log in manually)
.venv/bin/python scripts/login.py

# Generate media (headless, uses saved session)
.venv/bin/python scripts/generate.py --prompt "A calm ocean at sunset" --type video
.venv/bin/python scripts/generate.py --prompt "A photorealistic cat on a red chair" --type image
```

## How It Works

1. **One-time login**: `login.py` opens a visible Chromium window pointed at `labs.google/flow`. The user logs in with their Google account. The session (cookies + local storage) is saved to `.session/` and reused automatically.
2. **Headless generation**: `generate.py` launches Chromium in headless mode using the saved session, navigates to the generation UI, injects the prompt, triggers generation, waits for completion, and downloads the result to `.tmp/`.

## Session Management

Session state is stored in `.session/` (gitignored). If the session expires, re-run `login.py`.

## Inputs

| Arg | Description | Default |
|-----|-------------|---------|
| `--prompt` | The text prompt to generate from | *required* |
| `--type` | `image` or `video` | `video` |
| `--out` | Output directory | `.tmp/` |
| `--timeout` | Max wait time for generation (seconds) | `300` |

## Outputs

- Downloaded media file saved to `.tmp/<timestamp>_<type>.<ext>`
- Absolute path printed to stdout on success

## Process Detail

### login.py
1. Launch Chromium with `headless=False` + persistent context (`storage_state`)
2. Navigate to `https://labs.google/flow`
3. Pause — user logs in manually
4. Save `storage_state` to `.session/flow_auth.json`
5. Close browser

### generate.py
1. Load `storage_state` from `.session/flow_auth.json` (exit with clear error if missing — run login.py first)
2. Launch headless Chromium with saved state
3. Navigate to `https://labs.google/flow`
4. Detect media type selector and set it (image or video)
5. Find the prompt textarea and type the prompt
6. Click the generate / create button
7. Poll for a downloadable result (image src or video download link appearing in DOM)
8. Download the result to `.tmp/`
9. Print the output path

## Edge Cases & Learnings

- Google Flow UI is a React SPA — wait for elements with `page.wait_for_selector()` rather than fixed sleeps
- If the session is expired, `generate.py` will detect a redirect to the login page and exit with a clear message: "Session expired — run login.py again"
- Generation can take 30–180 seconds for video; use a generous timeout (default 300s)
- The UI may change; if selectors break, run `scripts/discover_selectors.py` to find new ones

## Files

```
google-flow-generator/
├── SKILL.md
└── scripts/
    ├── login.py           — one-time interactive login, saves session
    ├── generate.py        — headless generation using saved session
    └── discover_selectors.py — helper to dump interactive elements from the live page
```
