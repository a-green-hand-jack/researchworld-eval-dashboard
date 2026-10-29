"""GlaMBIE-style reconciliation of regional glacier mass change estimates (own implementation).

For one region and one annual grid (calendar or hydrological year) this
  1. homogenises every submitted solution to m w.e.,
  2. builds one annual series per observation group (altimetry, gravimetry, DEM-differencing+glaciological),
     calibrating annual variability to the multi-year (trend) constraints,
  3. merges the groups into one regional series and propagates uncertainties.
All series are *mass change per annual window* in m w.e. (specific mass change).
"""
import numpy as np, pandas as pd
from glambie_core import *

EPS = 1e-6
GROUPS = ['altimetry', 'gravimetry', 'demdiff_and_glaciological']
EXCLUDE_PREFIX = ('combined_Box', 'combined_ArcticInSituvGRACE')   # GRACE-contaminated "combined" series

def overlap_matrix(s, e, y0, T):
    """fraction of each annual window t covered by [s,e]  (T,)"""
    a = y0 + np.arange(T); b = a + 1
    return np.clip(np.minimum(e, b) - np.maximum(s, a), 0, None)

def split_solution(sol, y0, T):
    """Split into annual-resolution part (annual series on grid) and multi-year constraints."""
    d = sol['e'] - sol['s']
    ann = d <= 1 + EPS
    cons = []
    for k in np.where(~ann)[0]:
        cons.append(dict(s=sol['s'][k], e=sol['e'][k], rate=sol['ch'][k]/d[k], srate=sol['err'][k]/d[k], name=sol['name']))
    series = None
    if ann.any():
        sub = dict(sol); 
        for key in ('s', 'e', 'ch', 'err'): sub[key] = sol[key][ann]
        ch, er, _ = annual_series(sub, y0, T, 'indep')
        # quoted-error based annual error: sum in quadrature if windows are >=annual, otherwise mean monthly error / sqrt(12)
        dd = sub['e'] - sub['s']
        if np.median(dd) < 0.99:
            m = np.full(T, np.nan)
            for i in range(T):
                ov = overlap_matrix(sub['s'], sub['e'], y0, T)[i] if False else None
            er = np.full(T, np.nan)
            a = y0 + np.arange(T)
            for i in range(T):
                msk = (sub['s'] >= a[i]-EPS) & (sub['e'] <= a[i]+1+EPS)
                if msk.sum() > 0: er[i] = np.mean(sub['err'][msk])/np.sqrt(12)
        if np.isfinite(ch).sum() >= 2:
            series = (ch, er)
    return series, cons

def twoway(Y, w=None, iters=200):
    """Additive two-way fit Y[i,t] = mu[t] + b[i], sum(b)=0, NaN-tolerant. returns mu, b, resid"""
    n, T = Y.shape
    M = np.isfinite(Y); Y0 = np.where(M, Y, 0.0)
    W = M.astype(float) if w is None else np.where(M, w, 0.0)
    b = np.zeros(n); mu = np.zeros(T)
    for _ in range(iters):
        num = (W*(Y0 - b[:, None])).sum(0); den = W.sum(0)
        mu = np.where(den > 0, num/np.where(den > 0, den, 1), np.nan)
        R = np.where(M, Y0 - mu[None, :], 0.0)
        b = np.where((M & np.isfinite(mu)[None, :]).sum(1) > 0, (R*np.isfinite(mu)[None, :]).sum(1)/np.maximum((M & np.isfinite(mu)[None, :]).sum(1), 1), 0)
        b = b - b.mean()
    mu = np.where(den > 0, (W*(Y0 - b[:, None])).sum(0)/np.where(den > 0, den, 1), np.nan)
    res = np.where(M, Y0 - mu[None, :] - b[:, None], np.nan)
    return mu, b, res

def window_mean(x, wfrac):
    """mean of annual series x over a window described by overlap fractions wfrac; NaN if poorly covered"""
    m = np.isfinite(x) & (wfrac > 0)
    if wfrac.sum() == 0 or wfrac[m].sum() < 0.9*wfrac.sum(): return np.nan
    return np.sum(x[m]*wfrac[m])/wfrac[m].sum()

