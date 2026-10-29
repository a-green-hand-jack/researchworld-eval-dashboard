import glob, os, pandas as pd, numpy as np
rows=[]
for f in sorted(glob.glob('/work/data/glambie/input/*/*.csv')):
    reg=os.path.basename(os.path.dirname(f))
    name=os.path.basename(f)
    d=pd.read_csv(f)
    rname='_'.join(reg.split('_')[1:])
    rest=name[len(rname)+1:-4]
    src=rest.split('_')[0]
    dur=(d.end_dates-d.start_dates)
    rows.append(dict(region=reg,source=src,file=name,n=len(d),unit=d.unit.iloc[0].lower(),
        t0=d.start_dates.min(),t1=d.end_dates.max(),res_med=dur.median(),res_max=dur.max(),author=d.author.iloc[0]))
inv=pd.DataFrame(rows)
inv.to_csv('/work/outputs/input_inventory.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',300)
print(inv.drop(columns='file').to_string())
print(len(inv)); print(inv.groupby('source').size()); print(inv.groupby(['source','unit']).size())
