# Regression-based GATE estimation under network interference — code & reproduction

Paper: `paper/main.pdf` (NeurIPS 2025 template, source `paper/main.tex`, `refs.bib`, `checklist.tex`; tables 1/B are inlined in main.tex from `tab_small.tex`/`tab_main.tex`).

## Environment
Python 3.11; `python3 -m venv venv && venv/bin/pip install numpy scipy networkx matplotlib scikit-learn pandas pymupdf` (versions in `code/requirements.txt`). CPU only.

## Data (put in `/work/data`, paths hard-coded in `code/lib.py`)
- Stanford3: `https://nrvis.com/download/data/socfb/socfb-Stanford3.zip` (sha256 b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d), unzip -> `socfb-Stanford3.mtx` (CC BY-SA; Traud et al. 2012; Rossi & Ahmed 2015).
- ego-Facebook: `https://snap.stanford.edu/data/facebook_combined.txt.gz` (sha256 125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7) (McAuley & Leskovec 2012).
Both hashes were verified. Synthetic graphs are generated (seed 1). Louvain communities are cached in `results/cache`.

## Run (≈12 min wall-clock on 36 processes; set single-threaded BLAS/OpenMP, otherwise heavy oversubscription)
```
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd code
../venv/bin/python run_all.py E1 E2 E3 E4 E5 E6 E7   # -> results/E*.json   (seed of config k = k)
../venv/bin/python analyze.py > ../results/analysis.txt   # -> paper/tab_main.tex, fig_sweeps.pdf, fig_scaling.pdf, results/coverage_E1.csv
../venv/bin/python maketab2.py                            # -> paper/tab_small.tex (Table 1)
../venv/bin/python predsd.py                              # -> paper/fig_predsd.pdf, results/predsd.csv
```
`analyze.py` must be run before `maketab2.py`/`predsd.py` need only the JSONs. Table/figure map: Table 1 = maketab2.py; Table B = analyze.py; Fig 1 = analyze.py (E2–E5); Fig 2 left = analyze.py (E3, E6), right = predsd.py. Numbers quoted in the text come from `results/analysis.txt`, `results/coverage_E1.csv`, `results/predsd.csv`.
After regenerating tables, paste them into main.tex (they were inlined by replacing `\input{tab_*.tex}`; `\input` inside the tabular failed to compile).

## Files
`code/lib.py` graphs/outcome models/feature maps; `code/sim.py` simulator + estimators; `code/run_all.py` experiment grid; `code/look.py` helpers.

## Notes
- A first debug pass with R=100 (GBM 20) was overwritten by the final R=300 (GBM 60) run; an earlier launch was killed by thread oversubscription before finishing.
- No forbidden material (the restricted prior paper or pages discussing it) was searched for or encountered; no literature search was done beyond the starter list.
