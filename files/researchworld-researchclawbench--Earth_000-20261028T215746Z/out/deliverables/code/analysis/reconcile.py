"""Combine homogenised submissions within data groups and across groups.

Within a data group, a weighted least-squares (WLS) model estimates one
annual series z_y (m w.e., hydrological years) from
  * temporally resolved series whose absolute level counts
    (altimetry, gravimetry):              x_iy = z_y + e
  * temporally resolved series that carry only annual variability
    (glaciological, after Zemp et al. 2019, and -- for groups without
    their own resolved data -- the variability of the DEM-differencing +
    glaciological group):                 x_iy = z_y + b_i + e
  * multi-year trends (DEM differencing, ICESat-era altimetry, trend-only
    gravimetry), one row per native period: sum_y f_y z_y = v + e.
Errors are scaled by the Birge ratio sqrt(chi2/dof) when it exceeds 1, so
that disagreement between submissions widens the group uncertainty.

Across groups, the regional consensus is the inverse-variance weighted mean
of the available groups per year, with the same Birge-ratio inflation.
"""
import numpy as np
import pandas as pd

from homogenise import hydro_bounds, hydro_start

YEARS = np.arange(1999, 2025)          # hydrological-year labels solved for
GROUPS = ["altimetry", "gravimetry", "demdiff_and_glaciological"]
VAR_ONLY = {"glaciological"}           # sources used for variability only
BORROW_ERR_FACTOR = 2.0                # down-weighting of borrowed variability


def _overlap(a, b, h0):
    f = []
    for y in YEARS:
        ya, yb = hydro_bounds(y, h0)
        f.append(max(0.0, min(b, yb) - max(a, ya)) / (yb - ya))
    return np.array(f)


def random_effects(c, e):
    """DerSimonian-Laird random-effects mean of estimates c with errors e."""
    c, e = np.asarray(c, float), np.asarray(e, float)
    w = 1 / e ** 2
    m = np.sum(w * c) / np.sum(w)
    tau2 = 0.0
    if len(c) > 1:
        q = np.sum(w * (c - m) ** 2)
        tau2 = max(0.0, (q - (len(c) - 1)) /
                   (np.sum(w) - np.sum(w ** 2) / np.sum(w)))
    ws = 1 / (e ** 2 + tau2)
    mu = np.sum(ws * c) / np.sum(ws)
    return mu, np.sqrt(1 / np.sum(ws)), np.sqrt(tau2)


