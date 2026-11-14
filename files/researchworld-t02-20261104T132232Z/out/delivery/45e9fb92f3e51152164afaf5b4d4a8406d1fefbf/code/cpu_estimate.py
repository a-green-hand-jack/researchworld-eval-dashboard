"""Dedicated-CPU estimate per experiment: python3 cpu_estimate.py OUT.csv timing.csv NAME=runs.csv [...]
Per run, estimate = steps_run * cpu_ms_per_step(model, depth, width) * (f p^2) / (0.5 * 59^2): the step cost is taken from code/timing.py (single thread, p = 59,
f = 0.5) and scaled linearly with the number of training examples (full-batch step), log-log interpolated for untimed widths. Compared with the summed `wall` of
the same runs (measured on the shared host). This is an estimate (evaluation cost is inside the timing run; the linear scaling in f p^2 is approximate)."""
import sys
import numpy as np, pandas as pd
T = pd.read_csv(sys.argv[2])
def ms(model, depth, w):
    """Timed ms/step at (model, depth); log-log interpolation between timed widths, constant outside them (per-step overhead floor).
    Depth-2 widths are interpolated between the timed depth-2 points."""
    g = T[(T.model == model) & (T.depth == depth)].sort_values("width")
    return float(np.exp(np.interp(np.log(w), np.log(g.width), np.log(g.cpu_ms_per_step))))
rows = []
for spec in sys.argv[3:]:
    name, path = spec.split("=")
    d = pd.concat([pd.read_csv(f) for f in path.split('+')])   # several tables of one experiment joined with '+'
    est = sum(r.steps_run * ms(r.model, int(r.depth), r.width) * (r.train_frac * r.p ** 2) / (0.5 * 59 ** 2) for r in d.itertuples()) / 3.6e6
    rows.append(dict(experiment=name, runs=len(d), dedicated_cpu_h_est=est, contended_wall_h=d.wall.sum() / 3600))
R = pd.DataFrame(rows); R.loc[len(R)] = dict(experiment="total", runs=R.runs.sum(), dedicated_cpu_h_est=R.dedicated_cpu_h_est.sum(), contended_wall_h=R.contended_wall_h.sum())
R.to_csv(sys.argv[1], index=False); print(R.round(2).to_string(index=False))
