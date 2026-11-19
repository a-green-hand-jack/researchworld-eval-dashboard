# Compositional conformal research artifact

论文：**When Marginal Coverage Hides the Boundary: Evaluating Conformal Regions
for Compositional Responses**。

本研究针对**观测到的组成向量的联合覆盖**，不将分类标签集合的覆盖解释为潜在概率向量的覆盖。
数据完全合成。论文采用从 NeurIPS 官方下载的 **2026 年模板**，正文 8 页，未修改样式；
参考文献、技术附录及完整官方 checklist 另计。使用 preprint 选项，不代表已投稿或录用。
最终页数和自动检查结果见 `results/artifact_validation.json`。

## Deliverables

- `paper.pdf`: compiled full paper; identical copy at `paper/main.pdf`.
- `research_deliverables.zip`: portable source/results package with SHA256 manifest;
  excludes the virtual environment and copyrighted downloaded scholarly PDFs.
- `paper/main.tex`, `paper/references.bib`, `paper/checklist.tex`: complete sources.
- `paper/neurips_2026.sty`: unmodified official current-year style.
- `paper/generated/`: all data-derived tables and numeric macros.
- `src/`: every experiment, numerical check, analysis, and validation script.
- `results/runs.csv`: final seed-level results (15 methods, 1,500 independently
  simulated scenario/dimension/repetition cells; methods share draws within a cell).
- `results/summary.csv`, `paired_contrasts.csv`: unrounded uncertainty summaries.
- `results/boundary_sweep.csv`: 45 configurations, 4,000 calibration arrays each.
- `results/integration_check.csv`, `analytic_volume_check.csv`: numerical checks.
- `results/initial/`, `results/pilot/`: retained earlier runs, excluded from final means.
- `PROTOCOL.md`, `RESEARCH_LOG.md`: design chronology, access restrictions, additions,
  implementation failures, and audit details.
- `literature/READING_NOTES.md`, `literature/provenance.json`: sources actually read,
  direct source URLs, versions, and local checksums.
- `requirements.txt`: dependencies needed for the pipeline; `requirements-lock.txt`:
  complete recorded environment, including tools installed for exploration.
- `THIRD_PARTY_NOTICES.md`, `LICENSE`, `DATA_LICENSE.md`: provenance and licenses.

## Environment and installation

Executed on Linux x86_64, Python **3.11.2**, Intel Xeon Gold 6230 @ 2.10GHz,
40 logical CPUs available; main run used four CPU processes and one BLAS thread
per process. No GPU, paid API, account, or dataset download is needed. Main-run
and numerical-check timings and per-process memory peaks are measured in
`results/metadata.json` and `results/numerical_checks.json`. The final main run
including the atom sweep took approximately 16–17 seconds on this host, and the
higher-precision integration checks took approximately 30–44 seconds. These timings are
machine dependent; budget a few minutes on a typical laptop, plus environment
installation and LaTeX compilation. The complete installed virtual environment
occupied about 566 MiB; scientific results and source are much smaller.

From `/work` (or the unpacked artifact root):

```bash
uv venv --python python3 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

For a complete recreation of the recorded auxiliary tools, install
`requirements-lock.txt` instead. `uv` is only an installer; an ordinary Python
virtual environment and pip with the same versions also work. The supplied
virtual environment does not install pip, so use `uv pip`, not `.venv/bin/pip`.
Python is named `python3` on this host; the bare `python` command is absent.

LaTeX requires a TeX Live installation with `pdflatex`, `latexmk`, `bibtex`,
`natbib`, `lineno`, `times`, `amsmath`, `amsthm`, `graphicx`, `booktabs`,
`microtype`, `xcolor`, and `hyperref`. The original environment already had these.

## Reproduce everything

```bash
bash reproduce.sh
```

The script tests the scientific invariants, reruns all final experiments,
regenerates tables/figures/numeric macros, repeats higher-resolution and analytic
integration checks, compiles the PDF, and validates the artifact. Timing macros
will naturally change with the new run. Use `RESEARCH_PYTHON=/path/to/python`
to select another pinned environment. Supplied `results/initial` is used to check
that the added response-stratified controls did not alter earlier methods.

Individual commands, in dependency order:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
.venv/bin/python -m unittest discover -s src -p 'test_*.py' -v
.venv/bin/python src/run_experiments.py --reps 100 --workers 4
.venv/bin/python src/analyze.py
.venv/bin/python src/check_numerics.py
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error paper/main.tex
cp paper/main.pdf paper.pdf
.venv/bin/python src/validate_artifact.py
```

To rebuild the paper from supplied results without rerunning experiments:

