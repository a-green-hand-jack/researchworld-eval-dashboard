# Reproducing the composition-response analysis

Only independently generated synthetic data are used. No download, account or licensed dataset is needed. The logistic-normal generator and all constants are in `analysis/benchmark.py`. Python 3.11.2 and exact installed NumPy/SciPy/pandas versions are recorded in `analysis/environment.txt`; use `python3 -m pip install -r analysis/environment.txt` if needed. Set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` to avoid oversubscribing a small CPU host. Storage is far below 10 GB.

From the repository root:

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 analysis/checks.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 analysis/benchmark.py --output results/main.jsonl --reps 100 --start 1000 --dimensions 3 10 --calibration 99 499 --scenarios homogeneous heterogeneous --ntest 5000 --nvolume 8192
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 analysis/run_extensions.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 analysis/benchmark.py --output results/prior_scores.jsonl --reps 100 --start 1000 --dimensions 3 10 --calibration 99 499 --scenarios homogeneous heterogeneous --ntest 5000 --nvolume 8192 --methods tv kl_forward
python3 analysis/summarize.py results/main.jsonl results/weighted.jsonl results/prior_scores.jsonl --outdir results/main_summary
python3 analysis/summarize.py results/boundary.jsonl --outdir results/boundary_summary
python3 analysis/audit_results.py
python3 analysis/report_evidence.py
```

The seven-method core and matched-seed oracle-weighted extension are kept as separate raw files, then combined for complete ten-method summaries after the source-driven TV/KL supplement. The extension entrypoint also executes the predeclared rank and zero/replacement checks. Main seeds are 901000..901099; boundary seeds 902000..902049; coefficient seed 1729+K. Pilot seeds 900000/900001 are excluded from all final quantitative claims. Each manifest records actual source hashes, dependency versions, arguments and timings. Completed resource compute: core 116.110 s running wall/124.165104 CPU s; all extensions 43.878 s running wall/45.080784 CPU s, apart from startup. Reproduction should take a few minutes on one CPU thread plus summary time; actual speed depends on the host. The TV/KL supplement additionally used45.631351 CPU s (resource-reported ran44.498 s; sum of measured cell durations59.927 s). the pilot took about three seconds for two repetitions over the full core matrix with 2000 test points and 4096 area candidates per anchor.

`summary.csv` contains pointwise 95% t intervals across independent dataset replications; `paired_contrasts.csv` uses within-seed method differences; `shift_contrasts.csv` uses within-seed shifted-minus-iid differences. `diagnostics.csv` contains coverage distribution quantiles and empirical below-tolerance frequencies with Wilson intervals, plus infinite-region counts. These are finite-test diagnostics, not exact conditional-coverage certifications. K=3 area estimates use a chosen common Euclidean reference, 32 covariate anchors and 8192 uniform compositions per anchor. Candidate MC SE is separately recorded. K=10 radii are not cross-geometry efficiency comparisons. If any radius is infinite, its complete-cell mean is omitted; area and coverage retain all rows.

Method and generator details, numerical derivations, limitations and the evidence map accompany results in `analysis/` at delivery. Final figures/tables belong to the presentation owner; their script-to-display mapping is in `presentation/README.md` in the combined delivery.

Experiment-repo accessed only the permitted starter source arXiv:1904.06019 directly to verify weighted split inference (equations 7-10); its URL/hash and read extent are recorded in `analysis/notes/theory_checks.md`. No prohibited study, derivative or broad literature search was accessed by this position.

`analysis/evidence_map.md` maps supported/unsupported claims to exact cells and files; `analysis/methods.md` supplies the complete fitted model and estimands. `results/audit.json` records counts, successful jobs and exclusions. There were no failed resource runs or omitted confirmatory replications. The pilot and caught pre-main serialization defect are retained in the notes; pilot estimates do not enter the paper evidence.

The TV/KL controls were requested from permitted prior work after core results were available to analysis; their source-driven chronology and fixed matched seeds are in `analysis/notes/prior_score_supplement_freeze.md`. K3 TV is the same region as raw max and is not independent geometry evidence. The additional pilot `prior_score_pilot*` is excluded alongside the original pilot.

For zero/replacement results, `boundary_summary/pullback_equivalence.csv` reinterprets the already measured transformed membership event as coverage of the explicit original-target inverse-image region. It is distinct from the direct-untransformed-clr diagnostic, with no additional simulation or pullback area estimate. See methods.md.
