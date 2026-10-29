"""Audit and reassess the released GlaMBIE 1.0.0 observational benchmark.

This does not claim a new reduction of the 233 scientific submissions. The
released consensus is retained; method and covariance sensitivities are new.
All *_h95 fields are 95% half-widths, not standard deviations.
"""
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'outputs/mplconfig'))
import hashlib
import json
import platform
import sys
import numpy as np
import pandas as pd
import scipy
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
import seaborn as sns

DATA = ROOT / 'data/glambie'
OUT = ROOT / 'outputs'
FIG = ROOT / 'report/images'
METHODS = ['altimetry', 'gravimetry', 'demdiff_and_glaciological']
MLABEL = {'altimetry': 'Altimetry', 'gravimetry': 'Gravimetry', 'demdiff_and_glaciological': 'DEM + glaciological'}
RAW_METHODS = ['glaciological', 'demdiff', 'altimetry', 'gravimetry', 'combined']
NAMES = ['Global', 'Alaska', 'Western Canada & USA', 'Arctic Canada North',
         'Arctic Canada South', 'Greenland periphery', 'Iceland', 'Svalbard',
         'Scandinavia', 'Russian Arctic', 'North Asia', 'Central Europe',
         'Caucasus & Middle East', 'Central Asia', 'South Asia West', 'South Asia East',
         'Low Latitudes', 'Southern Andes', 'New Zealand', 'Antarctic & Subantarctic']
COLORS = {'altimetry': '#d48a00', 'gravimetry': '#6b54a2', 'demdiff_and_glaciological': '#087e8b'}
Z95 = 1.96


def save_csv(df, name):
    df.to_csv(OUT / name, index=False, float_format='%.12g')


