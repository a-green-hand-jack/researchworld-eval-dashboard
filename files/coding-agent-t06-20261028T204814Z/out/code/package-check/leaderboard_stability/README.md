# Outcome reversal audits for pairwise leaderboards

The completed research paper is [`paper/paper.pdf`](paper/paper.pdf), with LaTeX source [`paper/paper.tex`](paper/paper.tex). It uses the unmodified **ICML 2026 official submission template**. The main body is seven pages; references, the impact statement, disclosure, proofs, detailed results, and a completed reproducibility checklist follow it. This is a research deliverable, not an actual conference submission or accepted paper.

The study uses frozen public Arena, MT-Bench human/GPT-4, and two NBA season datasets. All experiments are offline CPU analyses. No new judgments, paid API calls, GPU use, or live leaderboard actions occurred.

## Reproduce everything

From the root of the extracted package:

```bash
# System requirements on Debian/Ubuntu (if not already installed):
# sudo apt-get install python3 python3-venv texlive-latex-extra texlive-fonts-recommended cm-super
bash run_all.sh
```

The script creates `.venv` and installs `requirements-lock.txt` if the environment does not exist, downloads the four fixed data files, checks their hashes, prepares outcomes, runs numerical checks, executes all experiments, generates every figure/table, compiles the paper, and audits the PDF. It exits on failures. It needs network access only for dependency installation and the listed data downloads. Raw files are about 204 MB in decimal units, stored under `data/raw/`, and are not in the submission archive.

Observed experiment wall times on an Intel Xeon Gold 6230 CPU @ 2.10 GHz were approximately **93 s main**, **17 s matched panels**, and **11 s supplementary analysis**, with numerical libraries limited to one thread. The scripts intentionally do not exploit the host's additional cores. These timings exclude installation, download, and first-use LaTeX plot caching; on this host the numerical pipeline takes a few minutes. Other machines and networks vary. The task's one-week allowance was not exhausted.

The exact recorded environment is in `requirements-lock.txt` and `ENVIRONMENT.json`; direct requirements are also listed in `requirements.txt`. Python is 3.11.2 on the original host. The paper compiles with pdfTeX/TeX Live 2022. Plot rendering uses LaTeX and Type-1 fonts. The conference style remains the 2026 official version, independent of the TeX engine release.

If `.venv` already exists but is not this environment, create a fresh environment or run `.venv/bin/pip install -r requirements-lock.txt` before reproduction. No credentials are required.

