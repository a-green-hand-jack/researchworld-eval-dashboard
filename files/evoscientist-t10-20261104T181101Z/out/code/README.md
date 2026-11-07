# Fixed-score interval-width audit

**Main deliverable:** [`paper.pdf`](paper.pdf), with [`paper.tex`](paper.tex), [`references.bib`](references.bib), the unmodified official `neurips_2026.sty`, and a fully answered official 2026 checklist. This is a research draft in the **NeurIPS 2026 Main Track submission format**, not a claim of acceptance or actual submission. Main text is 7 pages (limit 9); see `release_validation.json` for the final total and checks. 中文总结：[`final_report.md`](final_report.md).

## Result and scope

The answer is **conditional, not universal**. At 500 labels and 10,000 unlabeled scores in the prespecified sharp-tail law, the protected exact construction has 26.51% smaller mean width than PPI++ (paired pointwise MC95 reduction interval [26.28%,26.75%]), with zero observed misses in 3,000 trials. Both real prediction pools instead show substantial width penalties. Rare-event and shifted-data Wald failures are retained. These are not new general efficiency or universal optimality results.

Finite-sample validity is a mathematical guarantee for binary means under independent iid common-population sampling and fixed evaluation-independent partitions. Simulated hit rates are not proofs, and need not all exceed nominal in finite MC runs. The exact-family minimum observed rate is .943333; the minimum simultaneous MC lower bound is .927341, not .95. Output padding does not formally certify floating-point special-function error.

“Fixed inputs” means the SAME realized labels and unlabeled scores for all methods within a repeated trial. There are 103,500 distinct trial inputs, not 1,656,000 independent trials. No labels or unlabeled outcomes are used to train a base predictor; no active label allocation or predictor replacement occurs. Fixed partitions are statistical summaries of the immutable score.

## Files to use

- `submission_source.zip`: manuscript, official style/checklist, complete study code, environments, small summaries and audits. **No raw third-party arrays and no downloaded research PDFs.**
- `experiment_outputs.zip`: all original/supplemental raw endpoints, diagnostic files, configs/timing metadata, and the separate matched-budget ablation outputs. Not needed to run from scratch; useful for audit.
- `summary.csv`: 624 method/cell rows, coverage with Wilson MC95, mean width and MCSE, exact simultaneous lower bounds and adjusted undercoverage tests.
- `paired.csv`: 1,248 paired comparisons, ratio-of-mean-width effects with pointwise delta MC95, designated Holm-adjusted width tests. Undefined zero-denominator ratios remain NaN.
- `seed_summary.csv`: three independent seed blocks for all original/supplementary cells.
- `mass_ablation_summary.csv`: four exploratory matched-response-budget known-mass comparisons; not part of locked confirmatory families.
- `source_verification.md`, `retrieval_log.md`, `template_provenance.md`: source boundaries and provenance.
- `theory_audit.md`, `analysis_audit.md`, `paper_review.md`, `review_response.md`: audits and resolutions. Earlier review artifacts are historical and can describe issues since corrected; the response identifies the changes.
- `integrity_audit.json`, `release_validation.json`, `delivery_manifest.json`: row/pairing checks, PDF/replay checks and delivered-file digests.

Everything is relative to the workspace root. Private conversation/cache folders are not part of the submission archives.

## Environment

