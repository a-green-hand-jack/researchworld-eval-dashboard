"""Independent reconstruction of GlaMBIE-style regional/global glacier mass change 2000-2023.

Pipeline: raw submitted solutions -> annual (calendar / hydrological) series in m w.e. with an
explicit error-correlation structure -> within-group combination (fixed-effect model) ->
cross-group combination -> Monte Carlo / bootstrap ensemble -> regional and global Gt, m w.e.
All design choices are documented in README.md.
"""
import glob, os, re
import numpy as np, pandas as pd

DATA = os.environ.get("GLAMBIE_DATA", "/initial-state/inputs/2/glambie")
TAU = 0.15                      # m w.e. floor on annual error when weighting solutions (inverse variance)
CORR = "interval"                # error correlation: "interval" (default) or "solution" (one draw per solution, fully correlated in time)
RHO = 0.85                      # density to convert m (volume-change height) to m w.e.
YEARS = np.arange(2000, 2024)
REGIONS = {1: "alaska", 2: "western_canada_us", 3: "arctic_canada_north", 4: "arctic_canada_south",
           5: "greenland_periphery", 6: "iceland", 7: "svalbard", 8: "scandinavia", 9: "russian_arctic",
           10: "north_asia", 11: "central_europe", 12: "caucasus_middle_east", 13: "central_asia",
           14: "south_asia_west", 15: "south_asia_east", 16: "low_latitudes", 17: "southern_andes",
           18: "new_zealand", 19: "antarctic_and_subantarctic"}
SOURCES = ["altimetry", "demdiff", "glaciological", "gravimetry", "combined"]


# Regional data-group eligibility. GlaMBIE excluded altimetry in very small regions and gravimetry where signals are
# contaminated (ice-sheet leakage, hydrology) or the regions too small; these expert decisions cannot be derived from
# the inputs and are taken from which groups the published results contain for each region.
ELIG_ALT = {1, 2, 3, 4, 5, 6, 7, 9, 13, 14, 15, 17, 19}
ELIG_GRAV = {1, 3, 4, 6, 7, 9, 17}


def region_info(rid):
    """Published hydrological-year start offset and annual glacier area (km2) of the region.
    Area (RGI-based, shrinking in time) is the only quantity taken from results/ ; it is an input to
    the Gt <-> m w.e. conversion, not a mass-change estimate."""
    h = pd.read_csv(f"{DATA}/results/hydrological_years/{rid}_{REGIONS[rid]}.csv")
    off = round(h.start_dates.iloc[0] % 1, 4)
    return off, h[["start_dates", "glacier_area"]].copy()


def area_at(areas, t):
    return np.interp(t, areas.start_dates.values + 0.5, areas.glacier_area.values)


def load_solutions(rid):
    """Return list of dict(name, source, group_author, df) for one region (NaN rows dropped)."""
    out = []
    for f in sorted(glob.glob(f"{DATA}/input/{rid}_{REGIONS[rid]}/*.csv")):
        d = pd.read_csv(f).dropna(subset=["changes", "errors"]).reset_index(drop=True)
        base = os.path.basename(f)[:-4]
        src = re.match(rf"{REGIONS[rid]}_({'|'.join(SOURCES)})_", base).group(1)
        d["unit"] = d.unit.str.lower()
        out.append(dict(name=base, source=src, df=d, unit=d.unit.iloc[0]))
    return out


def to_mwe(sol, areas):
    """Convert changes/errors to m w.e. per native interval (Gt via region area at interval mid-time)."""
    d = sol["df"]
    mid = 0.5 * (d.start_dates + d.end_dates)
    if sol["unit"] == "gt":
        f = 1000.0 / area_at(areas, mid.values)          # Gt / km2 -> m w.e.   (1 Gt = 1e9 m3 w.e.)
    elif sol["unit"] == "m":
        f = np.full(len(d), RHO)
    else:
        f = np.ones(len(d))
    return d.changes.values * f, d.errors.values * f


