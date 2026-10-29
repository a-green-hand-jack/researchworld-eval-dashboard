#!/usr/bin/env python3
"""Audit and analyse GlaMBIE v1.0.0; no input files are modified.

Primary product: released calendar-year consensus, with independently checked
regional aggregation. Secondary product: transparent method-level hydrological
reconciliation, comparisons, and covariance sensitivity. Not a raw-data re-run.
Run from any working directory: /work/.venv/bin/python /work/code/analyze.py
"""
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR'] = str(ROOT / '.cache/matplotlib')
import json, hashlib, platform, itertools
import numpy as np
import pandas as pd
import scipy
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

DATA=ROOT/'data/glambie'; OUT=ROOT/'outputs'; IMG=ROOT/'report/images'
OUT.mkdir(exist_ok=True); IMG.mkdir(parents=True,exist_ok=True)
GROUPS=['demdiff_and_glaciological','altimetry','gravimetry']
GLABEL={'demdiff_and_glaciological':'DEM + glaciological','altimetry':'Altimetry','gravimetry':'Gravimetry'}
METHODS=['glaciological','demdiff','altimetry','gravimetry','combined']
MLABEL=['Glaciological','DEM differencing','Altimetry','Gravimetry','Hybrid']
NAMES=['Global','Alaska','Western Canada & USA','Arctic Canada North','Arctic Canada South','Greenland periphery','Iceland','Svalbard','Scandinavia','Russian Arctic','North Asia','Central Europe','Caucasus & Middle East','Central Asia','South Asia West','South Asia East','Low latitudes','Southern Andes','New Zealand','Antarctic & subantarctic']
COLORS=['#27647d','#d77a26','#8772a7']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130,'savefig.dpi':180,'axes.titleweight':'bold','axes.labelcolor':'#253442','text.color':'#253442','axes.edgecolor':'#63717c','font.family':'DejaVu Sans'})

def savefig(fig,name):
 fig.savefig(IMG/name,bbox_inches='tight',facecolor='white');plt.close(fig)

def frame_out(d,name): d.to_csv(OUT/name,index=False,float_format='%.12g')

def json_out(obj,name):
 def convert(x):
  if isinstance(x,np.generic):return x.item()
  raise TypeError(type(x).__name__)
 (OUT/name).write_text(json.dumps(obj,indent=2,default=convert,allow_nan=False)+'\n')

# 1. Complete inventory, retaining all archive files and provenance.
inv=[]; rawcoverage=[]; units={}; hashes=[]
for p in sorted(DATA.rglob('*')):
 if p.is_file(): hashes.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
for p in sorted((DATA/'input').glob('*/*.csv')):
 rid,region=p.parent.name.split('_',1); rid=int(rid)
 method=p.name[len(region)+1:].split('_')[0];d=pd.read_csv(p)
 dt=d.end_dates-d.start_dates
 numeric=d[['start_dates','end_dates','changes','errors']]
 finite=np.isfinite(numeric).all(axis=1); valid=finite & (dt>0)
 rec={'path':str(p.relative_to(ROOT)),'region_id':rid,'region':region,'method':method,'n_rows':len(d),'authors':';'.join(sorted(d.author.dropna().unique())),'units':';'.join(sorted(d.unit.dropna().unique())),'start':d.start_dates.min(),'end':d.end_dates.max(),'median_interval_years':dt.median(),'min_interval_years':dt.min(),'max_interval_years':dt.max(),'nonfinite_rows':int((~finite).sum()),'nonpositive_intervals':int((dt<=0).sum()),'negative_error_rows':int((d.errors<0).sum()),'zero_error_rows':int((d.errors==0).sum()),'duplicate_interval_rows':int(d.duplicated(['start_dates','end_dates']).sum()),'seasonal_template_name':bool('GlaciolSineWave' in p.name)}
 inv.append(rec)
 for u,n in d.unit.value_counts().items():units[u]=units.get(u,0)+int(n)
 for y in range(2000,2024):
  mask=valid & (d.start_dates<y+1) & (d.end_dates>y)
  if mask.any():rawcoverage.append({'region_id':rid,'method':method,'year':y,'file':p.name,'overlapping_intervals':int(mask.sum())})
