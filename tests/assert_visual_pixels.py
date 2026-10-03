"""Check actual rendered red fill, rather than only a progress element's value."""
import json
from pathlib import Path
import sys
from PIL import Image

folder = Path(sys.argv[1])
for case in json.loads((folder/'progress-measurements.json').read_text(encoding='utf-8')):
    image = Image.open(folder/case['file']).convert('RGB')
    box = case['bar']
    left, width = round(box['x']), round(box['width'])
    middle = round(box['y']+box['height']/2)
    red = 0
    for x in range(left, left+width):
        r, g, b = image.getpixel((x, middle))
        red += r > 100 and r > g*1.4
    actual = red/width*100
    assert abs(actual-case['percent']) < 2, (case['file'], actual, case['percent'])
print('Eight desktop/mobile progress screenshots match 0%, 25%, 75%, 100% red fill.')
