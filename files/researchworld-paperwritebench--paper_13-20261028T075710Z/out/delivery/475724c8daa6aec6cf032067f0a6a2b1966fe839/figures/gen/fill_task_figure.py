"""figures/ACM_task.jpg has empty text boxes; write labels into them.
Input: /initial-state/inputs/4/ACM_task.jpg (unchanged copy kept as figures/ACM_task_original.jpg).
Box labels follow the dataset overview (LMM free-form description -> e5-large-v2 embedding -> cosine-similarity label;
Task 3: menu-level description of the whole image fed to the second LMM call). Box coordinates are in pixels of the original."""
import shutil
from PIL import Image, ImageDraw, ImageFont
SRC = "/initial-state/inputs/4/ACM_task.jpg"
shutil.copyfile(SRC, "figures/ACM_task_original.jpg")
im = Image.open(SRC).convert("RGB")
d = ImageDraw.Draw(im)
F = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
def put(box, lines, size):
    f = ImageFont.truetype(F, size)
    x0, y0, x1, y1 = [round(v * 1.02) for v in box]
    h = sum(size * 1.15 for _ in lines)
    y = (y0 + y1) / 2 - h / 2
    for l in lines:
        w = d.textlength(l, font=f)
        d.text(((x0 + x1) / 2 - w / 2, y), l, font=f, fill="black")
        y += size * 1.15
put((743, 360, 997, 475), ["Free-form", "dish description"], 32)
put((1649, 505, 1953, 583), ["Predicted class"], 40)
put((1413, 1090, 1961, 1254), ["Menu-level description", "of the whole meal image"], 44)
put((1655, 1514, 1959, 1591), ["Predicted class"], 40)
f = ImageFont.truetype(F, 34)
d.text((round(868*1.02), round(150*1.02)), "Class names", font=f, fill="black")
im.save("figures/ACM_task.jpg", quality=95)
