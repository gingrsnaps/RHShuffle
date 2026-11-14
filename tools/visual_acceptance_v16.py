"""Headless visual contract for the shared public race summary.

Uses an installed Chromium/Chrome binary. It never starts the application,
contacts a provider, or reads private state.
"""
from pathlib import Path
import html, json, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'v16_countdown_uniformity.html'
BROWSER = next((shutil.which(name) for name in ('chromium','chromium-browser','google-chrome','chrome') if shutil.which(name)), None)


def run(width, height, screenshot):
    if not BROWSER:
        raise RuntimeError('Chromium or Chrome is required for visual acceptance.')
    uri = FIXTURE.resolve().as_uri()
    common = [BROWSER, '--headless', '--no-sandbox', '--disable-gpu', '--allow-file-access-from-files',
              f'--window-size={width},{height}']
    try:
        subprocess.run(common + [f'--screenshot={screenshot}', uri], check=True, timeout=20, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dumped = subprocess.check_output(common + ['--dump-dom', uri], text=True, timeout=20, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Chromium did not complete the visual fixture within 20 seconds. Run this check on a browser-capable CI runner.') from exc
    match = re.search(r'<pre id="result">(.*?)</pre>', dumped, re.S)
    if not match:
        raise RuntimeError('Visual fixture did not return computed measurements.')
    value = json.loads(html.unescape(match.group(1)))
    if value['fontA'] != value['fontB'] or value['lineA'] != value['lineB']:
        raise AssertionError(f'Countdown typography differs: {value}')
    if abs(value['heightA'] - value['heightB']) > 1:
        raise AssertionError(f'Race summary heights differ: {value}')
    return value


if __name__ == '__main__':
    out = ROOT / 'tests' / 'visual-output'
    out.mkdir(exist_ok=True)
    results = {
        'desktop': run(1440, 900, out / 'v16-countdown-desktop.png'),
        'mobile': run(430, 900, out / 'v16-countdown-mobile.png'),
    }
    print(json.dumps(results, indent=2))