inv=pd.DataFrame(inv);frame_out(inv,'input_inventory.csv');frame_out(pd.DataFrame(hashes),'input_checksums.csv');frame_out(pd.DataFrame(rawcoverage),'raw_interval_coverage.csv')
counts=inv.groupby(['region_id','method']).size().unstack(fill_value=0).reindex(columns=METHODS,fill_value=0)
frame_out(counts.reset_index(),'input_method_counts.csv')

# 2. Released benchmark, with explicit 95% intervals and derived 1-sigma fields.
frames=[];hydros=[]
for dirname,destination in [('calendar_years',frames),('hydrological_years',hydros)]:
 for p in sorted((DATA/'results'/dirname).glob('*.csv'),key=lambda x:int(x.stem.split('_')[0])):
  d=pd.read_csv(p);d.insert(0,'region_id',int(p.stem.split('_')[0]));destination.append(d)
cal=pd.concat(frames,ignore_index=True);hyd=pd.concat(hydros,ignore_index=True)
cal['year']=cal.start_dates.astype(int);cal['region_name']=cal.region_id.map(dict(enumerate(NAMES)))
assert len(cal)==480 and len(hyd)==453
assert cal.groupby('region_id').size().eq(24).all()
assert np.allclose(cal.end_dates-cal.start_dates,1)
assert np.isfinite(cal[['combined_gt','combined_gt_errors','combined_mwe','combined_mwe_errors','glacier_area']]).all().all()
assert (cal[['combined_gt_errors','combined_mwe_errors','glacier_area']]>0).all().all()
assert not cal.duplicated(['region_id','year']).any()
reg=cal[cal.region_id>0].copy(); glob=cal[cal.region_id==0].sort_values('year').copy()
check=[]
for year,d in reg.groupby('year'):
 g=glob[glob.year==year].iloc[0];a=d.glacier_area.to_numpy()
 check.append({'year':year,'global_gt_residual':d.combined_gt.sum()-g.combined_gt,'global_gt_ci95_residual':np.linalg.norm(d.combined_gt_errors)-g.combined_gt_errors,'global_area_residual':a.sum()-g.glacier_area,'global_mwe_residual':np.average(d.combined_mwe,weights=a)-g.combined_mwe,'global_mwe_ci95_residual':np.linalg.norm(d.combined_mwe_errors*a)/a.sum()-g.combined_mwe_errors})
check=pd.DataFrame(check);frame_out(check,'aggregation_checks.csv')
conversion=cal.combined_mwe*cal.glacier_area*0.000997-cal.combined_gt
assert np.max(np.abs(conversion))<1e-8
assert check.drop(columns='year').abs().to_numpy().max()<1e-7
rename={'glacier_area':'glacier_area_km2','combined_gt':'mass_change_gt','combined_gt_errors':'mass_change_gt_ci95','combined_mwe':'specific_change_mwe','combined_mwe_errors':'specific_change_mwe_ci95'}
product=cal.rename(columns=rename).copy()
product['mass_change_gt_sigma']=product.mass_change_gt_ci95/1.96
product['specific_change_mwe_sigma']=product.specific_change_mwe_ci95/1.96
product['specific_change_mwe_density1000']=product.mass_change_gt*1000/product.glacier_area_km2
product['specific_change_mwe_density1000_ci95']=product.specific_change_mwe_ci95*.997
product['source']='GlaMBIE 1.0.0 released calendar-year consensus'
frame_out(product,'annual_mass_change_2000_2023.csv')
frame_out(product[product.region_id==0],'global_annual_2000_2023.csv')
frame_out(product[product.region_id>0],'regional_annual_2000_2023.csv')
frame_out(hyd,'method_series_hydrological.csv')

