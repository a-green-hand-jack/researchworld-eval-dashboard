"""Approximate read-out of bar heights from the supplied figure_1.png (pixel measurement).
Per bar, scan the centre column upward from the baseline until the panel background is reached.
Calibration: 2.75 px per accuracy point (gridlines every 20 pts = 55 px) anchored on the CIFAR-10
Retrained test bar = 72% (experimental log); bottom panels are offset 286 px.
Run: python3 -I digitize_figure1.py /initial-state/inputs/2/figure_1.png > figure1_readout.csv"""
import sys, numpy as np, csv
from PIL import Image
im=np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int)
cols={'Retrained':(100,133,186),'Unlearned(+)':(223,147,106),'Unlearned(-)':(202,102,106)}
panels={'CIFAR-10':(0,0),'CIFAR-100':(0,432),'StanfordDogs':(286,0),'Caltech256':(286,432)}
groups=['Test','Remaining','Forget','MIA']
def locate(px,py):
    # bar left edges: first x of each colour run along a row just above the baseline
    row=im[py+232]; found=[]
    for cn,c in cols.items():
        m=np.abs(row-np.array(c)).sum(1)<12; m[:px]=False; m[px+432:]=False
        xs=np.where(m)[0]
        runs=np.split(xs,np.where(np.diff(xs)>1)[0]+1)
        found+= [(r[0],r[-1],cn) for r in runs if len(r)>8]
    return sorted(found)
bg=np.array([240,242,245])
tops={}
for pn,(py,px) in panels.items():
    bars=locate(px,py); assert len(bars)==12,(pn,len(bars))
    for i,(x0,x1,cn) in enumerate(bars):
        xc=(x0+x1)//2; y=py+232
        isbar=lambda yy: np.abs(im[yy,xc]-np.array(cols[cn])).sum()<40
        while y>py+5 and any(isbar(y-k) for k in range(1,4)): y-=1  # bridges 1-2 px gridlines inside bars
        tops[(pn,groups[i//3],cn)]=y-py
ref=tops[('CIFAR-10','Test','Retrained')]
w=csv.writer(sys.stdout); w.writerow(['dataset','metric','method','value_pct_approx'])
for k,t in tops.items(): w.writerow([*k,round(72+(ref-t)/2.75,1)])
