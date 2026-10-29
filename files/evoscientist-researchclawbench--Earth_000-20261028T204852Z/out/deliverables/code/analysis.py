import sys; sys.path.insert(0,'./code')
from glambie_recon import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, json
plt.rcParams.update({'font.size':9,'axes.grid':True,'grid.alpha':.3})
IM='./report/images/'; OUT='./outputs/'
inp=load_inputs()
R=pd.read_csv(OUT+'regional_annual.csv'); G=pd.read_csv(OUT+'global_annual.csv')
inp['dur']=inp.end_dates-inp.start_dates
files=inp.groupby('file').agg(rid=('region_id','first'),src=('source','first'),n=('dur','size'),dur=('dur','median'),t0=('start_dates','min'),t1=('end_dates','max'),valid=('changes',lambda x:x.notna().sum()),unit=('unit','first')).reset_index()
files.to_csv(OUT+'solution_inventory.csv',index=False)
# ---------- Fig1 data overview
cnt=files.pivot_table(index='rid',columns='src',values='file',aggfunc='count').fillna(0)[['glaciological','demdiff','altimetry','gravimetry','combined']]
fig,ax=plt.subplots(1,2,figsize=(13,4.8),gridspec_kw={'width_ratios':[1.2,1]})
cnt.index=[f'{i} {REGNAME[i]}' for i in cnt.index]
cnt.plot.barh(stacked=True,ax=ax[0],color=['#2ca02c','#d62728','#1f77b4','#9467bd','#ff7f0e']); ax[0].invert_yaxis()
ax[0].set_xlabel('Number of submitted solutions'); ax[0].set_title('(a) Input solutions per region and method (n=%d)'%len(files)); ax[0].legend(fontsize=7)
a1=files[files.rid==1].copy(); a1['o']=a1.src.map({'glaciological':0,'demdiff':1,'altimetry':2,'gravimetry':3,'combined':4}); a1=a1.sort_values(['o','t0'])
cm={'glaciological':'#2ca02c','demdiff':'#d62728','altimetry':'#1f77b4','gravimetry':'#9467bd','combined':'#ff7f0e'}
for i,(_,r) in enumerate(a1.iterrows()): ax[1].barh(i,r.t1-r.t0,left=r.t0,color=cm[r.src],height=.7)
ax[1].set_yticks(range(len(a1))); ax[1].set_yticklabels([f.replace('alaska_','')[:34] for f in a1.file],fontsize=6); ax[1].invert_yaxis()
ax[1].axvspan(2000,2024,color='k',alpha=.07); ax[1].set_xlabel('Year'); ax[1].set_title('(b) Temporal coverage of Alaska solutions')
plt.tight_layout(); plt.savefig(IM+'fig1_data_overview.png',dpi=160); plt.close()
# ---------- Fig2 regional series
fig,axs=plt.subplots(5,4,figsize=(15,15),sharex=True)
for rid,ax in zip(range(1,20),axs.flat):
    d=R[R.region_id==rid]
    ax.fill_between(d.year+.5,d.mwe-d.mwe_err,d.mwe+d.mwe_err,color='C0',alpha=.25,lw=0)
    ax.plot(d.year+.5,d.mwe,'C0-o',ms=3,label='This study'); ax.plot(d.year+.5,d.off_mwe,'k--',lw=1,label='GlaMBIE official')
    ax.axhline(0,c='k',lw=.5); ax.set_title(f'{rid} {REGNAME[rid]}',fontsize=9)
    if rid%4==1: ax.set_ylabel('m w.e. . yr')