# 3. Period summaries. Annual half-widths propagated under independence.
rows=[];cums=[]
for rid,d in cal.groupby('region_id'):
 d=d.sort_values('year'); e=d.iloc[:12];l=d.iloc[12:]
 rec={'region_id':rid,'region_name':NAMES[rid],'mean_gt_per_year':d.combined_gt.mean(),'mean_gt_ci95_independent':np.linalg.norm(d.combined_gt_errors)/24,'total_gt':d.combined_gt.sum(),'total_gt_ci95_independent':np.linalg.norm(d.combined_gt_errors),'mean_mwe_per_year':d.combined_mwe.mean(),'mean_mwe_ci95_independent':np.linalg.norm(d.combined_mwe_errors)/24,'sum_specific_mwe':d.combined_mwe.sum(),'early_gt_per_year':e.combined_gt.mean(),'late_gt_per_year':l.combined_gt.mean(),'late_minus_early_gt_per_year':l.combined_gt.mean()-e.combined_gt.mean(),'early_mwe_per_year':e.combined_mwe.mean(),'late_mwe_per_year':l.combined_mwe.mean(),'late_minus_early_mwe_per_year':l.combined_mwe.mean()-e.combined_mwe.mean(),'late_minus_early_ci95_independent':np.linalg.norm(d.combined_gt_errors)/12,'global_loss_share_pct':100*d.combined_gt.sum()/glob.combined_gt.sum(),'mean_area_km2':d.glacier_area.mean(),'area_2000_km2':d.glacier_area.iloc[0],'area_2023_km2':d.glacier_area.iloc[-1]}
 rows.append(rec)
 for k in range(1,25):
  sub=d.iloc[:k];cums.append({'region_id':rid,'end_year':int(sub.year.iloc[-1])+1,'cumulative_gt':sub.combined_gt.sum(),'cumulative_gt_ci95_independent':np.linalg.norm(sub.combined_gt_errors),'cumulative_specific_mwe':sub.combined_mwe.sum(),'cumulative_specific_mwe_ci95_independent':np.linalg.norm(sub.combined_mwe_errors)})
summary=pd.DataFrame(rows);frame_out(summary,'regional_period_summary.csv');frame_out(pd.DataFrame(cums),'cumulative_mass_change.csv')

# 4. Availability: distinguish available method means from their own variability.
av=[]
for _,d in hyd.iterrows():
 rec={'region_id':d.region_id,'start_dates':d.start_dates,'end_dates':d.end_dates,'display_year':int(np.floor(d.start_dates+.5))}
 for m in GROUPS:
  rec[m+'_present']=int(pd.notna(d[m+'_mwe']))
  rec[m+'_own_variability']=int(pd.notna(d[m+'_mwe']) and d[m+'_annual_variability']==1)
 rec['n_methods_present']=sum(rec[m+'_present'] for m in GROUPS)
 rec['n_methods_own_variability']=sum(rec[m+'_own_variability'] for m in GROUPS)
 av.append(rec)
av=pd.DataFrame(av);frame_out(av,'method_availability.csv')

# 5. Pairwise method differences on matched hydrological intervals.
# Trend comparisons include supplied method means; anomaly correlations require
# flag=1 for BOTH methods, avoiding correlations created by borrowed variability.
pairs=[]
for rid,d in hyd.groupby('region_id'):
 for a,b in itertools.combinations(GROUPS,2):
  common=d[[a+'_mwe',b+'_mwe']].notna().all(axis=1)
  if not common.any():continue
  z=d[common];diff=z[b+'_mwe']-z[a+'_mwe'];n=len(z)
  own=common & d[a+'_annual_variability'].eq(1) & d[b+'_annual_variability'].eq(1)
  zo=d[own];r=float(pearsonr(zo[a+'_mwe'],zo[b+'_mwe']).statistic) if len(zo)>2 else None
  # Pooled half-width assuming independence across methods and time. Descriptive.
  err=np.sqrt(np.sum(z[a+'_mwe_errors']**2+z[b+'_mwe_errors']**2))/n
  pairs.append({'region_id':rid,'region_name':NAMES[rid],'reference':a,'comparison':b,'n_matched_years':n,'start':z.start_dates.min(),'end':z.end_dates.max(),'bias_mwe_per_year':diff.mean(),'bias_ci95_independent':err,'rmse_mwe':np.sqrt(np.mean(diff**2)),'anomaly_rmse_mwe':np.sqrt(np.mean((diff-diff.mean())**2)),'n_own_variability_years':len(zo),'own_variability_correlation':r,'all_matched_correlation':float(pearsonr(z[a+'_mwe'],z[b+'_mwe']).statistic) if n>2 else None})
pairs=pd.DataFrame(pairs);frame_out(pairs,'method_pair_comparisons.csv')