def solve_group(subs, h0, borrow=None, min_year_frac=0.5, var_only=VAR_ONLY,
                abs_labels=(), n_iter=6):
    """subs: submissions of one group in one region. borrow: DataFrame with
    year, mwe, mwe_err of a variability series used for years the group
    does not resolve itself (None for the DEMdiff+glaciological group).

    Random-effects WLS: one annual series z_y and, per submission i,
      resolved, level counts:   x_iy = z_y + b_i + e
      resolved, variability:    x_iy = z_y + a_i + e        (a_i free)
      multi-year periods p:     sum_y f_py z_y + L_p b_i = v_p + e
    with b_i ~ N(0, tau^2) a submission-level rate bias (L_p = period
    length in years). tau is re-estimated by the method of moments, so a
    submission with many precise annual values cannot set the group level
    alone when the submissions disagree. Birge-ratio inflation of the
    covariance when residuals exceed the stated errors.
    Returns DataFrame(year, mwe, mwe_err, n_resolved, n_trend, borrowed)."""
    ny = len(YEARS)
    obs = []                 # (coef over years, series id, kind, value, err)
    n_res = np.zeros(ny, int)
    n_tr = np.zeros(ny, int)
    abs_years = np.zeros(ny, bool)
    n_abs = 0
    sid = 0
    # variability-only series (glaciological) derive from the same WGMS
    # glacier observations; treat them as fully dependent by inflating each
    # one's error by sqrt(n) so that their combination does not shrink it
    n_free = sum(1 for s in subs if s["resolved"] and s["source"] in var_only
                 and not any(t in s["label"] for t in abs_labels))
    for s in subs:
        if s["resolved"]:
            ann = s["annual"]
            ann = ann[ann.year.isin(YEARS) & np.isfinite(ann.mwe) &
                      np.isfinite(ann.mwe_err) & (ann.mwe_err > 0)]
            if not len(ann):
                continue
            is_free = (s["source"] in var_only and
                       not any(t in s["label"] for t in abs_labels))
            kind = "free" if is_free else "rand"
            infl = np.sqrt(max(n_free, 1)) if is_free else 1.0
            for y, v, e in zip(ann.year.values, ann.mwe.values,
                               ann.mwe_err.values * infl):
                f = np.zeros(ny)
                f[int(y - YEARS[0])] = 1.0
                obs.append((f, sid, kind, 1.0, v, e))
            ks = (ann.year.values - YEARS[0]).astype(int)
            n_res[ks] += 1
            if not is_free:
                abs_years[ks] = True
                n_abs += 1
            sid += 1
        else:
            used = False
            for _, r in s["native"].iterrows():
                if not (np.isfinite(r.mwe) and np.isfinite(r.mwe_err)
                        and r.mwe_err > 0):
                    continue
                f = _overlap(r.start_dates, r.end_dates, h0)
                if f.sum() <= 0:
                    continue
                obs.append((f, sid, "rand", f.sum(), r.mwe, r.mwe_err))
                abs_years |= f >= min_year_frac
                n_tr += (f > 0).astype(int)
                used = True
            if used:
                n_abs += 1
                sid += 1
    if not obs or not abs_years.any():
        return None
    span = np.zeros(ny, bool)
    idx = np.where(abs_years)[0]
    span[idx.min():idx.max() + 1] = True
    if borrow is None:
        own = np.where(n_res > 0)[0]
        if len(own):
            span[own.min():own.max() + 1] = True
    borrowed = np.zeros(ny, bool)
    if borrow is not None:
        need = span & (n_res == 0)
        if need.any():
            b = borrow.set_index("year")
            for k in np.where(span)[0]:
                y = YEARS[k]
                if y in b.index and np.isfinite(b.loc[y, "mwe"]):
                    f = np.zeros(ny)
                    f[k] = 1.0
                    obs.append((f, sid, "free", 1.0, b.loc[y, "mwe"],
                                BORROW_ERR_FACTOR * b.loc[y, "mwe_err"]))
                    borrowed[k] = need[k]
            sid += 1
    keep = span & ((n_res > 0) | borrowed)
    cols = np.where(keep)[0]
    if not len(cols):
        return None
    nz = len(cols)
    # observations reaching into unsolved years are rescaled to the solved part
    rows = []
    for f, q, kind, L, v, e in obs:
        part = f[keep].sum()
        if part <= 0:
            continue
        coef = f[cols] * (f.sum() / part)
        rows.append((coef, q, kind, L, v, e))
    sids = sorted(set(r[1] for r in rows))
    kinds = {r[1]: r[2] for r in rows}
    spos = {q: i for i, q in enumerate(sids)}
    nb = len(sids)
    rand = [q for q in sids if kinds[q] == "rand"]
    use_re = len(rand) > 1
    A = np.zeros((len(rows), nz + nb))
    yv = np.array([r[4] for r in rows])
    e0 = np.array([r[5] for r in rows])
    for i, (coef, q, kind, L, v, e) in enumerate(rows):
        A[i, :nz] = coef
        if kind == "free" or use_re:
            A[i, nz + spos[q]] = L
    tau = 0.1 if use_re else 0.0
    for _ in range(n_iter):
        P = np.zeros((nb, nz + nb))
        pw = np.zeros(nb)
        for q in sids:
            j = spos[q]
            P[j, nz + j] = 1.0
            if kinds[q] == "rand":
                pw[j] = 1 / max(tau, 1e-4) if use_re else 1e4
            else:
                pw[j] = 0.0      # free offset, no prior
        Aw = np.vstack([A / e0[:, None], P * pw[:, None]])
        yw = np.concatenate([yv / e0, np.zeros(nb)])
        N = Aw.T @ Aw
        if np.linalg.matrix_rank(N) < N.shape[0]:
            return None
        cov = np.linalg.inv(N)
        x = cov @ Aw.T @ yw
        if not use_re:
            break
        bi = np.array([x[nz + spos[q]] for q in rand])
        vb = np.array([cov[nz + spos[q], nz + spos[q]] for q in rand])
        new = np.sqrt(max(np.mean(bi ** 2 + vb), 1e-8))
        if abs(new - tau) < 1e-4:
            tau = new
            break
        tau = new
    res = (yv - A @ x) / e0
    dof = max(len(rows) - (nz + sum(kinds[q] == "free" for q in sids)), 1)
    birge = max(1.0, np.sqrt(np.sum(res ** 2) / dof))
    err = np.sqrt(np.clip(np.diag(cov)[:nz], 0, None)) * birge
    out = pd.DataFrame({"year": YEARS[cols], "mwe": x[:nz], "mwe_err": err,
                        "n_resolved": n_res[cols], "n_trend": n_tr[cols],
                        "borrowed": borrowed[cols]})
    out.attrs.update(birge=birge, tau=tau, n_level=len(rand))
    return out


