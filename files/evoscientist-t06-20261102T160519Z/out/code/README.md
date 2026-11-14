# Fixed-schedule pairwise leaderboard audit

## 交付与核心结论

- `paper.pdf`：完整论文，采用 **NeurIPS 2026 官方 Main Track 匿名提交模式**；正文 7 页，参考文献、附录与已填写的 16 项 checklist 另计。
- `paper/main.tex`、`appendix.tex`、`checklist_filled.tex`、`references.bib`：LaTeX 源文件；官方样式及来源证据在 `paper/template/`。
- `reproducibility.zip`：复现代码、文档、论文源文件和实际运行结果；**不含原始数据、论文下载文件、虚拟环境或重复实验副本**。
- `final_report.md`：中文结果摘要与证据范围；`artifacts/paper_self_review.md` 是保留的投稿风险自审，不是接收保证。

结果是**足以成功的实例预算，不是全局最小预算**。固定原始第一/第二名、固定比较安排和 ridge=1 的 BT 拟合后，Arena、MT 人类、MT GPT-4、NBA 2013/2014/2015 分别找到 2、46、61、3、4、8 条不同胜负记录翻转即可使原第二名严格超过原第一名。Arena 原两者本已接近：200 次经验重抽样中仅 110 次保持原方向，去除平局即改变次序，故不能表述为“两票推翻一个统计上确立的赢家”。评测设计的因果优劣未被识别。

## 1. Environment and one-command reproduction

Tested Python **3.11.15**, Linux x86_64, visible Intel Xeon Gold 6230 CPU. Numerical computation is sequential CPU-only, one BLAS/OpenMP thread; no GPU, training or paid API. Install system LaTeX (`pdflatex`, `bibtex`, `latexmk`, standard LaTeX packages including xurl) separately. Template bytes are already supplied, so paper compilation requires no template download.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock.txt
bash reproduce.sh
```

`requirements.txt` pins direct dependencies; `requirements.lock.txt` records the full **fresh replay environment**, including transitive packages. `artifacts/environment_freeze.txt` is the original working environment capture (it can include unrelated installed tools and is not the recommended installation input).

The driver downloads only task-authorized pinned data, verifies SHA256, prepares edge lists, runs tests, main experiments, supplement, report generation, numerical validation, LaTeX compilation and copies `paper/main.pdf` to root `paper.pdf`. It will overwrite numerical artifacts and measured timing fields with the new run. It does not rerun literature acquisition or the archived self-review. Raw files remain local under `data/raw/`; never add them to the submission archive.

## 2. Data access, units and versions

No login required at acquisition. Exact source URLs, bytes and all four checksums are in `data/manifest.json`. Script: `src/download.py`; actual source revision is embedded in each URL, never `main`.

| Local file | Source and fixed revision | License |
|---|---|---|
| `data/raw/arena.csv` | lmarena-ai/arena-human-preference-55k, `18c298340948c0e7f7727399fd459cca6ce0ca6f` | Apache-2.0 |
| `data/raw/mt_human.parquet` | lmsys/mt_bench_human_judgments, `f7d2896d2cc5d80f8b55c2bbc722613555233c25`, human split | CC-BY-4.0 |
| `data/raw/mt_gpt4.parquet` | same revision, gpt4_pair split | CC-BY-4.0 |
| `data/raw/nba.csv` | fivethirtyeight/data, `4c1ff5e3aef1816ae04af63218015066e186c147`, nba-elo/nbaallelo.csv | CC-BY-4.0 |

Arena uses all 57,477 votes/64 models; the >=100 appearance rule excludes none. Human MT uses 3,355 exported judge rows, GPT uses 2,400 exported pair-result rows (not underlying reciprocal API calls). Ties, including 380 inconsistent GPT results, are half-labels and never binary-flipped. NBA deduplicates `_iscopy==0`, selects each `year_id` separately, and includes regular season plus playoffs. No textual content is required for fitting. One edit = one distinct original decisive exported row/game; no fabricated reciprocal rows or double-counted ties. A game flip is a counterfactual recorded-outcome modification, not an error accusation.

For local-data/offline reruns, skip the downloader and run commands below; `validate.py` checks the existing manifest and original files. `download.py` uses the pinned HF metadata API to discover the two parquet paths when explicitly invoked, even if local files exist. README/LICENSE verification records are in `artifacts/compliance/`; full attribution/reuse boundaries in `THIRD_PARTY_NOTICES.md`.

## 3. Exact staged commands

Run from the unpacked root (paths also resolve from the scripts' own location):

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$PWD/src"
python src/download.py                    # network: allowed data only
python src/prepare.py                     # raw -> data/processed + artifacts/eda.csv
python -m pytest -q tests                  # seven tests
python src/run.py --repeats 100 --bootstrap 200
python src/supplement.py                   # MUST precede report.py
python src/report.py
python src/validate.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
cp paper/main.pdf paper.pdf
```

