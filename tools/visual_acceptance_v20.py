"""Optional live V20 mobile visual checks.

Usage:
  python tools/visual_acceptance_v20.py --base-url https://example.com --output screenshots

Requires Playwright and a Chromium installation. It performs read-only public checks.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from urllib.parse import urljoin


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', default='v20-screenshots')
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('Playwright is not installed. Install requirements-dev.txt and Playwright browsers.')
        return 2
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, path in [('shuffle','/'), ('empiredrop','/?provider=empiredrop')]:
            page = browser.new_page(viewport={'width':390,'height':844}, device_scale_factor=1)
            page.goto(urljoin(args.base_url, path), wait_until='networkidle')
            page.screenshot(path=str(out/f'{name}-390.png'), full_page=True)
            overflow = page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            if overflow > 1:
                failures.append(f'{name}: horizontal overflow {overflow}px')
            rows = page.locator('.responsive-results tbody tr')
            if rows.count():
                height = rows.nth(0).bounding_box()['height']
                if height > 82:
                    failures.append(f'{name}: compact row is {height:.1f}px tall')
            if page.locator('.public-table').count() != 1:
                failures.append(f'{name}: expected one grouped standings panel')
            page.close()
        browser.close()
    if failures:
        for failure in failures:
            print('FAIL:', failure)
        return 1
    print('PASS: V20 mobile grouped-list checks completed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