# 6. Independent, simplified equal-method reconstruction in hydrological years.
# Anchor group means on a common period. Use only flagged-own anomalies outside
# that period. This approximates, but does not replicate, all GlaMBIE calibration.
def reconcile(d,methods):
 vals=d[[m+'_mwe' for m in methods]]
 common=vals.notna().all(axis=1)
 assert common.any()
 means=vals.loc[common].mean()
 anomalies=vals-means
 for m in methods:anomalies.loc[~d[m+'_annual_variability'].eq(1),m+'_mwe']=np.nan
 rec=anomalies.mean(axis=1)+means.mean()
 return rec,common,means
recon=[];reconstats=[];loo=[]
for rid,d in hyd.groupby('region_id'):
 d=d.reset_index(drop=True)
 ms=[m for m in GROUPS if d[m+'_mwe'].notna().any()]
 rr,common,means=reconcile(d,ms)
 residual=rr-d.combined_mwe
 reconstats.append({'region_id':rid,'n_methods':len(ms),'n_common_years':int(common.sum()),'rmse_mwe':np.sqrt(np.mean(residual**2)),'bias_mwe':residual.mean(),'max_abs_error_mwe':residual.abs().max()})
 for i,row in d.iterrows():
  recon.append({'region_id':rid,'start_dates':row.start_dates,'end_dates':row.end_dates,'released_mwe':row.combined_mwe,'reconstructed_mwe':rr[i],'residual_mwe':residual[i],'reconstructed_gt':rr[i]*row.glacier_area*.000997,'released_gt':row.combined_gt,'n_methods':len(ms)})
 # Leave-one-method-out means on the SAME intersection: isolates weighting.
 if len(ms)>1:
  for m in ms:
   full=means.mean();left=means.drop(m+'_mwe').mean();delta=left-full
   area=summary.loc[summary.region_id==rid,'mean_area_km2'].iloc[0]
   loo.append({'region_id':rid,'region_name':NAMES[rid],'omitted_method':m,'n_common_years':int(common.sum()),'common_start':d.loc[common,'start_dates'].min(),'common_end':d.loc[common,'end_dates'].max(),'full_mean_mwe':full,'leave_one_out_mean_mwe':left,'shift_mwe_per_year':delta,'mean_area_equivalent_shift_gt_per_year':delta*area*.000997})
recon=pd.DataFrame(recon);reconstats=pd.DataFrame(reconstats);loo=pd.DataFrame(loo)
frame_out(recon,'simplified_reconciliation_hydrological.csv');frame_out(reconstats,'simplified_reconciliation_metrics.csv');frame_out(loo,'leave_one_method_out.csv')

# 7. Explicit covariance sensitivity. C95 = 1.96^2 Cov, so weights directly yield
# 95% half-widths. No correlations are estimated from climate signals.
H=reg.pivot(index='region_id',columns='year',values='combined_gt_errors').to_numpy()
Y=glob.combined_gt.to_numpy();T=np.arange(24);dist=abs(T[:,None]-T[None,:])
wmean=np.ones(24)/24;wdiff=np.r_[-np.ones(12)/12,np.ones(12)/12]
early=Y[:12].mean();late=Y[12:].mean()
wratio=np.r_[np.repeat(-late/early**2/12,12),np.repeat(1/early/12,12)]
wslope=(T-T.mean())/np.sum((T-T.mean())**2)
def covariance(time_kind,parameter,spatial):
 rt=(parameter**dist if time_kind=='ar1' else (1-parameter)*np.eye(24)+parameter*np.ones((24,24)))
 rr=(1-spatial)*np.eye(19)+spatial*np.ones((19,19))
 return rt*(H.T@rr@H)
def width(w,cov): return float(np.sqrt(max(0,w@cov@w)))
def fieller_increase(cov):
 # C95 already contains the squared 1.96 multiplier. Ratio of loss magnitudes.
 we=np.r_[np.ones(12)/12,np.zeros(12)]
 wl=np.r_[np.zeros(12),np.ones(12)/12]
 ve=we@cov@we;vl=wl@cov@wl;cross=we@cov@wl
 aa=early**2-ve;bb=-2*early*late+2*cross;cc=late**2-vl
 assert aa>0
 roots=np.sort(np.roots([aa,bb,cc]).real)
 return 100*(roots-1)

