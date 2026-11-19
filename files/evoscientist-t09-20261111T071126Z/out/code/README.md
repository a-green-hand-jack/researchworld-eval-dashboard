# Accuracy of regression-based GATE estimation under network interference — code and reproduction

Paper: `paper/main.tex` / `paper/main.pdf` (copy: `paper.pdf`), ICML 2026 template (`icml2026.sty`, downloaded from the ICML 2026 style package; main text = 7 pages, limit 8, references/appendix excluded). ICML 2026 requires no separate paper checklist (the template only asks for an Impact Statement, which is included).

## Layout
- `code/gate/` — library: `graphs.py` (graph loading/generation, Louvain partitions), `core.py` (outcome model, designs, estimators, theory helpers), `runner.py` (one simulation configuration).
- `code/run_experiments.py` — defines all configurations (E1, E2, E3, E5, E6, E7) and runs them in parallel; writes `results/<EXP>_{reps.csv.gz,graphs.csv,configs.csv}`.
- `code/analyze_E*.py`, `code/analysis_lib.py`, `code/make_paper_tables.py`, `code/extra_stats.py` — analysis, figures (`figures/*.pdf`), tables (`tables/*.csv`, `paper/tab_*.tex`), and ad-hoc statistics quoted in the text (`results/extra_stats.log`).
- `code/arxiv_check.py` — verifies that cited arXiv papers exist (metadata only).
- `data/get_data.sh` — downloads the two public graphs and checks sha256.
- `run_all.sh` — runs everything in order.
- (There is no E4: it was dropped from the plan during design; experiment ids were kept.)

## Environment
Python 3.11.15; numpy 2.4.6, scipy 1.17.1, networkx 3.6.1, pandas 3.0.6, matplotlib 3.11.2, scikit-learn 1.9.1 (`pip install numpy scipy networkx pandas matplotlib scikit-learn`). `pymupdf` was used only to look at rendered figures, not needed. LaTeX: pdflatex + bibtex (TeX Live). CPU only.

## Data (versions)
- Stanford3 (Facebook100): https://nrvis.com/download/data/socfb/socfb-Stanford3.zip, sha256 `b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d` (CC BY-SA; Traud, Mucha & Porter 2012; Rossi & Ahmed 2015). Largest connected component used: 11,586 nodes, 568,309 edges.
- SNAP ego-Facebook: https://snap.stanford.edu/data/facebook_combined.txt.gz, sha256 `125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7` (McAuley & Leskovec 2012). 4,039 nodes, 88,234 edges.
- Synthetic graphs (ER, BA, Watts–Strogatz, planted-partition SBM) are generated on the fly with seeds derived from the configuration.

## Seeds and determinism
Configuration `cid` of experiment index `k` (E1=1, E2=2, E3=3, E5=4, E6=5, E7=6 in the dict order of `EXPS`) has seed `1000*k+cid`; population `pi` uses `np.random.default_rng([seed, pi, 1])` (baseline), `[seed, pi, 2]` (assignments), `[seed, pi, 3]` (edge dropping); synthetic graphs use `[gseed*100+pi, 7919, n, d]`; Louvain uses a fixed seed (cached in `data/cache/`, which is regenerated if absent). E3's main grid shares graphs across designs and `s` via `gseed`.

## Commands and run time
`sh run_all.sh` (set `JOBS` = number of worker processes; default 36). Observed wall-clock on a shared 40-core machine, 36 workers (heavily contended at times, so upper bounds): E1 ≈ 32 min, E2 ≈ 47 min (102 configs, `--drop-last 1`), E3 ≈ 11 min, E5 ≈ 10 min, E6 ≈ 1 min, E7 ≈ 23 min (6 workers), analysis ≈ 15 min (`analyze_E7.py` re-runs Louvain on synthetic graphs if the cache is empty and can take several minutes). Total ≈ 2–3 h; memory < 5 GB per worker for the largest graph (Stanford3).

## Which script produces what
| Paper item | Produced by |
|---|---|
| Fig. 1 `figures/fig_varlaw.pdf`, `tables/E1_varlaw.csv`, `E1_slopes.csv` | `analyze_E1.py` (from E1) |
| Table 1 (`paper/tab_varlaw.tex`) | `make_paper_tables.py` (E1 + E7 tables) |
| E7 numbers, App. C (`tables/E7_degdiag.csv`) | `analyze_E7.py` |
| Fig. 2 `fig_bias.pdf`, `tables/E2_metrics.csv` | `analyze_E2.py` |
| Fig. 3 `fig_designs.pdf`, Fig. 6 `fig_sweeps.pdf`, `tables/E3_*.csv` (incl. leverage `E3_leverage.csv`) | `analyze_E3.py` |
| Fig. 4 `fig_mismatch.pdf`, Table 3 (`tab_mismatch.tex`), `tables/E5_*.csv` | `analyze_E5.py`, `make_paper_tables.py` |
| Table 2 (`tab_coverage.tex`), `tables/E6_coverage.csv` | `analyze_E6.py`, `make_paper_tables.py` |
| Other numbers quoted in the text (DM/regression SD ratio, harmonic vs mean degree, bias² vs variance, #simulated experiments) | `extra_stats.py` → `results/extra_stats.log` |

Raw simulation outputs used in the paper are included (`results/*.csv*`, 25 MB).

## Deviations, incomplete items and honest notes
- The `n = 64,000` point of the E2 `n`-sweep finished in an earlier invocation, but its output files were overwritten by a re-run (`--drop-last 1`) started to guard against a stalled process; it is not reported (paper, Limitation 7).
- Early diagnostic (not used for any claim): during development a 2-population × 40-replicate smoke test and `--quick` runs were executed and deleted.
- In E7, graph populations for synthetic graphs were regenerated in `analyze_E7.py`; the analysis reproduces them from the same seeds (Louvain results are deterministic given the seed).
- Confidence intervals in the paper come from bootstrapping over replicates and ignore population-to-population variability (3–4 populations per configuration).
- The fixed-population design means baseline noise is held fixed across assignment replicates; "SD" is the design-based SD within a population (pooled over populations via `sd_pop` where stated).
- Hypotheses were not formally pre-registered; the closed forms for the two-hop and missing-edge biases were derived after seeing E5 output.

## Disclosure on restricted material
The task forbids accessing the published paper that studies this question. While verifying related-work references with arXiv title queries (`code/arxiv_check.py`; it prints only id, title, date and the first authors), the metadata line of one result — arXiv:2309.07476, a paper on regression-based analysis of network experiments — was returned. Only its title/authors/date line was seen (via the API response), the paper was not opened or read, it is not cited, and nothing from it was used. `arxiv_check.py` (current version) no longer queries that title. No other restricted material was encountered.

## Tooling note
Heredoc/`execute` input to the sandbox shell occasionally rewrote ` / ` into ` . `; all code files were checked (`grep -n " \. "`) and the affected lines were fixed in the files shipped here.
