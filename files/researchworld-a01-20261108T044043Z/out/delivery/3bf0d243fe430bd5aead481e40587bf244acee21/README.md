# Score-space exposure on two LLM leaderboards

The manuscript is [paper/main.pdf](paper/main.pdf), with [LaTeX source](paper/main.tex), references and the completed NeurIPS 2026 checklist in `paper/`. Build with `cd paper && latexmk -pdf main.tex`.

The separate [reproducibility supplement](paper/reproducibility.zip) contains manuscript sources, all code, derived input matrices, measured results, figures, tables and an internal SHA-256 manifest. Regenerate it with `python3 paper/build_supplement.py`.

[REPRODUCE.md](REPRODUCE.md) documents pinned public inputs, environments, commands, seeds and measured computation times. Render the supplied results with `bash figures/src/make_all.sh results`. The minimal primary-cap analysis from supplied processed matrices is `bash code/run_minimal.sh`; the complete pipeline is `bash code/run_all.sh`.

The recorded analysis environment uses Python 3.11.2. Install dependencies with:

```sh
python3 -m pip install numpy==2.4.6 scipy==1.17.1 pandas==3.0.6 pyarrow==26.0.0 matplotlib==3.11.2 pillow==13.0.0 pytest==9.2.0
```

TeX Live with `latexmk`, BibTeX and the included official NeurIPS 2026 style builds the PDF. Rendering versions were checked in the report workspace; analysis/test versions are recorded by the analysis owner in REPRODUCE.md.

Scope: the manuscript measures required score changes under fixed rivals and stated gain caps. These are not calibrated training budgets. The OLLB score-component sensitivity changes task weighting as well as granularity. Cap-estimation uncertainty, per-task allowance ablations, observed joint gains and HELM allowance sensitivity are reported in the main text; the wider ordinal extension samples 60 targets with equal allocation across four rank strata, retaining the full rival set. Supplementary top-500 Copeland results separate certified feasibility from censored point-cost solves; conditional cost summaries cover solved targets only.