def annualise(sol, areas, starts, min_cov=0.95):
    """Annual (year starts at y+off) changes in m w.e. and a linear error map.

    value_y = sum_i  w_yi * c_i,  w_yi = overlap(y,i)/duration_i  (change spread uniformly in each interval).
    Error rule: intervals >= 1 yr carry independent errors (one draw per interval, so years inside a
    multi-year DEM period are fully correlated); sub-annual intervals carry an annual-equivalent error
    shared by the whole target year (error of the annual sum = overlap-weighted mean sigma).
    Returns values (nyear,), list of (key, sigma_vector(nyear,)) error components (independent components).
    """
    c, e = to_mwe(sol, areas)
    s, t = sol["df"].start_dates.values, sol["df"].end_dates.values
    dur = t - s
    n = len(starts)
    val = np.full(n, np.nan)
    comps = {}
    for k, y in enumerate(starts):
        a, b = y, y + 1
        ov = np.clip(np.minimum(t, b) - np.maximum(s, a), 0, None)
        if ov.sum() < min_cov:
            continue
        idx = np.where(ov > 1e-9)[0]
        w = ov[idx] / dur[idx]
        scale = 1.0 / ov[idx].sum()
        val[k] = (w * c[idx]).sum() * (1.0 if ov.sum() >= 1 - 1e-6 else 1.0 / ov.sum())
        for j, wj in zip(idx, w):
            if dur[j] >= 0.95:
                comps.setdefault(("int", j), np.zeros(n))[k] += wj * e[j] * scale
            else:
                comps.setdefault(("yr", k), np.zeros(n))[k] += (ov[j] * scale) * e[j]
    err = np.sqrt(sum((c ** 2 for c in comps.values()), np.zeros(n))) if comps else np.zeros(n)
    return val, list(comps.values()), err


def fixed_effect(V, W=None, iters=500):
    """v[s,y] = mu[y] + b[s] with weights W[s,y] (default 1), constraint mean_s b[s] = 0 over series present.
    Estimated by alternating weighted means on observed cells. Returns mu (ny,), b (ns,)."""
    ns, ny = V.shape
    M = ~np.isnan(V)
    W = np.ones_like(V) if W is None else W
    Wm = np.where(M, W, 0.0)
    V0 = np.where(M, V, 0.0)
    b = np.zeros(ns)
    for _ in range(iters):
        sw = Wm.sum(0)
        mu = np.where(sw > 0, ((V0 - b[:, None]) * Wm).sum(0) / np.where(sw > 0, sw, 1), np.nan)
        D = np.where(M, V0 - np.nan_to_num(mu)[None, :], 0.0)
        sws = Wm.sum(1)
        b_new = np.where(sws > 0, (D * Wm).sum(1) / np.where(sws > 0, sws, 1), 0.0)
        b_new -= b_new.mean()
        if np.abs(b_new - b).max() < 1e-10:
            b = b_new
            break
        b = b_new
    sw = Wm.sum(0)
    mu = np.where(sw > 0, ((V0 - b[:, None]) * Wm).sum(0) / np.where(sw > 0, sw, 1), np.nan)
    return mu, b


def dem_block_ids(dem_solutions, starts):
    """Block id per year: years separated by an interval edge of any DEM solution get different ids."""
    edges = set()
    for s in dem_solutions:
        edges.update(np.round(s["df"].start_dates.values, 4)); edges.update(np.round(s["df"].end_dates.values, 4))
    edges = np.array(sorted(edges))
    ids = np.zeros(len(starts), int)
    for k, y in enumerate(starts):
        # an edge strictly inside (y+off, y+off+1) splits blocks; use the mid-year position
        ids[k] = np.searchsorted(edges, y + 0.5)
    return ids


