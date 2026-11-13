#!/usr/bin/env python3
"""Source-level and template acceptance test that does not contact providers."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    commands = [
        [args.python, '-m', 'unittest', 'tests.test_navigation_v12', 'tests.test_admin_reliability_v13'],
        [args.python, 'wager_backend.py', '--check'],
    ]
    for command in commands:
        print('+', ' '.join(command))
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print('PASS: admin route, template, payout, dates and release checks completed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