Tested existing environment:
- CPython **3.11.15**, Linux x86_64.
- NumPy **2.4.6**, SciPy **1.17.1**, pandas **3.0.6**, matplotlib **3.11.2**.
- pypdf **6.1.3** for safe source extraction and PDF checks, pytest **8.4.2**.
- CPU only; four worker processes with one BLAS/OpenMP thread each. Host: Intel Xeon Gold 6230 @ 2.10GHz, 40 CPUs visible. No GPU, paid API, model downloads or training are required by any reproduction script.
- `pdflatex`, `bibtex`, and `latexmk`, with standard LaTeX packages `amsmath`, `amssymb`, `amsthm`, `natbib`, `booktabs`, `graphicx`, `longtable`, `hyperref`, `url`, `microtype`, `xcolor`. The actual official 2026 style is included and is not edited.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python reproduce.py
```

The driver changes subprocess cwd to its own directory, records per-stage logs/times, and stops on failure. It overwrites generated results with a reproducible rerun. Wall times and timestamps can change; scientific endpoints and summaries should agree to serialization/numerical precision. A completely fresh isolated virtual environment was not separately benchmarked; the pinned environment above was used for all reported runs.

To verify supplied artifacts without generating additional independent trials:

```bash
python reproduce.py --verify-only --skip-download
```

This runs the six tests and **deterministically replays three entire existing cells** (9,000 existing trial inputs, 14 original methods), including sharp-tail success, rare-event failure and real-pool data. It validates saved endpoints, PDF/page/style/checklist status and the absence of undefined references/overfull boxes. It does not add the replayed observations to the scientific sample size.

## Exact stage commands

Run from the workspace root, in order:

```bash
python download_data.py
python -m pytest test_intervals.py -q
python run_experiments.py --workers 4
python supplement_baselines.py
python summarize.py
python mass_ablation.py
python prepare_submission.py
latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
python verify_release.py --recompute
python prepare_submission.py --package
```

Optional mechanics-only smoke run: `python run_experiments.py --workers 4 --smoke`; output goes to `smoke_results/` and is never included in reported scientific results. Do not change batch size, scenario/cell ordering, NumPy generator or seed sequence if exact deterministic replay is desired.

The original primary run took **39.0803 s wall time** for 39 cells/14 methods; the two Hoeffding supplements took **7.7516 s** by their metadata. Individual cell wall times are saved in `results/*_timing.json`; primary cell times overlap across workers and must not be added as wall time. A four-worker reproduction including analysis, replay and LaTeX is expected to take **minutes on a comparable host**, not a week; downloads and TeX installation can dominate elsewhere. This estimate is not a measured portable guarantee. Peak concurrent memory and per-method times were not monitored for the original scientific runs. Batch 40 keeps a largest score array around 16 MB here (40×50,000×8 bytes), with additional arrays, DataFrames and worker overhead; a 4-core/16-GB CPU host is a conservative target, not a measured peak. Later driver `getrusage` figures describe max child RSS, not original-run or total concurrent peak memory.

## Data: version, access, and limits

Only `forest` and `galaxies` **PPI reference arrays**, associated with PPI (cited in the paper), from the `ppi-python` **v0.2.3** dataset loader are used. No other ML package is needed at runtime. Loader source explicitly inspected:

`https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/ppi_py/datasets/datasets.py`

`download_data.py` retrieves exactly the loader's two Google Drive IDs via a direct anonymous URL, validates SHA256, shape, binary outcomes, finite scores and range [0,1], and rejects any changed files. No automatic substitute is accepted on a hash mismatch.

| File | Rows | Target empirical proportion | SHA256 |
|---|---:|---:|---|
| `data/forest.npz` | 1,596 | 242/1596 | `9708f3be14850a55d03f88dad235c87b4a3b6c6e8cb81173cc580de8f7386ade` |
| `data/galaxies.npz` | 16,743 | 4341/16743 | `7be1d40a049f524fc51e150281541359a47c5eca80343dfac5b1c457fd7eae99` |

The PPI code repository is MIT according to the supplied brief; **no independent license for these NPZ arrays has been established**. The study does not relicense them. The released ZIP archives exclude the raw arrays; use the documented access route subject to applicable terms. Local cached files remain in the working directory as research inputs. The study's own code license is in `LICENSE`; it does not apply to data, the official style or external assets.

Arrays provide fixed `Y` and `Yhat`, not training data/model weights. Original training independence is not independently verified. Empirical-population experiments independently sample labeled and unlabeled indices **with replacement**. Overlap of source indices is allowed under independent draws. This is conditional empirical-law coverage, not original application-superpopulation coverage, predictor-training uncertainty, a new unique-label acquisition, or deployment validation. The evaluator uses the full label pool solely to define truth/draw inputs; methods only receive the sampled labeled responses. No unlabeled response is passed to inference.

## Seeds, design and methods

- Master seeds **1729, 2027, 7919**; per-cell `SeedSequence([master_seed,cell_id])`, NumPy `default_rng` (PCG64), batch size **40**. Batch size is part of deterministic stream layout.
- Eight synthetic cases × three n values = 24 main cells; three cases × three N/n values = nine sensitivity cells; two empirical pools × three n values = six cells. `results/design.json` contains the ordered complete design.
- Main/empirical: 1,000 trials per seed, total 3,000 per cell. Sensitivity: 500 per seed, total 1,500. Main n=100/500/2000, N=20n; sensitivity n=500, N/n=1/5/100.
- Original methods: labeled Wald/CP, original PPI Wald, unrestricted pooled-variance PPI++, four fitted fixed-bin Wald controls, three fixed-partition CP intervals, protected/unsafe selectors, known-mass CP diagnostic. Two descriptive supplements: label Hoeffding and original-PPI union-Hoeffding.
- All feasible procedures use the same label/sample budgets. Oracle weights are ONLY used in clearly labeled infeasible diagnostics. The matched-budget post-audit ablation regenerates the same four sharp-tail cells (7,500 rows), not additional independent trial inputs.
- Fixed variance cutoff: scalar PPI++ uses zero coefficient when pooled score variance ≤1e−14. The ideal positive-variance consistency theorem transfers to this code only above the cutoff; the below-cutoff fallback is labeled Wald, not the ideal efficient scalar. No headline cell has been shown to depend on this safeguard.

Multiplicity is documented in `multiplicity_manifest.json`: 180 exact-method/cell MC lower bounds, 72 designated paired-width tests, and 252 asymptotic undercoverage tests, **separate families**. The lock is declared before full outcome inspection after mechanics-only smoke checks, not externally authenticated preregistration. Hoeffding additions are descriptive; the matched-mass ablation is post-audit exploratory. Source/version chronology and failed attempts are in `experiment_log.md`.

## Every table and figure

| Paper display | Producer | Primary inputs / output |
|---|---|---|
| Table 1, synthetic n=500 | `summarize.py:make_tables` | raw endpoint CSVs → `summary.csv` → `generated/main_table.tex` |
| Table 2, paired selected effects | same | `paired.csv`, `summary.csv` → `generated/paired_table.tex` |
| Table 3, empirical populations | same | `summary.csv` → `generated/real_table.tex` |
| Table 4, synthetic-law specification | `run_experiments.py:probability/truth/sample`; typeset in `paper.tex` | Exact prespecified functions/analytic truths, **not measured performance** |
| Table 5, matched mass ablation | `mass_ablation.py` | same regenerated inputs + existing raw outputs → `mass_ablation_summary.csv`, `generated/mass_ablation.tex` |
| Table 6, all 624 results | `summarize.py:make_tables` | `summary.csv` → `generated/all_results.tex` |
| Figure 1, coverage/width | `summarize.py:make_figures` | `summary.csv` → `figures/coverage_width.{pdf,png}` |
| Figure 2, unlabeled-budget sensitivity | same | `summary.csv` → `figures/unlabeled_sensitivity.{pdf,png}` |
| Figure 3, real mean-width ratios with paired MC95 | same | `paired.csv` → `figures/real_width.{pdf,png}` |
| Figure 4, bin sensitivity | same | `summary.csv` → `figures/bin_ablation.{pdf,png}` |
| All empirical number macros | `summarize.py:make_tables` | summary/paired/run metadata → `generated/numbers.{tex,json}` |

No illustrative or placeholder performance numbers occur. Exact formulas, design sizes, probability bounds and known-law plots are not presented as measured experimental results. Prose failure counts/selector frequencies are reproducible from `results/*_diagnostics.csv.gz` and the read-only scripts in `artifacts/`. Audit CSV physical line numbers include the header; authoritative joins use `(cell_id,method,reference)` or `(seed,rep,method)`.

`artifacts/analysis_audit_checks.py` and `artifacts/paper_review_scan.py` are historical read-only audit scripts. They may use the original workspace locator `/work`; ordinary reproduction scripts use their own file location and are portable. The final `review_response.md` identifies display changes after those audits; old audit reports remain historical evidence, not assertions that a corrected defect persists.

## Source boundary and independent research

No search engine, paper-aggregation site, citation graph or attempts to infer the forbidden paper's identity were used. Only the three explicitly permitted original papers were actually read and cited:
1. PPI, arXiv:2301.09633v4 (main physical pages 1–7).
2. PPI++, arXiv:2311.01453 (main physical pages 1–13).
3. Stratified PPI, arXiv:2406.04291v2 (main physical pages 1–9).

**Incidental exposure log:** initial native PDF reads of the allowed PPI++ and Stratified-PPI originals included their bibliography pages despite pagination arguments. Reading stopped, no referenced URL was followed, and no prohibited identity or confirmed prohibited exposure was recognized. Later pypdf extraction physically excluded bibliography pages before reading. Details and extent are recorded in `retrieval_log.md`; the more complete final formula verification is `source_verification.md`, which supersedes the early partial `literature_notes.md`. No absence-of-duplication conclusion is inferred from this restricted literature access.

The official NeurIPS 2026 style archive/author handbook/checklist and ethics page were consulted only for format/compliance. `template/` retains downloaded originals, official text snapshots and provenance hashes. The official style file used in the root is byte-identical to the archived original. The bundled 2026 checklist requires a justification for **every** answer; all 16 are filled, including conservative **No** answers for unresolved licenses and incomplete original resource measurements.

## Failure handling and research transparency

The source extraction initially failed because `pdftotext` was missing; a later one-line extraction had a corrected syntax error. The first summary run reached EDA and failed on a missing import, fixed without changing observations/methods. Optional split-Hoeffding/empirical-Bernstein and learned-regressor ideas were considered but not evaluated; no results are attributed to them. The broad claim “more bins is always better” was rejected by theory audit and replaced by a refinement-only oracle statement. No unfavorable scenario was dropped.

Rare outcomes create [0,0] Wald intervals after zero labels. Shift can instead push the center beyond support and clip to [1,1]; these are different failure mechanisms. Original diagnostics do not save all preclipping centers or numerical-fallback flags; no claim of zero fallback events is made. An observed 100% hit rate is not true coverage=1. No human author, formal proof assistant or peer-review acceptance is represented as verification. The work was produced by an autonomous language-model research assistant and independently checked by subagents; the inference code does not invoke an LLM.
