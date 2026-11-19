# Fixed-game SHAP reliability audit

A reproducible empirical audit of whether **one** paired forward/reverse permutation run recovers the unordered three largest absolute Shapley contributions of a fixed prediction. This is an honest research artifact, **not a claim of peer-reviewed publication**, a new estimator, or certified deployment reliability.

- Manuscript: `paper.tex`; Chinese technical summary: [final_report.md](final_report.md).
- Measured main results: `analysis120/summary.json`; held-out next-90 results: `analysis90/summary.json`.
- Chronology, failures and repairs: [experiment_log.md](experiment_log.md).
- Every manuscript figure/table and its generator: [ARTIFACT_MAP.md](ARTIFACT_MAP.md).
- Data terms and provenance: [DATA_LICENSES.md](DATA_LICENSES.md).

## What the evidence supports

For Pima/ACS × LR/RF/MLP, exact-game macro top-three recovery rises from **0.7656 [0.7523, 0.7790]** at one cycle to **0.9656 [0.9597, 0.9709]** at 64. Intervals are descriptive paired instance-cluster bootstrap intervals, not population certificates. P64 Pima/MLP and ACS/MLP means remain **0.9400** and **0.9490**, below the illustrative 0.95 criterion; both intervals cross it. Small reference-gap strata remain difficult. German uses an approximate reference, not exact truth. High sign agreement, additivity and between-run agreement do not certify recovery or causal/safety validity.

The first 30 instances were **exploratory and inspected**. The uniform expansion to 120 was specified afterward, before expanded outcomes. The next 90 are held-out precision validation under the same ordering, fits and backgrounds, not an independent confirmatory study or original preregistration. All 27 expanded cells reproduce every stored first-30 array exactly. Sensitivity remains first10/seed11 only.

## Compact submission archive

`submission.zip` contains the PDF/LaTeX, code, version pins, frozen result NPZ/JSON, tables, figures, and audits; `RELEASE_MANIFEST.json` lists hashes. To remain below the official 100 MB supplement cap, it omits only redundant `analysis_inputs.npz` caches (source arrays are already in `results*/`). The full working tree retains these caches. After extracting the compact archive, regenerate canonical caches before running `test_precision_analysis.py`:

```sh
ROOT="$(pwd)"
python "$ROOT/analyze.py" --results "$ROOT/results120" --out "$ROOT/analysis120" \
  --expected-n 120 --start-instance 0 --stop-instance 120 --sensitivity-results "$ROOT/results"
python "$ROOT/analyze.py" --results "$ROOT/results120" --out "$ROOT/analysis90" \
  --expected-n 120 --start-instance 30 --stop-instance 120 --sensitivity-results "$ROOT/results"
python "$ROOT/test_precision_analysis.py"
sh "$ROOT/build.sh"
```

A clean extracted-archive check **passed**: both canonical analyses, the full analysis regression, and PDF rebuild completed without raw datasets, model files or network access. Details are in `release_replay.log`; this validates the archive rather than only the original working tree.

This replay needs neither raw data, model files, network, nor paid APIs. `package_release.py` rebuilds the compact archive with the same inclusion boundary. Downloaded original-paper PDFs/official HTML snapshots are local provenance copies, not redistributed archive contents; URLs and reading scopes remain in `sources.md`.

## 1. Environment

Run these commands **from the extracted release root**, wherever it is located:

```sh
ROOT="$(pwd)"
python3.11 -m venv "$ROOT/.venv"
. "$ROOT/.venv/bin/activate"
python -m pip install -r "$ROOT/requirements.txt"
python --version
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
```

Python **3.11** is required for the documented environment (observed 3.11.15). `requirements.txt` pins the observed inventory, including NumPy 2.4.6, pandas 3.0.6, SciPy 1.17.1, scikit-learn 1.9.1, SHAP 0.51.0, Folktables 0.0.12 and Matplotlib 3.11.2. This inventory was recorded at manuscript assembly; it is not a reconstructed historical lockfile. Cross-platform bitwise fit equality is not promised.