def build_group(sols, y0, T, anchored, fallback_err=0.25):
    """Combine solutions of one group on annual grid. anchored=True: multi-year constraints define the level
    (DEM-differencing + glaciological); else constraints are treated as extra 'solutions' in their window."""
    series, cons, names = [], [], []
    for s in sols:
        sr, cs = split_solution(s, y0, T)
        if sr is not None: series.append(sr); names.append(s['name'])
        cons += cs
    out = dict(n_series=len(series), n_cons=len(cons), names=names)
    if not series and not cons: return None
    Yc = np.array([x[0] for x in series]) if series else np.full((0, T), np.nan)
    Ye = np.array([x[1] for x in series]) if series else np.full((0, T), np.nan)
    na = np.isfinite(Yc).sum(0) if series else np.zeros(T, int)
    if series:
        mu, b, res = twoway(Yc)
        # pooled dispersion of annual values (solution-to-solution) about the group mean
        dof = np.maximum(na-1, 0); ssq = np.nansum(res**2, 0)
        pooled = np.sqrt(ssq[dof > 0].sum()/dof[dof > 0].sum()) if dof.sum() > 0 else np.nan
        sb = np.std(b, ddof=1) if len(b) > 1 else np.nan
    else:
        mu = np.full(T, np.nan); pooled = sb = np.nan
    out['pooled_sd'] = pooled; out['sb'] = sb
    # constraints
    Wc = []; deltas = []; dsd = []
    for c in cons:
        wf = overlap_matrix(c['s'], c['e'], y0, T)
        if wf.sum() < 0.5*(c['e']-c['s']) : continue          # window mostly outside grid
        wf_n = wf
        ref = window_mean(mu, wf_n) if series else np.nan
        Wc.append(wf_n); deltas.append(c['rate'] - ref if np.isfinite(ref) else np.nan); dsd.append(c['srate'])
        c['_rate'] = c['rate']
    y = mu.copy(); sig = np.full(T, np.nan); sig_tr = np.full(T, np.nan)
    Wc = np.array(Wc) if Wc else np.zeros((0, T)); deltas = np.array(deltas); dsd = np.array(dsd)
    rates = np.array([c['rate'] for c in cons if overlap_matrix(c['s'], c['e'], y0, T).sum() >= 0.5*(c['e']-c['s'])])
    for t in range(T):
        if len(Wc) == 0: break
        # constraint weights for year t (fraction of the year inside the constraint window)
        w = Wc[:, t]
        if w.sum() < 0.25: continue
        if anchored:
            if np.isfinite(mu[t]):
                ok = np.isfinite(deltas) & (w > 0)
                if ok.any(): y[t] = mu[t] + np.sum(w[ok]*deltas[ok])/w[ok].sum()
            else:
                y[t] = np.sum(w*rates)/w.sum()
        else:
            if na[t] > 0:
                ok = np.isfinite(deltas) & (w > 0)
                if ok.any(): y[t] = mu[t] + np.sum(w[ok]*deltas[ok])/(na[t] + w[ok].sum())
            else:
                y[t] = np.sum(w*rates)/w.sum()
    # trend (constraint) error and annual-variability error
    for t in range(T):
        w = Wc[:, t] if len(Wc) else np.zeros(0)
        cons_on = w > 0.25 if len(w) else np.zeros(0, bool)
        n_c = cons_on.sum() if len(w) else 0
        e_tr = np.sqrt(np.sum(dsd[cons_on]**2))/n_c if n_c else np.nan
        if n_c > 1:   # between-solution spread of rates adds a systematic component
            rr = rates[cons_on]; e_tr = np.sqrt(e_tr**2 + np.var(rr, ddof=1)/n_c)
        if na[t] >= 2 and np.isfinite(pooled):
            e_v = np.sqrt(pooled**2 + (sb if np.isfinite(sb) else 0)**2)/np.sqrt(na[t])
        elif na[t] == 1:
            q = np.nanmean(Ye[:, t]) if np.isfinite(Ye[:, t]).any() else np.nan; e_v = max(q if np.isfinite(q) else 0, pooled if np.isfinite(pooled) else 0, 0.05)
        else: e_v = np.nan
        tr_parts = [x for x in (e_tr,) if np.isfinite(x)]
        sbt = (sb if np.isfinite(sb) else 0)/np.sqrt(na[t]) if na[t] >= 1 else np.nan
        if np.isfinite(sbt): tr_parts.append(sbt)
        sig_tr[t] = np.sqrt(np.sum(np.square(tr_parts))) if tr_parts else np.nan
        if anchored:
            # annual variability around calibrated block means; trend error from constraints
            if n_c: sig[t] = np.sqrt(e_tr**2 + (e_v if np.isfinite(e_v) else fallback_err)**2*0.5)
            elif np.isfinite(y[t]): sig[t] = np.nan
        else:
            parts = [x for x in (e_tr, e_v) if np.isfinite(x)]
            if parts:
                # constraint and annual-resolved info combined as independent estimates of the same level
                sig[t] = 1/np.sqrt(np.sum([1/p**2 for p in parts]))
                if na[t] >= 2 and np.isfinite(pooled): sig[t] = max(sig[t], np.sqrt(pooled**2 + (sb if np.isfinite(sb) else 0)**2)/np.sqrt(na[t]+n_c))
    # years beyond constraint support (anchored group): inflate the last known trend error
    if anchored:
        last = np.where(np.isfinite(sig))[0]
        if len(last):
            L = last.max()
            for t in range(L+1, T):
                if np.isfinite(y[t]): sig[t] = sig[L]*(1+0.5*(t-L))
            first = last.min()
            for t in range(0, first):
                if np.isfinite(y[t]): sig[t] = sig[first]*(1+0.5*(first-t))
    out['y'] = y; out['sig'] = sig; out['sig_tr'] = np.where(np.isfinite(sig_tr), np.minimum(sig_tr, sig), sig_tr); out['na'] = na; out['cons'] = cons
    return out

