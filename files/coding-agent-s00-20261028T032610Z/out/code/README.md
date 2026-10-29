# Cover-time prediction on small graphs: reproduction

Environment: Python 3.11.2; numpy 2.4.6, networkx 3.6.1, pandas 3.1.0, matplotlib 3.11.2. CPU only.

    python -m venv .venv && .venv/bin/pip install numpy networkx pandas matplotlib
    cd src
    ../.venv/bin/python run.py --walks 300 --seed 0 --out ../data/results.csv   # ~2 min
    ../.venv/bin/python analyze.py ../data/results.csv ../data > ../data/analysis_log.txt
    cd ../paper && pdflatex main && bibtex main && pdflatex main && pdflatex main

Seeds: graph generation and walks use `--seed 0` (numpy default_rng); bootstrap and fold splits in analyze.py use seed 123.
Outputs: data/results.csv (per graph), data/summary.csv, data/per_family.csv, data/analysis_log.txt, figs/scatter.pdf.