def save_fig(fig, name):
    fig.savefig(FIG / name, dpi=210, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def ar1(n, rho):
    return rho ** np.abs(np.arange(n)[:, None] - np.arange(n)[None, :])


def halfwidth(h, weights, corr=None):
    h, weights = np.asarray(h), np.asarray(weights)
    v = h * weights
    return float(np.sqrt(max(0, v @ (np.eye(len(v)) if corr is None else corr) @ v)))


def annual_export(d):
    d = d.copy()
    d['year'] = d.start_dates.astype(int)
    d['region_name'] = d.region_id.map(dict(enumerate(NAMES)))
    d = d.rename(columns={'glacier_area': 'glacier_area_km2', 'combined_gt': 'mass_change_gt',
                          'combined_gt_errors': 'mass_change_gt_h95', 'combined_mwe': 'specific_mass_change_mwe',
                          'combined_mwe_errors': 'specific_mass_change_mwe_h95'})
    for v, h in [('mass_change_gt', 'mass_change_gt_h95'), ('specific_mass_change_mwe', 'specific_mass_change_mwe_h95')]:
        d[v + '_lower95'] = d[v] - d[h]
        d[v + '_upper95'] = d[v] + d[h]
    return d[['region_id', 'region', 'region_name', 'year', 'start_dates', 'end_dates', 'glacier_area_km2',
              'mass_change_gt', 'mass_change_gt_h95', 'mass_change_gt_lower95', 'mass_change_gt_upper95',
              'specific_mass_change_mwe', 'specific_mass_change_mwe_h95',
              'specific_mass_change_mwe_lower95', 'specific_mass_change_mwe_upper95']]


def inventory():
    records, rows, manifest = [], [], []
    for p in sorted(DATA.rglob('*')):
        if p.is_file():
            manifest.append({'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size})
    for p in sorted((DATA / 'input').glob('*/*.csv')):
        rid, region = p.parent.name.split('_', 1)
        method, team = p.stem[len(region) + 1:].split('_', 1)
        d = pd.read_csv(p)
        dt = d.end_dates - d.start_dates
        records.append({'file': str(p.relative_to(ROOT)), 'region_id': int(rid), 'region': region,
                        'method': method, 'submission_label': team, 'rows': len(d),
                        'units': '|'.join(sorted(d.unit.unique())), 'start': d.start_dates.min(),
                        'end': d.end_dates.max(), 'min_duration_yr': dt.min(), 'median_duration_yr': dt.median(),
                        'max_duration_yr': dt.max(), 'missing_changes': int(d.changes.isna().sum()),
                        'missing_errors': int(d.errors.isna().sum()), 'negative_errors': int((d.errors < 0).sum()),
                        'zero_errors': int((d.errors == 0).sum()), 'nonpositive_durations': int((dt <= 0).sum()),
                        'duplicate_intervals': int(d.duplicated(['start_dates', 'end_dates']).sum())})
        d = d.assign(file=str(p.relative_to(ROOT)), region_id=int(rid), method=method, duration_yr=dt)
        rows.append(d)
    inv, raw = pd.DataFrame(records), pd.concat(rows, ignore_index=True)
    save_csv(inv, 'input_inventory.csv')
    save_csv(pd.DataFrame(manifest), 'data_manifest_sha256.csv')
    save_csv(raw.groupby(['method', 'unit']).size().rename('n_intervals').reset_index(), 'input_units.csv')
    return inv, raw


def load_results(folder):
    ds = []
    for p in sorted((DATA / 'results' / folder).glob('*.csv')):
        ds.append(pd.read_csv(p).assign(region_id=int(p.stem.split('_')[0])))
    return pd.concat(ds, ignore_index=True).sort_values(['region_id', 'start_dates']).reset_index(drop=True)


def audit(cal, hydro, raw):
    g = cal[cal.region_id == 0].sort_values('start_dates')
    r = cal[cal.region_id > 0]
    grouped = r.groupby('start_dates')
    checks = pd.DataFrame({'year': g.start_dates.astype(int).values,
                          'global_minus_regional_gt': g.combined_gt.values - grouped.combined_gt.sum().values,
                          'global_minus_regional_area_km2': g.glacier_area.values - grouped.glacier_area.sum().values,
                          'global_minus_regional_gt_h95': g.combined_gt_errors.values - np.sqrt(grouped.combined_gt_errors.apply(lambda s: (s*s).sum()).values),
                          'global_minus_regional_mwe': g.combined_mwe.values - r.assign(w=r.glacier_area*r.combined_mwe).groupby('start_dates').w.sum().values/g.glacier_area.values,
                          'global_minus_regional_mwe_h95': g.combined_mwe_errors.values - np.sqrt(r.assign(v=(r.glacier_area*r.combined_mwe_errors)**2).groupby('start_dates').v.sum().values)/g.glacier_area.values})
    save_csv(checks, 'aggregation_audit.csv')
    ratio = 1000 * cal.combined_gt / (cal.glacier_area * cal.combined_mwe)
    unit_resid = cal.combined_gt - .997 * cal.glacier_area * cal.combined_mwe / 1000
    unit_sensitivity = g[['start_dates', 'combined_gt']].copy()
    unit_sensitivity['conventional_1000kg_per_mwe_gt'] = g.glacier_area*g.combined_mwe/1000
    unit_sensitivity['conventional_minus_archived_gt'] = unit_sensitivity.conventional_1000kg_per_mwe_gt-unit_sensitivity.combined_gt
    save_csv(unit_sensitivity, 'unit_convention_sensitivity.csv')
    check_summary = {
        'calendar_rows': len(cal), 'hydrological_rows': len(hydro),
        'n_calendar_years': int(g.start_dates.nunique()), 'n_regions': int(r.region.nunique()),
        'all_calendar_intervals_one_year': bool(np.allclose(cal.end_dates-cal.start_dates, 1)),
        'all_calendar_regions_have_24_years': bool((cal.groupby('region_id').size()==24).all()),
        'all_calendar_fields_finite': bool(np.isfinite(cal.select_dtypes('number')).all().all()),
        'all_calendar_halfwidths_positive': bool((cal[['combined_gt_errors', 'combined_mwe_errors']]>0).all().all()),
        'mass_conversion_factor_median': float(np.nanmedian(ratio)),
        'max_mass_conversion_residual_gt': float(np.abs(unit_resid).max()),
        'input_rows': len(raw), 'input_units_actual': sorted(raw.unit.unique()),
        'raw_missing_changes': int(raw.changes.isna().sum()), 'raw_missing_errors': int(raw.errors.isna().sum()),
        'raw_negative_errors': int((raw.errors < 0).sum()), 'raw_zero_errors': int((raw.errors == 0).sum()),
        'raw_nonpositive_durations': int((raw.duration_yr<=0).sum()),
        'raw_nonfinite_numeric_rows': int((~np.isfinite(raw[['start_dates','end_dates','changes','errors']])).any(axis=1).sum()),
    }
    check_summary.update({f'max_abs_{c}': float(checks[c].abs().max()) for c in checks if c!='year'})
    # Checks concern the actual scientific invariants, including the archive's 0.997 conversion.
    assert check_summary['all_calendar_regions_have_24_years']
    assert check_summary['all_calendar_fields_finite']
    assert check_summary['all_calendar_halfwidths_positive']
    assert checks.global_minus_regional_gt.abs().max() < 1e-8
    assert checks.global_minus_regional_mwe.abs().max() < 1e-10
    assert checks.global_minus_regional_gt_h95.abs().max() < 1e-8
    assert np.abs(unit_resid).max() < 1e-8
    (OUT/'audit_summary.json').write_text(json.dumps(check_summary, indent=2))
    return checks, check_summary


def period_summary(cal):
    records = []
    for rid, d in cal.groupby('region_id'):
        d = d.sort_values('start_dates')
        y, h = d.combined_gt.values, d.combined_gt_errors.values
        b, hb = d.combined_mwe.values, d.combined_mwe_errors.values
        n = len(d)
        early = d.start_dates < 2012
        late = ~early
        contrast = np.where(late, 1/late.sum(), -1/early.sum())
        weights = np.ones(n)/n
        records.append({'region_id': int(rid), 'region': d.region.iloc[0], 'region_name': NAMES[rid],
                        'mean_gt_per_yr': y.mean(), 'mean_gt_h95_independent': halfwidth(h, weights),
                        'mean_gt_h95_fully_correlated': h.mean(), 'cumulative_gt': y.sum(),
                        'cumulative_gt_h95_independent': halfwidth(h, np.ones(n)),
                        'mean_mwe_per_yr': b.mean(), 'mean_mwe_h95_independent': halfwidth(hb, weights),
                        'mean_mwe_h95_fully_correlated': hb.mean(), 'cumulative_specific_mwe': b.sum(),
                        'mean_area_km2': d.glacier_area.mean(), 'area_2000_km2': d.glacier_area.iloc[0],
                        'area_2023_km2': d.glacier_area.iloc[-1],
                        'early_mean_gt': y[early].mean(), 'late_mean_gt': y[late].mean(),
                        'late_minus_early_gt': float(contrast @ y), 'contrast_h95_independent': halfwidth(h, contrast),
                        'contrast_h95_ar1_07': halfwidth(h, contrast, ar1(n, .7))})
    summary = pd.DataFrame(records)
    global_mean = summary.loc[summary.region_id==0, 'mean_gt_per_yr'].iloc[0]
    global_delta = summary.loc[summary.region_id==0, 'late_minus_early_gt'].iloc[0]
    summary['share_global_loss_pct'] = summary.mean_gt_per_yr/global_mean*100
    summary['share_global_increase_pct'] = summary.late_minus_early_gt/global_delta*100
    save_csv(summary, 'regional_period_summary.csv')
    return summary


def covariance_analysis(g, r):
    y, h = g.combined_gt.values, g.combined_gt_errors.values
    n = len(g)
    early = np.arange(n) < 12
    late = ~early
    w = np.ones(n)/n
    contrast = np.where(late, 1/12, -1/12)
    emean, lmean = y[early].mean(), y[late].mean()
    # Percent increase of positive mass loss = late/early - 1; y are both negative.
    ratio_gradient = np.where(early, -100*lmean/(emean**2*12), 100/(emean*12))
    x = g.start_dates.values + .5
    X = np.column_stack([np.ones(n), x-x.mean()])
    W = np.diag(1/(h/Z95)**2)
    coeff = np.linalg.solve(X.T @ W @ X, X.T @ W)
    beta = coeff @ y
    scenarios = [('Independent years', np.eye(n))]
    for rho in [.3, .5, .7, .9]:
        scenarios.append((f'AR1 rho={rho}', ar1(n, rho)))
    scenarios.extend([('Common error across all years', np.ones((n,n))),
                      ('Independent half-period common errors', np.equal.outer(early, early).astype(float))])
    rec = []
    for name, corr in scenarios:
        rec.append({'scenario': name, 'mean_gt_per_yr': y.mean(), 'mean_h95': halfwidth(h,w,corr),
                    'cumulative_h95': halfwidth(h,np.ones(n),corr),
                    'late_minus_early_gt_per_yr': contrast @ y,
                    'contrast_h95': halfwidth(h,contrast,corr),
                    'increase_pct': (lmean/emean-1)*100,
                    'increase_pct_h95_delta': halfwidth(h,ratio_gradient,corr),
                    'loss_acceleration_gt_per_yr2': -beta[1],
                    'acceleration_h95': halfwidth(h,coeff[1],corr)})
    scenarios_df = pd.DataFrame(rec)
    save_csv(scenarios_df, 'temporal_covariance_scenarios.csv')
    # Covariances in physical units use standard deviations, unlike h95 arrays.
    cov = np.diag(h/Z95) @ ar1(n,.7) @ np.diag(h/Z95)
    np.save(OUT/'global_annual_covariance_ar1_07_gt2.npy', cov)
    pd.DataFrame(cov, index=g.start_dates.astype(int), columns=g.start_dates.astype(int)).to_csv(OUT/'global_annual_covariance_ar1_07_gt2.csv')
    cumulative = g[['start_dates','end_dates']].copy()
    cumulative['cumulative_gt'] = np.cumsum(y)
    cumulative['cumulative_mwe_dynamic_area'] = g.combined_mwe.cumsum().values
    for k, corr in [('independent',np.eye(n)), ('ar1_07',ar1(n,.7)), ('common',np.ones((n,n)))]:
        cumulative[f'cumulative_gt_h95_{k}'] = [halfwidth(h[:i],np.ones(i),corr[:i,:i]) for i in range(1,n+1)]
    save_csv(cumulative,'global_cumulative.csv')
    # Cross-region correlation sensitivity is separate from temporal sensitivity.
    hp = r.pivot(index='start_dates',columns='region_id',values='combined_gt_errors')
    rr = []
    for c in np.linspace(0,1,101):
        hh = np.sqrt((1-c)*(hp**2).sum(axis=1)+c*hp.sum(axis=1)**2)
        rr.extend({'region_correlation': c, 'year': int(yr), 'global_annual_h95_gt': float(v)} for yr,v in hh.items())
    spatial = pd.DataFrame(rr)
    save_csv(spatial, 'spatial_covariance_sensitivity.csv')
    dense = pd.DataFrame([{'rho': rho, 'mean_h95': halfwidth(h,w,ar1(n,rho)),
                           'contrast_h95': halfwidth(h,contrast,ar1(n,rho)),
                           'ratio_h95': halfwidth(h,ratio_gradient,ar1(n,rho))} for rho in np.linspace(0,.99,100)])
    save_csv(dense,'temporal_covariance_curve.csv')
    return scenarios_df, cumulative, spatial, dense


def method_analysis(hydro):
    annual, pair_records, coverage = [], [], []
    for rid, d in hydro.groupby('region_id'):
        d = d.sort_values('start_dates')
        values = d[[m+'_mwe' for m in METHODS]].to_numpy(float)
        errors = d[[m+'_mwe_errors' for m in METHODS]].to_numpy(float)
        flags = d[[m+'_annual_variability' for m in METHODS]].to_numpy(float)
        present = np.isfinite(values)
        native = present & (flags==1)
        for j,m in enumerate(METHODS):
            coverage.append({'region_id': int(rid),'region_name': NAMES[rid], 'method': m,
                             'n_trend_years': int(present[:,j].sum()), 'n_native_variability_years': int(native[:,j].sum()),
                             'n_borrowed_or_unflagged_years': int((present[:,j]&~native[:,j]).sum())})
        for i, (_, row) in enumerate(d.iterrows()):
            ids = np.where(native[i])[0]
            vs, hs = values[i,ids], errors[i,ids]
            k = len(ids)
            equal = np.mean(vs) if k else np.nan
            w = 1/hs**2 if k else np.array([])
            ivw = (w@vs)/w.sum() if k else np.nan
            rec = {'region_id': int(rid), 'region_name':NAMES[rid], 'start_dates':row.start_dates,
                   'end_dates':row.end_dates, 'published_mwe':row.combined_mwe, 'n_methods_trend':int(present[i].sum()),
                   'n_methods_native':int(k), 'native_equal_mean_mwe':equal,'native_inverse_variance_mean_mwe':ivw,
                   'ivw_minus_equal_mwe':ivw-equal, 'equal_minus_published_mwe':equal-row.combined_mwe,
                   'available_method_mean_mwe':float(np.nanmean(values[i])),
                   'native_equal_h95_independent':np.sqrt(np.sum(hs**2))/k if k else np.nan,
                   'native_ivw_h95_independent':1/np.sqrt(np.sum(w)) if k else np.nan}
            for j,m in enumerate(METHODS):
                others = np.setdiff1d(ids,[j])
                rec['leave_out_'+m+'_minus_equal_mwe'] = np.mean(values[i,others])-equal if j in ids and len(others)>0 else np.nan
            annual.append(rec)
        # Pair comparisons require each source to supply annual variability itself.
        for a,b in [('altimetry','demdiff_and_glaciological'),('gravimetry','demdiff_and_glaciological'),('altimetry','gravimetry')]:
            ia,ib=METHODS.index(a),METHODS.index(b)
            mask=native[:,ia]&native[:,ib]
            if mask.sum()<3:
                continue
            va,vb=values[mask,ia],values[mask,ib]
            ha,hb=errors[mask,ia],errors[mask,ib]
            residual=va-vb
            pooled_h=np.sqrt(ha**2+hb**2)
            pair_records.append({'region_id':int(rid),'region_name':NAMES[rid], 'method_a':a,'method_b':b,
                                 'n_years':int(mask.sum()),'first_start':d.start_dates.values[mask].min(),
                                 'last_end':d.end_dates.values[mask].max(),'mean_a_mwe':va.mean(),'mean_b_mwe':vb.mean(),
                                 'mean_difference_mwe':residual.mean(),
                                 'difference_mean_h95_independent':np.sqrt(np.sum(pooled_h**2))/len(va),
                                 'difference_sd_mwe':residual.std(ddof=1),
                                 'rmse_mwe':np.sqrt(np.mean(residual**2)),
                                 'centered_rmse_mwe':np.sqrt(np.mean((residual-residual.mean())**2)),
                                 'anomaly_correlation':pearsonr(va,vb).statistic,
                                 'fraction_within_independence_h95':float(np.mean(np.abs(residual)<=pooled_h))})
    annual,pairs,coverage=pd.DataFrame(annual),pd.DataFrame(pair_records),pd.DataFrame(coverage)
    save_csv(annual,'method_annual_sensitivity.csv')
    save_csv(pairs,'method_native_pair_comparison.csv')
    save_csv(coverage,'method_coverage.csv')
    return annual,pairs,coverage


def literature_comparison(g, hydro):
    rec=[]
    for title, start, end, ref_value, ref_h in [('Hugonnet et al. (2021)',2000,2020,-267.,16.),
                                               ('Zemp et al. (2019), Table 1',2006,2016,-332.,144.)]:
        # Zemp et al. explicitly define their decade by hydrological years
        # 2006/07 through 2015/16. Sum 10-year regional means in that convention.
        source = hydro if title.startswith('Zemp') else g
        d=source[(source.start_dates>=start)&(source.start_dates<end)]
        n=end-start
        benchmark_mean=d.combined_gt.sum()/n
        rec.append({'reference':title,'first_year':start,'last_year':end-1,'n_years':n,
                    'reference_gt_per_yr':ref_value,'reference_h95':ref_h,
                    'time_basis':'Regional hydrological years' if title.startswith('Zemp') else 'Calendar years',
                    'benchmark_gt_per_yr':benchmark_mean,
                    'benchmark_h95_independent':np.sqrt(np.sum(d.combined_gt_errors**2))/n,
                    'benchmark_minus_reference_gt_per_yr':benchmark_mean-ref_value,
                    'fraction_less_negative_pct':(1-benchmark_mean/ref_value)*100,
                    'independent_validation':False})
    df=pd.DataFrame(rec)
    save_csv(df,'literature_comparison.csv')
    return df


def figures(inv,raw,cal,hydro,summary,g,r,cumulative,pairs,annual,coverage,spatial,dense,lit,checks):
    sns.set_theme(style='ticks',context='paper',font_scale=1.13)
    plt.rcParams.update({'axes.spines.top':False,'axes.spines.right':False,'font.family':'DejaVu Sans','axes.titleweight':'bold'})
    # 1. Inventory and actual method support, not misleading raw-data counts.
    fig,axes=plt.subplots(1,3,figsize=(16,7),gridspec_kw={'width_ratios':[1.2,.9,1.2]})
    count=inv.groupby(['region_id','method']).size().unstack(fill_value=0).reindex(index=range(1,20),columns=RAW_METHODS)
    sns.heatmap(count,annot=True,fmt='d',cmap='YlGnBu',cbar=False,ax=axes[0],xticklabels=['Glaciol.','DEM','Altim.','Gravim.','Hybrid'],yticklabels=NAMES[1:])
    axes[0].set(xlabel='',ylabel='',title='a  Archived CSV files by method')
    axes[0].tick_params(axis='x',rotation=40)
    for method in RAW_METHODS:
        dur=raw.loc[raw.method==method,'duration_yr'].values
        axes[1].hist(dur,bins=np.geomspace(.06,80,30),histtype='step',linewidth=1.6,label=method.replace('combined','hybrid'))
    axes[1].set(xscale='log',yscale='log',xlabel='Observation interval (years)',ylabel='Number of intervals',title='b  Native temporal resolution')
    axes[1].legend(fontsize=8,frameon=False)
    mat=annual.pivot(index='region_id',columns='start_dates',values='n_methods_native')
    # Hydrological starts differ by hemisphere: use ordinal row-year index.
    mat=np.array([annual[annual.region_id==rid].sort_values('start_dates').n_methods_native.to_numpy().tolist()+[np.nan]*(24-len(annual[annual.region_id==rid])) for rid in range(1,20)])
    sns.heatmap(mat,cmap=sns.color_palette(['#e0e8ed','#65a9b8','#165779']),vmin=1,vmax=3,ax=axes[2],cbar_kws={'label':'Methods with own annual variability','ticks':[1,2,3]},yticklabels=False)
    axes[2].set(title='c  Annual variability support',xlabel='Hydrological interval index (2000 onward)',ylabel='')
    axes[2].set_xticks(np.array([0,5,10,15,20,23])+.5,labels=['0','5','10','15','20','23'],rotation=0)
    fig.suptitle('Data availability and evidence structure',fontsize=15,y=1.02)
    fig.tight_layout();save_fig(fig,'figure_01_data_overview.png')
    # 2. Annual and cumulative released benchmark, both physical units.
    fig,axes=plt.subplots(3,1,figsize=(11,11),sharex=True)
    x=g.start_dates.to_numpy()+.5
    for ax,col,err,label in [(axes[0],'combined_gt','combined_gt_errors','Annual mass change (Gt)'),(axes[1],'combined_mwe','combined_mwe_errors','Annual specific change (m w.e.)')]:
        ax.bar(x,g[col],width=.72,color='#b94b50',alpha=.9)
        ax.errorbar(x,g[col],yerr=g[err],fmt='none',ecolor='#353535',capsize=2,lw=1)
        ax.axhline(0,color='k',lw=.7)
        ax.set_ylabel(label)
    axes[0].set_title('a  Global mass balance; error bars show released 95% intervals',loc='left')
    axes[1].set_title('b  Area-normalized mass balance',loc='left')
    xc=np.r_[2000,g.end_dates.values];yc=np.r_[0,cumulative.cumulative_gt.values]
    for label,col,color in [('AR(1), ρ = 0.7','ar1_07','#b5c6d4'),('Independent years','independent','#6d94b0')]:
        hc=np.r_[0,cumulative['cumulative_gt_h95_'+col].values]
        axes[2].fill_between(xc,yc-hc,yc+hc,color=color,label=label)
    axes[2].plot(xc,yc,color='#19394d',lw=2)
    axes[2].set(xlabel='Calendar year',ylabel='Cumulative mass change (Gt)',title='c  Cumulative loss; 95% covariance scenarios')
    axes[2].legend(frameon=False,loc='lower left')
    axes[2].set_xlim(1999.7,2024.3)
    axes[2].set_xticks(range(2000,2025,2))
    fig.tight_layout();save_fig(fig,'figure_02_global_benchmark.png')
    # 3. All regional specific time series and regional loss rates.
    fig,axes=plt.subplots(1,2,figsize=(15,8),gridspec_kw={'width_ratios':[1.6,1]})
    heat=r.pivot(index='region_id',columns='start_dates',values='combined_mwe').reindex(range(1,20))
    sns.heatmap(heat,cmap='RdBu',center=0,vmin=-2,vmax=2,ax=axes[0],yticklabels=NAMES[1:],xticklabels=[str(int(v)) for v in heat.columns],cbar_kws={'label':'Annual specific change (m w.e.)','shrink':.7,'extend':'min'})
    axes[0].set(title='a  Regional calendar-year mass balance',xlabel='Calendar year',ylabel='')
    axes[0].tick_params(axis='x',rotation=90)
    sr=summary[summary.region_id>0].sort_values('mean_gt_per_yr')
    yp=np.arange(len(sr))
    axes[1].barh(yp,-sr.mean_gt_per_yr,color='#bf6266')
    axes[1].errorbar(-sr.mean_gt_per_yr,yp,xerr=sr.mean_gt_h95_independent,fmt='none',ecolor='#333',capsize=2)
    axes[1].set_yticks(yp,labels=sr.region_name)
    axes[1].invert_yaxis();axes[1].set(xlabel='Mean mass loss (Gt yr⁻¹)',title='b  Contribution to global loss')
    fig.tight_layout();save_fig(fig,'figure_03_regional_pattern.png')
    # 4. Method-native pair comparisons, plotted without borrowed variability.
    fig,axes=plt.subplots(1,3,figsize=(16,6),gridspec_kw={'width_ratios':[1.2,1,1]})
    for a,color,marker in [('altimetry',COLORS['altimetry'],'o'),('gravimetry',COLORS['gravimetry'],'s')]:
        p=pairs[(pairs.method_a==a)&(pairs.method_b==METHODS[2])]
        axes[0].scatter(p.mean_b_mwe,p.mean_a_mwe,c=color,marker=marker,s=45,label=MLABEL[a])
        for _,row in p.iterrows():axes[0].annotate(str(int(row.region_id)),(row.mean_b_mwe,row.mean_a_mwe),xytext=(3,4),textcoords='offset points',fontsize=8)
        axes[2].scatter(p.mean_difference_mwe,p.anomaly_correlation,c=color,marker=marker,s=45,label=MLABEL[a])
    lim=[-1.6,.1];axes[0].plot(lim,lim,color='gray',ls='--');axes[0].set(xlim=lim,ylim=lim,xlabel='DEM + glaciological (m w.e. yr⁻¹)',ylabel='Other method (m w.e. yr⁻¹)',title='a  Matched-period regional means')
    axes[0].legend(frameon=False)
    for j,(a,offset) in enumerate([('altimetry',-.13),('gravimetry',.13)]):
        p=pairs[(pairs.method_a==a)&(pairs.method_b==METHODS[2])]
        axes[1].errorbar(p.mean_difference_mwe,p.region_id+offset,xerr=p.difference_mean_h95_independent,fmt='o' if j==0 else 's',color=COLORS[a],capsize=2,ms=4)
    axes[1].axvline(0,color='gray',lw=.8);axes[1].set_yticks(range(1,20),labels=[str(i) for i in range(1,20)]);axes[1].invert_yaxis();axes[1].set(xlabel='Other − DEM + glaciol. (m w.e. yr⁻¹)',ylabel='Region ID (Table 2)',title='b  Mean differences and conditional 95% intervals')
    axes[2].axvline(0,color='gray',ls='--');axes[2].set(xlabel='Mean difference (m w.e. yr⁻¹)',ylabel='Annual anomaly correlation',title='c  Agreement in variability',ylim=(-1.05,1.05))
    fig.tight_layout();save_fig(fig,'figure_04_method_comparison.png')
    # 5. Weight sensitivity conditioned on >=2 native method observations.
    aa=annual[annual.n_methods_native>=2]
    fig,axes=plt.subplots(1,2,figsize=(13,7))
    regids=sorted(aa.region_id.unique())
    data=[aa.loc[aa.region_id==rid,'ivw_minus_equal_mwe'].values for rid in regids]
    bp=axes[0].boxplot(data,orientation='horizontal',tick_labels=[NAMES[i] for i in regids],patch_artist=True,showfliers=True)
    for patch in bp['boxes']:patch.set_facecolor('#8cb5c1')
    axes[0].axvline(0,color='gray',ls='--');axes[0].set(xlabel='Inverse-variance − equal mean (m w.e.)',title='a  Annual weight sensitivity by region')
    leave=[aa['leave_out_'+m+'_minus_equal_mwe'].dropna().values for m in METHODS]
    axes[1].boxplot(leave,tick_labels=['Altimetry','Gravimetry','DEM +\nglaciological'],patch_artist=True)
    axes[1].axhline(0,color='gray',ls='--');axes[1].set(ylabel='Omission − full native equal mean (m w.e.)',title='b  Leave-one-method-out sensitivity')
    fig.tight_layout();save_fig(fig,'figure_05_weight_sensitivity.png')
    # 6. Uncertainty dependence on assumptions.
    fig,axes=plt.subplots(1,3,figsize=(15,4.8))
    axes[0].plot(dense.rho,dense.mean_h95,color='#226681',lw=2);axes[0].set(xlabel='Lag-1 temporal error correlation ρ',ylabel='95% half-width (Gt yr⁻¹)',title='a  Uncertainty of 24-year mean')
    axes[1].plot(dense.rho,dense.contrast_h95,color='#ad4c51',lw=2)
    delta=abs(summary.loc[summary.region_id==0,'late_minus_early_gt'].iloc[0])
    axes[1].axhline(delta,color='black',ls='--',label=f'Observed increase: {delta:.1f}')
    axes[1].set(xlabel='Lag-1 temporal error correlation ρ',ylabel='95% half-width (Gt yr⁻¹)',title='b  Uncertainty of half-period difference')
    axes[1].legend(fontsize=8,frameon=False)
    for year in [2000,2011,2023]:
        p=spatial[spatial.year==year];axes[2].plot(p.region_correlation,p.global_annual_h95_gt,label=str(year),lw=2)
    axes[2].set(xlabel='Pairwise regional error correlation c',ylabel='Annual 95% half-width (Gt)',title='c  Spatial covariance sensitivity');axes[2].legend(frameon=False)
    fig.tight_layout();save_fig(fig,'figure_06_covariance_sensitivity.png')
    # 7. Literature context and actual global closure audit.
    fig,axes=plt.subplots(1,2,figsize=(13,5),gridspec_kw={'width_ratios':[1.2,1]})
    for i,row in lit.iterrows():
        axes[0].errorbar(row.reference_gt_per_yr,i+.1,xerr=row.reference_h95,fmt='s',color='#b9793f',capsize=4,label='Reference assessment' if i==0 else None)
        axes[0].errorbar(row.benchmark_gt_per_yr,i-.1,xerr=row.benchmark_h95_independent,fmt='o',color='#236d86',capsize=4,label='Released benchmark, matched periods' if i==0 else None)
    axes[0].set_yticks(range(len(lit)),labels=[f'{x.reference}\n'+(f'{x.first_year}/07–2015/16 (hydrol.)' if x.reference.startswith('Zemp') else f'{x.first_year}–{x.last_year} (calendar)') for _,x in lit.iterrows()])
    axes[0].set(xlabel='Mean glacier mass change (Gt yr⁻¹)',title='a  Literature comparison (shared inputs)');axes[0].legend(frameon=False,loc='lower left',fontsize=8)
    axes[1].plot(checks.year,checks.global_minus_regional_gt,'o-',label='Mass closure (Gt)',ms=4)
    axes[1].plot(checks.year,checks.global_minus_regional_gt_h95,'s-',label='95% half-width closure (Gt)',ms=3)
    axes[1].axhline(0,color='gray',lw=.6);axes[1].ticklabel_format(axis='y',style='sci',scilimits=(0,0))
    axes[1].set(xlabel='Calendar year',ylabel='Global − aggregated regions (Gt)',title='b  Aggregation audit; numerical precision');axes[1].legend(frameon=False,fontsize=8)
    fig.tight_layout();save_fig(fig,'figure_07_validation_context.png')
    # 8. Complete regional annual mass series and published uncertainties.
    fig,axes=plt.subplots(5,4,figsize=(16,15),sharex=True)
    for rid,ax in zip(range(1,20),axes.flat):
        d=r[r.region_id==rid]
        ax.fill_between(d.start_dates+.5,d.combined_gt-d.combined_gt_errors,d.combined_gt+d.combined_gt_errors,color='#e6b9bc',alpha=.8)
        ax.plot(d.start_dates+.5,d.combined_gt,color='#94434b',lw=1.2)
        ax.axhline(0,color='gray',lw=.6);ax.set_title(f'{rid:02d} {NAMES[rid]}',fontsize=10,loc='left')
        ax.set_ylabel('Gt');ax.set_xticks([2000,2010,2020])
    axes.flat[-1].axis('off')
    fig.suptitle('Regional calendar-year mass change; shading shows released 95% intervals',y=1.005,fontsize=15)
    fig.tight_layout();save_fig(fig,'figure_08_regional_series.png')


def main():
    OUT.mkdir(exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    inv,raw=inventory()
    cal=load_results('calendar_years');hydro=load_results('hydrological_years')
    g=cal[cal.region_id==0].copy().sort_values('start_dates');r=cal[cal.region_id>0].copy()
    save_csv(annual_export(cal),'benchmark_annual_all.csv')
    save_csv(annual_export(r),'benchmark_regional_annual.csv')
    save_csv(annual_export(g),'benchmark_global_annual.csv')
    checks,aud=audit(cal,hydro,raw)
    summary=period_summary(cal)
    scenarios,cumulative,spatial,dense=covariance_analysis(g,r)
    annual,pairs,coverage=method_analysis(hydro)
    lit=literature_comparison(g,hydro)
    figures(inv,raw,cal,hydro,summary,g,r,cumulative,pairs,annual,coverage,spatial,dense,lit,checks)
    aa=annual[annual.n_methods_native>=2]
    alt=pairs[(pairs.method_a=='altimetry')&(pairs.method_b==METHODS[2])]
    grav=pairs[(pairs.method_a=='gravimetry')&(pairs.method_b==METHODS[2])]
    sg=summary[summary.region_id==0].iloc[0]
    ranked=summary[summary.region_id>0].sort_values('mean_gt_per_yr')
    metrics={'n_input_files':len(inv),'n_input_intervals':len(raw),
             'method_file_counts':inv.method.value_counts().to_dict(),
             'n_input_submission_labels':int(inv.submission_label.nunique()),
             'n_uzh_seasonal_files':int(inv.submission_label.str.contains('UZH_GlaciolSineWave').sum()),
             'n_files_excluding_uzh_auxiliary':int((~inv.submission_label.str.contains('UZH_GlaciolSineWave')).sum()),
             'global_mean_gt':float(sg.mean_gt_per_yr),'global_mean_h95_independent':float(sg.mean_gt_h95_independent),
             'global_cumulative_gt':float(sg.cumulative_gt),'global_cumulative_h95_independent':float(sg.cumulative_gt_h95_independent),
             'global_mean_mwe':float(sg.mean_mwe_per_yr),'global_mean_mwe_h95_independent':float(sg.mean_mwe_h95_independent),
             'global_cumulative_specific_mwe':float(sg.cumulative_specific_mwe),
             'global_loss_sealevel_mm':float(-sg.cumulative_gt/362.5),
             'global_loss_sealevel_h95':float(sg.cumulative_gt_h95_independent/362.5),
             'increase_pct':float((sg.late_mean_gt/sg.early_mean_gt-1)*100),
             'top5_share_pct':float(ranked.head(5).share_global_loss_pct.sum()),
             'area_change_pct':float((g.glacier_area.iloc[-1]/g.glacier_area.iloc[0]-1)*100),
             'n_native_multimethod_regionyears':len(aa),'n_hydrological_regionyears':len(annual),
             'n_single_native_regionyears':int((annual.n_methods_native==1).sum()),
             'n_single_method_regions':int((coverage[coverage.method!=METHODS[2]].groupby('region_id').n_trend_years.sum()==0).sum()),
             'ivw_equal_median_abs_mwe':float(aa.ivw_minus_equal_mwe.abs().median()),
             'ivw_equal_p95_abs_mwe':float(aa.ivw_minus_equal_mwe.abs().quantile(.95)),
             'ivw_equal_max_abs_mwe':float(aa.ivw_minus_equal_mwe.abs().max()),
             'altimetry_equal_region_mean_difference_mwe':float(alt.mean_difference_mwe.mean()),
             'gravimetry_equal_region_mean_difference_mwe':float(grav.mean_difference_mwe.mean()),
             'altimetry_median_anomaly_correlation':float(alt.anomaly_correlation.median()),
             'gravimetry_median_anomaly_correlation':float(grav.anomaly_correlation.median()),
             'median_native_methods':float(annual.n_methods_native.median()),
             'mean_gt_h95_all_regions_all_years_common':float(r.combined_gt_errors.sum()/24),
             'conventional_unit_cumulative_gt':float(sg.cumulative_gt/.997),
             'n_calendar_global_point_losses':int((g.combined_gt<0).sum())}
    (OUT/'key_metrics.json').write_text(json.dumps(metrics,indent=2))
    versions={'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,
              'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'seaborn':sns.__version__,
              'data_doi':'10.5904/wgms-glambie-2024-07','primary_paper_doi':'10.1038/s41586-024-08545-z',
              'uncertainty_convention':'95% half-width = 1.96 standard deviations',
              'random_sampling':'None; all calculations are deterministic'}
    (OUT/'run_metadata.json').write_text(json.dumps(versions,indent=2))
    print(json.dumps(metrics,indent=2))
    print(scenarios.to_string(index=False))
    print('Audit assertions passed. Figures and tabular outputs written.')


if __name__=='__main__':
    main()
