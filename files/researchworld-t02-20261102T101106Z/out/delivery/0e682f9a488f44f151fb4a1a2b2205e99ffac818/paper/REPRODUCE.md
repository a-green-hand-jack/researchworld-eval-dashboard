# Reproduction document (paper-repo)

Status: complete for the delivered version. All sweeps listed in `experiments/README.md` finished; what was planned but not run is listed in section 8.

Repository layout: `experiments/` (trainer, sweep runner, analysis; owner experiment-repo), `results/` (CSV/JSON aggregated from the run logs), `figures/` (figure and table generators and outputs; owner figtab-repo), `paper/` (LaTeX source, PDF, checklist, this file), `venue/` (NeurIPS 2026 rules and unmodified template).

## 1. Environment
- Host: Debian 12, Intel Xeon Gold 6230 @ 2.1 GHz (40 logical CPUs on the shared host; each job single-threaded, `torch.set_num_threads(1)`; sandbox limit 2 CPUs / 4 GB), no GPU.
- Python 3.11.2; torch 2.14.1+cpu, numpy 2.4.6, pandas 3.0.6, scipy 1.17.1 (`results/versions.txt`); matplotlib 3.11.2 for the figures.
- Paper build: TeX Live 2022 (pdfTeX 1.40.24), `cd paper && latexmk -pdf main.tex`; template NeurIPS 2026 (`venue/template/SOURCE.md`, unmodified `neurips_2026.sty`).

## 2. Data
No download, account, license or version to pin. For a prime `p` all `p^2` pairs `(a,b)` are enumerated in memory and labelled `(a op b) mod p` (`op` in add/sub/mul; `experiments/grok.py:make_data`). Primary setting `p = 53`, add. A fraction `f` of the pairs, drawn by a random permutation seeded with `10000 + seed` (or `--split_seed`), is the training set; the rest is the validation set, evaluated in full.

## 3. Seeds
Seeds 0-4 per cell (a cell = one configuration). Seed `s` controls initialization (`torch.manual_seed(s)`) and, unless `--split_seed` is given, the train/validation split. Seed lists per sweep: `experiments/sweep.py`. Full-batch training has no data-order randomness.

## 4. Commands and run time
- One run: `python experiments/grok.py --arch tf --width W --p 53 --op add --frac F --wd WD --lr 1e-3 --seed S --max_steps 30000 --out FILE`.
- A sweep shard: `cd experiments && python sweep.py run NAME SHARD NSHARDS --procs 2`; aggregation: `python analyze.py <sweeps>`; figures/tables: `cd figures/src && python make_all.py` (see `figures/README.md`).
- Measured run time: each run JSON stores `wall_s`. experiment-repo reports 15-90 min per 30k-step run on one core of the shared host (load about twice the core count); runs that generalise stop 500 steps later. Total measured compute: about 59 run-hours of single-core wall time over the 169 run logs (sum of `wall_s` over `results/*_runs.csv`) (`experiments/README.md`, sum of `wall_s`); the figures, tables and statistics take minutes. The paper build takes under a minute.

## 5. Artifact map: table/figure -> script -> inputs
Numbering follows `paper/main.tex`. All figure/table scripts are in `figures/src/` (`cd figures/src && python make_all.py` regenerates all of them; inputs `results/*_{runs,cells}.csv`, `results/*_stats.json`, `experiments/runs/<sweep>/*.json`). The `.tex` tables are included by `main.tex` from `figures/tables/`.