scenarios=[];covs={}
for name,kind,param,spatial in [('Independent','ar1',0,0),('AR1 rho=0.3','ar1',.3,0),('AR1 rho=0.6','ar1',.6,0),('AR1 rho=0.9','ar1',.9,0),('Persistent q=0.10','persistent',.1,0),('Persistent q=0.25','persistent',.25,0),('Persistent q=1.00','persistent',1,0),('Spatial c=0.10','ar1',0,.1),('Spatial c=0.25','ar1',0,.25),('AR1 rho=0.6; spatial c=0.10','ar1',.6,.1)]:
 c=covariance(kind,param,spatial);covs[name]=c;fieller=fieller_increase(c)
 scenarios.append({'scenario':name,'temporal_model':kind,'temporal_parameter':param,'spatial_correlation':spatial,'mean_gt_per_year':Y.mean(),'mean_gt_ci95':width(wmean,c),'total_gt_ci95':width(np.ones(24),c),'late_minus_early_gt_per_year':late-early,'late_minus_early_ci95':width(wdiff,c),'increase_percent':100*(late/early-1),'increase_percent_ci95_delta':100*width(wratio,c),'increase_percent_ci95_fieller_lower':fieller[0],'increase_percent_ci95_fieller_upper':fieller[1],'ols_slope_gt_per_year2':float(wslope@Y),'ols_slope_ci95_measurement_only':width(wslope,c)})
scenarios=pd.DataFrame(scenarios);frame_out(scenarios,'covariance_sensitivity.csv')
np.savez_compressed(OUT/'global_covariance_scenarios.npz',**{k.replace(' ','_'):v/1.96**2 for k,v in covs.items()})
# Descriptive endpoint sensitivity, no inference from a deterministic curve fit.
trends=[]
for start,end in [(2000,2023),(2000,2021),(2000,2019),(2002,2023),(2005,2023)]:
 d=glob[glob.year.between(start,end)];slope=np.polyfit(d.year,d.combined_gt,1)[0]
 trends.append({'start':start,'end':end,'mean_gt_per_year':d.combined_gt.mean(),'ols_slope_gt_per_year2':slope})
frame_out(pd.DataFrame(trends),'endpoint_sensitivity.csv')

# 8. Literature comparisons with exact non-overlapping year bounds.
comparisons=[]
for source,start,end,pub,puberr in [('GlaMBIE Team (2025)',2000,2023,-273,16),('Hugonnet et al. (2021)',2000,2019,-267,16)]:
 d=glob[glob.year.between(start,end)]
 comparisons.append({'source':source,'first_calendar_year':start,'last_calendar_year':end,'published_gt_per_year':pub,'published_ci95':puberr,'consensus_gt_per_year':d.combined_gt.mean(),'consensus_ci95_independent':np.linalg.norm(d.combined_gt_errors)/len(d),'difference_gt_per_year':d.combined_gt.mean()-pub,'relative_less_negative_pct':100*(d.combined_gt.mean()-pub)/abs(pub)})
comparisons=pd.DataFrame(comparisons);frame_out(comparisons,'literature_comparisons.csv')

# 9. Figures.
fig,axs=plt.subplots(1,2,figsize=(14,8),gridspec_kw={'width_ratios':[1,1.25]},layout='constrained')
im=axs[0].imshow(counts.to_numpy(),aspect='auto',cmap='Blues',vmin=0)
axs[0].set(yticks=np.arange(19),yticklabels=NAMES[1:],xticks=np.arange(5),xticklabels=MLABEL,title='a  Submitted archive files by region and method')
axs[0].tick_params(axis='x',rotation=40)
for i in range(19):
 for j in range(5):axs[0].text(j,i,str(counts.iloc[i,j]),ha='center',va='center',color='white' if counts.iloc[i,j]>=6 else '#253442',fontsize=9)
fig.colorbar(im,ax=axs[0],shrink=.6,label='Number of CSV files')
mat=av.pivot(index='region_id',columns='display_year',values='n_methods_own_variability').reindex(columns=range(2000,2024))
im=axs[1].imshow(mat,aspect='auto',vmin=.5,vmax=3.5,cmap=plt.get_cmap('viridis',3))
axs[1].set(yticks=np.arange(19),yticklabels=[],xticks=np.arange(0,24,3),xticklabels=np.arange(2000,2024,3),title='b  Methods supplying their own annual variability',xlabel='Hydrological-year display label')
fig.colorbar(im,ax=axs[1],ticks=[1,2,3],shrink=.6,label='Method groups (blank = no released interval)')
savefig(fig,'01_data_overview.png')

