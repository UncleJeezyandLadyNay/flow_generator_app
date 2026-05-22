#!/usr/bin/env python3
"""
login.py — One-time interactive Google login for Google Flow.

Opens a visible Chromium window so you can log in manually with your
Google account. Once you're logged in and see the Google Flow interface,
press ENTER in this terminal to save the session and close the browser.

Session is saved to .session/flow_auth.json and reused by generate.py.

Usage:
    .venv/bin/python scripts/login.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# ── resolve project root (two levels up from this script) ─────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent   # Google_Flow_Veo/
SKILL_ROOT = Path(__file__).resolve().parent.parent    # google-flow-generator/
SESSION_DIR = ROOT / ".session"
SESSION_FILE = SESSION_DIR / "flow_auth.json"

FLOW_URL = "https://labs.google/fx/tools/flow"
EDITOR_URL = "https://labs.google/fx/tools/flow"


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright is not installed.")
        print("Run:  .venv/bin/pip install playwright && .venv/bin/playwright install chromium")
        sys.exit(1)

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Google Flow — One-Time Login")
    print("=" * 60)
    print(f"\nOpening Chromium and navigating to: {FLOW_URL}")
    print("\nPlease log in with your Google account in the browser window.")
    print("Once you can see the Google Flow interface (you're logged in),")
    print("come back here and press ENTER to save your session.\n")

    with sync_playwright() as p:
        # Use system Chrome so Google Flow doesn't flag it as an unsupported browser.
        # Fall back to Playwright's Chromium if Chrome isn't installed.
        launch_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
        ]
        try:
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                args=launch_args,
            )
            print("Using system Chrome.")
        except Exception:
            print("System Chrome not found — falling back to Playwright Chromium.")
            browser = p.chromium.launch(
                headless=False,
                args=launch_args,
            )

        context = browser.new_context(
            viewport=None,  # let the maximized window set the size
            java_script_enabled=True,
        )
        # Remove the webdriver flag Google uses to detect automation
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        import re as _re

        page = context.new_page()

        # ── Step 1: Land on Flow and trigger the OAuth sign-in flow ───────────
        print(f"Loading {FLOW_URL} ...")
        page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2000)

        # Click "Create with Google Flow" to force the sign-in redirect,
        # then wait for the navigation to fully settle before checking the URL.
        for label in [r"create with google flow", r"try in google flow"]:
            btn = page.get_by_role("button", name=_re.compile(label, _re.I))
            if btn.count() > 0 and btn.first.is_visible():
                print(f"Clicking '{btn.first.text_content().strip()}' to trigger sign-in...")
                btn.first.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=8_000)
                except Exception:
                    pass
                page.wait_for_timeout(1000)
                break

        print(f"Current URL: {page.url}")

        # ── Step 2: Wait for the user to complete Google sign-in ──────────────
        if "accounts.google.com" in page.url or "signin" in page.url.lower():
            print("\n>>> Sign-in page detected.")
            if sys.stdin.isatty():
                print("    Sign in to your Google account in the browser window.")
                input("    Press ENTER once you are fully signed in: ")
            else:
                print(">>> Non-interactive: sign in to your Google account in the browser window.")
                print("    Watching for sign-in to complete (5 min timeout)...")
                try:
                    page.wait_for_url(
                        lambda url: "accounts.google.com" not in url and "signin" not in url.lower(),
                        timeout=300_000,
                    )
                    print(f"✓ Sign-in complete. URL: {page.url}")
                except Exception:
                    print("Timed out waiting for sign-in — saving whatever session exists.")
        else:
            print("No sign-in page detected — may already be authenticated.")

        # ── Step 3: Navigate back to Flow editor and fully initialize the session
        print(f"\nNavigating back to editor: {EDITOR_URL}")
        page.goto(EDITOR_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(3000)

        # Click entry button again if needed
        for label in [r"create with google flow", r"try in google flow"]:
            btn = page.get_by_role("button", name=_re.compile(label, _re.I))
            if btn.count() > 0 and btn.first.is_visible():
                print(f"Clicking '{btn.first.text_content().strip()}' to open editor...")
                btn.first.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass
                page.wait_for_timeout(2000)
                break

        print(f"Editor page: {page.url}")

        if "auth/error" in page.url:
            print("\nERROR: Google Flow auth error — the account may not have access to Flow,")
            print("       or the sign-in was not completed. Try running with '!' for a fully")
            print("       interactive terminal: ! .venv/bin/python scripts/login.py")

        if sys.stdin.isatty():
            input(">>> Confirm you can see the Flow editor, then press ENTER to save session: ")

        # Save session state
        storage_state = context.storage_state()
        with open(SESSION_FILE, "w") as f:
            json.dump(storage_state, f, indent=2)

        context.close()
        browser.close()

    # Summarize what was saved
    cookie_count = len(storage_state.get("cookies", []))
    origin_count = len(storage_state.get("origins", []))

    print(f"\n✅ Session saved to: {SESSION_FILE}")
    print(f"   Cookies: {cookie_count}  |  Origins: {origin_count}")
    print(f"   Saved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nYou can now run:")
    print('  .venv/bin/python scripts/generate.py --prompt "Your prompt here" --type video')


if __name__ == "__main__":
    main()
