"""Approximate digitization of bar heights in figures/figure_1.png.
Axis calibration: bar baseline (y=0) and top spine (y=80) found from the image.
Usage: digitize_fig1.py <png> [out.csv]"""
import sys, csv, numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(int)
COL = {'Retrained':(100,133,186),'Unlearned(+)':(223,147,106),'Unlearned(-)':(202,102,106)}
PANELS = {'CIFAR-10':(0,432,0,262),'CIFAR-100':(432,864,0,262),
          'StanfordDogs':(0,432,285,545),'Caltech256':(432,864,285,545)}
GROUPS = ['Test','Remaining','Forget','MIA']
def m(c,tol=14): return (np.abs(im-np.array(c)).sum(axis=2) < tol*3)
rows=[]
for pn,(x0,x1,y0,y1) in PANELS.items():
    # collect bar column runs per colour (exclude legend: legend is upper right, small height)
    bars=[]
    for cn,c in COL.items():
        mk=m(c)[y0:y1,x0:x1]
        colh=mk.sum(axis=0)
        xs=np.where(colh>25)[0]   # bar columns (legend swatches are <15 px tall)
        # split into runs
        runs=np.split(xs,np.where(np.diff(xs)>1)[0]+1)
        for r in runs:
            if len(r)<8: continue
            xm=r[len(r)//2]
            ys=np.where(mk[:,xm])[0]
            # keep only the run that reaches the baseline (drops legend swatches above MIA bars)
            br=np.split(ys,np.where(np.diff(ys)>6)[0]+1)[-1]
            bars.append((x0+xm,cn,y0+br.min(),y0+br.max()))
    bars.sort()
    base=np.median([b[3] for b in bars])+1.0      # baseline pixel row
    # top spine: darkest horizontal line in panel near top
    dark=(im[y0:y1,x0+60:x1-10].sum(axis=2)<3*110).sum(axis=1)
    spine=base-226.5   # 80% gridline/top edge: panel plot area is 226 px tall (checked on gridlines at 20/40/60%)
    print(pn,'baseline',base,'spine',spine,'nbars',len(bars))
    for i,(x,cn,top,bot) in enumerate(bars):
        rows.append(dict(panel=pn,group=GROUPS[i//3],method=cn,px_top=int(top),baseline=float(base),spine=spine))
# calibrate 80 -> spine
out=[]
for r in rows:
    scale=80/(r['baseline']-r['spine'])
    r['value_est']=round((r['baseline']-r['px_top'])*scale,1)
    out.append(r)
w=csv.DictWriter(open(sys.argv[2] if len(sys.argv)>2 else '/dev/stdout','w'),fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