fig,axs=plt.subplots(2,1,figsize=(12,9),layout='constrained')
years=glob.year.to_numpy();err=glob.combined_gt_errors.to_numpy()
axs[0].bar(years,Y,color='#347b92',width=.78)
axs[0].errorbar(years,Y,yerr=err,fmt='none',ecolor='#293b47',lw=1,capsize=2,label='Released 95% interval')
axs[0].hlines([early,late],[1999.5,2011.5],[2011.5,2023.5],color='#db8736',lw=2.5,label='12-year means')
axs[0].axhline(0,color='#65747c',lw=.8);axs[0].set(ylabel='Annual mass change (Gt)',title='a  Annual global glacier mass change',xlim=(1999.3,2023.7));axs[0].legend(loc='lower left',frameon=False)
cum=np.r_[0,np.cumsum(Y)];ends=np.arange(2000,2025)
for name,color in [('AR1 rho=0.6; spatial c=0.10','#efd6b2'),('AR1 rho=0.6','#b9d6dd'),('Independent','#7eabb8')]:
 c=covs[name];h=np.r_[0,[np.sqrt(c[:k,:k].sum()) for k in range(1,25)]]
 axs[1].fill_between(ends,cum-h,cum+h,color=color,label=name)
axs[1].plot(ends,cum,color='#203d4d',lw=2)
axs[1].set(ylabel='Cumulative mass change (Gt)',xlabel='Calendar year boundary',title='b  Cumulative loss and covariance sensitivity',xlim=(1999.5,2024.5));axs[1].legend(frameon=False,loc='lower left')
savefig(fig,'02_global_mass_change.png')

fig,axs=plt.subplots(1,2,figsize=(15,9),layout='constrained',gridspec_kw={'width_ratios':[1.4,1]})
mat=reg.pivot(index='region_id',columns='year',values='combined_mwe')
im=axs[0].imshow(mat,aspect='auto',cmap='RdBu',norm=TwoSlopeNorm(vmin=-3.5,vcenter=0,vmax=1))
axs[0].set(yticks=np.arange(19),yticklabels=NAMES[1:],xticks=np.arange(0,24,3),xticklabels=np.arange(2000,2024,3),title='a  Regional specific annual change',xlabel='Calendar year')
fig.colorbar(im,ax=axs[0],shrink=.7,label='m w.e. per annual interval',extend='min')
s=summary[summary.region_id>0].sort_values('mean_gt_per_year',ascending=False)
axs[1].barh(np.arange(19),-s.mean_gt_per_year,xerr=s.mean_gt_ci95_independent,color='#347b92',error_kw={'ecolor':'#253442','capsize':2})
axs[1].set(yticks=np.arange(19),yticklabels=s.region_name,title='b  Contributions to total mass loss',xlabel='Mean annual mass loss (Gt yr$^{-1}$)')
savefig(fig,'03_regional_patterns.png')

fig,axs=plt.subplots(5,4,figsize=(16,15),sharex=True,layout='constrained')
for rid,ax in enumerate(axs.flat,1):
 if rid==20:ax.axis('off');ax.text(.03,.8,'Calendar years 2000–2023\n\nShading: released 95% interval\nBlue line: specific mass change\n\nVertical scale varies by region.',transform=ax.transAxes,fontsize=12);continue
 d=reg[reg.region_id==rid];ax.fill_between(d.year,d.combined_mwe-d.combined_mwe_errors,d.combined_mwe+d.combined_mwe_errors,color='#d9e7ec');ax.plot(d.year,d.combined_mwe,color='#27647d',lw=1.3);ax.axhline(0,color='#999999',lw=.6);ax.set_title(NAMES[rid],fontsize=10);ax.set_xticks([2000,2010,2023]);ax.set_ylabel('m w.e.',fontsize=9)
savefig(fig,'04_regional_annual_uncertainty.png')

