#!/usr/bin/env python3
"""
discover_selectors.py — Debug helper for when the Google Flow UI changes.

Opens a VISIBLE browser with the saved session, navigates to Google Flow,
then dumps all interactive elements (buttons, inputs, textareas, links)
to stdout and to .tmp/selectors_<timestamp>.json.

Use this when generate.py can't find the prompt input or generate button.

Usage:
    .venv/bin/python scripts/discover_selectors.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_FILE = ROOT / ".session" / "flow_auth.json"
TMP_DIR = ROOT / ".tmp"
FLOW_URL = "https://labs.google/fx/tools/flow"


def main():
    if not SESSION_FILE.exists():
        print(f"ERROR: No session file at {SESSION_FILE}")
        print("Run login.py first.")
        sys.exit(1)

    with open(SESSION_FILE) as f:
        storage_state = json.load(f)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: Playwright not installed. Run: .venv/bin/pip install playwright")
        sys.exit(1)

    print(f"Opening {FLOW_URL} with saved session...")
    print("Dumping all interactive elements...\n")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            )
        except Exception:
            browser = p.chromium.launch(
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            )
        context = browser.new_context(
            storage_state=storage_state,
            viewport=None,
            java_script_enabled=True,
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()
        import re as _re

        # Watch for new tabs opened by the entry button
        new_page = None
        def on_page(p):
            nonlocal new_page
            new_page = p
        context.on("page", on_page)

        page.goto(FLOW_URL, wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(3000)
        print(f"URL after load: {page.url}")
        print(f"Title: {page.title()}")

        # Click "New project" to enter the editor (project gallery is the landing page)
        for label in [r"new project", r"create with google flow", r"try in google flow"]:
            btn = page.get_by_role("button", name=_re.compile(label, _re.I))
            if btn.count() > 0 and btn.first.is_visible():
                print(f"Clicking '{btn.first.text_content().strip()}' ...")
                btn.first.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass
                break

        page.wait_for_timeout(6000)
        print(f"Editor URL: {page.url}")

        # Switch to new tab if one opened
        active = new_page if new_page else page
        if new_page:
            new_page.wait_for_load_state("networkidle", timeout=15_000)
            print(f"New tab opened: {new_page.url}")
        print(f"Active page URL: {active.url}")
        print(f"Active page title: {active.title()}")

        # Pierce shadow DOM with a recursive JS traversal
        elements = active.evaluate("""() => {
            const results = [];
            const TAGS = new Set(['button','input','textarea','select','a']);
            const ROLES = ['button','textbox','tab','combobox','searchbox','option'];

            function collect(root) {
                const walker = document.createTreeWalker(
                    root,
                    NodeFilter.SHOW_ELEMENT,
                    null,
                    false
                );
                let node;
                while ((node = walker.nextNode())) {
                    const tag = node.tagName.toLowerCase();
                    const role = node.getAttribute('role') || '';
                    if (!TAGS.has(tag) && !ROLES.includes(role)
                        && !node.hasAttribute('contenteditable')
                        && tag !== 'div') continue;
                    const rect = node.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    results.push({
                        tag,
                        type: node.type || null,
                        role: node.getAttribute('role'),
                        id: node.id || null,
                        name: node.name || null,
                        ariaLabel: node.getAttribute('aria-label'),
                        placeholder: node.placeholder || null,
                        contenteditable: node.getAttribute('contenteditable'),
                        textContent: node.textContent?.trim().slice(0, 80) || null,
                        className: (node.className || '').slice(0, 120),
                        dataTestId: node.getAttribute('data-testid'),
                        rect: {w: Math.round(rect.width), h: Math.round(rect.height)},
                        inShadow: node.getRootNode() !== document,
                    });
                    // Recurse into shadow roots
                    if (node.shadowRoot) collect(node.shadowRoot);
                }
            }
            collect(document.body);
            return results;
        }""")

        context.close()
        browser.close()

    # Print and save
    print(json.dumps(elements, indent=2))
    print(f"\nTotal elements found: {len(elements)}")

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = TMP_DIR / f"selectors_{ts}.json"
    with open(out, "w") as f:
        json.dump(elements, f, indent=2)
    print(f"\nSaved to: {out}")


if __name__ == "__main__":
    main()
