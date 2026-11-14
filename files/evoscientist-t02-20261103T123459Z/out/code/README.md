# Modular grokking and model width — reproducible research artifact

## Read first / 主要结论

- **Downloadable bundle:** `grokking_study.zip`; archive SHA-256 in `grokking_study.zip.sha256`, per-file integrity in `artifact_manifest.json`. `make_bundle.py` rebuilds it without exporting hidden runtime folders or environments.
- **Paper:** `paper.pdf`; complete LaTeX: `paper.tex`, `references.bib`, unchanged official `iclr2027_conference.{sty,bst}` and support files.
- **Scope:** a quadratic network on modular addition, CPU-only, not a Transformer or language-model study. Prior model-wise grokking is acknowledged; no first-discovery claim.
- **Main test:** widening32→128 accelerates the observable held-out endpoint more than training interpolation, contradicting the prespecified preferential-interpolation hypothesis. Paired interaction **D=1.57834**, unadjusted95% bootstrapCI **[0.99379,2.01636]**, Holm-adjusted **p=0.0234375**.
- **Range dependence:** a post-hoc, exploratory64→256 interaction reverses direction: D=-0.172, unadjusted95%CI[-0.269,-0.083]. Both arms have8/8 observed events, but the +50 shift and early sampling still matter. All adjacent pairs are reported; this does not rescue the failed primary prediction or add confirmatory tests.
- **Important boundary:** a first99% qualifying onset is not lasting acquisition. At width128, half-decay runs have clock-compatible first onsets, yet7/8 finish below99%. Width32 clock comparisons are mostly censored and inconclusive.
- Numbers are actual runs. `final_report.md` is the concise Chinese research report; `analysis/` contains unrounded statistics and all seed-level effects.

## Artifact contents

| Path | Purpose |
|---|---|
| `research_request.md` | Original brief/constraints, merged by document |
| `todos.md`, `design_review.md` | Prospective design sketches (not results; superseded by frozen protocol) |
| `protocol.json`, `confirm_jobs.json` | Authoritative frozen protocol and exact240-job ledger |
| `train.py` | Synthetic data, model, optimizer, metrics, raw CSVs/checkpoints |
| `run_jobs.py` | Bounded CPU launcher; exact-command successful jobs can resume |
| `results/confirm/` | All240 frozen runs: configs, summaries,401-row trajectories, final checkpoints, command logs |
| `results/pilot/` | All13 independent exploratory/validation runs; never pooled with confirmation |
| `results/reproaudit/` | One technical duplicate, not a new statistical seed |
| `source_history/train_pilot_v1.py` | Exact hash-matching source used for first9 pilots |
| `analyze.py` | Ledger validation, restricted events, uncertainty, primary tests and tables |
| `stability.py` | **Post-hoc descriptive** retention/persistent-to-end audit, not a changed primary endpoint |
| `verify_constructive.py` | Non-trained eight-unit cosine expressivity check |
| `plot.py`, `figure-spec.md` | Reproducible PNG/PDF graphics and semantic specification |
| `export_tex.py` | Numerical LaTeX macros and primary table directly from saved outputs |
| `verify_artifacts.py` | Event/checkpoint/hash/energy/PDF audit |
| `test_train.py`, `test_analysis.py`, `test_launcher.py` | Data/gradient/projection/optimizer/statistical/cache-provenance tests |
| `reproduce.sh` | Full/resume or analysis-only reproduction |
| `environment.json`, `hardware.txt`, `requirements*.txt` | Recorded environment and exact package versions |
| `experiment_log.md`, `protocol_deviations.md` | Pilots, failures, post-hoc additions and access incidents |
| `literature_notes.md`, `literature/ACCESS_AUDIT.md` | Direct-original reading and restricted-access provenance |
| `template/PROVENANCE.md` | Official ICLR2027 template, page cap and required disclosure evidence |
| `verification_report.json`, `self_review.md` | Final checks and independent AI self-review |

## Environment

