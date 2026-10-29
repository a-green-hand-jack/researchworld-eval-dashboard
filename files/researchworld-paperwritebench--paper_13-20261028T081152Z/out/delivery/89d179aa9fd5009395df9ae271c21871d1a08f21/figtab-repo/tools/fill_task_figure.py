"""Fill the empty text boxes of the supplied ACM_task.jpg with the labels the task definitions give.
Usage: python3 fill_task_figure.py <supplied ACM_task.jpg> <output ACM_task.jpg>
Labels come from the supplied overview (Task 1: LMM free-form description -> e5-large-v2 embedding -> cosine similarity
with label embeddings; Task 3: description of the whole meal -> per-dish classification of the crop).
Coordinates are for the 2036x1673 supplied image (displayed coordinates x 1.02)."""
import sys
from PIL import Image, ImageDraw, ImageFont
S = 1.02
F = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
src, dst = sys.argv[1:3]
im = Image.open(src).convert("RGB")
d = ImageDraw.Draw(im)

def put(box, lines, size, anchor_center=True):
    x0, y0, x1, y1 = [v * S for v in box]
    font = ImageFont.truetype(F, int(size * S))
    h = len(lines) * font.size * 1.15
    y = (y0 + y1) / 2 - h / 2
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((x0 + x1) / 2 - w / 2, y), ln, font=font, fill="black")
        y += font.size * 1.15

put((743, 361, 997, 474), ["Free-form", "description"], 38)          # Task 1: LMM output
put((1650, 505, 1953, 582), ["Predicted label"], 36)                  # Task 1: arg-max cosine similarity
put((862, 85, 1040, 130), ["Class names"], 34)                        # Task 1: text-encoder input
put((1413, 1091, 1961, 1254), ["Description of the", "whole meal image"], 40)  # Task 3
put((1655, 1514, 1959, 1591), ["Predicted dish"], 36)                 # Task 3
im.save(dst, quality=95)
