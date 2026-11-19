# Stability of Bradley-Terry leaderboard rankings (paper-repo)

A NeurIPS 2026 main-track-format paper and the code that regenerates its numbers. Every number in the paper is read from `results/` by `paper/quoted_numbers.py`; nothing in the text stands for a result that was not computed.

## Layout
| path | content | owner |
| --- | --- | --- |
| `paper/main.tex`, `paper/references.bib`, `paper/checklist.tex`, `paper/neurips_2026.sty` | LaTeX source (the `.sty` is the unmodified official file) | paper |
| `paper/main.pdf` | the paper built from the current `main` | paper |
| `paper/quoted_numbers.py` -> `paper/quoted_numbers.tex` | every number quoted in the text, read from `results/*.csv` | paper |
| `code/`, `results/` | analysis code and result tables; definitions in `results/README.md`, commands in `code/REPRODUCE.md` | experiment |
| `figures/`, `tables/` | figure/table generators, outputs, input manifests | presentation |
| `venue/` | template, requirements, checklist guide, format checker (`venue/tools/check_paper.py`) | venue |

## Reproduction notes
**Environment.** Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, pyarrow 26.0.0, scikit-learn 1.9.1 (fitter validation only); CPU only, no network needed once the data are in place. Exact versions per run: `results/*.meta.json`. Paper build: TeX Live with `latexmk -pdf` (in `paper/`).

**Data** (stay outside the repository in `data/`; loaders in `code/btlib/data.py` refuse a file with a wrong sha256; set `BT_DATA` to the directory; if unset, `<repository root>/data` is used):
| file | source and version | sha256 | licence |
| --- | --- | --- | --- |
| `arena55k.csv` | HF `lmarena-ai/arena-human-preference-55k` @18c298340948c0e7f7727399fd459cca6ce0ca6f, `train.csv` | 0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2 | apache-2.0 |
| `mt_human.parquet` | HF `lmsys/mt_bench_human_judgments` @f7d2896d2cc5d80f8b55c2bbc722613555233c25, `data/human-00000-of-00001-25f4910818759289.parquet` | 4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769 | cc-by-4.0 |
| `mt_gpt4.parquet` | same repository and revision, `data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet` | 57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71 | cc-by-4.0 |
| `nbaallelo.csv` | github `fivethirtyeight/data` @4c1ff5e3aef1816ae04af63218015066e186c147, `nba-elo/nbaallelo.csv` | d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc | CC-BY-4.0 |

Synthetic data appear only in the control paragraph of the paper (Section 4.2, synthetic Bradley-Terry data with the real pair counts, code `code/s2_controls.py`); they are labelled synthetic there and carry `synthetic=True` / `kind=syn` in `results/controls.csv` and `results/control_comparison.csv`. All other numbers are from real data.

**Key counts.** MT-Bench matching uses 1,814 unordered (question, turn, model pair) keys present in both files (headline) and 1,232 order-sensitive keys that also match in presentation order (robustness); `code/REPRODUCE.md` explains the two counts. `results/s3_uncert.csv` holds the per-resample budgets of the dataset-level bootstrap (resamples of all comparisons, each searched anew); `results/s5_budget_intervals.csv` summarises them into the intervals of Table 2.

**Seeds, commands, run times.** Seeds per experiment, the command table (groups A-E and collection) and measured wall times are in `code/REPRODUCE.md` and `results/runtimes.csv` (`bash code/run_all.sh <group>`; about 10 wall-hours when the steps run one after another, at most about 20 CPU-hours; dominated by the NBA-season adversarial searches and the second-round steps). Random perturbations use 200 seeds per size, the bootstrap 1000 resamples, regression cluster bootstraps 2000, dataset-level intervals 100-200 resamples (`results/s3_uncert.csv`).

