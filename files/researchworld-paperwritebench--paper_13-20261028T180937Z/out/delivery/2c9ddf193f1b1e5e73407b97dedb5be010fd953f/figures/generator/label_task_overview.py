"""Fill the empty boxes of the supplied ACM_task.jpg (Task overview) with the text the boxes were left without.
Only the empty white boxes (and the unlabeled input arrow of Task 1) are written to; the rest of the image is untouched.
Usage: label_task_overview.py INPUT_JPG OUTPUT_JPG
Box coordinates are in pixels of the original 2036x1673 image (read from the image).
"""
import sys
from PIL import Image, ImageDraw, ImageFont

src, dst = sys.argv[1], sys.argv[2]
FONT = '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
ITAL = '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'
im = Image.open(src).convert('RGB')
d = ImageDraw.Draw(im)
S = 1.02  # displayed -> original

def box_text(box, lines, size, font=FONT):
    x0, y0, x1, y1 = [int(v * S) for v in box]
    f = ImageFont.truetype(font, size)
    hs = [d.textbbox((0, 0), t, font=f)[3] for t in lines]
    gap = int(size * 0.25)
    total = sum(hs) + gap * (len(lines) - 1)
    y = y0 + ((y1 - y0) - total) / 2 - 4
    for t, h in zip(lines, hs):
        w = d.textlength(t, font=f)
        assert w <= (x1 - x0) - 8, (t, w, x1 - x0)
        d.text((x0 + ((x1 - x0) - w) / 2, y), t, font=f, fill=(0, 0, 0))
        y += h + gap

# Task 1: LMM output box, final label box, and the text-encoder input arrow
box_text((743, 361, 997, 474), ['Free-form dish', 'description'], 36)
box_text((1649, 505, 1953, 582), ['Predicted label'], 36)
f = ImageFont.truetype(FONT, 27)
for i, t in enumerate(['Class names', '(218 classes)']):
    w = d.textlength(t, font=f)
    d.text((int(1033 * S) - w, int((70 + 30 * i) * S)), t, font=f, fill=(0, 0, 0))
# Task 3: description box (entire image) and final label box
box_text((1413, 1091, 1961, 1254), ['Description of the entire', 'image (all dishes)'], 38)
box_text((1654, 1514, 1960, 1590), ['Dish label'], 36)
im.save(dst, quality=95)
