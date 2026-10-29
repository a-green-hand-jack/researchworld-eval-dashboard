# 成对比较排行榜稳定性：论文与复现材料

论文 **How Small Is a Small Edit? Exposure, Uncertainty, and Matched Judges in Pairwise Leaderboard Audits** 使用未经修改的 **ICML 2026 官方模板**。正文不超过 8 页，含参考文献、附录、影响声明、AI 使用披露及已填写的研究/复现检查清单。ICML 2026 官方 CFP 没有要求在论文内附 NeurIPS 格式的 checklist，因此附的是明确标注的研究检查清单。

- 论文 PDF：`paper.pdf`（同 `paper/main.pdf`）
- LaTeX 源：`paper/main.tex`、`paper/references.bib`、`paper/generated/`，官方样式及原始模板包在 `paper/`、`paper/vendor/`
- 完整代码：`src/`；一键复现：`reproduce.sh`
- 数据来源、版本、校验和：`data/manifest.json`、`data/PROVENANCE.md`
- 实测结果与日志：`results/`；四张图的 PDF 与高分辨率 PNG：`figures/`
- 研究预案及变更：`notes/protocol.md`、`notes/research_log.md`
- 文献访问边界及实际阅读记录：`notes/access_log.md`
- 分发包：`submission.zip`，**不包含原始或预处理数据、虚拟环境或下载的文献 PDF**。

研究比较了众包投票、专家判断、GPT-4 裁判和三个 NBA 常规赛季。所有报告的数字均来自实际执行。删除证据是达到翻转的一组可行改动，**不是最优攻击或最少改动的证明**；未找到证据也不等于证明稳健。跨数据集差异是描述性比较，不用于推断裁判质量的因果效应。

## Environment

Tested with Python **3.11.2**, a standard Linux CPU, one BLAS/OpenMP thread, and TeX Live 2022 (`latexmk`, `pdflatex`, `bibtex`). All installed Python packages and exact versions are pinned in `requirements.txt`. NumPy/SciPy implement CPU dense Newton solves; pandas/PyArrow load the public files; Matplotlib generates conventional scientific plots. PyMuPDF checks and renders the compiled artifact. No GPU, account, API key, paid service, or new model judgments are required.

## Full reproduction

From this directory:

```bash
bash reproduce.sh
```

This creates `.venv`, installs the pinned environment, downloads frozen public data to `data/raw/`, verifies the supplied SHA-256 hashes, preprocesses, checks the scientific core, runs every experiment and control, generates all paper figures/tables, compiles, and validates `paper.pdf`. The download script uses the Python standard library, not an external dataset-loading service. If the exact environment is already installed:

```bash
AUDIT_SKIP_INSTALL=1 bash reproduce.sh
```

An Internet connection is needed only for installation and the listed public datasets. Total raw dataset downloads are about 204 MB. Raw data stay under `data/`; they are not included in the distribution archive. Existing raw files are hashed and reused. Do not publish the `data/raw/` or `data/processed/` directories as part of the code package.

On this host the primary and control scripts each took roughly 20–30 seconds with one thread; exact measured durations are in `results/run_metadata.json` and `results/controls_metadata.json`. Allow **2–10 minutes for analysis, plots, and compilation on a typical CPU**, plus network/installation time (often several minutes). This range is a practical expectation, not a claimed measurement on other hardware. The one-week budget was an upper limit, not the actual runtime. No described experiment remains pending.

Paper-only compilation, using the included generated figures/tables:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
cp main.pdf ../paper.pdf
```

The official ICML 2026 template is already included; it need not be fetched during reproduction. The original zip URL and checksum are in the access log. We use high-resolution raster renderings of plots inside the paper so its fonts are all embedded Type 1; standalone vector PDFs of each plot are supplied separately.

## Individual commands

All commands run from the project root; set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`.

```bash
.venv/bin/python src/download.py
.venv/bin/python src/prepare.py
.venv/bin/python src/test_core.py
.venv/bin/python src/experiment.py --bootstrap 400 --random-reps 200
.venv/bin/python src/controls.py
.venv/bin/python src/uncertainty.py
.venv/bin/python src/report.py
# Compile as above, then:
.venv/bin/python src/verify.py
```

`src/experiment.py` overwrites combined `attacks.csv` with the requested dataset list, so use its default complete list for reproducing the paper. `controls.py` includes independent row-level replay of all saved successful attacks.

## Statistical and algorithmic settings

