# Reproduction notes (experiments/, results/)

Task: width vs. delayed generalisation (grokking) on modular arithmetic. All numbers in the paper come from the run JSONs in `experiments/runs/<sweep>/` via `experiments/analyze.py` (and `analyze_mech.py` when present) into `results/`.

## Environment
Python 3.11, torch 2.14.1 (CPU), numpy, pandas, scipy (see `results/versions.txt`). No GPU, no downloads, no external data: the data are all p^2 pairs (a,b) with label (a op b) mod p, generated in memory (`grok.py:make_data`).

## What a run is
`python experiments/grok.py --arch tf|mlp --width W --p 53 --op add|mul --frac F --wd WD --lr LR --seed S --max_steps 30000 --out FILE`
- Data: p=53 (2809 pairs); a random fraction F is the training set, the rest validation. Split seed = `--seed` unless `--split_seed` is given (10000+seed is the split RNG).
- Model `tf`: 1-layer transformer, tokens [a, b, '='], read-out at '=', width = d_model, 4 heads (1 if width<16), MLP width 4*d_model, ReLU, no LayerNorm, embedding init N(0, 1/d). Model `mlp`: embeddings of a and b concatenated, two hidden ReLU layers of size 4*width.
- Optimiser: AdamW(lr 1e-3, betas (0.9, 0.98), weight decay 1.0 unless varied), 10-step linear warm-up, full-batch, cross-entropy.
- Logging every 250 steps: train/val accuracy and loss over the full train and val sets, global L2 weight norm.
- t_fit / t_gen = first logged step with train / val accuracy >= 0.99 (resolution 250 steps); D = t_gen - t_fit. A run stops 500 steps after t_gen or at `max_steps`; if t_gen is absent the run is right-censored at `steps_run`.
- Interventions: `--init_mult` (all parameters multiplied at init), `--lr_ref R` (lr * sqrt(R/width)), `--split_seed`.