## Run stages separately

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/python src/download.py
.venv/bin/python src/prepare.py
.venv/bin/python src/test_methods.py
.venv/bin/python src/experiment.py --reps 500 --boot 1000
.venv/bin/python src/matched.py
.venv/bin/python src/supplement.py
.venv/bin/python src/verify_results.py
.venv/bin/python src/report.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
cd ..
.venv/bin/python src/audit_pdf.py
```

The `--reps` and `--boot` flags are useful for development, but **the paper's stated protocol requires 500 and 1000**. `report.py` reads saved results; it does not fetch data or simulate missing outputs. The reproducible numerical values are independent of PDF creation timestamps and machine-dependent runtime fields.

## Data sources, versions, and rights

`DATA_MANIFEST.json` contains complete immutable URLs, byte counts, and SHA-256 checksums. The same manifest is generated as `data/manifest.json`. Sources are:

| Source | Fixed version | Files / license |
|---|---|---|
| `lmarena-ai/arena-human-preference-55k` on Hugging Face | `18c298340948c0e7f7727399fd459cca6ce0ca6f` | `train.csv`, Apache-2.0 |
| `lmsys/mt_bench_human_judgments` on Hugging Face | `f7d2896d2cc5d80f8b55c2bbc722613555233c25` | human and gpt4_pair parquet, CC-BY-4.0 |
| FiveThirtyEight/data, `nba-elo/nbaallelo.csv` | `4c1ff5e3aef1816ae04af63218015066e186c147` | CSV, CC-BY-4.0 |

`download.py` verifies each full raw file before use. `prepare.py` preserves all Arena and MT records in the primary analysis; the NBA filter is `_iscopy == 0`, `lg_id == 'NBA'`, `is_playoffs == 0`, and `year_id` equal to 2014 or 2015. One game is one record. Ties and GPT-4 `tie (inconsistent)` outcomes are half-wins. The supplemental checks document different treatments. Arena prompt strings are hashed only to define clusters; conversations are not otherwise analyzed or redistributed.

Raw and processed datasets are deliberately absent from the source/submission archive and ignored by `.gitignore`. The local `/work/data/` retains them as requested. Reproduction regenerates processed outcomes and matched example panels. Dataset licenses and source attribution remain applicable to downloaded data; no ownership of these data is claimed.

## Methods and seeds

- `src/bt.py`: pair-aggregated ridge BT solver, influence coefficients, sequential refitted audits, and exact pair-balanced radius.
- `src/test_methods.py`: independent optimizer/finite-difference checks, exhaustive small synthetic test, and rejection of an unbalanced input to the exact formula. Synthetic data are unit-test fixtures only.
- `src/experiment.py`: the five main datasets; selected edits, baselines, ridge/tie checks, all leader challengers plus top-ten adjacency, random reversal trials, and cluster bootstraps.
- `src/matched.py`: 500 paired schedules; 99 shared question/pair/turn cells per pair, 1,485 rows per design; one human annotation uniformly chosen per selected cell; exact-radius verification.
- `src/supplement.py`: exact full-GPT thresholds for all 15 pairs; inconsistent-tie/annotator/deduplication checks; 1,000 question bootstraps of the exact GPT focal radius.
- `src/verify_results.py`: independent BFGS fits on the five real datasets before/after the saved main witnesses, with explicit optimizer status and residuals.

Base seed: **20261028**. Main random corruption uses base + `100*d`; cluster-gap bootstrap uses base + `100*d + 1`, with `d=0,...,4` in the dataset order Arena, MT human, MT GPT-4, NBA 2014, NBA 2015. Matched panels use **20270028**. Exact GPT radius bootstrap uses **20273028**. Unit-test fixtures use **174**. Stable sorting resolves equal selection scores by row order. Changing input row order can change which tied rows are selected.

Numerical convergence and proof assumptions are in the paper. An unbalanced-data crossing is generally an **upper bound** on the optimum, not a certificate; the balanced formula supplies exact thresholds under its checked assumptions. Capped searches are recorded as missing thresholds, not as infinite robustness. The raw-win baseline's linear predicted threshold is deliberately null because its score units are not logit units.

## Every paper table and figure

All are generated by **`src/report.py`** from saved numerical artifacts; no empirical table/figure was hand-drawn or populated with estimated results.

| Paper artifact | Generated source | Numerical producer/input |
|---|---|---|
| Table 1: data/gaps/uncertainty | `paper/generated/data_table.tex` | `experiment.py`: `summary.csv`, `bootstrap.csv` |
| Table 2: budgets and random controls | `paper/generated/radii_table.tex` | `experiment.py`: `attacks.json`, `allpairs.csv`, `noise.csv` |
| Table 3: selection baselines | `paper/generated/baselines.tex` | `experiment.py`: `attacks.json` |
| Table 4: matched-panel summaries | `paper/generated/matched_table.tex` | `matched.py`: `matched.csv` |
| Table 5: linear-approximation errors | `paper/generated/approximation.tex` | `experiment.py`: `allpairs.csv` |
| Table 6: penalty/tie sensitivity | `paper/generated/ablations.tex` | `experiment.py`: `ablations.csv` |
| Table 7: preprocessing checks | `paper/generated/supplement.tex` | `supplement.py`: `supplement.csv` |
| Figure 1: random-corruption curves | `figures/noise.pdf` | `experiment.py`: `noise.csv`, `summary.csv` |
| Figure 2: exact matched radii | `figures/matched.pdf` | `matched.py`: `matched.csv` |
| Figure 3: predicted/refitted thresholds | `figures/approximation.pdf` | `experiment.py`: `allpairs.csv` |
| Prose macros | `paper/generated/numbers.tex` | same results plus `gpt_radius_bootstrap.csv`, runtime metadata |

Full rank scores are in `results/rankings.csv`; individual random trials and bootstraps are retained. `attacks.json` stores the actual selected row indices plus the before/after crossing gaps. These indices refer to the processed canonical rows, which `prepare.py` recreates and links to original record identifiers. `results/balanced_exact.csv` gives all full-GPT exact pairs. `verification.json` records independent solver residuals and precision-loss warnings; agreement was checked separately from optimizer status flags.

## Formatting, access protocol, and known limitations

Official template: `https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip`, linked from `https://icml.cc/Conferences/2026/AuthorInstructions`. `TEMPLATE_MANIFEST.json` records hashes of the downloaded archive and unmodified vendored styles. The official Call for Papers at `https://icml.cc/Conferences/2026/CallForPapers` states an eight-page main limit, excluding references/impact/appendices. The consulted ICML instructions/template do not provide a mandatory in-paper checklist; a completed voluntary checklist is in Appendix C. The impact statement and AI-assistance disclosure are included. A separate `PLAIN_LANGUAGE_SUMMARY.md` is supplied.

Read `RESEARCH_LOG.md` for the independent-research access protocol, permitted literature read, access failures, correction of a reporting field, unsuccessful baselines, and experiments not attempted. A final combined shell replay received SIGTERM (exit 143) after all numerical stages completed; reporting and compilation were resumed separately. All 13 checked numerical output files matched the previous run byte-for-byte. `results/reproduction_check.json` records this distinction; the combined-shell interruption is not reported as a successful one-shot execution. Only directly identified permitted starter literature was consulted; no search was made for the unnamed excluded paper or its identity.

The analysis is exploratory and conditional on these historical datasets. It does not establish a causal effect of judge type, general reliability of a class of evaluators, globally optimal attacks for arbitrary graphs, or population confidence guarantees under unobserved user/annotator/team dependence. The original Arena top order changes if all ties are removed. GPT-4 is both an evaluated model and the automated judge. These limitations are central to the paper.

## Deliverable layout

- `paper/`: official styles, bibliography, LaTeX, generated tables, and compiled paper.
- `src/`: all acquisition, analysis, validation, and reporting code.
- `results/`: numerical outputs and verification metadata, with no conversation text.
- `figures/`: publication PDF figures.
- `run_all.sh`, requirements, provenance manifests, environment, research log, and documentation.
- `submission.tar.gz`: a clean submission bundle excluding raw/processed data, downloaded literature, `.venv`, temporary build files, and unrelated local working logs. Selected numerical verification stdout logs are included. The bibliography and access notes provide literature provenance; literature PDFs are not redistributed.

To rebuild the submission archive after reproduction, run `.venv/bin/python src/package.py`. `SUBMISSION_MANIFEST.json` lists SHA-256 hashes of its contents.

Code created for this study is released under the MIT License (`LICENSE`). Third-party conference styles retain their original notices; public data retain the licenses listed above.
