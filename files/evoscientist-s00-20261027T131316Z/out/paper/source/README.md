# Cover-time prediction on small graphs — reproduction

Environment: Python 3.11, numpy 2.4.6, scipy 1.17.1, pandas (analyze.py only). CPU only, about 1–2 min per seed.

    python3 cover_experiment.py --seed 0 --R 1000 --out results.csv > run_log.txt
    python3 analyze.py results.csv > analysis.txt
    python3 cover_experiment.py --seed 1 --R 1000 --out results_seed1.csv > run_log_seed1.txt
    python3 analyze.py results_seed1.csv > analysis_seed1.txt
    pdflatex paper.tex   # run twice

- Graph generation seed = --seed; Monte Carlo RNG seed = seed+1000; bootstrap seed 12345.
- Exact values (n<=10) come from a sparse linear solve over (vertex, visited-set) states.
- Files: results*.csv (per-graph data), analysis*.txt (tables), paper.tex / paper.pdf.
- Caveat: the official ICML/ICLR/NeurIPS LaTeX style was not available offline; paper.tex uses the
  article class and must be re-typeset with the chosen venue's template before submission.
- Excluded per task: the original paper answering this question and its mirrors/discussions were not consulted.