def combine_groups(group_series, weighting="iv", errors="dependent"):
    """Per-year combination of group series (dict name -> DataFrame).

    errors="dependent" (default): the groups share area, density and
    glaciological variability and are not independent, so the combined
    variance is the weighted mean of the group variances (no reduction by
    averaging) plus the weighted variance of the group values about the
    mean (inter-method disagreement).
    errors="independent": standard error of the weighted mean, inflated by
    the Birge ratio when groups disagree beyond their errors."""
    group_series = {k: v for k, v in group_series.items() if v is not None}
    if not group_series:
        return pd.DataFrame(columns=["year", "mwe", "mwe_err", "n_groups", "groups"])
    allyears = sorted(set().union(*[set(g.year) for g in group_series.values()]))
    out = []
    for y in allyears:
        v, e, names = [], [], []
        for n, g in group_series.items():
            r = g[g.year == y]
            if len(r):
                v.append(r.mwe.iloc[0])
                e.append(r.mwe_err.iloc[0])
                names.append(n)
        v, e = np.array(v), np.array(e)
        if weighting == "iv":
            w = 1 / e ** 2
        else:
            w = np.ones_like(v)
        m = np.sum(w * v) / np.sum(w)
        if errors == "dependent":
            se = np.sqrt(np.sum(w * e ** 2) / np.sum(w) +
                         np.sum(w * (v - m) ** 2) / np.sum(w))
        else:
            if weighting == "iv":
                se = np.sqrt(1 / np.sum(w))
            else:
                se = np.sqrt(np.sum(e ** 2)) / len(e)
            if len(v) > 1:
                chi2 = np.sum((v - m) ** 2 / e ** 2) / (len(v) - 1)
                se *= max(1.0, np.sqrt(chi2))
        out.append((y, m, se, len(v), "+".join(names)))
    return pd.DataFrame(out, columns=["year", "mwe", "mwe_err", "n_groups",
                                      "groups"])


def hydro_to_calendar(cons, sine_native, region):
    """Convert hydrological-year values to calendar years by distributing
    each hydrological year over its months with the seasonal anomaly of the
    glaciological sine-wave series (Zemp et al.), which sums to zero within
    the hydrological year so that annual totals are preserved."""
    h0 = hydro_start(region)
    if h0 == 0:
        c = cons[["year", "mwe", "mwe_err"]].copy()
        return c
    months = []
    nat = sine_native
    for _, r in cons.iterrows():
        a, b = hydro_bounds(int(r.year), h0)
        edges = a + np.arange(13) / 12.0
        seas = np.zeros(12)
        if nat is not None:
            for k in range(12):
                sel = (np.abs(nat.start_dates - edges[k]) < 1e-3)
                if sel.any():
                    seas[k] = nat.mwe[sel].iloc[0]
            if np.count_nonzero(seas) < 12:
                seas[:] = 0.0
            seas = seas - seas.mean()
        for k in range(12):
            months.append((edges[k], r.mwe / 12 + seas[k], r.mwe_err / 12))
    m = pd.DataFrame(months, columns=["t", "v", "e"])
    out = []
    for Y in range(2000, 2025):
        sel = (m.t >= Y - 1e-6) & (m.t < Y + 1 - 1e-6)
        if sel.sum() == 12:
            # errors of the two contributing hydrological years taken as
            # fully correlated (linear sum of the monthly shares)
            out.append((Y, m.v[sel].sum(), m.e[sel].sum()))
    return pd.DataFrame(out, columns=["year", "mwe", "mwe_err"])