def combine_groups(gs, T):
    """Level-matched inverse-variance merge of group series; returns mean, error, bias, diagnostics."""
    names = list(gs)
    Y = np.array([gs[g]['y'] for g in names]); S = np.array([gs[g]['sig'] for g in names])
    S = np.where(np.isfinite(Y) & ~np.isfinite(S), np.nanmedian(S[np.isfinite(S)]) if np.isfinite(S).any() else 0.3, S)
    Wt = np.where(np.isfinite(Y), 1/S**2, 0.0)
    mu, b, res = twoway(Y)            # equal weight per observation group (robust to noisy error estimates)
    n = np.isfinite(Y).sum(0)
    if len(names) > 1:
        dof = np.maximum(n-1, 0); ssq = np.nansum(res**2, 0)
        sp = np.sqrt(ssq[dof > 0].sum()/dof[dof > 0].sum()) if dof.sum() > 0 else 0.0
        sbb = np.sqrt(np.sum(b**2)/(len(names)-1))
    else: sp = sbb = 0.0
    e_ivw = 1/np.sqrt(Wt.sum(0))
    err = np.sqrt(e_ivw**2 + (sp**2 + sbb**2)/np.maximum(n, 1))
    Str = np.array([gs[g]['sig_tr'] for g in names]); Str = np.where(np.isfinite(Y) & ~np.isfinite(Str), S, Str)
    e_tr = np.sqrt(np.nansum(np.where(np.isfinite(Y), Str, 0)**2, 0))/np.maximum(n, 1)
    err_tr = np.sqrt(e_tr**2 + sbb**2/np.maximum(n, 1))      # temporally-correlated (trend-type) part
    err_tr = np.minimum(err_tr, err)
    return mu, err, b, dict(sp=sp, sb=sbb, n=n, err_tr=err_tr)

def borrow_variability(gs, y0, T):
    """Groups that only supply multi-year constraints in some years (no annual-resolved data) get their annual
    variability from the groups that do (additive calibration to the constraint windows)."""
    # reference variability: level-matched mean of the annual-informed group values
    Y = np.array([np.where(gs[g]['na'] > 0, gs[g]['y'], np.nan) if g != 'demdiff_and_glaciological' else gs[g]['y'] for g in gs])
    ref, _, _ = twoway(Y)
    for g, r in gs.items():
        if g == 'demdiff_and_glaciological': continue
        flat = (r['na'] == 0) & np.isfinite(r['y'])
        if not flat.any(): continue
        cons = [c for c in r['cons'] if overlap_matrix(c['s'], c['e'], y0, T).sum() >= 0.5*(c['e']-c['s'])]
        for t in np.where(flat)[0]:
            num = den = 0.0
            for c in cons:
                wf = overlap_matrix(c['s'], c['e'], y0, T)
                if wf[t] < 0.25: continue
                rm = window_mean(ref, wf)
                if not np.isfinite(rm): continue
                num += wf[t]*(c['rate'] - rm); den += wf[t]
            if den > 0 and np.isfinite(ref[t]): r['y'][t] = ref[t] + num/den
        r['borrowed'] = flat

def run_region(rid, y0, T, allow=None, exclude=EXCLUDE_PREFIX):
    sols = [s for s in load_solutions(rid) if not s['name'].startswith(exclude)]
    gs = {}
    for g in GROUPS:
        if allow is not None and g not in allow: continue
        ss = [s for s in sols if s['group'] == g]
        if not ss: continue
        r = build_group_dem(ss, y0, T) if g == 'demdiff_and_glaciological' else build_group(ss, y0, T, anchored=False)
        if r is not None and np.isfinite(r['y']).any(): gs[g] = r
    borrow_variability(gs, y0, T)
    mu, err, b, diag = combine_groups(gs, T)
    return dict(groups=gs, mu=mu, err=err, b=b, diag=diag)

