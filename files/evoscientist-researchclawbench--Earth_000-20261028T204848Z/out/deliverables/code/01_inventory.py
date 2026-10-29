"""Inventory of GlaMBIE input datasets: source type, unit, temporal coverage/resolution."""
import glob, os, re
import pandas as pd, numpy as np
rows=[]
for f in sorted(glob.glob('data/glambie/input/*/*.csv')):
    reg=f.split('/')[-2]; name=os.path.basename(f)[:-4]
    rnum=int(reg.split('_')[0]); rname=reg.split('_',1)[1]
    rest=name[len(rname)+1:]
    src=rest.split('_')[0]; grp=rest[len(src)+1:]
    d=pd.read_csv(f)
    dur=(d.end_dates-d.start_dates)
    rows.append(dict(region_id=rnum,region=rname,source=src,dataset=grp,author=d.author.iloc[0],
        unit=d.unit.iloc[0].lower(),n=len(d),start=d.start_dates.min(),end=d.end_dates.max(),
        med_dur=dur.median(),max_dur=dur.max(),file=f))
inv=pd.DataFrame(rows).sort_values(['region_id','source','dataset'])
inv.to_csv('outputs/input_inventory.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',400); pd.set_option('display.max_colwidth',40)
print(inv.drop(columns='file').to_string())
print(inv.groupby('source').size()); print(inv.groupby(['source','unit']).size())
