"""Read approximate values off the solid (moving-average) curves of the two Task-2 JPEGs by colour matching.
Axis calibration (pixel rows of y ticks, columns of x ticks) was set by hand from the supplied images; precision ~ +-0.01-0.02."""
import sys, numpy as np
from PIL import Image
def curves(path, y0, y1, ytop, ybot_val, cols, xlo, xhi):
    im = np.asarray(Image.open(path).convert("RGB")).astype(int)
    out = {}
    for name, rgb in cols.items():
        m = (np.abs(im - np.array(rgb)).sum(2) < 40)
        res = []
        for x in range(xlo, xhi):
            ys = np.where(m[:, x])[0]
            ys = ys[(ys > ytop) & (ys < y1)]
            res.append((x, ys.mean() if len(ys) else np.nan))
        out[name] = res
    return out