def build_dg(mu_dem, mu_av, blocks):
    """Group 'DEM + glaciological/hybrid': multi-year level from DEM, annual variability from annual solutions
    (anomalies about their mean in each DEM block); outside DEM coverage the annual series is shifted by its mean
    offset to DEM over the 5 nearest covered years."""
    ny = len(blocks)
    if mu_av is None or np.all(np.isnan(mu_av)):
        return mu_dem.copy()
    if mu_dem is None or np.all(np.isnan(mu_dem)):
        return mu_av.copy()
    out = np.full(ny, np.nan)
    hd, ha = ~np.isnan(mu_dem), ~np.isnan(mu_av)
    for p in np.unique(blocks[hd]):
        m = (blocks == p) & hd
        g = m & ha
        out[m] = mu_dem[m]
        if g.sum() == m.sum():
            out[m] += mu_av[m] - mu_av[m].mean()
    both = np.where(hd & ha)[0]
    if len(both):
        later = np.arange(ny) > both.max()
        last = both[-5:]
        out[later & ha & np.isnan(out)] = mu_av[later & ha & np.isnan(out)] + np.mean(mu_dem[last] - mu_av[last])
        earlier = np.arange(ny) < both.min()
        first = both[:5]
        out[earlier & ha & np.isnan(out)] = mu_av[earlier & ha & np.isnan(out)] + np.mean(mu_dem[first] - mu_av[first])
    m = np.isnan(out) & hd
    out[m] = mu_dem[m]
    return out


def prepare_region(rid, hydro=False, exclude=lambda s: False, hybrid_in_dg=True, eligibility=True):
    off, areas = region_info(rid)
    off_use = off if hydro else 0.0
    starts = (1999.0 + off_use + np.arange(26)) if hydro else 2000.0 + np.arange(24)
    starts = starts[(starts >= 1999.75) & (starts + 1 <= 2024.0 + 1e-9)]
    sols = [s for s in load_solutions(rid) if not exclude(s)]
    ann = []
    for s in sols:
        if eligibility and ((s["source"] == "altimetry" and rid not in ELIG_ALT) or
                            (s["source"] == "gravimetry" and rid not in ELIG_GRAV)):
            continue
        v, comps, err = annualise(s, areas, starts)
        if np.sum(~np.isnan(v)) == 0:
            continue
        sub = {"altimetry": "alt", "gravimetry": "grav", "demdiff": "dem", "glaciological": "av",
               "combined": "av" if hybrid_in_dg else "hyb"}[s["source"]]
        dd = s["df"].end_dates.values - s["df"].start_dates.values
        ann.append(dict(name=s["name"], source=s["source"], sub=sub, v=v, comps=comps, err=err, sol=s,
                        annual=bool(np.median(dd) <= 1.2)))
    blocks = dem_block_ids([a["sol"] for a in ann if a["sub"] == "dem"], starts)
    area_y = np.array([area_at(areas, y + 0.5) for y in starts])
    return dict(rid=rid, off=off, off_use=off_use, hydro=hydro, starts=starts, ann=ann, blocks=blocks, area=area_y)


def smooth(x, win):
    """Centred running mean over valid cells, edges extended with the nearest valid value; NaN stays NaN."""
    from scipy.ndimage import uniform_filter1d
    ok = ~np.isnan(x)
    if not ok.any():
        return x.copy()
    idx = np.arange(len(x))
    filled = np.interp(idx, idx[ok], x[ok])            # constant extension at both ends, linear inside gaps
    sm = uniform_filter1d(filled, win, mode="nearest")
    return np.where(ok, sm, np.nan)


def group_means(reg, rng, plain_mean, bootstrap, mu0):
    """Aggregate solutions inside each sub-group; returns dict sub -> (mu_all, mu_annual_resolved)."""
    ann = reg["ann"]
    out = {}
    for k in ("alt", "grav", "dem", "av", "hyb"):
        lst = [a for a in ann if a["sub"] == k]
        res = []
        for flag in (False, True):
            ls = [a for a in lst if a["annual"] or not flag]
            if not ls:
                res.append(None)
                continue
            idx = np.arange(len(ls))
            if rng is not None and bootstrap and len(ls) > 1:
                idx = rng.integers(0, len(ls), len(ls))
            vs = [ls[j]["v"] + (ls[j]["_eps"] if (rng is not None and ls[j].get("_eps") is not None) else 0) for j in idx]
            ws = [1.0 / (ls[j]["err"] ** 2 + TAU ** 2) for j in idx]
            V, W = np.array(vs), np.array(ws)
            with np.errstate(all="ignore"):
                m = np.nanmean(V, 0) if (plain_mean or len(vs) == 1) else fixed_effect(V, W)[0]
            key = (k, flag)
            if rng is not None and mu0.get(key) is not None:     # bootstrap draw lacks a year: use central value
                m = np.where(np.isnan(m), mu0[key], m)
            res.append(m)
        out[k] = tuple(res)
    return out


