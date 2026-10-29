"""Simplified re-implementation of GlaMBIE-style reconciliation of regional glacier mass change.
Inputs: data/glambie/input (solutions); area time series from data/glambie/results (used ONLY for Gt<->m w.e. conversion).
Output: annual (calendar-year) regional + global series with uncertainties."""
import numpy as np, pandas as pd, glob, os, warnings
warnings.filterwarnings('ignore')
from load import load_inputs, BASE

DT=1/12; T0=1995.0; T1=2025.0
T=np.arange(T0,T1,DT)            # month starts
TC=T+DT/2                          # month centres
NM=len(T)
RHO_ICE=0.85                        # m (ice-equivalent elevation) -> m w.e.
RHO_WITHIN=0.5                      # assumed error correlation between solutions of the same data group
GROUPS=['dg','altimetry','gravimetry']
REGNAME={1:'Alaska',2:'Western Canada & US',3:'Arctic Canada North',4:'Arctic Canada South',5:'Greenland Periphery',
 6:'Iceland',7:'Svalbard',8:'Scandinavia',9:'Russian Arctic',10:'North Asia',11:'Central Europe',12:'Caucasus & Middle East',
 13:'Central Asia',14:'South Asia West',15:'South Asia East',16:'Low Latitudes',17:'Southern Andes',18:'New Zealand',19:'Antarctic & Subantarctic'}

SMALL_AREA_KM2=5000.0
# regions where GRACE-type gravimetry is known to be contaminated by neighbouring ice sheets, hydrology or GIA
GRAV_CONTAMINATED={2,5,13,14,15,19}
def default_exclusions(rid,mean_area):
    """Groups excluded a priori in a region (documented method-suitability rules)."""
    ex=set()
    if mean_area<SMALL_AREA_KM2: ex|={'gravimetry','altimetry'}
    if rid in GRAV_CONTAMINATED: ex.add('gravimetry')
    return ex

def region_files():
    m={}
    for f in glob.glob(BASE+'/results/calendar_years/*.csv'):
        b=os.path.basename(f); m[int(b.split('_')[0])]=f
    return m

def area_monthly(rid):
    d=pd.read_csv(region_files()[rid])
    mid=(d.start_dates+d.end_dates)/2
    return np.interp(TC,mid,d.glacier_area)     # km2, constant extrapolation

def nanmean(a,axis=0):
    with np.errstate(all='ignore'):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore'); return np.nanmean(a,axis=axis)

def sol_to_monthly(d,area,rho=RHO_ICE):
    """rate (m w.e./yr) and error-rate (m w.e./yr) on monthly grid for one solution (DataFrame of one file)."""
    d=d.dropna(subset=['changes']).copy()
    unit=d.unit.iloc[0].lower()
    dur=(d.end_dates-d.start_dates).values
    ch=d.changes.values; er=d.errors.values.astype(float)
    # error fill: NaN errors -> median error-rate of solution, else NaN handled later
    rate=ch/dur
    # annual-equivalent error rate: multi-year/annual periods -> e/dur (rate error, mostly systematic);
    # sub-annual (monthly) periods -> e*sqrt(dur): monthly errors are treated as independent uncertainties of the
    # monthly state and averaged over the 12 months of a year (stated Gt monthly errors exceed the signal std, so
    # treating them as independent increments (e/sqrt(dur)) is not credible; see report)
    erate=np.where(dur>=1.0,er/dur,er*np.sqrt(dur))
    eann=np.where(dur>=1.0,er/dur,er/np.sqrt(dur))   # error of a single calendar-year anomaly (independent increments)
    if np.isnan(erate).all(): erate=np.full_like(rate,np.nan); eann=erate.copy()
    else:
        erate=np.where(np.isnan(erate),np.nanmedian(erate),erate); eann=np.where(np.isnan(eann),np.nanmedian(eann),eann)
    R=np.full(NM,np.nan); E=np.full(NM,np.nan); EA=np.full(NM,np.nan); cnt=np.zeros(NM)
    Rs=np.zeros(NM); Es=np.zeros(NM); EAs=np.zeros(NM)
    for s,e,r,x,xa in zip(d.start_dates.values,d.end_dates.values,rate,erate,eann):
        idx=np.where((TC>=s)&(TC<e))[0]
        Rs[idx]+=r; Es[idx]+=x; EAs[idx]+=xa; cnt[idx]+=1
    ok=cnt>0; R[ok]=Rs[ok]/cnt[ok]; E[ok]=Es[ok]/cnt[ok]; EA[ok]=EAs[ok]/cnt[ok]
    if unit=='gt':
        f=1e3/area           # Gt -> m w.e.
        R=R*f; E=E*f; EA=EA*f
    elif unit=='m':
        R=R*rho; E=E*rho; EA=EA*rho
    return R,E,EA

def group_of(src,combined_to='dg'):
    if src in('glaciological','demdiff'): return 'dg'
    if src=='combined': return combined_to
    return src

EDGE='shift'   # 'shift': window shifted inward at series edges (constant level over the last/first W/2 yr); 'truncate': shrinking window
def ma(x,W):
    """nan-aware centred moving average over W years; edge handling per EDGE."""
    n=int(round(W/DT))|1; h=n//2
    out=np.full(len(x),np.nan); ok=~np.isnan(x)
    c=np.concatenate([[0],np.cumsum(np.where(ok,x,0))]); k=np.concatenate([[0],np.cumsum(ok)])
    if not ok.any(): return out
    i0=np.argmax(ok); i1=len(x)-np.argmax(ok[::-1])      # valid span [i0,i1)
    for i in range(i0,i1):
        if EDGE=='shift' and (i1-i0)>n:
            a=min(max(i0,i-h),i1-n); b=a+n
        else:
            a=max(i0,i-h); b=min(i1,i+h+1)
        cnt=k[b]-k[a]
        if cnt>0: out[i]=(c[b]-c[a])/cnt
    return out