`report.py` needs main-run and supplementary CSVs, not just `run.py`. It generates eight tables, three vector PDF/PNG figures and `paper/numbers.tex`. `MainFitCount` is only the instrumented primary BT-object count, not total project optimization calls; `MaxGradient` is a maximum.

### Config and seeds
- Objective: sum logistic loss + `lambda/2 * ||theta||²`, lambda=1; all observations, no supervised train/test split or predictive claim.
- Ties `y=.5`, decisive reversal `y -> 1-y`; every selected original row at most once; strict margin `< -1e-7`.
- Frozen initial positive flip benefits; powers-of-two bracket + prefix bisection; cap floor(20% decisive rows). Verify returned k and k−1. **Not necessarily earliest prefix and never certified global minimum**; failure is unresolved, not robustness through the cap.
- Target: original fitted leader versus original runner-up. Reversal dethrones original leader; it need not put the runner-up at overall rank one.
- Control seeds `20261102+j`, bootstrap `7300+j`, dataset order Arena / MT human / MT GPT / NBA2013 / NBA2014 / NBA2015, j=0..5.
- 100 random subsets per control and budget. Pointwise Wilson 95% Monte Carlo intervals, not simultaneous significance tests. Uniform, incident-uniform, incident-positive-benefit, and edge-count-matched controls at the same witnessed k.
- 200 empirical row (Arena/NBA) or question-cluster (MT) resamples, **changing schedules**, fixed selected target names. Percentile summaries are descriptive, not selection-valid population/minimum-budget CIs. Auxiliary first-30 witness checks are positive-margin-conditioned and refer to resampled slots, including repeated original IDs.
- Matching seeds 100..119. Exact 1,232 **ordered** question/pair/turn cells for MT; choose one human judge row per cell (20 choices), GPT run once. Arena induced full-fit top-six pool 3,222; sample 2,400 without replacement, 20 distinct row-set hashes. Overlapping subsamples are not independent populations.
- Fixed-target sensitivities lambda .1 and10, dropping ties, excluding inconsistent GPT results, NBA home coefficient; penalty includes home coefficient. Reselected-target `ablations.csv` is retained separately, not used as evidence of same-claim sensitivity.

## 4. Runtime and resource evidence

Accepted main run: **42.03 s**; supplementary comparator/original-row verification: **3.46 s**. Fresh pinned virtual environment / relocated-source main replay: **41.26 s**, **301.87 MiB child-process peak RSS** (Linux `resource.getrusage`; JSON in `artifacts/resource_replay.json`). Seven tests also pass there. These are actual single-thread container measurements, not guarantees for all CPUs. Allow a few minutes for numerical reproduction on a modest CPU, plus network/dependency/LaTeX time. Raw data total about 204 MB; no 140k release was downloaded. Full project wall/CPU time, source reading, failed setups and paper drafting were not completely metered. Earlier corrected and failed runs are logged rather than presented as part of the 42 s benchmark.

### Independent environment/relocation replay

The delivered `artifacts/validation.json` records comparison of **13 deterministic CSVs** with the completed replay, relative tolerance1e-8 / absolute1e-9; runtime/metadata naturally differ. To repeat without overwriting accepted artifacts:

```bash
mkdir -p reproduction_check/{data,artifacts,paper}
cp -r src tests reproduction_check/
# Use an ABSOLUTE link target; a relative target is relative to the link's directory.
ln -s "$PWD/data/raw" reproduction_check/data/raw
python3.11 -m venv reproduction_check/venv
reproduction_check/venv/bin/python -m pip install -r requirements.lock.txt
python src/resource_replay.py --root reproduction_check \
  --python "$PWD/reproduction_check/venv/bin/python" \
  --output artifacts/resource_replay.json
python src/validate.py --replay reproduction_check
```

