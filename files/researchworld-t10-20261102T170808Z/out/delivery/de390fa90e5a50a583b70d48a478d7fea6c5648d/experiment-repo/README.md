# Fixed-input confidence intervals for population means

This repository supplies reproducible statistical analyses to the study's paper and presentation owners. It does not contain the final paper. Start with `analysis/methods.md`; measured conclusions will be in `analysis/findings.md`.

## Reproduction

Python 3.11.2, CPU only. Install `requirements.txt` in a virtual environment. Raw frozen prediction files are included under `data/`, with source URLs, SHA-256 hashes, and package versions in `provenance/manifest.json`. `python code/download_data.py` checks existing copies or downloads missing files. These files come from PPI v0.2.3; code is MIT but no separate data-file license was declared in the supplied material. Redistribution follows the research workspace supplied-data convention; external users should check original dataset terms.

Set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` for consistent CPU behavior. Run from the repository root:

```sh
python code/run_experiments.py --group synthetic --reps 5000 --ns 100 500 2000 --out results/synthetic --stress
python code/run_experiments.py --group real --reps 5000 --ns 100 500 2000 --out results/real --stress
python code/run_experiments.py --group synthetic --scenarios bounded_quadratic --reps 3000 --ns 2000 10000 --out results/bounded
python code/add_exact_baseline.py results/synthetic results/real results/bounded
python code/add_full_eb_baseline.py results/synthetic results/real results/bounded
python code/summarize.py results/synthetic results/real results/bounded --out results
python code/theory.py
python code/verify_implementation.py
```

The final optional verification command additionally needs ppi-python==0.2.3, numba and statsmodels; the research calculations themselves use NumPy, SciPy, pandas and PyArrow. Verification compares 24 baseline endpoint pairs against the actual reference implementation. Timing pilots: 140 synthetic trial sets at n=2000/N=20000, including degree-12 stress methods, took 1.30 seconds; 70 at n=100 took 0.247 seconds. Actual main elapsed times are recorded in result metadata (shared-host load may vary). The synthetic and real commands are independent and were run as parallel tracked jobs.

`results/*/*.parquet` contains every replicate's scenario, n/N, repetition ID, root seed, method, truth, interval endpoints, width and coverage. `results/summary.csv` has Wilson coverage intervals and width MC standard errors; `results/paired.csv` has paired ratios of mean widths, delta-method uncertainties and differences. Exact MC conventions, score distributions, seeds, guarantees and limitations are in `analysis/methods.md`. No tuning selects methods based on evaluation outcomes.

Final figure/table generation belongs to figtab-repo and is delivered with the paper; all numeric figure inputs originate in the above summaries/trials. A report must distinguish finite-sample EB/Clopper-Pearson guarantees from CLT intervals and must include failures. No withheld literature was sought or encountered; the only literature accessed for the analysis beyond the supplied reference source was the directly addressed Maurer–Pontil 2009 empirical-Bernstein paper (arXiv:0907.3740).

`python code/coverage_diagnostics.py` adds exploratory exact one-sided binomial undercoverage tests, with Holm adjustment over all scenario/sample-size cells separately for each method. Failure to reject undercoverage is not proof of validity; theorem-backed methods retain their theoretical distinction regardless of Monte Carlo outcomes.

The finite-N follow-up is reproduced by `python code/run_experiments.py --group synthetic --scenarios linear quadratic no_signal --ratio 1 --reps 3000 --ns 2000 --out results/ratio1`. Include `results/ratio1` in the summarizer/audit inputs. `python code/audit_results.py results/synthetic results/real results/bounded results/ratio1` validates draw records and writes tail diagnostics; `python code/write_findings.py` regenerates the claim-to-output notes. The output scenario name `no_signal` replaces the original internal name `null` to avoid CSV missing-value parsing; the seed ordinal is unchanged.
