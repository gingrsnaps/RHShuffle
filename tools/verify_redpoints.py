"""Optional offline audit, not a server launcher: python tools/verify_redpoints.py receipts.json"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fairness import verify

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify RedPoints receipts without contacting a server.')
    parser.add_argument('file', type=Path)
    parser.add_argument('--commitment', help='Previously saved commitment; for a single receipt.')
    args = parser.parse_args()
    try:
        values = json.loads(args.file.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(f'Cannot read receipt JSON: {exc}')
    values = values if isinstance(values, list) else [values]
    if not values or args.commitment and len(values) != 1:
        parser.error('Provide receipts, or one receipt when using --commitment.')
    checks = []
    for index, value in enumerate(values, 1):
        try: passed = verify(value, args.commitment)
        except (ValueError, KeyError, TypeError): passed = False
        checks.append(passed)
        label = value.get('request_id', f'receipt-{index}') if isinstance(value, dict) else f'receipt-{index}'
        print(('PASS' if passed else 'FAIL') + ' ' + str(label))
    raise SystemExit(0 if all(checks) else 1)