fig,axs=plt.subplots(1,3,figsize=(16,6),layout='constrained')
for ax,method,color in zip(axs[:2],GROUPS[1:],COLORS[1:]):
 p=pairs[(pairs.reference==GROUPS[0])&(pairs.comparison==method)].sort_values('region_id',ascending=False)
 ax.errorbar(p.bias_mwe_per_year,np.arange(len(p)),xerr=p.bias_ci95_independent,fmt='o',color=color,capsize=3)
 ax.axvline(0,color='#aaa',lw=1);ax.set(yticks=np.arange(len(p)),yticklabels=p.region_name,xlabel='Method minus DEM + glaciological (m w.e. yr$^{-1}$)',title=GLABEL[method]+' on matched intervals')
p=pairs[pairs.reference==GROUPS[0]]
for method,color in zip(GROUPS[1:],COLORS[1:]):
 q=p[p.comparison==method];axs[2].scatter(q.n_own_variability_years,q.own_variability_correlation,color=color,s=50,label=GLABEL[method])
 for _,r in q.iterrows():axs[2].annotate(str(int(r.region_id)),(r.n_own_variability_years,r.own_variability_correlation),xytext=(3,3),textcoords='offset points',fontsize=8)
axs[2].set(ylim=(-1.05,1.1),xlabel='Years with own variability in both groups',ylabel='Pearson correlation',title='Annual variation agreement');axs[2].axhline(0,color='#aaa',lw=1);axs[2].legend(frameon=False,loc='lower right')
savefig(fig,'05_method_comparison.png')

fig,axs=plt.subplots(1,3,figsize=(16,5.5),layout='constrained')
axs[0].plot(check.year,check.global_gt_residual,'o-',color=COLORS[0],label='Gt closure');axs[0].plot(check.year,check.global_gt_ci95_residual,'s-',color=COLORS[1],label='95% interval closure');axs[0].set(xlabel='Calendar year',ylabel='Numerical residual (Gt)',title='a  Independent global aggregation');axs[0].ticklabel_format(axis='y',style='sci',scilimits=(0,0));axs[0].legend(frameon=False)
for n,color in [(1,'#b7c3ca'),(2,COLORS[0]),(3,COLORS[1])]:
 d=recon[recon.n_methods==n];axs[1].scatter(d.released_mwe,d.reconstructed_mwe,s=15,alpha=.65,color=color,label=f'{n} method group'+('s' if n>1 else ''))
lo=min(recon.released_mwe.min(),recon.reconstructed_mwe.min());hi=max(recon.released_mwe.max(),recon.reconstructed_mwe.max());axs[1].plot([lo,hi],[lo,hi],'k--',lw=.8);axs[1].set(xlabel='Released hydrological consensus (m w.e.)',ylabel='Simplified reconstruction (m w.e.)',title='b  Method-level reconstruction');axs[1].legend(frameon=False,fontsize=9)
for i,row in comparisons.iterrows():
 axs[2].errorbar(row.published_gt_per_year,i+.1,xerr=row.published_ci95,fmt='o',color=COLORS[1],capsize=3,label='Published study' if i==0 else None)
 axs[2].errorbar(row.consensus_gt_per_year,i-.1,xerr=row.consensus_ci95_independent,fmt='s',color=COLORS[0],capsize=3,label='This benchmark export' if i==0 else None)
axs[2].set(yticks=range(2),yticklabels=['GlaMBIE\n2000–2023','Hugonnet et al.\n2000–2019'],xlabel='Mean mass change (Gt yr$^{-1}$)',title='c  Matched-period literature comparison');axs[2].set_ylim(-.3,1.65);axs[2].legend(frameon=False,loc='upper left',fontsize=9)
savefig(fig,'06_validation.png')

fig,axs=plt.subplots(1,2,figsize=(14,7),layout='constrained')
s=scenarios.iloc[::-1];pos=np.arange(len(s))
axs[0].barh(pos,s.mean_gt_ci95,color=['#c68b50' if 'spatial' in x.lower() else '#347b92' for x in s.scenario]);axs[0].set(yticks=pos,yticklabels=s.scenario,xlabel='95% half-width of 24-year mean (Gt yr$^{-1}$)',title='a  Mean-loss uncertainty')
axs[1].errorbar(-s.late_minus_early_gt_per_year,pos,xerr=s.late_minus_early_ci95,fmt='o',color='#347b92',capsize=4);axs[1].axvline(0,color='#a94a41',lw=1);axs[1].set(yticks=pos,yticklabels=[],xlabel='Increase in mass-loss rate (Gt yr$^{-1}$)',title='b  Difference between 12-year means')
savefig(fig,'07_covariance_sensitivity.png')