axs.flat[0].legend(fontsize=7)
G_=G
ax=axs.flat[19]; ax.fill_between(G.year+.5,G.mwe-G.gt_err_quad/G['area']*1e3,G.mwe+G.gt_err_quad/G['area']*1e3,color='C3',alpha=.25,lw=0)
ax.plot(G.year+.5,G.mwe,'C3-o',ms=3); ax.plot(G.year+.5,G.mwe_official,'k--',lw=1); ax.set_title('Global (sum of regions)',fontsize=9)
plt.tight_layout(); plt.savefig(IM+'fig2_regional_timeseries.png',dpi=130); plt.close()
# ---------- Fig3 global
fig,ax=plt.subplots(1,2,figsize=(12,4.2))
ax[0].bar(G.year+.5,G['gt'],width=.8,color='C0',alpha=.7,label='This study',yerr=G.gt_err_quad,capsize=2,error_kw=dict(lw=.8))
ax[0].plot(G.year+.5,G.gt_official_global,'k_',ms=9,mew=2,label='GlaMBIE official (Gt)')
ax[0].fill_between(G.year+.5,G['gt']-G.gt_err_lin,G['gt']+G.gt_err_lin,color='C0',alpha=.12,lw=0,label='Fully-correlated bound')
ax[0].set_ylabel('Global glacier mass change (Gt/yr)'); ax[0].legend(fontsize=7); ax[0].set_title('(a) Annual global mass change')
cs=G['gt'].cumsum(); co=G.gt_official_global.cumsum()
ax[1].plot(G.year+1,cs,'C0-o',ms=3,label='This study'); ax[1].plot(G.year+1,co,'k--',label='GlaMBIE official')
ax[1].set_ylabel('Cumulative mass change since 2000 (Gt)'); ax[1].set_title('(b) Cumulative'); ax[1].legend()
ax2=ax[1].twinx(); ax2.set_ylim(-ax[1].get_ylim()[0]/362.5*-1*-1 if False else ax[1].get_ylim()[0]/-362.5, ax[1].get_ylim()[1]/-362.5); ax2.set_ylabel('Sea-level equivalent (mm)'); ax2.grid(False)
plt.tight_layout(); plt.savefig(IM+'fig3_global.png',dpi=160); plt.close()
# ---------- validation stats
rows=[]
for rid in range(1,20):
    d=R[R.region_id==rid]
    rows.append(dict(region_id=rid,region=REGNAME[rid],area_km2=d.area.mean(),mean_mwe=d.mwe.mean(),mean_mwe_off=d.off_mwe.mean(),
       total_gt=d['gt'].sum(),total_gt_off=d.off_gt.sum(),rmse_mwe=np.sqrt(((d.mwe-d.off_mwe)**2).mean()),corr=np.corrcoef(d.mwe,d.off_mwe)[0,1],
       within_off_1sigma=np.mean(np.abs(d.mwe-d.off_mwe)<=np.sqrt(d.mwe_err**2+d.off_mwe_errors**2)),
       mean_err_mwe=d.mwe_err.mean(),mean_err_mwe_off=d.off_mwe_errors.mean(),
       r_2000_2011=d[d.year<=2011]['gt'].mean(),r_2012_2023=d[d.year>=2012]['gt'].mean(),r_2000_2011_off=d[d.year<=2011].off_gt.mean(),r_2012_2023_off=d[d.year>=2012].off_gt.mean()))
V=pd.DataFrame(rows); V.to_csv(OUT+'validation_regional.csv',index=False)
gs=dict(total=G['gt'].sum(),total_off=G.gt_official_global.sum(),corr=np.corrcoef(G['gt'],G.gt_official_global)[0,1],rmse=np.sqrt(((G['gt']-G.gt_official_global)**2).mean()),
  bias=(G['gt']-G.gt_official_global).mean(),
  r1=G[G.year<=2011]['gt'].mean(),r2=G[G.year>=2012]['gt'].mean(),r1o=G[G.year<=2011].gt_official_global.mean(),r2o=G[G.year>=2012].gt_official_global.mean(),
  mwe_mean=G.mwe.mean(),mwe_off=G.mwe_official.mean(),err_q=G.gt_err_quad.mean(),err_lin=G.gt_err_lin.mean(),err_off=G.gt_err_official.mean())
# trend-detrended correlation (interannual variability only), global
def detr(x,y): 
    p=np.polyfit(x.year,x['gt'],1); return x['gt']-np.polyval(p,x.year)
gs['corr_detrended']=np.corrcoef(detr(G,0),G.gt_official_global-np.polyval(np.polyfit(G.year,G.gt_official_global,1),G.year))[0,1]
# anomaly-only stats per region
gs['median_region_corr']=V['corr'].median(); gs['median_region_rmse']=V.rmse_mwe.median()
json.dump({k:float(v) for k,v in gs.items()},open(OUT+'global_stats.json','w'),indent=1)
print(json.dumps({k:round(float(v),3) for k,v in gs.items()},indent=1)); print(V.round(3).to_string())
# ---------- Fig4 validation
fig,ax=plt.subplots(1,3,figsize=(15,4.5))
ax[0].scatter(R.off_mwe,R.mwe,s=8,c=R.region_id,cmap='tab20'); lim=[-3.5,1.5]; ax[0].plot(lim,lim,'k-',lw=.7); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
ax[0].set_xlabel('GlaMBIE official (m w.e./yr)'); ax[0].set_ylabel('This study (m w.e./yr)'); 
rr=np.corrcoef(R.off_mwe,R.mwe)[0,1]; ax[0].set_title(f'(a) Regional annual values, r={rr:.2f}, n={len(R)}')
x=np.arange(19); ax[1].bar(x-.2,V.total_gt_off/24,.4,label='GlaMBIE official',color='k',alpha=.7); ax[1].bar(x+.2,V.total_gt/24,.4,label='This study',color='C0')
ax[1].set_xticks(x); ax[1].set_xticklabels([str(i) for i in V.region_id]); ax[1].set_xlabel('Region ID'); ax[1].set_ylabel('Mean 2000-2023 mass change (Gt/yr)'); ax[1].legend(); ax[1].set_title('(b) Regional mean rates')
ax[2].bar(x-.2,V['corr'],.4,color='C2',label='Pearson r'); ax[2].set_ylabel('r'); ax[2].set_ylim(0,1.3)
ax3=ax[2].twinx(); ax3.bar(x+.2,V.rmse_mwe,.4,color='C1',label='RMSE (m w.e.)'); ax3.set_ylabel('RMSE (m w.e./yr)'); ax3.grid(False)
ax[2].set_xticks(x); ax[2].set_xticklabels([str(i) for i in V.region_id]); ax[2].set_xlabel('Region ID'); ax[2].set_title('(c) Per-region agreement'); 
h1,l1=ax[2].get_legend_handles_labels(); h2,l2=ax3.get_legend_handles_labels(); ax[2].legend(h1+h2,l1+l2,fontsize=7,loc='upper center',ncol=2)
plt.tight_layout(); plt.savefig(IM+'fig4_validation.png',dpi=150); plt.close()
# ---------- group comparison
res=reconcile_cache={rid:reconcile_region(rid,inp) for rid in range(1,20)}
rowsg=[]
for rid,r in res.items():
    m=(T>=2003)&(T<2020)
    for g,lv in r['glev'].items():
        mm=m&~np.isnan(lv)
        if mm.sum()<12*8: continue
        # group rate incl. its anomaly; compare to consensus over same months, with offsets removed and applied
        rowsg.append(dict(rid=rid,group=g,n_sol=len(r['groups'][g]),grp_rate=np.nanmean(lv[mm]),grp_rate_aligned=np.nanmean(lv[mm])+r['off'][g],cons=np.nanmean(r['rate'][mm]),offset=r['off'][g],months=int(mm.sum())))