Use a previously absent `reproduction_check/` directory or remove only your own old replay first. The raw snapshot is shared; this is execution reproducibility, not independent data collection or an independently implemented solver. The final source includes validation/reporting refinements after the numerical replay; deterministic numerics were not changed by those documentation/plotting refinements.

## 5. Every table and figure -> generating code

All rendered numerical tables/figures use **`src/report.py`**, not hand-entered table values. Main experiments come from `run.py`; extra ablations/comparators from `supplement.py`.

| Paper output | Generated file | Result inputs under `artifacts/` |
|---|---|---|
| Table1 primary witnesses | `paper/tables/main.tex` | `baseline.csv`, row evidence `witness_rows.csv` + `witness_verification.csv` |
| Figure1 budgets + margins | `paper/figures/budget_and_margin.pdf` | `baseline.csv`, `uncertainty.csv` |
| Table2 controls | `paper/tables/controls.tex` | `controls.csv`, summarized `control_summary.csv` |
| Table3 matched support/size | `paper/tables/matched.tex` | `matched.csv`, `matching_protocol.json` |
| Table4 data audit | `paper/tables/eda.tex` | `eda.csv` |
| Table5 empirical resampling | `paper/tables/bootstrap.tex` | `uncertainty.csv`, `bootstrap_summary.csv` |
| Figure2 dose responses | `paper/figures/dose_response.pdf` | `random_curves.csv`; nominal grid, integer budgets recorded |
| Figure3 adjacent pairs | `paper/figures/adjacent_pairs.pdf` | `adjacent.csv`, `adjacent_summary.csv` |
| Table6 frozen-target ablations | `paper/tables/fixed_ablations.tex` | `fixed_target_ablations.csv` |
| Table7 flip/deletion comparison | `paper/tables/methods.tex` | `method_comparison.csv`, `baseline.csv` |
| Table8 runtimes | `paper/tables/runtime.tex` | `runtime.csv`, overall `run_metadata.json` |

Same-basename PNGs are supplied for inspection; paper uses vectors. `src/bt.py` contains estimator/search; `tests/test_bt.py` checks symmetry, two-player stationarity, influence finite differences, orientation/duplication invariance, tiny exhaustive flips, home design, strict tie semantics. `src/validate.py` independently reconstructs row-based primary fits, checks data hashes, ratios, matching IDs, repeat counts, citation keys, source markers and optional replay CSV agreement. `src/resource_replay.py` measures a separate run. No dependency on private files, paid services, installed agent skills or persistent memory for reproduction.

## 6. Failures, interpretation and independence

Read `experiment_log.md` for all material departures: initial missing requests dependency; unrecognized GPT inconsistent-tie label halted parsing; invalid whole-pool pseudo-replicates were caught and replaced; argmax tie metric corrected; first replay setup failed because external time utility was absent and a symlink was relative, then fixed with Python resource measurement and an absolute symlink. Supplement and report ordering is explicit. Old audit/reflection files intentionally preserve their historical diagnoses, not claims that the corrected artifact still has those defects.

Literature access was bounded to five explicitly authorized sources; only actually read sources are cited. No open keyword search, citation-following, prohibited-paper identification, or access to an identified prohibited source occurred. `artifacts/literature_notes.md` records sources, reading extent and permitted access log. Official conference template/policy and pinned dataset license pages were read separately to meet task requirements; their references/further-reading links were not followed. No prohibited-source incident was identified. A subagent memory preflight returned an existing project-summary snippet, not a fetched paper, and was not used as code-audit evidence.

This is a completed empirical audit and reproducibility package, **not a guarantee of NeurIPS acceptance**. The independent self-review finds substantial residual main-conference novelty risk. The scientific contribution is bounded evidence and accounting; no global optimum, causal design superiority, real label-error rate, or live attack access is claimed. No requested experiment is silently fabricated: source limitations and exploratory bootstrap-slot semantics remain explicit.

LLM assistance covered planning, source synthesis, direct code implementation, auditing, analysis and drafting; no new judging labels or paid API requests. Original code/documentation license: `LICENSE`; third-party terms: `THIRD_PARTY_NOTICES.md`.
