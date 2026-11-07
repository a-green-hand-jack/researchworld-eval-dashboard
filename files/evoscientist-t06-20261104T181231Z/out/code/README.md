# Pairwise leaderboard stability: exposure-aware audit

**Paper:** `paper.pdf` (NeurIPS 2026 official main-track template, 8 content pages; references, technical appendix, and completed 16-item checklist follow). LaTeX entry: `paper/main.tex`.

## 研究结论（限于所分析的固定快照）
- 1% 全局预算下，静态影响排序选择的结果翻转在六个完整队列中的四个改变原始前两名次序；这不是随机噪声的发生率或最优攻击阈值。
- Arena 的574次全局编辑触及某个参赛者17.41%的比较；将每位参赛者的暴露限制为1%后，选中555次编辑，效应显著减小，但原始前两名本来接近打平。
- NBA每季13次全局编辑，与严格1%逐队约束下最多1/2/1次编辑不是等成本实验。未发现翻转不构成稳健性证明。
- 人类与GPT-4裁判的匹配分析按1,814个共同问题–轮次–模型对单元等权；单元翻转不等于单条原始投票翻转。队列设计差异不支持因果结论。

## Deliverables and reading order
- `paper.pdf`: compiled complete paper.
- `paper_sources.zip`: LaTeX, official style/checklist originals and provenance, completed checklist, generated tables and vector/PNG figures. No raw datasets or third-party research PDFs.
- `reproducibility.zip`: code, tests, pinned requirements, generated scientific artifacts/witnesses, paper source, README, and provenance/failure logs. No raw datasets, conversations, local dependency tools, or downloaded research PDFs.
- `final_report.md`: short report with measured results, limitations, and artifact map.
- `artifacts/self_review.md`: independent adversarial self-review; `artifacts/review_resolution.md` records subsequent fixes. The original review is not silently overwritten.
- `artifacts/claim_ledger.json`, `validation.json`, `pdf_audit.json`, `reproduction_run.json`: numerical provenance, witness replay, PDF compliance, and timed replay.

