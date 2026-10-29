"""Fill the empty boxes of the supplied ACM_task.jpg. Usage: fill_task_figure.py IN.jpg OUT.jpg
Texts follow description_eg.jpg (Question1 <entire_image> -> description; Question2 <cropped_image> + description -> answer)
and the research overview (free-form description -> text embedding -> highest cosine similarity label)."""
import sys
from PIL import Image, ImageDraw, ImageFont
S = 2036 / 2000  # coordinates below are in the 2000px-wide display of the 2036px original
im = Image.open(sys.argv[1]).convert("RGB"); d = ImageDraw.Draw(im)
F = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
def put(box, lines, size, align="center"):
    x0, y0, x1, y1 = [v * S for v in box]
    f = ImageFont.truetype(F, int(size * S))
    lh = f.size * 1.15; y = (y0 + y1) / 2 - lh * len(lines) / 2
    for t in lines:
        w = d.textlength(t, font=f)
        x = (x0 + x1) / 2 - w / 2 if align == "center" else x1 - w
        d.text((x, y), t, font=f, fill="black"); y += lh
put((743, 361, 997, 474), ["Free-form", "description", "of the dish"], 34)
put((1650, 505, 1953, 582), ["Label with highest", "cosine similarity"], 30)
put((640, 112, 850, 166), ["Class names"], 34, align="right")
put((1413, 1091, 1961, 1254), ["Description of the", "entire image"], 38)
put((1655, 1514, 1959, 1590), ["Predicted dish label"], 32)
im.save(sys.argv[2], quality=95)