# Group eligibility (observational-physics screening): GRACE only where regional glacier mass signal is resolvable
# (not contaminated by ice-sheet leakage/hydrology or too small); altimetry excluded for Alaska (poor, non-representative
# CryoSat-2/ICESat coverage over steep terrain).  Follows the screening used in the GlaMBIE product.
GRAV_REGIONS = {1, 3, 4, 6, 7, 9, 17}
def allowed_groups(rid):
    a = {'demdiff_and_glaciological'}
    if rid in GRAV_REGIONS: a.add('gravimetry')
    if rid != 1: a.add('altimetry')
    return a


def build_group_dem(sols, y0, T, ext_years=3):
    """DEM-differencing + glaciological group.
    Level (trend) sources: geodetic multi-year solutions (DEM differencing, multi-year combined) and annual 'combined'
    products; each solution carries equal weight.  Glaciological series (WGMS, UZH sine-wave) provide only
    annual variability, which is calibrated onto each multi-year geodetic solution (additive shift per period)."""
    gl, comb_ann, cons, names = [], [], [], []
    for s in sols:
        sr, cs = split_solution(s, y0, T)
        if s['src'] == 'glaciological':
            if sr is not None: gl.append(sr)
        elif s['src'] == 'combined' and sr is not None:
            comb_ann.append((s['name'], sr))
        for c in cs: cons.append(c)
    # annual variability: glaciological if available, else the annual combined products
    shape_src = [x[0] for x in gl] if gl else [x[1][0] for x in comb_ann]
    if not shape_src and not comb_ann and not cons: return None
    V, _, _ = twoway(np.array(shape_src)) if shape_src else (np.full(T, np.nan), None, None)
    # fill gaps in V by the mean of the available combined series (anomaly only)
    # --- calibrated series for each geodetic solution (grouped by solution name)
    by_sol = {}
    for c in cons: by_sol.setdefault(c['name'], []).append(c)
    S, Sn, Serr = [], [], []
    for name, cl in by_sol.items():
        y = np.full(T, np.nan); se = np.full(T, np.nan); W = np.zeros(T); offs = []; ofs_t = np.full(T, np.nan)
        for c in cl:
            wf = overlap_matrix(c['s'], c['e'], y0, T)
            if wf.sum() < 0.5*(c['e'] - c['s']): continue
            ref = window_mean(V, wf)
            d = c['rate'] - ref if np.isfinite(ref) else np.nan
            for t in np.where(wf > 0.25)[0]:
                if np.isfinite(d) and wf[t] >= np.max(np.where(True, 0.25, 0)): 
                    ofs_t[t] = d; se[t] = c['srate']
            if np.isfinite(d): offs.append((c['e'], d, c['srate']))
        if not offs: continue
        # extrapolate offset beyond/before the supported period using the mean offset of the nearest 10 years
        offs.sort(); last = offs[-ext_years:] if len(offs) >= 1 else offs
        dlast = np.mean([o[1] for o in last]); elast = np.mean([o[2] for o in last])
        sup = np.isfinite(ofs_t)
        idx = np.where(sup)[0]
        for t in range(T):
            if not sup[t]:
                ofs_t[t] = dlast if t > idx.max() else np.mean([o[1] for o in offs[:ext_years]])
                se[t] = elast*(1 + 0.5*(t-idx.max())) if t > idx.max() else np.mean([o[2] for o in offs[:ext_years]])*(1+0.5*(idx.min()-t))
        S.append(V + ofs_t); Sn.append(name); Serr.append(se)
    for name, sr in comb_ann:
        S.append(sr[0]); Sn.append(name); Serr.append(np.full(T, np.nanmedian(sr[1])/np.sqrt(5)) if np.isfinite(sr[1]).any() else np.full(T, 0.1))
    S = np.array(S); Serr = np.array(Serr)
    mu, b, res = twoway(S)
    n = np.isfinite(S).sum(0)
    dof = np.maximum(n-1, 0); pooled = np.sqrt(np.nansum(res**2)/dof.sum()) if dof.sum() > 0 else np.nan
    # trend error: independent quoted errors of the sources + between-source dispersion of levels
    sb = np.std(b, ddof=1) if len(b) > 1 else 0.0
    sig = np.full(T, np.nan); sig_tr = np.full(T, np.nan)
    for t in range(T):
        ok = np.isfinite(S[:, t])
        if not ok.any(): continue
        e_q = np.nanmean(Serr[ok, t])   # geodetic sources share DEMs/outlines: treat their errors as fully correlated
        e_b = sb/np.sqrt(ok.sum())
        e_v = (pooled if np.isfinite(pooled) else 0.2)/np.sqrt(ok.sum())
        sig[t] = np.sqrt(e_q**2 + e_b**2 + e_v**2); sig_tr[t] = np.sqrt(e_q**2 + e_b**2)
    return dict(y=mu, sig=sig, sig_tr=sig_tr, na=n, n_series=len(S), n_cons=len(cons), names=Sn, pooled_sd=pooled, sb=sb, S=S, V=V)