# Consolidated numerical findings used in the report.
news={
 'n_input_files':len(inv),'n_input_rows':int(inv.n_rows.sum()),'method_file_counts':inv.method.value_counts().to_dict(),'input_units_rows':units,'n_author_strings':len(set(';'.join(inv.authors).split(';'))),'n_seasonal_templates':int(inv.seasonal_template_name.sum()),
 'raw_qc':{k:int(inv[k].sum()) for k in ['nonfinite_rows','nonpositive_intervals','negative_error_rows','zero_error_rows','duplicate_interval_rows']},
 'n_calendar_rows':len(cal),'n_hydrological_rows':len(hyd),'n_methods_present_counts':av.n_methods_present.value_counts().sort_index().to_dict(),'n_own_methods_counts':av.n_methods_own_variability.value_counts().sort_index().to_dict(),
 'group_presence':{m:int(av[m+'_present'].sum()) for m in GROUPS},'group_own_variability':{m:int(av[m+'_own_variability'].sum()) for m in GROUPS},
 'global_mean_gt':float(Y.mean()),'global_total_gt':float(Y.sum()),'global_mean_mwe':float(glob.combined_mwe.mean()),'global_sum_specific_mwe':float(glob.combined_mwe.sum()),'early_mean_gt':float(early),'late_mean_gt':float(late),'early_ci95':float(np.linalg.norm(err[:12])/12),'late_ci95':float(np.linalg.norm(err[12:])/12),'increase_percent':float(100*(late/early-1)),
 'global_total_sle_mm':float(-Y.sum()/362.5),'global_sle_ci95':float(np.linalg.norm(err)/362.5),'global_mean_sle_mm_per_year':float(-Y.mean()/362.5),'global_ci95_independent':float(np.linalg.norm(err)/24),'global_total_ci95_independent':float(np.linalg.norm(err)),
 'regional_specific_acceleration_count':int((summary.loc[summary.region_id>0,'late_minus_early_mwe_per_year']<0).sum()),'regional_acceleration_count':int((summary.loc[summary.region_id>0,'late_minus_early_gt_per_year']<0).sum()),'all_regional_mean_negative':bool((summary.loc[summary.region_id>0,'mean_gt_per_year']<0).all()),
 'most_negative_year':int(years[np.argmin(Y)]),'most_negative_gt':float(Y.min()),'most_negative_ci95':float(err[np.argmin(Y)]),'last_two_year_share_pct':float(Y[-2:].sum()/Y.sum()*100),'last_five_year_share_pct':float(Y[-5:].sum()/Y.sum()*100),
 'max_closure_residual_gt':float(check.global_gt_residual.abs().max()),'max_closure_residual_ci95':float(check.global_gt_ci95_residual.abs().max()),'max_conversion_residual_gt':float(np.abs(conversion).max()),
 'reconstruction_rmse_all_mwe':float(np.sqrt(np.mean(recon.residual_mwe**2))),'reconstruction_rmse_multimethod_mwe':float(np.sqrt(np.mean(recon.loc[recon.n_methods>1,'residual_mwe']**2))),'reconstruction_max_abs_mwe':float(recon.residual_mwe.abs().max()),
 'largest_reconstruction_rmse_region':NAMES[int(reconstats.loc[reconstats.rmse_mwe.idxmax(),'region_id'])],
 'method_mean_bias_region_equal':{m:float(pairs.loc[(pairs.reference==GROUPS[0])&(pairs.comparison==m),'bias_mwe_per_year'].mean()) for m in GROUPS[1:]},
 'leave_out_sum_equivalent_shift_gt':loo.groupby('omitted_method').mean_area_equivalent_shift_gt_per_year.sum().to_dict(),
 'environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}}
json_out(news,'findings.json')
print(json.dumps(news,indent=2))
print('\nCOVARIANCE SENSITIVITY\n',scenarios.to_string(index=False))
print('\nLITERATURE\n',comparisons.to_string(index=False))
print('\nREGIONS\n',summary[['region_name','mean_gt_per_year','mean_gt_ci95_independent','mean_mwe_per_year','late_minus_early_gt_per_year','global_loss_share_pct']].to_string(index=False))