Tested with Linux x86_64, Intel Xeon Gold6230, Python3.11.15, CPU PyTorch2.15.0+cpu, NumPy2.4.6, SciPy1.17.1, pandas3.0.6 and matplotlib3.11.2. The host reports40 logical CPUs; no exclusive CPU allocation is claimed. Actual training uses **one intra-op and one inter-op thread per process**, eight worker processes. GPU/CUDA is not used. See the recorded files for exact values.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The CPU wheel index is declared in `requirements.txt`. `requirements-lock.txt` records the full originally installed environment, including tooling not needed for the minimal experiment. PDF compilation additionally needs `pdflatex`, `bibtex`, `latexmk`, standard LaTeX packages (amsmath,booktabs,longtable,hyperref,graphicx), and Times-compatible fonts; typically TeX Live's latex-extra/fonts-recommended packages suffice. No paid API or network service is required after dependencies are installed.

## Fast reproduction from the supplied actual results

Run **from this workspace root**:

```bash
bash reproduce.sh --analysis-only
```

This runs unit tests, validates/reanalyzes all240 logs, performs the post-hoc stability audit and static construction check, regenerates all6 figures and LaTeX numbers, compiles the paper, then audits all checkpoints and the PDF. It normally takes seconds to a few minutes depending on CPU/TeX installation; use `analysis/timing.json` for measured training times, not this analysis estimate.

Equivalent explicit commands:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest test_train.py test_analysis.py test_launcher.py -q
python analyze.py
python stability.py
python verify_constructive.py
python plot.py
python export_tex.py
latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
python verify_artifacts.py --checkpoints --paper
```

The analysis refuses incomplete or altered-ledger results. It checks the frozen training-source hash. **Do not edit `train.py` or overwrite `protocol.json` to make a run pass validation.**

## Fresh training / resumption

```bash
WORKERS=8 bash reproduce.sh
```

With supplied results present this resumes/skips successful exact commands whose trainer-source hash also matches. Cached-only replays write `confirm_jobs.json.latest_attempt.json` without replacing the original measured execution duration. The initial launcher is archived in `source_history/run_jobs_v1.py`; this release-only provenance fix does not change training. For a genuinely fresh rerun, first preserve the existing directory (for example `mv results/confirm results/confirm.original`) and preserve `confirm_jobs.json.execution.json`, then execute the same command. Keep pilots and original evidence. `WORKERS=1` or4 changes only scheduling, not the model or statistical protocol. Exact timing will change.

Single-run example:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python train.py --p 31 --fraction .7 --width 128 --seed 0 \
  --steps 20000 --eval-every 50 --lr .01 --decay .1 \
  --threads 1 --task add --normalization sqrt --checkpoint \
  --tag standalone --out results/standalone
```

The full ledger, not this example, defines the experiment. There is no early stopping or adaptive horizon extension. Failed numerical runs would be failures, not administrative censors. Every planned run is retained.

**Runtime:** `analysis/timing.json` gives actual summed process CPU-hours, per-run wall ranges and checkpoints; `confirm_jobs.json.execution.json` gives end-to-end launcher elapsed time and command-level durations. CPU time excludes interpreter startup; per-run timings include diagnostics. These shared-host wall times are not hardware-independent efficiency claims. The full experiment is small enough for a single CPU workstation within the stated week; slower machines should budget based on a measured pilot. All files are far below the1GB artifact-storage budget; no large model download is part of the experiment.

## Data, seeds and versioning

No dataset download, account, license or third-party snapshot is needed. `dataset()` in `train.py` enumerates allp² ordered pairs and computes integer labels directly. Mainp31/fraction.7 gives672 training and289 held-out pairs; fractions.3/.5 andp23 are separate planned controls. Subtraction is addition with a relabeled second operand, not an independent algorithm family.

- Confirmatory seed clusters: **0--7**, jointly determining initialization and split.
- NumPy split seed: `seed+10000`; global label-permutation seed: `seed+20000`.
- Independent pilot/validation identifiers:900--903. Analysis bootstrap seed:20261103.
- Each run stores its config, source SHA-256, split SHA-256, initial-tensor SHA-256 (final trainer), environment versions and actual metrics.
- Source bytes, rather than an external data version, fix generation. Nine early pilots used archived source SHA `68c98c0b4067e5bef61ef4603e116d0e72142bd1e88675f1d830057d546e0cda`; all confirmation and four validation pilots use the hash in `protocol.json`. The changes add diagnostics/metadata and normalization controls before confirmation, not changes during it. `recover_pilot_source.py` recreates the exact old bytes only when their hash matches the saved early runs.

