"""Core routines: loading, homogenisation and annual aggregation of GlaMBIE input series."""
import glob, os
import numpy as np, pandas as pd
D = '/work/data/glambie'
RHO_CONV = 0.85  # m (elevation change) -> m w.e.
REGIONS = {1:'alaska',2:'western_canada_us',3:'arctic_canada_north',4:'arctic_canada_south',5:'greenland_periphery',
           6:'iceland',7:'svalbard',8:'scandinavia',9:'russian_arctic',10:'north_asia',11:'central_europe',
           12:'caucasus_middle_east',13:'central_asia',14:'south_asia_west',15:'south_asia_east',16:'low_latitudes',
           17:'southern_andes',18:'new_zealand',19:'antarctic_and_subantarctic'}
GROUP_OF = {'altimetry':'altimetry','gravimetry':'gravimetry','demdiff':'demdiff_and_glaciological',
            'glaciological':'demdiff_and_glaciological','combined':'demdiff_and_glaciological'}

def official(rid, kind='hydrological_years'):
    return pd.read_csv(f"{D}/results/{kind}/{rid}_{REGIONS[rid]}.csv")

def area_fn(rid):
    """glacier area (km2) as function of time, from the regional area time series (hydrological-year midpoints)."""
    o = official(rid)
    t = 0.5*(o.start_dates+o.end_dates); a = o.glacier_area
    return lambda x: np.interp(x, t, a)

def flag_filled(s, e, ch, minrun=3):
    """Boolean keep-mask: drop runs (>=minrun) of identical consecutive values in sub-annual series
    (interpolated gap fill, e.g. across the GRACE/GRACE-FO gap)."""
    keep = np.ones(len(ch), bool)
    if len(ch) < minrun or np.median(e-s) > 0.1: return keep
    i = 0
    while i < len(ch):
        j = i
        while j+1 < len(ch) and abs(ch[j+1]-ch[i]) <= 1e-6*max(abs(ch[i]), 1e-3): j += 1
        if j-i+1 >= minrun: keep[i:j+1] = False
        i = j+1
    return keep

def load_solutions(rid):
    """Return list of dict(name, src, group, s, e, ch(mwe), err(mwe))."""
    rn = REGIONS[rid]; out = []
    af = area_fn(rid)
    for f in sorted(glob.glob(f"{D}/input/{rid}_{rn}/*.csv")):
        d = pd.read_csv(f)
        name = os.path.basename(f)[len(rn)+1:-4]; src = name.split('_')[0]
        u = d.unit.iloc[0].lower()
        s, e = d.start_dates.values, d.end_dates.values
        ch, er = d.changes.values.astype(float), d.errors.values.astype(float)
        keep = flag_filled(s, e, ch)
        s, e, ch, er = s[keep], e[keep], ch[keep], er[keep]
        if u == 'gt':
            k = 1000.0/af(0.5*(s+e))                 # Gt -> m w.e.
        elif u == 'm':
            k = RHO_CONV                             # elevation change -> m w.e.
        else:
            k = 1.0
        out.append(dict(name=name, src=src, group=GROUP_OF[src], s=s, e=e, ch=ch*k, err=er*k, unit=u))
    return out

def annual_series(sol, ystart, nyears, err_mode='indep'):
    """Aggregate a solution onto annual windows [ystart+i, ystart+i+1].
    Change in window = sum(rate*overlap). Only windows fully covered are returned.
    Returns arrays ch, err, has_var(bool: window resolved by sub-multi-year data)."""
    s, e, ch, er = sol['s'], sol['e'], sol['ch'], sol['err']
    dur = e - s
    ch_o = np.full(nyears, np.nan); er_o = np.full(nyears, np.nan); var_o = np.zeros(nyears, bool)
    for i in range(nyears):
        a, b = ystart+i, ystart+i+1
        ov = np.clip(np.minimum(e, b)-np.maximum(s, a), 0, None)
        if ov.sum() < 1-1e-3: continue
        m = ov > 1e-9
        frac = ov[m]/dur[m]
        ch_o[i] = np.sum(ch[m]*frac)
        if err_mode == 'indep':
            er_o[i] = np.sqrt(np.sum((er[m]*frac)**2))
        elif err_mode == 'corr':
            er_o[i] = np.sum(er[m]*frac)
        elif err_mode == 'mean':
            er_o[i] = np.sum(er[m]*frac)/ max(m.sum(),1) 
        var_o[i] = dur[m].max() <= 1.0 + 1e-6
    return ch_o, er_o, var_o