| Paper item | Script | Inputs |
|---|---|---|
| Fig. 1 `width_trends_main` | `fig_width_trends.py` | `main_runs.csv`, `main_cells.csv`, `main_stats.json` |
| Table 1 `t1_main` | `tables.py` | `main_cells.csv`, `main_stats.json` |
| Fig. 2 `curves_main` | `fig_curves.py` | `experiments/runs/main/*.json` |
| Fig. 3 `wd_alpha` | `fig_wd_alpha.py` | `wd_*`, `wd0_*`, `alpha_*`, `main_*` |
| Fig. 4 `frac` | `fig_frac.py` | `frac_*`, `main_*` |
| Table 2 (verdicts) | hand-compiled in `main.tex` from `main_stats.json`, `sens_stats.json`, `mech_stats.json`, `wd_stats.json`, `frac_cells.csv`, `wd0_stats.json`, `lrscale_stats.json`; every entry is also in Tables 4-5 (`t3_trend`, `t4_mechanism`), which are generated | see left |
| Fig. 5 `grok_survival_main` | `fig_grok_survival.py` | `main_*` |
| Fig. 6 `regimes_main` | `fig_regimes.py` | `main_*` and the other sweeps' `*_runs.csv` |
| Fig. 7 `mechanism` | `fig_mechanism.py` | `mech_stats.json`, `mech_alpha_cells.csv`, run JSONs |
| Fig. 8 `budget` | `fig_budget.py` | `main_runs.csv`, `long_runs.csv`, `sens_stats.json` |
| Fig. 9 `scope` | `fig_scope.py` | `mlp_*`, `mul_*`, `lrscale_*`, `lrscale2_*`, `wd_*`, `frac_*`, `main_*` |
| Table 3 `t2_scope` | `tables.py` | scope sweeps' `*_cells.csv` |
| Table 4 `t3_trend` | `tables.py` | `*_stats.json` |
| Table 5 `t4_mechanism` (total-L2 and RMS-norm regressions) | `tables.py` | `mech_stats.json`, `verdicts.json` |
| Table 6 `t5_wd_alpha` (wd slope, init-scale effect) | `tables.py` | `mech_stats.json`, `verdicts.json` |

Statistics in `results/` come from `cd experiments && python analyze.py main frac wd wd0 alpha lrscale lrscale2 long mul mlp thr1 && python analyze_mech.py && python analyze_sens.py && python verdicts.py` (fixed bootstrap seed 0; `verdicts.py` adds the `verdict` keys from the negligibility bands set in story-repo `plan/VERDICTS.md` after the results were seen, and writes `results/verdicts.json`, including the per-parameter RMS-norm regressions and the A3 Wilson contrasts). Numbers quoted in the paper text are read from these files; the text is typed by hand and the verdict table (Table 2) is the one place where numbers are copied by hand, which is why every entry can be matched against the generated Tables 4-5.

## 6. Provenance
Each run JSON stores its configuration, torch version, log and wall time; `results/` is produced from them by `experiments/analyze.py`. The final results files in `results/` were last changed at commit `1b50623` (experiment-repo delivery, PR #9); the figures and tables at `e5c47d3` (PR #11) plus later generator fixes. Results and run logs are kept in the repository. The first pilot (embedding init N(0,1)) is not in `runs/`; no reported run used it (`experiments/README.md`).

## 7. Withheld-paper exposure
The task withholds a published paper on this question and anything discussing it. paper-repo: none encountered; literature use is limited to the eleven starter references, whose title/author/year were checked against arXiv metadata (abstracts read; the full texts of references 4-8 were not read), and no search used model size/scale + grokking terms. No other position recorded an exposure in its repository, wiki or issues at the time of writing; the venue document (`venue/venue.md` section 5) states the rule.

## 8. Unfinished or failed runs
All 169 launched run logs finished (30 main, 20 wd, 20 alpha, 22 frac, 3 wd0, 10 lrscale, 9 lrscale2, 6 long, 30 mlp, 6 mul, 13 thr1); none failed. The 13 `thr1` runs are deterministic re-runs of grokked `main` runs continued past the crossing, so there are 156 distinct runs. Planned or discussed but **not run** (reported as not run in Section 5 of the paper): `splitfix` (split-seed vs init-seed separation), `p=113` anchor runs, a second prime, init multiplier below 0.5, a finer training-fraction grid, depth, optimizer and batch-size variation, and a norm-matched comparison (not achievable with multipliers 0.5, 1, 2). `mul` has 2 widths x 3 seeds; `wd0` and `lrscale2` have 3 seeds (`lrscale` 5 seeds at widths 32 and 128; `lrscale2` covers widths 16, 64, 256). The exact 1.0-threshold re-runs cover widths >= 64 only. 30k-step cells at widths 16 and 32 are right-censored (reported with the 100k `long` check).

## 9. LLM/agent assistance
The studied models are small transformers/MLPs trained on synthetic data; no LLM is part of the method. The code, analysis and manuscript were produced by LLM-based agents working as separate roles under the human-set task; all numbers come from the shipped runs.

## 10. Build record
Built PDF: 17 pages in total; main text (including figures, through the conclusions) ends on page 7 and references start there, within the 9-page limit; the checklist and appendices follow. Template version: NeurIPS 2026 (`venue/template/SOURCE.md`).