Installation normally needs Internet access and compatible wheels. Offline installation requires an already prepared wheelhouse for the target platform:

```sh
# On a connected compatible machine:
python -m pip download -r "$ROOT/requirements.txt" -d "$ROOT/wheelhouse"
# On the offline machine, after creating/activating the venv:
python -m pip install --no-index --find-links "$ROOT/wheelhouse" -r "$ROOT/requirements.txt"
```

No GPU, paid API or extra Jinja2 dependency is needed. Table writers emit escaped LaTeX directly. PDF building additionally requires a TeX installation with pdfLaTeX, BibTeX and the packages imported by `paper.tex`; Python requirements do not install TeX.

## 2. Data acquisition (online; not needed for saved-result replay)

```sh
python "$ROOT/get_data.py"
```

The downloader resolves `data/` relative to its own script. It skips existing German/Pima downloads and an existing ACS pickle, extracts German, and writes `data/manifest.json` with local file sizes/SHA-256. It **records** hashes; it does not reject changed upstream bytes by comparison to a pinned remote checksum. Compare against the reference hashes in `DATA_LICENSES.md`; do not blindly trust a downloaded pickle from a third party.

| Dataset actually used | Exact identifier/version and URL | Local input and interpretation |
|---|---|---|
| German Credit | Hans Hofmann (1994), UCI **dataset144**, DOI **10.24432/C5NC77**; [dataset](https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data); downloader: `https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip` | `data/german/german.data`: original categorical variant, 1,000 × 20 predictors; positive = bad credit (class 2). The numeric variant in the ZIP is not used. |
| Pima diabetes | OpenML **37, version 1, file37**; downloader: `https://www.openml.org/data/download/37/dataset_37_diabetes.arff`; identity API: `https://www.openml.org/api/v1/json/data/37` | `data/pima.arff`: 768 × 8; positive = `tested_positive`. Local MD5 matches API value `3cbaa3e54586aa88cf6aacb4033e4470`. |
| ACSIncome | U.S. Census **2018 ACS 1-Year PUMS Vermont person records**, via **Folktables 0.0.12**; installed downloader constructs `https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pvt.zip`; [official documentation](https://www.census.gov/programs-surveys/acs/microdata/documentation/2018.html) | `data/acs/2018/1-Year/psam_p50.csv` (6,436 × 286 before task filtering), locally serialized as `data/acs2018vt.pkl`; ACSIncome retains 3,767 persons/10 predictors; positive = income > $50,000. Census ZIP URL is source-code-derived, not an independently authenticated original acquisition transaction. |

ACS uses the installed filter `AGEP>16`, `PINCP>100`, `WKHP>0`, `PWGTP>=1`, not a substituted prose threshold. Pima zeros in `plas,pres,skin,insu,mass` become missing. Train-only per-feature imputation/scaling or one-hot encoding is used; raw categorical groups switch jointly.

**Release boundary:** do not bundle raw datasets, ACS pickle/row-level subsets, or fitted `model_*.joblib` files in the release archive. The downloader and derived audit results are supplied instead. These files may exist in the local working tree; local availability is not permission to redistribute. German's official page declares **CC BY 4.0** (retain attribution/license/change notices if separately redistributed). OpenML's exact label **“Public”** does not settle detailed Pima reuse terms. Census copyright/terms verification remains unresolved; Folktables' MIT software license does not license Census records. A downloader is not a substitute for compliance with source terms.

## 3. Offline replay of supplied results (no fitting, raw data or network)

Required inputs: `results120/*.npz` and matching JSON/data manifests; retained `results/` main30 and B16 NPZ/JSON/manifests. Joblib models and raw `data/` are unnecessary. Keep `analysis/` and `analysis30/` as historical archives. To avoid overwriting frozen analysis outputs:

```sh
mkdir -p "$ROOT/replay"
python "$ROOT/analyze.py" --results "$ROOT/results120" \
  --out "$ROOT/replay/analysis120" --expected-n 120 \
  --start-instance 0 --stop-instance 120 \
  --sensitivity-results "$ROOT/results"
python "$ROOT/analyze.py" --results "$ROOT/results120" \
  --out "$ROOT/replay/analysis90" --expected-n 120 \
  --start-instance 30 --stop-instance 120 \
  --sensitivity-results "$ROOT/results"
python "$ROOT/analyze.py" --results "$ROOT/results" \
  --out "$ROOT/replay/analysis30" --expected-n 30 \
  --start-instance 0 --stop-instance 30 \
  --sensitivity-results "$ROOT/results"
python "$ROOT/replay/analysis120/plot.py" --out "$ROOT/replay/analysis120"
python "$ROOT/analyze.py" --self-test
```

Expected status for each complete replay: `complete`, 27 main cells and six B16 cells. Expanded replays require a passed 27-cell exact prefix audit. All 120 source instances are validated **before** slicing to 90. B16 always compares original first10 B8/B16, including in the next90 report; it is not next90 sensitivity.

**CLI traps:** there is **no `--original-results` option**. `--sensitivity-results` also supplies the original30 prefix-audit baseline and campaign accounting; n120 requires it explicitly. Always pass `--out`: the default is `analysis`, and the original `/work/analysis` and `/work/analysis30` are protected in this implementation. Exit code 2 means incomplete/invalid main inputs; code 3 means prefix audit failure. Do not treat stale tables or `--partial exact` as final all-dataset results.

For the supplied canonical analyses, this additional analysis-only regression checks all seeds/methods, cohorts, paired intervals, contrast correction and immutable n30 archive. It writes verification JSON into `analysis120/` and `analysis90/` (no model evaluation):

```sh
python "$ROOT/test_precision_analysis.py"
```

This regression expects those **canonical** directories and the archived `analysis/`/`analysis30/`, not the optional `replay/` names above.

## 4. Full data-to-results reproduction

Use a separate extracted copy with empty result directories if you want fresh computation; compatible existing cells skip, they do not rerun. Never mix n30 and n120 cells in one directory. The commands below retain the paper's seeds and budgets, with eight workers for main runs and four for the small sensitivity run; worker count changes scheduling, not the sampling recipe.

```sh
mkdir -p "$ROOT/results" "$ROOT/results120"
python "$ROOT/get_data.py"                 # online only when data absent
python "$ROOT/debug_regression.py"          # offline loading/resume checks; no fitting
python "$ROOT/tests.py"                     # numerical + fitted Pima/SHAP smoke checks
python "$ROOT/postreview_checks.py"         # temporary loading/manifest isolation check
python "$ROOT/experiment.py" --jobs 8 --instances 30 --output "$ROOT/results"
python "$ROOT/experiment.py" --jobs 4 --sensitivity --output "$ROOT/results"
python "$ROOT/experiment.py" --jobs 8 --instances 120 --output "$ROOT/results120"
python "$ROOT/analyze.py" --results "$ROOT/results120" \
  --out "$ROOT/analysis120" --expected-n 120 \
  --start-instance 0 --stop-instance 120 \
  --sensitivity-results "$ROOT/results"
python "$ROOT/analyze.py" --results "$ROOT/results120" \
  --out "$ROOT/analysis90" --expected-n 120 \
  --start-instance 30 --stop-instance 120 \
  --sensitivity-results "$ROOT/results"
python "$ROOT/analyze.py" --results "$ROOT/results" \
  --out "$ROOT/analysis30_replay" --expected-n 30 \
  --start-instance 0 --stop-instance 30 \
  --sensitivity-results "$ROOT/results"
python "$ROOT/analysis120/plot.py" --out "$ROOT/analysis120"
python "$ROOT/render_paper_tables.py"
python "$ROOT/make_failure_example.py"
python "$ROOT/analyze.py" --self-test
python "$ROOT/test_precision_analysis.py"
```

`tests.py` fits a small model and writes `results/tests.json` plus a Pima main30 manifest; run it **before** campaigns, not as part of raw-free replay. `test_precision_analysis.py` also compares with the supplied historical analysis archive; a newly recomputed platform-dependent result can differ from that archive and must be investigated rather than silently accepted. Resume rejects incompatible saved shapes/metadata without replacing them. Pilot mode is isolated under `results/pilot/` and cannot stand in for main cells. Fresh experiments create local fitted models; exclude them again when packaging.

### Frozen seeds and protocol

- Models: seeds **11,23,47**, LR `C=1,max_iter=1000`; RF `40` trees, depth `6`, leaf minimum `4`, `n_jobs=1`; MLP `(32,16)`, `alpha=.01,max_iter=350`, internal early stopping `.15`, patience `20`. Complete resolved parameters are in result JSON sidecars. No external-validation tuning or calibration.
- Nominal splits 60/20/20: split seeds **2026**, then **2027**; stratified Pima/German, household-group ACS. Actual train/validation/test counts: Pima **460/154/154**, ACS **2250/773/744**, German **600/200/200**.
- Audit ordering `default_rng(9041)`; background `default_rng(9042)` samples 16 training rows without replacement, primary uses first **B=8**. ACS retains first person of each unseen household in a person permutation: unique households, **unequal household inclusion**, no survey-weighted inference.
- **R=20**, nested cycles **P=1,4,16,64**. For zero-based instance position `i`, repetition `r`, training seed `s`: `u=11000000+100000*s+1000*i+r`. IID one-way uses `u+20000000` and `2P` paths; Kernel uses `u+30000000+P`. German reference pools use `500000+100*i+s` and `900000+100*i+s`, **512 cycles each**, separate from evaluation streams. Dataset/model names intentionally do not enter the stream map.
- Exact Pima/ACS finite-background coalition cubes; grouped raw players; positive-class **probability**, identity link. German pooled-reference agreement is not exact accuracy. Kernel P64 enumerates both exact cubes and is not evidence of superiority of a randomized estimator.
- Bootstrap **2,000**, seed **20261104**. Dataset indices Pima=0/ACS=1/German=2: expanded/sliced `SeedSequence([20261104,di,start,n])`; original30 `[20261104,di]`; sensitivity `[20261104,16,di]`. Seeds/runs reduce within instance; all methods/budgets/models retain paired instance indices within dataset. The three training seeds are fixed settings, not independent model-population samples.
- Top-three = unordered absolute set, exact ties favor lower raw-feature index. Material sign uses reference magnitude >=0.01; undefined games are omitted only for that metric. `material_feature_coverage` means **fraction of games with any material feature**, not feature-level coverage. Claimed contrasts use a descriptive 63-contrast joint max-centered-absolute-deviation correction; marginal cell intervals do not certify 0.95 reliability.

## 5. Figures, tables and manuscript build

The analysis commands already render the three figures and analysis-owned tables. Two additional scripts are mandatory for appendix inputs:

```sh
python "$ROOT/render_paper_tables.py"    # paper_tables/macro_metrics.tex, cohorts.tex
python "$ROOT/make_failure_example.py"   # failure_example.tex + measured JSON
sh "$ROOT/build.sh"
```

Both table scripts read the **canonical** `analysis120/` or `results120/` beside the scripts; they do not accept `--out` and do not consume optional `replay/` outputs automatically. See `ARTIFACT_MAP.md` for all inputs. Building only `paper.tex` without `analysis120/*.tex`, the three figure PDFs and `paper_tables/*.tex` fails, including appendix imports. No Jinja2 installation is required.

The manuscript uses the **official NeurIPS 2026 Main Track** template unmodified. Initial submission allows **9 main content pages**, including figures/tables; the checked preview has **8 main pages**. References and appendices follow; the **mandatory filled checklist must be last in the same final PDF**, outside that limit. `paper_preview.pdf` omits the checklist and is not a submission substitute. Formatting compliance does not imply novelty or acceptance.

Final release validation is recorded in `build_validation.json`: **8 main-content pages**, **26 total pages**, references start at page 9, and the completed 16-item checklist starts at page 20. The official style hash matches the downloaded template; there are no undefined references or overfull boxes. Rebuild with `sh "$ROOT/build.sh"`. `paper_preview.pdf` is a historical intermediate, not the final deliverable.

## 6. Cost and expected reproduction time

Measured successful experiment CPU: original30+B16 **260.540218 s**, expanded120 including prefix replay **934.138349 s**; total **1,194.678566 s = 0.3319 CPU hours**. This excludes unavailable failed/incomplete overhead, orchestration, installation/downloads, analysis/rendering and TeX build costs. The original **24 CPU-hour** allowance was a budget, **not the observed cost or expected duration**.

Expanded cell wall times sum to **1,615.335063 s**; original30+B16 sum to **539.120842 s**. These are summed cell times, not elapsed parallel makespan. Next90 is a subset analysis, not another experiment campaign. Shared cached predictions include target/reference and control work, so timings cannot be allocated to individual estimators or interpreted as deployment latency.

**Planning estimates, not measurements:** with compatible packages/data already installed, allow roughly **1–5 minutes** for analysis/figure replay and **5–30 minutes** for the full small-model workflow plus checks/build on a comparable multi-core CPU; slower/constrained machines may take longer. These minute-to-tens-of-minutes estimates are motivated by the recorded ~20 CPU-minutes and ~36 summed cell-wall minutes, not a recorded end-to-end stopwatch. Online package/data transfer time is additional and network-dependent. Peak RAM/historical allocation were not measured; post-hoc host details in `environment.json` must not be represented as required or allocated resources.

## 7. Provenance, independence and remaining limits

Only five original research works were actually read/cited: Lundberg–Lee arXiv1705.07874 **v2**; Chen et al. arXiv2006.16234 **v1**; Musco–Witter arXiv2410.01917 **v3 (2026-10-08)**; Nogueira et al. JMLR18(174), **2018**; Ding et al. arXiv2108.04884 **v3**. `sources.md` records URLs, precise reading scopes and version caveats. Official conference/template/ethics and data/license material are separate provenance sources (`official/`, `DATA_LICENSES.md`).

Independence rule: do not search for, infer the identity of, access or use the prohibited prior work or pages discussing/reproducing it. The recorded strategy used direct allowed-original/official endpoints, no topic search, citation graph, recommendations or repository discovery. `access_log.jsonl` records literature/venue requests; `data_access_log.jsonl` records data-license GETs, actual scoped reads and failures. Original raw-data requests were not all transaction-logged; hashes do not fill that gap. No prohibited material was recognized in displayed readings; this is a scoped exposure record, not exhaustive proof of absence. Stop and log location/amount if future prohibited exposure is recognized. Documentation writing added no external access.

An LLM-based assistant autonomously designed, executed, analyzed, wrote and self-reviewed the study; no independent human validation occurred. Novelty/main-conference suitability remains unresolved and acceptance is not guaranteed. Weak model fits, approximate German truth, one background realization, post-exploratory expansion, unequal ACS inclusion and absent causal/fairness/human-use validation limit conclusions. This release is for computational explanation auditing, not clinical or credit decisions.

**Post-review status:** the historical sensitivity-manifest overwrite blocker in `self_review.md` is fixed by `_b16` manifest/model namespaces. `postreview_checks.py` **was executed**, and `postreview_checks.json` records unchanged main30 manifests for Pima and ACS after sensitivity loading. This is a bounded loading regression, not a new full campaign; valid measured results were not regenerated.
