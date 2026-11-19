"""Mechanical audit facts and convergence/coverage/Monte-Carlo diagnostics, not new policy selection."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sensitivity import alias_groups
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'artifacts';out.mkdir(exist_ok=True);original=json.loads((ROOT/'protocol/manifests.json').read_text());sens=json.loads((ROOT/'protocol/sensitivity_manifests.json').read_text());rows=[]
    metadata=pd.read_parquet(ROOT/'data/raw/openllm.parquet');metadata['priority']=metadata.Precision.map({'bfloat16':0,'float16':1}).fillna(2);metadata=metadata.sort_values(['fullname','priority','eval_name']).drop_duplicates('fullname').set_index('fullname')
    for m in original:
        if m['dataset']!='openllm' or m['regime']!='organization':continue
        meta=metadata.loc[m['ids']];tr=meta.iloc[m['all_train']];te=meta.iloc[m['all_test']]
        shared=set(v for v in tr['Model sha'].dropna().astype(str) if v.strip())&set(v for v in te['Model sha'].dropna().astype(str) if v.strip())
        pairs=sum(int((tr['Model sha']==s).sum())*int((te['Model sha']==s).sum()) for s in shared)
        rows.append(dict(seed=m['seed'],shared_nonempty_sha=len(shared),shared_sha_train_test_pairs=pairs))
    pd.DataFrame(rows).to_csv(out/'alias_overlap.csv',index=False)
    wide=[]
    for m in sens:
        df=pd.read_csv(ROOT/f'data/processed/{m["dataset"]}.csv',index_col=0)[m['panel']];T=m['panel'][m['nc']:];test=df.iloc[m['test']]
        wide.append(dict(dataset=m['dataset'],condition=m['sensitivity'],seed=m['seed'],candidate=m['nc'],audit=len(T),train=len(m['train']),validation=len(m['val']),test=len(m['test']),test_groups=len(set(m['groups'][i] for i in m['test'])),observed_test_audit_min=int(test[T].notna().sum(axis=1).min()),observed_test_audit_max=int(test[T].notna().sum(axis=1).max()),test_fraction=len(m['test'])/len(df)))
    pd.DataFrame(wide).to_csv(out/'sensitivity_cohorts.csv',index=False)
    connected=[m for m in sens if m['dataset']=='openllm']
    comp=np.array(connected[0]['components']);sizes=pd.Series(comp).value_counts();giant=str(sizes.index[0]);placements=[]
    for m in connected:
        placements.append(dict(seed=m['seed'],train_giant_rows=int(np.sum(comp[m['train']]==giant)),validation_giant_rows=int(np.sum(comp[m['val']]==giant)),test_giant_rows=int(np.sum(comp[m['test']]==giant)),test_rows=len(m['test']),test_giant_fraction=float(np.mean(comp[m['test']]==giant))))
    (out/'connected_components.json').write_text(json.dumps(dict(n_components=len(sizes),giant_rows=int(sizes.iloc[0]),total_rows=len(comp),giant_fraction=float(sizes.iloc[0]/len(comp)),placements=placements),indent=2))
    conv=[]
    for folder in ['results','results/sensitivity']:
        for p in sorted((ROOT/folder).glob('*_done.json')):
            r=json.loads(p.read_text());best=None
            for t in r['tuning']:
                if t['kind']!='lowrank':continue
                if best is None or t['risk']<best['risk']-1e-4 or (abs(t['risk']-best['risk'])<=1e-4 and (t['rank'],-t['alpha'])<(best['rank'],-best['alpha'])):best=t
            if best:conv.append(dict(run=p.stem,rank=best['rank'],alpha=best['alpha'],val_risk=best['risk'],converged_starts=sum(l['converged'] for l in best['fits']),total_starts=len(best['fits']),max_iterations=max(l['iterations'] for l in best['fits'])))
    pd.DataFrame(conv).to_csv(out/'selected_lowrank.csv',index=False)
    mc=[]
    for p in sorted((ROOT/'results/predictions').glob('*dense.npz')):
        arr=np.load(p);X=arr['truth'];nc=int(arr['nc']);Z=(X-arr['mu'])/arr['sd'];core=[1,2,4] if p.name.startswith('mteb') else [1,2];pathloss=np.zeros((50,len(core)))
        for ki,k in enumerate(core):
            prefix='random__k'+str(k)+'__pattern'
            for key in arr.files:
                if not key.startswith(prefix) or key.endswith('__rows') or key.endswith('__anchors'):continue
                ix=arr[key+'__rows'];P=arr[key];T=np.arange(nc,Z.shape[1]);loss=((P[:,:,T]-Z[ix][:,T])**2).mean(axis=2)
                pathloss[:,ki]+=loss.sum(axis=1)/len(X)
        meanloss=pathloss.mean(axis=1);mc.append(dict(run=p.stem,core_random_nmse=meanloss.mean(),bank_mc_se=meanloss.std(ddof=1)/np.sqrt(50),relative_mc_se=meanloss.std(ddof=1)/np.sqrt(50)/meanloss.mean()))
    pd.DataFrame(mc).to_csv(out/'random_bank_mc.csv',index=False)
    print(pd.DataFrame(wide).to_string(index=False));print(pd.DataFrame(mc).to_string(index=False))
if __name__=='__main__':main()
