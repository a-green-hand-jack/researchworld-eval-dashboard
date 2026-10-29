# 小图上随机游走覆盖时间的简单预测

交付论文：[paper.pdf](paper.pdf)；LaTeX 源文件：[paper.tex](paper.tex)。论文使用原样保存的 **NeurIPS 2023 官方模板**（preprint 模式），正文以英文撰写。

实验结论：在本次生成的 189 张图上，四统计量模型的规模插值误差为 **19.9%**（蒙特卡洛 95% 区间 19.7–20.2%），仅用顶点数模型为 63.4%。留出整类图时，四统计量模型误差为 **29.0%**。这里误差指按图类别等权平均的绝对百分比误差；预测目标是**均匀随机起点的期望覆盖时间**，不是最坏起点覆盖时间。网格和棒棒糖图误差较大；这些数值不代表对所有 30 顶点以内图的保证。

## Reproduction

Tested with Linux x86-64, Python 3.11.2, GCC, and pdfLaTeX/BibTeX from TeX Live 2022. CPU: Intel Xeon Gold 6230 @ 2.10 GHz. No GPU, external graph data, paid service, or account is required. The scientific experiment takes approximately 20 seconds in this environment; dependency installation and LaTeX compilation are additional. `experiment.py` sets BLAS/OpenMP thread counts to one when not already set in the environment.

```bash
cd /work
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make reproduce
```

The Makefile defaults to `.venv/bin/python`; override with `make PYTHON=/path/to/python reproduce` if needed. Required system programs are `gcc`, `make`, `pdflatex`, and `bibtex`. LaTeX packages include `natbib`, `environ`, `geometry`, `amsmath`, `amssymb`, `booktabs`, `graphicx`, and `microtype`; standard TeX Live distributions provide them. The official style is bundled, so reproduction does not fetch it.

To run just the experiment and generate the paper's numeric table:

```bash
make experiment
```

To compile the PDF using the checked-in results:

```bash
make paper
```

## Experimental specification

- Sizes: 6, 10, 14, 18, 22, 26, 30. All graphs are simple, undirected, unweighted, and connected.
- Seven deterministic families at each size: path, cycle, star, complete, grid, lollipop, and barbell. ER and random labeled tree families each have ten draws per size. Total: 189 graph records; repeated isomorphism classes are allowed in independently generated draws.
- The grid is a row-major truncated square lattice with width `floor(sqrt(n))`. Horizontal edges do not wrap between rows. Lollipops use clique size `floor(2*n/3)`; barbells use two cliques of size `floor(n/3)`, with all remaining vertices internal to the joining path.
- ER sampling uses `p=min(0.6,2*log(n)/n)` and rejection until connected. NetworkX random labeled trees use uniform Prüfer sequences.
- Master seed: **20261027**. NumPy `SeedSequence.spawn(189)` yields per-record graph and walk seeds, both recorded in `graphs.csv`. NetworkX/Python RNG generates graphs; the C simulator uses xorshift64* with rejection to produce unbiased bounded integers. Each trajectory gets a fresh uniform starting vertex from its graph's pseudorandom stream. Initial vertex counts as visited at time zero.
- Each graph has **8,192** uncensored walks, totaling **1,548,288**. All lengths are retained. Graph ID is the zero-based row index everywhere.
- Four features: log vertex count, log mean degree, log maximum degree, log diameter. Training-fold standardization, then ridge penalty 1; fit log simulated means and exponentiate directly. Equal weight per training graph. The `n_only` baseline uses only log vertex count. No tuning or feature search.
- Size interpolation: train on sizes 6, 10, 18, 22, 30 (135 records), test on 14 and 26 (54). No test graphs enter scaling or fitting.
- Leave-one-family-out: nine fits, each holding out every graph of one family across all sizes. Remove from training any graph isomorphic to any held-out graph. Weisfeiler–Lehman hashes screen candidates, followed by exact `networkx.is_isomorphic` checks. Removed training counts are in `summary.json`.
- MAPE is computed separately within each family, then averaged equally across the nine families. The universal baseline is `2*m*(n-1)`, valid also for the larger worst-start expectation, but evaluated here as a numerical estimate of the uniform-start expectation.
- Per-graph intervals use sample standard errors and Student-t quantiles. Metric intervals use **300** bootstrap resamples of **64** disjoint batches of **128** walks per graph, independently per graph, with refitting. Bootstrap seed: **20261028**. These are approximate **Monte Carlo intervals conditional on the graph suite**, not graph-population confidence intervals or per-walk prediction intervals.