Early-pilot rerun example (use a new output directory):

```bash
python source_history/train_pilot_v1.py --width 64 --seed 900 --steps 12000 \
  --tag pilot --out results/pilot_reproduction
```

The other early configs are explicit in `pilot_jobs.json`; validation configs are in `validation_jobs.json`. They are exploratory, not additional independent confirmatory observations.

## Statistical interpretation

Events require99% accuracy for3 observations spaced50 updates apart. Latest confirmable onset is19,900. A capped non-event is **not an observed time**. The primary width multiplier concerns `50+min(T,19900)` and geometric seed effects, not uncensored raw-time speedup. Three paired sign-flip contrasts receive Holm correction; all95% effect intervals are unadjusted seed-cluster bootstrap intervals. Wilson intervals concern each arm's event incidence. Eight clusters do not separately identify split and initialization variance.

`stability.py` was added after regression was noticed; its persistent-to-observed-end endpoint is descriptive/post-hoc and does not replace the frozen first onset. `verify_constructive.py` uses analytically specified weights; its100% full-grid accuracy is **not learned generalization** and is not part of the240 training runs. Oracle-projected accuracies mix training/held-out predictions by the known rule and are diagnostic-only; no primary result uses them as predictions.

## Every table and figure: provenance map

| Paper item | Script | Data / generated output |
|---|---|---|
| Table1 training ledger | `freeze_protocol.py` (already frozen; **do not overwrite**) | `confirm_jobs.json`, `protocol.json` |
| Table2 main widths | `analyze.py` | raw main CSV/summaries → `analysis/width_table.tex`, `groups.csv` |
| Table3 primary contrasts | `analyze.py`, `export_tex.py` | `analysis/contrasts.json` → `primary_table.tex` |
| Appendix full controls table | `analyze.py` | all240 summaries → `analysis/controls_table.tex` |
| Appendix stability table | `stability.py` | raw curves → `analysis/stability_table.tex` |
| Figure1 width/onset/final accuracy | `plot.py:width` | main trajectories/summaries → `figures/width.{png,pdf}` |
| Figure2 decay curves/clock | `plot.py:clock` | main+decay curves → `figures/clock.{png,pdf}` |
| Figure3 feature/label controls | `plot.py:controls` | main/frozen/shuffle/capacity arms → `figures/controls.{png,pdf}` |
| Appendix normalization | `plot.py:normalization` | main/mean/matched arms → `figures/normalization.{png,pdf}` |
| Appendix boundary tests | `plot.py:robustness` | main/middata/lowdata/modulus/subtract → `figures/robustness.{png,pdf}` |
| Appendix continuous losses/energies | `plot.py:trajectories` | raw main curves → `figures/trajectories.{png,pdf}` |
| Appendix exploratory width-grid table | `analyze.py` | main runs → `analysis/secondary_width_table.tex`; not a new confirmatory family |
| Numeric prose/macros | `export_tex.py` | analysis outputs → `analysis/numbers.tex` |
| Exact classifier accuracy/margin | `verify_constructive.py` | generated exhaustive pairs → `analysis/constructive.json` |

Curve bands are **seed min--max**, not confidence intervals. Figures use no smoothing, extrapolated transitions or illustrative fake results. All original per-seed effects are retained in `analysis/contrasts.json`.

## Literature independence and conference format

Only seven directly supplied original papers were read. There were no topical searches, citation/repository expansion or attempts to infer the excluded work. `literature_notes.md` records pages actually read; direct PDF hashes and access provenance are saved. No known forbidden exposure occurred. Since the excluded work's identity is undisclosed, this is an access-procedure audit, not an identity-based guarantee. Setup failures and direct template404 probes are logged.

The official **ICLR2027** released template was retrieved from the official author-guideline link. Main-text cap is9 pages at initial submission; references, appendices and required AI-use statement are excluded. No separate mandatory ICLR checklist was specified in those guidelines; the mandatory AI-use statement is included. `REPRODUCIBILITY_CHECKLIST.md` is an artifact-specific completed checklist, not an invented conference form. The actual conference deadline has passed; this is a formatting target, **not a claim of submission, acceptance, eligibility or human scientific verification**. AI participation is disclosed accurately.
