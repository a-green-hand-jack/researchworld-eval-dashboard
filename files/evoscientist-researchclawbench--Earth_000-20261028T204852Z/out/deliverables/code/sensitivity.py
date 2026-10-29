import sys; sys.path.insert(0,'./code')
from glambie_recon import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, json
import glambie_recon as gr
inp=load_inputs(); OUT='./outputs/'
og=official(0); og['year']=np.round(og.start_dates).astype(int); og=og.set_index('year')
comb_files=set(inp[inp.source=='combined'].file)
def run(label,**kw):
    rho=kw.pop('rho_within',0.5); gr.RHO_WITHIN=rho; gr.EDGE=kw.pop('edge','shift')
    rows=[]
    for rid in range(1,20):
        r=reconcile_region(rid,inp,**kw); a=annualise(r); a['rid']=rid; rows.append(a)
    gr.RHO_WITHIN=0.5; gr.EDGE='shift'
    A=pd.concat(rows); g=A.groupby('year').agg(G=('gt','sum'),err_q=('gt_err',lambda x:np.sqrt((x**2).sum())))
    o=og.combined_gt.loc[g.index]
    # regional rmse vs official
    off=pd.concat([official(r).assign(rid=r) for r in range(1,20)]); off['year']=np.round(off.start_dates).astype(int)
    M=A.merge(off[['rid','year','combined_mwe']],on=['rid','year'])
    return dict(variant=label,total_gt=g.G.sum(),rate_2000_11=g.G[g.index<=2011].mean(),rate_2012_23=g.G[g.index>=2012].mean(),
        global_corr=np.corrcoef(g.G,o)[0,1],global_rmse=np.sqrt(((g.G-o)**2).mean()),
        reg_rmse_median=M.groupby('rid').apply(lambda d:np.sqrt(((d.mwe-d.combined_mwe)**2).mean())).median(),
        reg_corr_median=M.groupby('rid').apply(lambda d:np.corrcoef(d.mwe,d.combined_mwe)[0,1]).median(),err_q=g.err_q.mean()),g
V=[('Baseline',{}),('Edge: truncated window',dict(edge='truncate')),('MA window 3 yr',dict(W=3.0)),('MA window 8 yr',dict(W=8.0)),('Equal anomaly weights',dict(weight_anom='equal')),
 ('No inter-group alignment',dict(align=False)),('Exclude hybrid (combined) solutions',dict(drop_files=tuple(comb_files))),
 ('No a-priori exclusions',dict(drop_groups=())),('DEM-diff/alt density 0.90',dict(rho=0.90)),('DEM-diff/alt density 0.80',dict(rho=0.80)),
 ('Drop gravimetry everywhere',dict(drop_groups=None)),('Drop altimetry everywhere',dict(drop_groups=None)),('dg only',dict(drop_groups=None)),('Within-group error corr 0.0',dict(rho_within=0.0)),('Within-group error corr 1.0',dict(rho_within=1.0))]
# custom drops: build via per-region default + extra
def drops(extra): return lambda rid: default_exclusions(rid,0)  # placeholder
out=[]; series={}
for lab,kw in V:
    if kw.get('drop_groups',1) is None:
        extra={'Drop gravimetry everywhere':{'gravimetry'},'Drop altimetry everywhere':{'altimetry'},'dg only':{'gravimetry','altimetry'}}[lab]
        rows=[]
        # emulate by per-region call
        import types
        def runx(extra):
            rs=[]
            for rid in range(1,20):
                area=area_monthly(rid); ex=default_exclusions(rid,area[(T>=2000)&(T<2024)].mean())|extra
                r=reconcile_region(rid,inp,drop_groups=ex); a=annualise(r); a['rid']=rid; rs.append(a)
            return pd.concat(rs)
        A=runx(extra); g=A.groupby('year').agg(G=('gt','sum'),err_q=('gt_err',lambda x:np.sqrt((x**2).sum())))
        off=pd.concat([official(r).assign(rid=r) for r in range(1,20)]); off['year']=np.round(off.start_dates).astype(int)
        M=A.merge(off[['rid','year','combined_mwe']],on=['rid','year']); o=og.combined_gt.loc[g.index]
        d=dict(variant=lab,total_gt=g.G.sum(),rate_2000_11=g.G[g.index<=2011].mean(),rate_2012_23=g.G[g.index>=2012].mean(),global_corr=np.corrcoef(g.G,o)[0,1],global_rmse=np.sqrt(((g.G-o)**2).mean()),
          reg_rmse_median=M.groupby('rid').apply(lambda d:np.sqrt(((d.mwe-d.combined_mwe)**2).mean())).median(),reg_corr_median=M.groupby('rid').apply(lambda d:np.corrcoef(d.mwe,d.combined_mwe)[0,1]).median(),err_q=g.err_q.mean())
    else:
        d,g=run(lab,**kw)
    out.append(d); series[lab]=g.G; print(d,flush=True)
S=pd.DataFrame(out); S.to_csv(OUT+'sensitivity.csv',index=False); pd.DataFrame(series).to_csv(OUT+'sensitivity_global_series.csv')
print(S.round(3).to_string())
fig,ax=plt.subplots(1,2,figsize=(14,4.8))
S2=S.iloc[::-1]
ax[0].barh(range(len(S2)),-S2.total_gt/1000,color=['C3' if v=='Baseline' else 'C0' for v in S2.variant]); ax[0].axvline(-og.combined_gt.sum()/1000,c='k',ls='--',label='GlaMBIE official'); ax[0].set_yticks(range(len(S2))); ax[0].set_yticklabels(S2.variant,fontsize=7)
ax[0].set_xlabel('Global loss 2000-2023 (Tt)'); ax[0].legend(); ax[0].set_xlim(4,8.5); ax[0].set_title('(a) Total loss')
ax[1].barh(range(len(S2)),S2.global_rmse,color=['C3' if v=='Baseline' else 'C0' for v in S2.variant]); ax[1].set_yticks(range(len(S2))); ax[1].set_yticklabels([]); ax[1].set_xlabel('Global annual RMSE vs official (Gt/yr)'); ax[1].set_title('(b) Annual agreement')
plt.tight_layout(); plt.savefig('./report/images/fig8_sensitivity.png',dpi=150)