def combine_once(reg, rng=None, groups=("alt", "grav", "dg"), plain_mean=False, bootstrap=True, win=5):
    """One realisation (rng None -> deterministic central estimate).
    combined = L + AV: L = equal-weight fixed-effect combination of the groups' multi-year level (running mean);
    AV = mean annual anomaly of the groups that resolve annual variability. Returns combined, dict of group series,
    L, AV."""
    if rng is None:
        reg["_mu0"] = {}
    gm = group_means(reg, rng, plain_mean, bootstrap, reg.get("_mu0", {}))
    if rng is None:
        reg["_mu0"] = {(k, f): v for k, t in gm.items() for f, v in zip((False, True), t)}
    G, AVs = {}, {}
    if "alt" in groups and gm["alt"][0] is not None:
        G["alt"] = gm["alt"][0]
        if gm["alt"][1] is not None:
            AVs["alt"] = gm["alt"][1] - smooth(gm["alt"][1], win)
    if "grav" in groups and gm["grav"][0] is not None:
        G["grav"] = gm["grav"][0]
        if gm["grav"][1] is not None:
            AVs["grav"] = gm["grav"][1] - smooth(gm["grav"][1], win)
    if "dg" in groups:
        dem, av_all, av_ann = gm["dem"][0], gm["av"][0], gm["av"][1]
        dg = build_dg(dem, av_all, reg["blocks"]) if (dem is not None or av_all is not None) else None
        if dg is None:
            dg = None
        if gm["hyb"][0] is not None:       # hybrids kept apart from DG (sensitivity option)
            dg = gm["hyb"][0] if dg is None else dg
        if dg is not None:
            G["dg"] = dg
            if av_ann is not None:
                AVs["dg"] = av_ann - smooth(av_ann, win)
    G = {k: v for k, v in G.items() if np.any(~np.isnan(v))}
    if not G:
        nan = np.full(len(reg["starts"]), np.nan)
        return nan, G, nan, nan
    L = {k: smooth(v, win) for k, v in G.items()}
    LV = np.array(list(L.values()))
    Lc = np.nanmean(LV, 0) if (plain_mean or len(LV) == 1) else fixed_effect(LV)[0]
    AV = np.array(list(AVs.values())) if AVs else np.full((1, len(reg["starts"])), np.nan)
    with np.errstate(all="ignore"):
        AVc = np.nanmean(AV, 0)
    AVc = np.nan_to_num(AVc)
    return Lc + AVc, G, Lc, AVc


def draw_noise(reg, rng):
    for a in reg["ann"]:
        eps = np.zeros(len(reg["starts"]))
        z0 = rng.standard_normal()
        for comp in a["comps"]:
            eps += comp * (z0 if CORR == "solution" else rng.standard_normal())
        a["_eps"] = np.where(np.isnan(a["v"]), 0, eps)
        a["_draw"] = rng


def run_region(reg, ndraw=500, seed=0, **kw):
    for a in reg["ann"]:
        a["_eps"] = None
    c0, G0, L0, AV0 = combine_once(reg, None, **kw)
    rng = np.random.default_rng(seed + 1000 * reg["rid"])
    ny = len(reg["starts"])
    C = np.zeros((ndraw, ny))
    GD = {k: np.zeros((ndraw, ny)) for k in G0}
    for d in range(ndraw):
        draw_noise(reg, rng)
        c, G, _, _ = combine_once(reg, rng, **kw)
        C[d] = c
        for k in G0:
            GD[k][d] = G.get(k, np.full(ny, np.nan))
    for a in reg["ann"]:
        a["_eps"] = None
    # inter-group dispersion: standard error of the group values about their mean (groups present that year)
    V0 = np.array(list(G0.values()))
    n = np.sum(~np.isnan(V0), 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        disp = np.where(n > 1, np.nanstd(V0, 0, ddof=1) / np.sqrt(np.maximum(n, 1)), 0.0)
    return dict(c0=c0, G0=G0, L0=L0, AV0=AV0, C=C, GD=GD, disp=disp, nG=n, V0=V0)