GD=pd.DataFrame(rowsg); GD.to_csv(OUT+'group_comparison.csv',index=False)
fig,ax=plt.subplots(figsize=(11,4.3))
cols={'dg':'#d62728','altimetry':'#1f77b4','gravimetry':'#9467bd'}; w=.25
for k,g in enumerate(['dg','altimetry','gravimetry']):
    d=GD[GD.group==g]; ax.bar(d.rid-1+(k-1)*w,(d.grp_rate*d.rid.map(lambda i:R[R.region_id==i].area.mean())/1e3),w,color=cols[g],label={'dg':'DEM-diff + glaciological (+hybrid)','altimetry':'Altimetry','gravimetry':'Gravimetry'}[g])
cons=GD.groupby('rid').cons.first(); ax.plot(cons.index-1,cons*[R[R.region_id==i].area.mean()/1e3 for i in cons.index],'k_',ms=14,mew=2,label='Consensus (same months)')
ax.set_xticks(range(19)); ax.set_xticklabels([str(i) for i in range(1,20)]); ax.set_xlabel('Region ID'); ax.set_ylabel('Mean rate 2003-2019 before alignment (Gt/yr)'); ax.set_yscale('symlog',linthresh=5); ax.legend(fontsize=7)
ax.set_title('Per-method regional rates before inter-group alignment (months with data, 2003-2019)')
plt.tight_layout(); plt.savefig(IM+'fig5_method_comparison.png',dpi=150); plt.close()
# method spread statistics (relative to consensus)
GD['diff_pct']=100*(GD.grp_rate-GD.cons)/GD.cons.abs()
print(GD.round(3).to_string())
# ---------- fig6 group time series examples
fig,axs=plt.subplots(2,3,figsize=(15,7))
for ax,rid in zip(axs.flat,[1,7,3,13,17,6]):
    r=res[rid]; 
    for g,c in cols.items():
        if g in r['glev']:
            lvl=r['glev'][g]+r['off'][g]; an=np.nan_to_num(r['gan'][g]) if g in r['gan'] else 0
            ser=[np.nanmean((lvl+an)[(T>=y)&(T<y+1)]) if np.any(~np.isnan(lvl[(T>=y)&(T<y+1)])) else np.nan for y in range(2000,2024)]
            ax.plot(np.arange(2000,2024)+.5,ser,'-',color=c,alpha=.8,label=g)
    d=R[R.region_id==rid]; ax.plot(d.year+.5,d.mwe,'k-',lw=2,label='consensus'); ax.set_title(f'{rid} {REGNAME[rid]}'); ax.set_ylabel('m w.e./yr')
axs.flat[0].legend(fontsize=7)
plt.tight_layout(); plt.savefig(IM+'fig6_group_series.png',dpi=140); plt.close()
# ---------- fig7 regional contributions
fig,ax=plt.subplots(1,2,figsize=(13,4.5))
order=V.sort_values('total_gt').index; x=np.arange(19)
ax[0].barh(x-.2,V.loc[order,'r_2000_2011'],.4,label='2000-2011',color='C0'); ax[0].barh(x+.2,V.loc[order,'r_2012_2023'],.4,label='2012-2023',color='C3')
ax[0].set_yticks(x); ax[0].set_yticklabels(V.loc[order,'region']); ax[0].set_xlabel('Mean mass change (Gt/yr)'); ax[0].legend(); ax[0].set_title('(a) Regional rates by period')
sh=V.total_gt/V.total_gt.sum()*100; ax[1].barh(x,sh.loc[order],color='C2'); ax[1].set_yticks(x); ax[1].set_yticklabels(V.loc[order,'region']); ax[1].set_xlabel('Share of global 2000-2023 loss (%)'); ax[1].set_title('(b) Contribution to global loss')
plt.tight_layout(); plt.savefig(IM+'fig7_regional_contrib.png',dpi=150); plt.close()