def build_group(sols,W=5.0,lowres_thr=2.0):
    """sols: list of dict(R,E,dur). Returns level, anomaly, error arrays (monthly) and n solutions."""
    L=[s for s in sols if s['dur']>=lowres_thr]; H=[s for s in sols if s['dur']<lowres_thr]
    level=np.full(NM,np.nan); anom=np.full(NM,np.nan)
    if H:
        Hs=[]; A=[]
        for s in H:
            sm=ma(s['R'],W); sm[np.isnan(s['R'])]=np.nan   # level only where solution exists
            Hs.append(sm); A.append(s['R']-sm)
        Hs=np.array(Hs); anom=nanmean(np.array(A))
        hs=nanmean(Hs)
    if L:
        Lev=nanmean(np.array([s['R'] for s in L]))
        if H:
            ov=~np.isnan(Lev)&~np.isnan(hs)
            off=np.nanmean(Lev[ov]-hs[ov]) if ov.any() else 0.0
            level=np.where(~np.isnan(Lev),Lev,hs+off)
        else: level=Lev
    elif H: level=hs
    # error: rms of solution error-rates (correlated within group) ; quadrature with sample spread
    Es=np.array([s['E'] for s in sols]); Rs=np.array([s['R'] for s in sols])
    n=len(sols); err=np.sqrt(nanmean(Es**2)*(RHO_WITHIN+(1-RHO_WITHIN)/n))
    EAs=np.array([s['EA'] for s in sols]); eann=np.sqrt(nanmean(EAs**2))
    return level,anom,err,len(sols),eann

def align_levels(levels,iters=20):
    """Offset each group level so its mean over overlap with the others matches the mean of the others."""
    g=list(levels); off={k:0.0 for k in g}
    for _ in range(iters):
        for k in g:
            others=[levels[o]+off[o] for o in g if o!=k]
            if not others: continue
            mo=nanmean(np.array(others)); ov=~np.isnan(mo)&~np.isnan(levels[k])
            if ov.any(): off[k]=np.nanmean(mo[ov]-levels[k][ov])
        # centre offsets to zero-mean to prevent drift
        m=np.mean(list(off.values()))
        for k in g: off[k]-=m
    return off

def reconcile_region(rid,inp=None,W=5.0,weight_anom='ivar',combined_to='dg',rho=RHO_ICE,drop_groups='default',align=True,drop_files=()):
    inp=load_inputs() if inp is None else inp
    d=inp[inp.region_id==rid]; area=area_monthly(rid)
    if drop_groups=='default': drop_groups=default_exclusions(rid,area[(T>=2000)&(T<2024)].mean())
    grp={g:[] for g in GROUPS}
    for fn,df in d.groupby('file'):
        if fn in drop_files: continue
        g=group_of(df.source.iloc[0],combined_to)
        if g in drop_groups: continue
        R,E,EA=sol_to_monthly(df,area,rho)
        if np.isnan(R).all(): continue
        dur=np.median((df.end_dates-df.start_dates).values)
        grp[g].append(dict(R=R,E=E,EA=EA,dur=dur,file=fn))
    lev={};an={};er={};ns={};ea={}
    for g,s in grp.items():
        if s: lev[g],an[g],er[g],ns[g],ea[g]=build_group(s,W)
    off=align_levels(lev) if (align and len(lev)>1) else {k:0.0 for k in lev}
    L=np.array([lev[g]+off[g] for g in lev])
    level=nanmean(L); ng=np.sum(~np.isnan(L),axis=0)
    spread=np.where(ng>1,np.nanstd(L,axis=0,ddof=1) if len(lev)>1 else 0,0)
    ag=[g for g in an if not np.all(np.isnan(an[g]))]
    if ag:
        A=np.array([an[g] for g in ag])
        if weight_anom=='ivar':
            Wt=np.array([1.0/np.nanmean(ea[g][~np.isnan(an[g])]**2) for g in ag])[:,None]*np.ones((1,NM))
        else: Wt=np.ones((len(ag),NM))
        Wt=np.where(np.isnan(A),0,Wt)
        anomaly=np.nansum(np.nan_to_num(A)*Wt,axis=0)/np.maximum(Wt.sum(0),1e-12)
    else: anomaly=np.zeros(NM)
    rate=level+anomaly
    Eg=np.array([er[g] for g in lev]); Eg=np.where(np.isnan(L),np.nan,Eg)
    with np.errstate(all='ignore'):
        u=np.sqrt(np.nansum(Eg**2,axis=0))/ng
        u=np.sqrt(u**2+ np.where(ng>1,spread**2/np.maximum(ng,1),0))
    return dict(rate=rate,level=level,anomaly=anomaly,u=u,ng=ng,groups=grp,glev=lev,gan=an,gerr=er,off=off,area=area)

def annualise(res,years=range(2000,2024)):
    rows=[]
    for y in years:
        m=(T>=y-1e-6)&(T<y+1-1e-6)
        r=np.mean(res['rate'][m]); u=np.mean(res['u'][m]); a=np.mean(res['area'][m])
        rows.append(dict(year=y,mwe=r,mwe_err=u,area=a,gt=r*a/1e3,gt_err=u*a/1e3,ngroups=int(np.min(res['ng'][m]))))
    return pd.DataFrame(rows)

def official(rid_or_global,hydro=False):
    if rid_or_global==0:
        return pd.read_csv(BASE+'/results/calendar_years/0_global.csv')
    return pd.read_csv(region_files()[rid_or_global])
