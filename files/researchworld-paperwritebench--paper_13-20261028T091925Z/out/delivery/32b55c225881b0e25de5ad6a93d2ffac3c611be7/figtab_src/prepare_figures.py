"""Prepare paper-ready figures from the frozen inputs (/initial-state/inputs/4).

- ACM_task.jpg: the supplied schematic has empty boxes; we fill them with
  generic role labels (no example outputs are invented) taken from the
  research overview (free-form description -> e5-large-v2 -> cosine argmax).
- All others are copied unchanged (re-encoded only if wider than 2000 px).
"""
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont

SRC = sys.argv[1] if len(sys.argv) > 1 else "/initial-state/inputs/4"
DST = sys.argv[2] if len(sys.argv) > 2 else "figures"
os.makedirs(DST, exist_ok=True)
FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

def centered(d, box, lines, size):
    f = ImageFont.truetype(FONT, size)
    x0, y0, x1, y1 = box
    h = len(lines) * (size + 6)
    y = (y0 + y1 - h) / 2
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((x0 + x1 - w) / 2, y), ln, font=f, fill="black")
        y += size + 6

im = Image.open(f"{SRC}/ACM_task.jpg").convert("RGB")
s = 2036 / 2000  # coordinates below were read on a 2000-px-wide view
d = ImageDraw.Draw(im)
sc = lambda b: tuple(int(v * s) for v in b)
centered(d, sc((750, 365, 992, 470)), ["Free-form", "dish description"], 36)
centered(d, sc((1655, 510, 1948, 578)), ["Predicted label"], 36)
centered(d, sc((1420, 1096, 1955, 1248)), ["Menu-level description", "of the whole meal image"], 38)
centered(d, sc((1660, 1518, 1953, 1586)), ["Predicted label"], 36)
centered(d, sc((600, 105, 850, 170)), ["218 class names"], 34)
im.save(f"{DST}/ACM_task.jpg", quality=95)

for p in sorted(glob.glob(f"{SRC}/*.jpg")):
    n = os.path.basename(p)
    if n == "ACM_task.jpg":
        continue
    im = Image.open(p).convert("RGB")
    if im.width > 2000:
        im = im.resize((2000, round(im.height * 2000 / im.width)), Image.LANCZOS)
    im.save(f"{DST}/{n}", quality=95)
