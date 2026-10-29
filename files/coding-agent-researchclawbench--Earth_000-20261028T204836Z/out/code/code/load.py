import glob, os, re
import numpy as np, pandas as pd
D='/work/data/glambie'
def inventory():
    rows=[]
    for f in sorted(glob.glob(D+'/input/*/*.csv')):
        reg=f.split('/')[-2]
        d=pd.read_csv(f)
        base=os.path.basename(f)
        rn=reg.split('_',1)[1]
        rest=base[len(rn)+1:-4]
        src=rest.split('_')[0]
        dur=(d.end_dates-d.start_dates)
        rows.append(dict(region=reg,file=f,src=src,name=rest,n=len(d),start=d.start_dates.min(),end=d.end_dates.max(),
            dur_med=dur.median(),unit=d.unit.iloc[0].lower(),neg_gap=int((d.start_dates.values[1:]<d.end_dates.values[:-1]-1e-6).sum())))
    return pd.DataFrame(rows)
if __name__=='__main__':
    inv=inventory(); pd.set_option('display.width',250,'display.max_rows',500,'display.max_colwidth',60)
    print(len(inv)); print(inv.groupby('src').size()); print(inv.unit.value_counts())
    print(inv.drop(columns='file').to_string())
