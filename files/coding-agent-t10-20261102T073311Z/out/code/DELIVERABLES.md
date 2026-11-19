# Deliverables

- `paper.pdf`: compiled complete research report in the official NeurIPS 2026 template; 7 body pages, followed by references, proofs, full experimental results, reproducibility details and the completed official checklist.
- `paper/main.tex`, `paper/references.bib`, `paper/checklist.tex`, `paper/neurips_2026.sty`, `paper/generated/`, `paper/full_tables.tex`: complete compilable LaTeX source, bibliography, unmodified official style, generated numerical material and figures.
- `paper_source.zip`: portable LaTeX source bundle, including all needed generated assets and a compiled PDF.
- `code/`: all inference methods, simulation/data sampling, acquisition, scientific checks, summaries and document audits.
- `README.md`, `requirements.lock.txt`, `data/manifest.json`: full reproduction commands, exact dependency versions, fixed data version/downloads/checksums, seed policy, measured runtimes, figure/table mapping and licensing limitations.
- `results/raw/`: every reported repetition's endpoints and coverage, with condition metadata; `results/summary.csv`: all 551 method summaries and Monte Carlo uncertainty.
- `logs/`: actual run logs, independent-access record, unsuccessful setup/processing attempts, scientific verification and final audits.
- `research_artifact.tar.gz`: code, paper, data inputs, results, reproduction instructions and audit/source records; excludes the virtual environment and transient rendering/build files.

All results were actually run on CPU. No prohibited-paper search or identified encounter occurred. No paid API, new labeling or predictor retraining was used. The report distinguishes strict finite-sample coverage from normal approximations, and retains negative and invalid-coverage outcomes.