## Sweeps (`experiments/sweep.py`; runs in `experiments/runs/<sweep>/`; seeds 0-4 unless noted; all complete)
| sweep | grid | runs |
|---|---|---|
| `main` | tf, add, p=53, f=0.4, wd=1, widths 8,16,32,64,128,256 | 30 |
| `wd` | wd in {0.5 (T_max 60000), 2} x widths 64,128 (wd=1 cells from `main`) | 20 |
| `alpha` | init multiplier 0.5, 2 x widths 32,128 (alpha=1 from `main`) | 20 |
| `frac` | f in {0.25, 0.5} x widths 32,128 (f=0.4 from `main`); plus two earlier f=0.3 w=16 runs | 22 |
| `wd0` | wd=0 control, width 64, seeds 0-2 | 3 |
| `lrscale` | lr*sqrt(64/width), widths 32,128, seeds 0-2 | 6 |
| `long` | main cells w=16,32, seeds 0-2, T_max 100000 (budget check) | 6 |
| `mlp` | 2-hidden-layer MLP, widths 8..256 | 30 |
| `mul` | modular multiplication, widths 64,128, seeds 0-2 | 6 |
`thr1` (13 runs: the grokked `main` runs at w>=64, deterministic re-runs continued 5000 steps past t_gen, for the exact val-acc-1.0 threshold) is run as `python sweep.py run thr1 ...`; its output feeds `analyze_sens.py` S2c.
`splitfix` is defined in `sweep.py` but was not run (dropped by the plan's cut order).

Commands: `cd experiments && python sweep.py run NAME SHARD NSHARDS --procs 2` (skips finished runs); then
`python analyze.py main frac wd wd0 alpha lrscale long mul mlp` (-> `results/<sweep>_{runs,cells}.csv`, `<sweep>_stats.json`), `python analyze_mech.py` (-> `results/mech_stats.json`, `mech_alpha_cells.csv`), `python analyze_sens.py` (-> `results/sens_stats.json`).
Bootstrap RNG seed is fixed (0); results re-run identically.

## Norm measure for A2(ii) (which one, and why)
Primary for comparing widths: per-parameter RMS weight at t_fit, L2/sqrt(#params). Total L2 of all parameters grows with sqrt(#params), roughly linearly in width, even at identical per-parameter size, so it is collinear with width by construction. Both are reported (`results/mech_stats.json`, summary in `results/verdicts.json` under `A2ii_norm_measure`): with all 66 f=0.4 runs, "width acts only through t_fit and norm" is refuted under total L2 (width coefficient -0.57 [-1.17, -0.13]) and inconclusive under RMS (0.59 [-0.83, 2.26]). The 26-run `main_only` fits are unstable under both and not used.

## Width-scaled lr
`lrscale` (widths 32,128; seeds 0-4) and `lrscale2` (widths 16,64,256; seeds 0-2) use lr*sqrt(64/width). `analyze_sens.py` S3/S3b compare them with `main` on the same seeds (`results/sens_stats.json`, `results/sens_lrscale_grid.csv`).

## Results of the last two checks (details in `results/sens_stats.json`, `results/sens_lrscale_grid.csv`)
- Exact threshold 1.0 (`thr1`, 13 re-runs that reproduce `main` t_gen exactly): val acc 1.0 is reached in 9 of 13 within 5000 steps of the 0.99 crossing (median lag 2250 steps). AFT slope over widths >= 64: -0.28 [-0.55, 0.02] vs -0.26 [-0.59, 0.09] for 0.99 on the same runs: same estimate, both inconclusive because only three widths are in the window.
- Width-scaled lr, seeds 0-4 at widths 32/128: grokked 2/5 and 3/5 (fixed lr: 1/5 and 5/5; Fisher p = 1.0 vs 0.048). Seeds 0-2 over widths 16-256: grokked 0,0,3,1,1 of 3 (fixed lr: 0,0,3,3,2). The scaled-lr AFT slope is degenerate (10 of 15 runs censored, CI collapses to [-0.05, 0]) and is rated inconclusive. The width advantage at w >= 128 is weaker under scaled lr, but 30k steps censor most scaled-lr runs, so a dependence on lr cannot be excluded or confirmed.

## Cost
44 run-hours of wall time in total (sum of `wall_s`) on 1 core each, on a shared host with load about 2x the core count; runs that generalise stop early. A 30k-step run took 5-120 min depending on width and load.

## Readings the analyses support (details and CIs in `results/`)
- Lengthening the budget matters: `long` extends `main` runs bit-for-bit (checked in `analyze_sens.py`) and 3 of 6 w=16/32 runs generalise between 35k and 58k steps. Narrow widths are therefore delayed, not "never generalising"; the 30k-step `main` cells at w<=32 are right-censored, not negative. `sens_stats.json` S0 (30k) vs S1 (extended) gives the A1 slope under both budgets.
- `t_fit` (0.99 train acc) is at the logging resolution (250 steps) for w>=64, so the delay D is essentially t_gen there; at w=8 the net mostly does not fit at all (see `regime`).
- Threshold sensitivity: 0.9/0.95 are exact from the logs; 1.0 is only a censored bound because a run stops 500 steps after the 0.99 crossing (3 of 14 grokked runs reach val 1.0 inside the window). The 1.0 threshold would need re-runs with a later stop; not done.
- Norm-matching through `alpha` is not achievable (see `norm_matched` in `mech_stats.json`); the alpha effect is a total effect of init scale.
- Norm at t_gen is outcome-contaminated; the `*_fit` regressions are the admissible A2-ii test, and they are inconclusive (wide CIs, width and norm collinear).
- `wd` runs with wd=0.5 have T_max 60000, others 30000; the AFT analyses handle this through per-run censoring times.

## Provenance / caveats
- Threshold 0.99 is the pre-registered primary; the 1.0 sensitivity is computed from the logs.
- The embedding-init rule was changed (N(0,1) -> N(0,1/d)) after the first pilot only; no reported run used the former. The pilot runs are not in `runs/`.
- Each result JSON stores its full config and the torch version; the git commit that produced a sweep is the one current when the sweep was launched (see git log of `experiments/`).