```bash
.venv/bin/python src/analyze.py
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error paper/main.tex
cp paper/main.pdf paper.pdf
```

`paper/generated/check_numbers.tex` is supplied, so the latter route needs no
additional integration run. A quick exploratory run may use `--reps 2 --out
results/smoke_new`; do not point paper analysis at those outputs. The final
analysis intentionally uses the full `results/runs.csv`.

## Seeds, data, and experimental units

All observations are generated by `src/core.py`; there is no external data version
or download. Generator v1 is the code in this artifact, with its final SHA256 in
`MANIFEST.sha256`. Master seed is **20261102**. The three experimental dimensions
are **3, 8, 20**. Each of five mechanisms uses **100** repetitions, with independent
pilot/calibration/test sizes **1000/499/2000**. Calibration error is **0.1**. The
four stream seeds are spawned from `SeedSequence([20261102, scenario_index, K,
rep])`. `scenario_index` follows `dense, hetero, zeros, mixed, shift`; `rep` is
0 through 99. Methods share all observations and integration points inside a
repetition. Different dimensions and scenarios use distinct streams. The atom
sweep uses seed **20261103**.

The raw data generator asserts that every numerical zero is a declared structural
zero. Scores and membership functions define closed-simplex behavior explicitly.
H-Z and H-GZ choose thresholds by the **candidate** target's stratum; they do not
observe the realized test response before forming the region. Empty/tiny strata
use infinity according to the exact split-conformal rank rule.

The final CSV has one row per method per independent cell, not one row per test
target. Metrics are `coverage`, `g0`, `g1`, `boundary`, `interior`, `v2`, `v1`;
`boundary` is missing when its population probability is zero, and `v1/v2` are
missing for K>3. `n_boundary`, `n_g1`, `n_cal_g0_zero`, and infinite-threshold
flags provide denominators and diagnostic counts. Underlying observations are
regenerated from seeds rather than stored. `summary.csv` additionally includes
the SD and 5th/95th seed quantiles, standard error, and pointwise t intervals.
Method comparisons use paired repetition differences. These intervals quantify
Monte Carlo uncertainty under the declared simulator, not uncertainty about
unrepresented real data populations.

## Figure and table map

All analysis outputs are generated by `src/analyze.py` from `results/runs.csv`
and `results/boundary_sweep.csv` produced by `src/run_experiments.py`.

| Paper item | Generated asset | Source |
|---|---|---|
| Figure 1, exact CLR atom transition | `figures/transition.pdf` | `boundary_sweep.csv` |
| Figure 2, support/group diagnostics | `figures/conditional.pdf` | `runs.csv` |
| Figure 3, covariate shift | `figures/shift.pdf` | `runs.csv` |
| Figure 4, smoothing sensitivity | `figures/smoothing.pdf` | `runs.csv` |
| Figure 5, size-measure weight sensitivity | `figures/volume_weights.pdf` | measured `v1/v2` in `runs.csv` |
| Table 1, geometry | `paper/generated/geometry.tex` | `runs.csv` |
| Table 2, reliability/shift | `paper/generated/reliability.tex` | `runs.csv` |
| Appendix D.1–D.5, all results | `paper/generated/full_*.tex` | `runs.csv` |
| Abstract and text result numbers | `paper/generated/numbers.tex` | `runs.csv`, metadata |
| Numerical validation numbers | `paper/generated/check_numbers.tex` | `src/check_numerics.py` outputs |

No numerical results were hand-filled. Theory curves in Figure 1 are explicitly
identified as analytic; plotted experiment points come from actually generated
score arrays. Figure 5 is a deterministic reweighting of measured size components,
not a separate experiment. All paper figures are vector PDFs.

## Interpretation and limits

The main finding is that marginal validity, covariate-group validity, and
zero-status validity are different objectives. Ordinary rank calibration cannot
make them interchangeable. Raw CLR's infinity extension has an exact binomial
whole-simplex transition. Smoothing changes geometry and does not grant boundary
coverage. Response/covariate stratification repairs its own conditional target but
can require large regions in sparsely sampled cells. An efficient density oracle
can sacrifice minority groups; it is not a practical fitted-density result.

The experiment does not validate real classifiers, latent probabilities inferred
from single labels, multiple-zero support patterns, unknown shift weights,
nonexchangeable time series, or high-dimensional volume comparisons. Only a fixed
analytic predictor and disclosed synthetic laws were tested. Two response-stratified
controls were added after the initial results and are explicitly exploratory.
The work was autonomously designed and written by an LLM-based agent without
human scientific review; no model calls are required to run any experiment.