## Validation and limitations

The simulator is compared with uniform-start formulas, with `L=n-1` and `H_k=sum(1/i for i=1..k)`:

- Path: `L*(7*L-1)/6`.
- Cycle: `n*(n-1)/2`.
- Complete graph: `(n-1)*H_(n-1)`.
- Star (`n>=3`): `2*(n-1)*H_(n-1)-2+1/n`.

For one six-vertex graph per family, independently solve the visited-subset linear equations in `exact_cover`. Where formulas also apply, their agreement with those equations is asserted to numerical tolerance `1e-8`. This gives 33 distinct graph comparisons against Monte Carlo; maximum absolute standardized discrepancy is 2.42. An assertion checks that no discrepancy exceeds five standard errors. Per-graph reference values and discrepancies are saved in `validation.json`.

Nonisomorphic generated graphs with identical four features are compared descriptively. The largest observed ratio is IDs 37 and 39, both with `n=6, m=10, mean_degree=10/3, max_degree=5, diameter=2`. The additional subset-state solutions are 16.087103 and 22.395435 steps. They imply an unavoidable relative error of at least 16.4% on one of the pair for any prediction depending only on these inputs. The pair was selected after observing feature collisions; this is not a prespecified hypothesis test. Exact-state values mean solutions of finite-state equations, evaluated in double precision.

The benchmark does not sample all connected graphs, odd sizes, or sizes below six. Random families have only one parameter regime. The deterministic families have two test graphs each in interpolation. Training weights favor the more numerous random-family records, while evaluation weights families equally. Good performance on a family is conditional on these generators and sizes. Structural improvements, alternate weighting, and worst-start prediction are not tested.

## Files

| File | Contents |
|---|---|
| `paper.tex`, `paper.pdf`, `references.bib` | Paper source, compiled PDF, supplied background references |
| `neurips_2023.sty` | Unmodified official conference style |
| `experiment.py` | Graph generation, simulation orchestration, regression, uncertainty, exact checks, plotting |
| `simulate.c` | C walk simulator; compiled automatically to `simulate.so` |
| `report.py` | Builds `results/table.tex` from numeric results |
| `requirements.txt`, `Makefile` | Exact Python package versions and commands |
| `results/graphs.csv` | Graph statistics, seeds, simulated means, standard errors, 95% intervals |
| `results/graphs.json` | Edge lists indexed by graph ID |
| `results/walk_times.npz` | `times`: unsigned integer array `(189,8192)`, one row per graph |
| `results/predictions.csv` | Per-graph predictions for both evaluation protocols |
| `results/summary.json` | Aggregate and family errors, MC intervals, full coefficients, checks, timings |
| `results/validation.json` | Formula/subset-state validation results |
| `results/results.pdf`, `results/results.png` | Main figure in vector and raster forms |
| `experiment.log`, `latex-build.log` | Captured experiment results and build output |
| `SOURCE_ACCESS.md` | External access provenance and restricted-content compliance |

All table entries are generated from `summary.json`. Prose reports rounded values from the supplied seeded run. Timings may change on rerun. Package versions are pinned for reproducible graph generation; floating-point library differences can cause minor numeric differences. `pymupdf` is used only to inspect the delivered PDF, not by the experiment.

