"""Read bar heights off figure_1.png (864x568) by pixel measurement.
Usage: python3 -I digitize_fig1.py <figure_1.png> <out.csv>. Axis 0..80 calibrated per panel from the
plot frame; a constant -0.6 pt bias of the measured top edge is corrected using the CIFAR-10 panel,
whose values are known from the log. Precision about +-1 point; these are NOT log values."""
import sys, csv
from PIL import Image
import numpy as np
im=np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int)
cols={'Retrained':(100,133,186),'Unlearned+':(223,147,106),'Unlearned-':(202,102,106)}
panels={'CIFAR-10':(0,0,10,236),'CIFAR-100':(0,432,10,236),'StanfordDogs':(285,0,296,522),'Caltech256':(285,432,296,522)}
metrics=['test_acc','remaining_acc','forget_acc','mia']
raw={}
for name,(y0,x0,top,base) in panels.items():
    sc=(base-top)/80.0
    for k,c in cols.items():
        m=(np.abs(im-np.array(c)).sum(2)<14)[y0:y0+280,x0:x0+432].copy()
        m[:top-y0+52,300:]=False; m[base-y0+2:,:]=False
        cs=np.where(m.sum(0)>=8)[0]
        gs=[g for g in np.split(cs,np.where(np.diff(cs)>2)[0]+1) if len(g)>=12]
        assert len(gs)==4,(name,k,len(gs))
        for met,g in zip(metrics,gs):
            ys=np.where(m[:,g[len(g)//2]])[0]
            raw[(name,k,met)]=(base-(ys.min()+y0))/sc
known={'Retrained':[72,74,72,50],'Unlearned-':[70,71,68,51.4]}   # CIFAR-10 values from the log
bias=np.mean([raw[('CIFAR-10',k,met)]-v for k,vs in known.items() for met,v in zip(metrics,vs)])
print('bias (pt) on CIFAR-10 vs log:',round(bias,2),file=sys.stderr)
with open(sys.argv[2],'w',newline='') as f:
    w=csv.writer(f); w.writerow(['dataset','method']+metrics)
    for name in panels:
        for k in cols: w.writerow([name,k]+[round(raw[(name,k,met)]-bias,1) for met in metrics])
