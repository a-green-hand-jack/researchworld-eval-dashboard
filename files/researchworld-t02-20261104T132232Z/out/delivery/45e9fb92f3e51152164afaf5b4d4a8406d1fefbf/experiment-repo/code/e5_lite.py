"""E5-lite: weight-norm trajectory vs fit/generalisation times from the logged curves (no extra compute).
python3 e5_lite.py OUT_PREFIX RUNDIR:RUNS_CSV:LABEL [...]
Per run: total weight norm at step 0, at t_fit, at its peak (and the step of the peak, t_peak), at t_gen (sustained 0.99), at the last log;
t_half = first step after the peak where the norm has fallen halfway from the peak to its last logged value.
Per (label, width): medians and Spearman (across runs) of t_gen with t_peak and t_half."""
import sys, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr

rows = []
for spec in sys.argv[2:]:
    rundir, csv, label = spec.split(":")
    d = pd.read_csv(csv).set_index("run_id")
    for rid, r in d.iterrows():
        j = json.load(open(f"{rundir}/{rid}.json")); L = j["log"]
        st = np.array(L["step"]); w = np.array(L["wnorm"]); ip = int(np.argmax(w))
        at = lambda t: float(np.interp(t, st, w)) if pd.notna(t) else np.nan
        half = w[ip] - 0.5 * (w[ip] - w[-1])
        after = np.where((st > st[ip]) & (w <= half))[0]
        rows.append(dict(label=label, run_id=rid, width=r.width, seed=r.seed, w0=w[0], w_fit=at(r.t_fit99_s), w_peak=w[ip], t_peak=int(st[ip]),
                         w_gen=at(r.t_gen99_s), w_last=w[-1], t_fit=r.t_fit99_s, t_gen=r.t_gen99_s, t_half=int(st[after[0]]) if len(after) else np.nan,
                         diverged=r.diverged))
R = pd.DataFrame(rows); R.to_csv(sys.argv[1] + "_runs.csv", index=False)
S = []
for (lab, w), g in R.groupby(["label", "width"]):
    ok = g.dropna(subset=["t_gen"])
    rho_p = spearmanr(ok.t_gen, ok.t_peak)[0] if len(ok) > 3 else np.nan
    okh = ok.dropna(subset=["t_half"])
    rho_h = spearmanr(okh.t_gen, okh.t_half)[0] if len(okh) > 3 else np.nan
    S.append(dict(label=lab, width=int(w), n=len(g), n_gen=len(ok), w0=g.w0.median(), w_fit=g.w_fit.median(), w_peak=g.w_peak.median(), t_peak=g.t_peak.median(),
                  w_gen=ok.w_gen.median(), w_last=g.w_last.median(), t_fit=g.t_fit.median(), t_gen=ok.t_gen.median(), t_half=okh.t_half.median(),
                  frac_peak_before_gen=float((ok.t_peak < ok.t_gen).mean()) if len(ok) else np.nan,
                  frac_fall_at_gen=float(((ok.w_peak - ok.w_gen) / (ok.w_peak - ok.w_last)).median()) if len(ok) else np.nan,
                  rho_tgen_tpeak=rho_p, rho_tgen_thalf=rho_h))
S = pd.DataFrame(S); S.to_csv(sys.argv[1] + "_summary.csv", index=False)
print(S.round(2).to_string())