- Master seed: **20261028**. Seeds are explicit, not process-dependent hashes.
- Primary bootstrap seed: master + sum of Unicode code points of dataset name. Arena resamples rows, MT resamples 80 questions, NBA resamples game dates. 400 replicates, percentile 95% pointwise intervals.
- Random-edit seed: master + 701 + name code-point sum; 200 repetitions per dataset/mechanism, nested budgets 0.1%, 0.5%, 1%, 2%, 5%. Floored integer budget, at least one record. Reversal draws from decisive records only; all-record `N` remains its denominator.
- Paired matched-question bootstrap: master + 2001; 300 replicates. Identical resampled question multiplicities for the two judges. Expanded bootstrap records retain integer edit units. The original leading pair stays fixed; already reversed draws receive zero edit cost. Cap 20%, disclosed exploratory extension.
- Annotation selection: initial pandas seed 20261028; 50 alternate selections generated from master + 3001. Uniformly select one **actual** human annotation per common question/turn/pair unit.
- Size control: master + 4001; 50 subsamples of 1,200 records per source. Missing contestant exposures are retained and reported; this is not an equal-information comparison.
- Approximation checks: master + 5001, reinitialized per source; 100 boundary draws with replacement per mechanism; each evaluated at all five budgets.
- Primary estimator: sum of fractional-outcome logistic losses; symmetric ridge `1e-6`, centered scores; fixed initial adjacent boundaries; row-level deletion or decisive-label reversal.
- Primary attack cap 5% of `N`, fixed influence ordering, full refits at tested prefixes, geometric expansion factor 1.6 and bracket bisection. A returned witness gap must be below `-1e-8`. A witness is an upper bound on minimum edits; neither bisection monotonicity nor global optimality is assumed.
- Numerical tolerance: Newton stopping threshold `2e-7 + 1e-11 * total_weight`; reject fits with maximum absolute gradient exceeding `2e-5`. Exact mathematical gauge is solved with the `11'/M` projector. Tested positive-curvature ridge values are `1e-6`, `1e-4`, `.01`, `1`.
- No attack ever edits the conversation text, model identity, or schedule of a reversal. Deletion changes the schedule by removing whole records.

## Every figure and table

All presentation artifacts are generated by **`src/report.py`**, with input files listed below. No spreadsheet editing or manual numeric substitution is required. `paper/generated/numbers.tex` supplies additional numeric prose macros. Filenames are stable and correspond to the paper's current order.

| Paper artifact | Generated file | Experimental source |
| --- | --- | --- |
| Table 1: data | `paper/generated/data.tex` | `prepare.py` → `results/data_summary.csv` |
| Table 2: leading pairs | `paper/generated/leaders.tex` | `experiment.py` → `results/attacks.csv` |
| Table 3: boundary coverage and separation | `paper/generated/boundaries.tex` | `attacks.csv`, `uncertainty.py` → `simultaneous.csv` |
| Table 4: matched judges | `paper/generated/matched.tex` | `controls.py` → `matched_extended.csv`, `paired_bootstrap.csv` |
| Appendix Table 5: ablations | `paper/generated/ablations.tex` | `controls.py` → `ablations.csv` |
| Appendix Table 6: complete random edits | `paper/generated/random_full.tex` | `experiment.py` → `random.csv` |
| Figure 1: witness profiles | `figures/profiles.pdf` / `.png` | `attacks.csv` |
| Figure 2: random edits | `figures/random.pdf` / `.png` | `random.csv`; Wilson / mean Monte Carlo intervals |
| Figure 3: paired bootstrap contrast | `figures/matched.pdf` / `.png` | `paired_bootstrap.csv` |
| Appendix Figure 4: approximation error | `figures/approximation.pdf` / `.png` | `controls.py` → `approximation.csv` |

`ranking_<dataset>.csv` contains every baseline participant's score, exposure, rank, and pointwise bootstrap score interval. `attacks_<dataset>.csv` records every tested boundary, kind, and scope; `trace_<dataset>.csv` contains tested prefix sizes and exact refit gaps. `witnesses_<dataset>.npz` saves **zero-based indices in the canonical processed dataset** for each successful prefix; `data/processed/<dataset>.npz` includes the original frame index as `row_id`. For Arena this is a zero-based CSV row; for NBA it is the original CSV row of the `_iscopy=0` observation; for matched MT it indexes the deterministic `mt_matched_units.csv`. Empty witness arrays mean no witness found. These indices are not mutable live-platform identifiers.

`bootstrap_<dataset>.npz` saves bootstrap scores, fixed pairs, and baseline order. `witness_validation.csv` independently replays 535 successes from modified row weights/outcomes, including restricted attacks and auxiliary datasets. `deliverable_checks.json` records PDF page count, main-text page count, Type 1 fonts, checksum, connected primary graphs, maximum replay gradient, and validation count. `src/verify.py` also checks principal reported counts, the matched schedule, missing citations, and LaTeX overflow.

## Access restrictions, attribution, and limitations

No open-ended literature search, citation following, prior robustness code access, live-platform interaction, or forbidden-work identification was performed. The bibliography contains only six read, explicitly allowlisted starter papers. The exact reading scope and the unsuccessful original DOI access are disclosed in `notes/access_log.md`. Literature coverage is intentionally limited. The complete research and writing process used an autonomous Codex language-model agent; this is disclosed in the paper.

Own source code is provided under the MIT License (`LICENSE`). Official ICML style files retain their original notices. Data are attributable to the respective dataset authors and FiveThirtyEight under the source licenses listed in `data/PROVENANCE.md`; no ownership of their records is claimed. Conclusions, uncertainty assumptions, heuristic failures, and non-causal cross-design interpretation are discussed in the paper. A successful counterfactual edit set is not evidence that anyone actually altered the original data.
