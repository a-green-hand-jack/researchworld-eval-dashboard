import pandas as pd, glob, os, re
BASE='./data/glambie'
def load_inputs():
    rows=[]
    for f in sorted(glob.glob(BASE+'/input/*/*.csv')):
        reg=os.path.basename(os.path.dirname(f)); rid=int(reg.split('_')[0])
        name=os.path.basename(f)[:-4]
        d=pd.read_csv(f)
        grp=re.search(r'_(glaciological|demdiff|altimetry|gravimetry|combined)_',name).group(1)
        d['region_id']=rid; d['region']=reg; d['source']=grp; d['file']=name
        rows.append(d)
    return pd.concat(rows,ignore_index=True)
if __name__=='__main__':
    d=load_inputs()
    print(d.file.nunique(), d.groupby('region_id').file.nunique().to_dict())
    print(d.groupby(['source','unit']).file.nunique())
    d['dur']=d.end_dates-d.start_dates
    s=d.groupby(['file']).agg(src=('source','first'),n=('dur','size'),dur=('dur','median'),t0=('start_dates','min'),t1=('end_dates','max'),unit=('unit','first'))
    print(s.groupby('src')[['dur','t0','t1']].describe().T.to_string())
    print(d.isna().sum())
