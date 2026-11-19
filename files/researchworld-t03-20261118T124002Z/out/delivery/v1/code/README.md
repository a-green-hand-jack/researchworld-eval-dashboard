# Analysis code for "Is one SHAP run enough?"

Audit of when a single run of a stochastic, budget-limited SHAP estimator gives reliable evidence for a tabular model's prediction.
`docs/PROTOCOL.md` fixes the design and the verdict rules (written before any result; amendments listed at its end), `results/README.md`
gives the schema of every result file, `results/STATUS.md` says what has run and what has not.

## Layout
- `shapaudit/` library: `data.py` (German Credit via OpenML, ACS-Employment via folktables, Arrhythmia via OpenML), `models.py` (LR, MLP, LightGBM),
  `cells.py` (exact interventional value tables, live value function for d above the table range, instance/background selection),
  `estimators.py` (re-implementation of shap 0.51.0 KernelSHAP incl. its l1-regularised default, l1-off KernelSHAP, PermutationExplainer, Covert–Lee
  KernelSHAP with standard error, Leverage SHAP Algorithm 1, exact Shapley from the table), `certs.py` (E5 certificate rules),
  `runs.py` (run grid), `metrics.py` (top-k read-outs), `yardstick.py` (E4 retrain/background variants).
- `scripts/` one script per stage (below). `results/` small machine-readable results. `docs/PROTOCOL.md`.
- Bulk arrays (value tables, raw run arrays; about 4 GB for the Tier-1 cells) are not delivered: they live in `$WORK/cells/<cell>` (`/hutian/work` here) and are recomputed by the commands below.

## Environment
Python 3.11, `pip install -r requirements.txt` (numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, lightgbm 4.7.0, torch 2.14.1 CPU, shap 0.51.0, folktables 0.0.12).
Everything runs on CPU. Run with `PYTHONPATH=.` from the repository root. Data are downloaded on first use into `data/raw`.
Determinism: every random draw is seeded from crc32 of (cell, instance, arm, budget, rerun); model seeds are 0, 1, 2. A cell id is `<dataset>_d<sub|full>_<model>[_logit]_s<seed>`.

## Pipeline (commands)
1. Tables (exact value tables, φ\*, trained model; n = 100 test instances, background m = 30):
   `scripts/build_many.sh DATASET MODEL [D_SUB|full] [prob|logit]` (seeds 0–2) or `scripts/build_cell.py --dataset D --model M --seed S [--d_sub K] [--output prob|logit]`.
   Datasets `german` (d = 20), `ACSEmployment` (d = 16), models `lr|mlp|gbdt`.
   Live cells (d above the table range; GBDT on the raw margin, φ\* from interventional TreeSHAP): `scripts/build_live.py --dataset arrhythmia --d_sub {40,100,279} --model gbdt --seed 0 --n_inst 30`.
2. E1–E3 run grid (R = 20 reruns, all arms × budgets ×{¼,½,1,2,4,16} of 2d+2048 coalitions): `scripts/run_many.sh est CELL`, then `scripts/summarize_cell.py --cell CELL --tag R20`.
   R ≈ 200 subset (30 stratified instances, ×{¼,1,4}): `scripts/select_r200.py CELL` gives the instances; `scripts/run_estimators.py --cell CELL --R 200 --tag R200 --inst LIST --mults 0.25,1,4`; `scripts/summarize_r200.py --cells ...`.
3. E5 certificates (7-stage nested Covert–Lee stream, rules naive/bonf/maxt/split/shapk, R = 20 fresh reruns): `scripts/run_many.sh certs CELL`, `scripts/summarize_certs.py --cells ...` (writes pooled `certificate_coverage.csv`; run over all cells at once), `scripts/compare_cost.py` (price of calibration), `scripts/oracle_tightness.py --cells ...` (certified share vs the oracle “certify iff r_k(x;B) ≥ 1−δ”, R ≈ 200 subset).
4. Pooled analysis C1–C5 (cluster bootstrap over seeds then instances): `scripts/analyze_pooled.py --tag R20 --out results --nboot 500`.
5. E4 yardstick: `scripts/run_yardstick.py --dataset D --model M --seed 0` then `scripts/summarize_yard.py --cells ...`.
6. d-curve: `scripts/dcurve.sh DATASET DSUB OUTPUT MODEL...`; Tier 2 Leverage SHAP: `scripts/run_tier2_leverage.sh`; E7 controls: `scripts/e7_controls.py --cells ...`.
7. E0 fidelity of the re-implementation against live shap 0.51.0: `scripts/e0_fidelity.py` (`results/e0_fidelity_*.json`).

## Figure/table → data
Figures and tables are built by `figtab/` from `results/` only: `verdicts_R20.csv` (Table 1, Fig 1–3), `certificate_coverage.csv`, `fixed_budget_pooled.csv`, `cost_at_equal_reliability.csv` (Table 2, Fig 4),
`oracle_tightness.csv`, `r200_subset.csv`, `yardstick_summary.csv`, `bias_variance_R20.csv`, `instances_R20.csv`, `e7_controls.csv`.

## Cost
Table construction dominates for d = 20 (2^20 coalitions × 30 background rows per instance). Jobs ran on the shared 2-core `local-compute` host under heavy load (load average ≈ 40), so wall-clock times in the job log overstate the compute needed; `results/STATUS.md` lists the totals at delivery.