**Paper artifact -> script** (numbering as in the paper; the generated files keep the figure-plan names given here).
| paper artifact | script | inputs | output |
| --- | --- | --- | --- |
| all numbers in the text | `paper/quoted_numbers.py` | `results/*.csv` (every file named in the script's `load` calls: `adv_budgets`, `random_survival`, `random_tau`, `regression_coef`, `method_validity*`, `control_comparison`, `ablations_summary`, `additions`, `matched_*`, `s2_matched_agreement`, `s3_uncert`, `s5_*`) | `paper/quoted_numbers.tex` |
| Table 1 (datasets) | `tables/table1_datasets.py` | `results/dataset_summary.csv` | `tables/table1_datasets.tex` |
| Table 2 (verified removal budgets, with dataset-level intervals) | `tables/table0_headline.py` | `results/adv_budgets.csv`, `s5_budget_intervals.csv` | `tables/table0_headline.tex` |
| Table 3 (removal, addition, relabelling, constrained adversary) | `tables/table5_additions.py` | `results/additions.csv`, `s5_constrained.csv` | `tables/table5_additions.tex` |
| Table 4 (appendix, regression) | `tables/table2_regression.py` | `results/regression_coef.csv` | `tables/table2_regression.tex` (full set: `table2b_regression_full.tex`) |
| Table 5 (appendix, search vs. heuristics) | `tables/table3_method_validity.py` | `results/method_validity.csv` | `tables/table3_method_validity.tex` |
| Table 6 (appendix, exhaustive validation) | `tables/table3b_exhaustive.py` | `results/method_validity_exhaustive.csv` | `tables/table3b_exhaustive.tex` |
| Table 8 (appendix, estimator variants) | `tables/table7_estimator.py` | `results/s5_estimator.csv`, `s5_estimator_rank.csv` | `tables/table7_estimator.tex` |
| Table 7 (appendix, published-output claims and z < 1 shares) | `tables/table6_published.py` | `results/s5_published_summary.csv`, `s5_z_shares.csv` | `tables/table6_published.tex` |
| Table 9 (appendix, ablations) | `tables/table4_ablations.py` | `results/ablations_summary.csv` | `tables/table4_ablations.tex` |
| Figure 1 (leaderboards) | `figures/fig1_leaderboards.py` | `results/base_*.csv` | `figures/fig1_leaderboards.pdf`; NBA variant `fig1b_nba.pdf` (not in the paper) |
| Figure 2 (survival under removal) | `figures/fig2_survival.py` | `results/random_survival.csv`, `random_tau.csv`, `adv_budgets.csv` | `figures/fig2_survival_remove.pdf`; label-flip variant `fig2_survival_flip.pdf` and grid variants `fig2b_*` (not in the paper) |
| Figure 3 (budget vs. margin; panel b: first-order estimate) | `figures/fig4_budget_vs_z.py` | `results/adv_budgets.csv`, `regression_coef.csv`, `s5_khat.csv` | `figures/fig4_budget_vs_z.pdf` |
| Figure 4 (controls) | `figures/fig6_controls.py` | `results/control_comparison.csv`, `s5_control_summary.csv` | `figures/fig6_controls.pdf` |
| Figure 5 (appendix, window sweep) | `figures/fig8_window.py` | `results/s5_window_*.csv` | `figures/fig8_window.pdf` |
| Figure 6 (appendix, noise-equivalent budget) | `figures/fig7_noise.py` | `results/adv_budgets.csv`, `s5_noise.csv` | `figures/fig7_noise.pdf` |
| Figure 7 (appendix, budgets by rank) | `figures/fig3_budgets.py` | `results/adv_budgets.csv` | `figures/fig3_budgets.pdf` |
| Figure 8 (appendix, matched labeller) | `figures/fig5_matched.py` | `results/matched_pairs.csv` | `figures/fig5_matched.pdf` |
| out-of-sample table, restarts table (not in the paper; numbers quoted in the text) | `tables/table8_oos.py`, `tables/table9_restarts.py` | `results/s5_oos_summary.csv`, `s5_restarts_summary.csv` | `tables/table8_oos.tex`, `tables/table9_restarts.tex` |
| analyses | `code/s*.py` | see the command table in `code/REPRODUCE.md` | `results/` |

`python3 figures/make_all.py --results results --out .` (run from the repository root) regenerates all figures and tables.

Build the paper: `cd paper && python3 quoted_numbers.py && latexmk -pdf main.tex`; format check: `python3 venue/tools/check_paper.py paper/main.pdf paper`.

**Independence note.** The task statement says an earlier published paper studies this question. It was deliberately not searched for, read or cited, nor was any paper citing or discussing it; no accidental encounter is known. The paper does not refer to it.

**Failed / abandoned / unfinished.** See `code/REPRODUCE.md` (an earlier stage-1 run on a development tree was discarded and rerun from the committed tree; a non-optimal greedy led to the polishing step). Cut by plan: LLM-judge labels on Arena battles (undeclared licence), Arena 140k, WebDev Arena.

**LLM assistance.** All positions of this study (planning, code, analysis, writing, review) were AI agents based on Claude models; every reported number is computed by the shipped code. MT-Bench GPT-4 judgments are an analysed dataset, not part of the method.

**Excluded-content disclosure.** The paper listed as item 8 of the starter reading list, and anything citing or discussing it, was not searched for, opened or read by this position. `code/REPRODUCE.md` records the same for the analysis. Incident log: none known for this position.
