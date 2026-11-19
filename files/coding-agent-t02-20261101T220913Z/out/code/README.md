# Model scale and grokking on modular addition — code, data and reproduction

Everything in the paper (`paper/main.tex`, `paper/main.pdf`) is produced by the code in this directory.
All data are synthetic and generated in memory (`code/grok.py:make_data`); nothing is downloaded.

## Layout
```
code/grok.py        data, models (1-layer transformer, MLP), AdamW training loop, seed-ensemble trainer
code/sweep.py       resumable parallel sweep runner (one JSON per run, existing files are skipped)
code/ana.py         loading runs, t_fit / t_gen / memorise-first labels, bootstrap helpers
code/fig_e*.py      analysis + figures + stats json for each experiment;  code/make_tables.py  LaTeX tables
exps/e*.py          experiment definitions (grids)           exps/run_rest*.sh  queueing helpers used while running
results/<exp>/*.json  raw per-run results incl. full learning curves (every 50 steps, every 10 before step 400)
tables/, figs/      csv/json/tex tables and pdf figures consumed by the paper
PREREG.md           hypotheses written before E1 results were inspected (+ clearly marked addendum)
paper/              LaTeX source (ICLR 2027 template), refs.bib, compiled main.pdf
```

## Environment
Python 3.11.2, `torch==2.15.0` (CPU), `numpy==2.4.6`, `scipy==1.17.1`, `matplotlib==3.11.2`, `pandas==3.1.0`
(`requirements_min.txt`; full freeze in `requirements.txt`). LaTeX: TeX Live pdflatex + latexmk, bibtex.
```
python3 -m venv venv && venv/bin/pip install -r requirements_min.txt
```
Hardware used: a container limited to **4 CPU cores** (cgroup quota; `nproc` reports 40). No GPU. Every run uses 1 thread;
sweeps run 4 worker processes (`sweep.run_grid(..., nproc=4)`). Change `nproc` if you have more cores.

## Seeds / data versions
`seed` (0..7 in E1; 0..2 or 0..3 elsewhere) seeds the model initialisation (`torch.manual_seed(seed)`) and the
train/validation split (`torch.Generator().manual_seed(10000+seed)`, random permutation of all p^2 pairs). The
data have no versions; they are the exhaustive table of (a+b) mod p (or a-b, a^2+b^2 for E6).
Runs are deterministic given seed and thread count up to floating-point summation order; the seed-ensemble
trainer used for the smallest widths in E3 is numerically equivalent to separate runs (checked in `code/test_ens.py`,
trajectories agree to float noise, which grows chaotically later in training).

## Commands, approximate cost (4 cores) and outputs
Measured single-process wall time summed over runs (inflated by CPU contention) in parentheses.
| step | command (from `code/`) | cost | produces |
|---|---|---|---|
| E1 width sweep (64 runs) | `python ../exps/e1_width.py` then `python fig_e1.py` | ~8 core-h | Fig. 1,2, Table 1, `tables/e1_*` |
| E2 optimiser clock (72 runs; baseline cells copied from E1) | `python ../exps/e2_clock.py; python fig_e2.py` | ~6 core-h | Fig. 4, Table 3, `tables/e2_*` |
| E3 capacity vs N (90 runs) | `python ../exps/e3_capacity.py; python fig_e3.py` | ~3 core-h | Fig. 3, `tables/e3_*` |
| E4 other axes (76 runs) | `python ../exps/e4_arch.py; python fig_e4.py` | ~11 core-h | Fig. 6, `tables/e4_*` |
| E5 rescaling (64 runs) | `python ../exps/e5_rescale.py; python fig_e5.py` | ~7 core-h | Fig. 5, Table 4, `tables/e5_*` |
| E6 other operations (32 runs) | `python ../exps/e6_ops.py; python fig_e6.py` | ~10 core-h | Table 2 |
| tables | `python make_tables.py` | seconds | `tables/*_tab.tex` |
| paper | `cd paper && latexmk -pdf main.tex` | | `paper/main.pdf` |
`PREREG.md` documents which hypotheses were fixed before looking at results. `exps/e1_width.py` must run before
`e2_clock.py` and `e5_rescale.py` (they reuse E1 seeds as the c=1 / baseline cells). The first E3 launch crashed at d=6
(not divisible by 4 heads); the script was changed to start at d=8 and re-run with completed runs cached.
`results/pilot2` is the one-seed exploratory pilot mentioned in the paper (`exps` has no script for it; it is
`exps/pilot2.py` (run with an older version of grok.py that logged every 100 steps; widths were run with 38 processes)).

## Figure/table → script
Fig.1 `fig_e1.py` (e1_curves) · Fig.2 `fig_e1.py` (e1_summary) · Table 1 `fig_e1.py`+`make_tables.py` · Fig.3 `fig_e3.py` ·
Fig.4 `fig_e2.py` · Fig.5 `fig_e5.py` · Fig.6 `fig_e4.py` · Table 2 `fig_e6.py` · Table 3 (scorecard) hand-written from the stats files ·
Tables 4,5 (appendix) `fig_e2.py`/`fig_e5.py`+`make_tables.py` · Table 6 (cost) `code/cost.py`. `run_all.sh` chains everything.
All numbers quoted in the text are read from `tables/*_stats.json` / `*_table.csv`.

## Incidental encounter with excluded material (as required by the task)
While verifying a citation with the literature-search tool (query: "Grokking modular arithmetic Gromov"), the result list
contained an item titled "Controlling Grokking with Nonlinearity and Data Symmetry" (arXiv 2411.05353; title and a ~600-character
abstract snippet shown by the search tool: it concerns controlling grokking by changing activation profile, depth and width).
I did not open it, did not read beyond that snippet, did not cite it, and do not know whether it is the excluded paper.
No other result touching the excluded topic was opened. No searches on "model size/width/scale and grokking" were issued.
