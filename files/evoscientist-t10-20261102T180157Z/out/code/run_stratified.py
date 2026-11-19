"""Additional exact comparator: replay the identical data draws, not new inputs."""
import argparse, json, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from run_experiments import ROOT,BASE_SEED,SCENARIOS,conditional_mean,moments,wilson
from exact_stratified import stratified_interval

def cell(config):
    name,n,ratio,reps,tag=config; N=n*ratio
    rng=np.random.default_rng(np.random.SeedSequence([BASE_SEED,SCENARIOS.index(name),n,ratio]))
    real=name in ['galaxies','forest']
    data=np.load(ROOT/'data'/f'{name}.npz') if real else None
    mu=float(data['Y'].mean()) if real else moments(name)[0]
    rows=[]; t0=time.perf_counter()
    for rep in range(reps):
        if real:
            il=rng.integers(0,len(data['Y']),n); iu=rng.integers(0,len(data['Y']),N)
            y=data['Y'][il]; sl=data['Yhat'][il]; su=data['Yhat'][iu]
        else:
            sl=rng.uniform(size=n); su=rng.uniform(size=N)
            y=rng.binomial(1,conditional_mean(name,sl))
        lo,hi,raw=stratified_interval(y,sl,su)
        rows.append((name,n,N,ratio,tag,rep,'cp_strat2',mu,lo,hi,hi-lo,raw,int(lo<=mu<=hi),-1))
    cols=['scenario','n','N','ratio','grid','rep','method','truth','lower','upper','width','raw_width','covered','selected']
    df=pd.DataFrame(rows,columns=cols)
    stem=f'{name}_n{n}_r{ratio}'
    (ROOT/'results'/'supplement_raw').mkdir(exist_ok=True)
    df.to_csv(ROOT/'results'/'supplement_raw'/f'{stem}.csv.gz',index=False,compression='gzip',float_format='%.12g')
    # Paired uncertainty relative to SAME original data draws.
    orig=pd.read_csv(ROOT/'results'/'raw'/f'{stem}.csv.gz')
    pp=orig[orig.method=='ppipp'].sort_values('rep').width.to_numpy()
    assert len(pp)==reps
    w=df.width.to_numpy(); rat=w.mean()/pp.mean(); lo,hi=wilson(df.covered.sum(),reps)
    out=dict(scenario=name,n=n,N=N,ratio=ratio,grid=tag,method='cp_strat2',reps=reps,truth=mu,
        coverage=df.covered.mean(),cov_lo=lo,cov_hi=hi,width=w.mean(),width_se=w.std(ddof=1)/np.sqrt(reps),
        raw_width=w.mean(),width_ratio_ppipp=rat,ratio_se=((w-rat*pp)/pp.mean()).std(ddof=1)/np.sqrt(reps),
        paired_diff=(w-pp).mean(),paired_diff_se=(w-pp).std(ddof=1)/np.sqrt(reps),seconds=time.perf_counter()-t0)
    print(stem,'strat done',flush=True)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--jobs',type=int,default=4);a=p.parse_args();t=time.perf_counter()
    config=json.loads((ROOT/'results'/'config.json').read_text()); cells=config['cells']
    with ProcessPoolExecutor(max_workers=a.jobs) as pool: out=list(pool.map(cell,cells))
    pd.DataFrame(out).to_csv(ROOT/'results'/'stratified_summary.csv',index=False)
    (ROOT/'results'/'stratified_config.json').write_text(json.dumps({'method':'cp_strat2','replayed_cells':cells,'wall_seconds':time.perf_counter()-t,'threshold':.5,'error_allocation':[1/3]*3},indent=2))
    print('SUPPLEMENT TOTAL',time.perf_counter()-t,flush=True)

if __name__=='__main__':main()