## Environment
Linux CPU, Python **3.11.15**. Numerical dependencies are exactly pinned in `requirements.txt`: NumPy2.4.6, SciPy1.17.1, pandas3.0.6, Matplotlib3.11.2, PyArrow26.0.1, pytest9.2.0, pypdf6.21.4. Transitive versions are recorded in `artifacts/environment_freeze.txt`.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
.venv/bin/python reproduce.py
```

PDF compilation additionally requires TeX Live (`pdflatex`, `latexmk`, BibTeX, standard `psnfss`/Courier, amsmath, microtype, hyperref, booktabs packages). Used pdfTeX1.40.26, TeX Live2025/dev/Debian. The official `neurips_2026.sty` is included unchanged. No custom bibliography style is required (`plainnat` is from TeX Live). `python reproduce.py --skip-paper` regenerates all measurements, figures and tables without TeX. A provided PDF is still included in the archives.

All source paths resolve relative to the extracted project, not `/work`. Commands work from any current directory. The complete driver verifies/downloads data, runs11 tests, executes all analyses, cold-replays338 deterministic witnesses, regenerates all tables/figures/checklist, compiles the paper, and rejects Type-3/unembedded fonts or a content-page overrun. It also compares scientific CSV SHA256s against any preexisting supplied outputs. PDF timestamps and measured runtimes may differ even when scientific CSVs are identical.

## Data acquisition and terms
Run `python src/download_data.py`. No login is required. Original records go in `data/`; never commit or redistribute that directory. Download size is about204MB in total. Only the required columns of conversations are parsed; prompts are hashed for clustering, not reproduced in outputs.

| Local file | Fixed source | License | Verification |
|---|---|---|---|
| `arena55k.csv` | `lmarena-ai/arena-human-preference-55k`, commit `18c298340948c0e7f7727399fd459cca6ce0ca6f`, `train.csv` | Apache-2.0 | SHA256 `0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2` |
| `mt_human.parquet` | `lmsys/mt_bench_human_judgments`, commit `f7d2896d2cc5d80f8b55c2bbc722613555233c25`, `data/human-00000-of-00001-25f4910818759289.parquet` | CC-BY-4.0 | SHA256 `4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769` |
| `mt_gpt4.parquet` | same MT commit, `data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet` | CC-BY-4.0 | computed SHA256 in `artifacts/data_manifest.json` |
| `nbaallelo.csv` | FiveThirtyEight/data commit `4c1ff5e3aef1816ae04af63218015066e186c147`, `nba-elo/nbaallelo.csv` | CC-BY-4.0 | SHA256 `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc` |

Exact public URLs are in `src/download_data.py` and `artifacts/data_manifest.json`. Hugging Face source pages: https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k and https://huggingface.co/datasets/lmsys/mt_bench_human_judgments . NBA: https://github.com/fivethirtyeight/data/tree/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo . Saved dataset cards and repository license verify terms in `artifacts/asset_terms/`. Creators are credited in the paper; derived outputs do not relicense their original data.

## Commands and artifacts
```bash
python src/download_data.py
python -m pytest tests -q
python src/run_experiments.py --bootstrap 300 --random 100
python src/run_stress.py --replicates 100
python src/bootstrap_sensitivity.py
python src/validate_results.py
python src/summarize.py
python src/plot_figures.py
python src/complete_checklist.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
python src/audit_pdf.py
```
For a branch smoke test use `--bootstrap 10 --random 3 --prefix smoke_` on the main runner and `--replicates 3 --prefix smoke_` on the stress runner. `--pilot` intentionally tests Arena only and skips ablations. Smoke/full CSVs are namespaced; deterministic witness sets share paths and are identical when the method/configuration is identical. Do not mistake smoke intervals for final evidence.

### Table and figure provenance
All numeric table TeX and `results_macros.tex` are generated by **`src/summarize.py`** from the indicated CSVs. All four numbered figures are generated by **`src/plot_figures.py`** as PDF+300dpi PNG.

| Paper item | LaTeX/image stem | Input measurements / originating script |
|---|---|---|
| Table1 | `data_baseline` | `baselines.csv`, `bootstrap.csv` / `run_experiments.py` |
| Table2 | `primary` | `perturbations.csv`, original bootstrap, `random.csv` / main runner |
| Table3 | `matched` | common-cell main-run measurements / `data.py`, main runner |
| Table4 | manual source-provenance table | fixed task commits, independently fetched dataset cards/LICENSE; **metadata, not an experimental estimate** |
| Table5 | `uncertainty` | original bootstrap + random subsets / main runner |
| Table6 | `controls` | count-matched/cap-feasible `controls.csv` / `run_stress.py` |
| Table7 | `feasibility` | `constraint_feasibility.csv` / `run_stress.py` |
| Table8 | `stress` | `ablations.csv`, `linear_integer.csv` / main+stress runners |
| Table9 | `specifications` | `ablations.csv` / main runner |
| Table10 | `semantics` | `judgment_semantics.csv` / stress runner |
| Table11 | `groups` | `question_groups.csv` / stress runner |
| Table12 | `grid_witness` | complete `perturbations.csv` budget grid / main runner |
| Table13 | `bootstrap_effects` | exploratory `bootstrap_sensitivity_summary.csv` / `bootstrap_sensitivity.py` |
| Figure1 | `exposure_response` | primary endpoint, original bootstrap, random subset summaries |
| Figure2 | `sensitivity_curves` | full-grid endpoint + random summaries |
| Figure3 | `approximation` | exact/linear reductions for8 cohorts,3 operations |
| Figure4 | `bootstrap_effects` | exploratory recomputed bootstrap + original endpoint/SD |

`artifacts/eda.json` records source exclusions, tie labels, judge composition, connectedness, participant degrees, and cluster counts. `mt_*_cell_provenance.csv` records aggregate membership/multiplicity. NPZ witness IDs use Unicode; loading never needs pickle. `src/validate_results.py` checks IDs, responses, unique indices, budgets/caps and cold-start fit margins. Fit diagnostics include all primary/supplementary/exploratory fit records, not merely successful displayed settings.

## Seeds, estimands and uncertainty
Base seed **20261104**. Main random seeds base+r; cluster draws base+100000+b; extra random controls base+200000+r. The fixed original top pair is never reselected inside a replicate. Ridge is0.1 on **sum** loss; sensitivity ridge0.01/1. Budgets0,.1,.5,1,2,5,10% use integer floors. Ties are0.5 and unchanged by reversal. Main random controls sample non-ties uniformly; strict-cap random controls are random-order greedy, **not uniform feasible subsets**.

Original bootstrap SD scales the continuous effect but is not a post-edit standard error. Original percentile intervals, conditional random-subset ranges, Wilson probability intervals and post-outcome exploratory procedure intervals are different quantities. No multiplicity-adjusted significance, causal evaluator effect, nonlinear optimum, exact minimum edit threshold, or robustness certificate is claimed. Full/matched MT cohorts overlap. Question/cell/game/vote edit costs are not interchangeable. See paper Sections3–6 and `artifacts/plan_deviations.md`.

## Runtime, resource budget and failures
The main experiment, extra controls and exploratory bootstrap each take seconds to tens of seconds on the supplied host; the complete CPU-only pipeline is on the order of minutes including validation/rendering/TeX, excluding network and initial installation. **Measured** stage times and cumulative child peak RSS are in `artifacts/reproduction_run.json` and typeset in `paper/resources.tex`; the clean extracted-archive check has a separate `artifacts/clean_reproduction_report.json`. Host-specific runtimes are not promises for other hardware. No large-data/GPU training is hidden. Original pilot, smoke, source/dependency recovery, failed NPZ replay and the blocked CPU-model inspection are documented in `experiment_log.md`, `artifacts/plan_deviations.md`, and `access_and_failure_log.md`.

## Access restrictions, literature and LLM disclosure
Only explicitly permitted starter PDFs were consulted, by exact IDs; no broad paper search, citation graph, related-work page or attempt to identify the unspecified prohibited work was used. Read sections/versions and all access failures are recorded in `artifacts/literature_notes.md` and `access_and_failure_log.md`. No recognized prohibited source was encountered outside that explicitly allowed set. Source PDFs remain in the working area for provenance but are not included in archives. Official template/ethics and exact data-card/license pages were also consulted; no further-reading links were followed.

An LLM research assistant (EvoScientist) substantially assisted design, reading, implementation, interpretation, and writing; its underlying model identity was not exposed. All empirical numbers come from actual supplied scripts; no new LLM labels or paid API calls were used. Human scholarly/legal review is still appropriate before a real conference submission. New code is MIT-licensed; other assets retain their original terms. This is an offline research audit, not authorization to manipulate live systems.
