# paper-repo: "Is one SHAP run enough?"

Delivered layout (owners in `.forgejo/CODEOWNERS`):

- `paper/`    LaTeX sources of the paper (main text, appendix, statements, bibliography)
- `template/` the ICML 2027 style kit
- `figtab/`   figures and tables included by the paper, with the scripts that generate them
- `code/`     all experiment code, environment, data steps, seeds, commands, expected run times,
              and which script produces which figure and table
- `results/`  result files the figures and tables are generated from

Reproduction notes (environment, data steps, seeds, commands, expected run times, and which script produces which figure and table) are in `code/README.md`.

The PDF is built by the system from `paper/main.tex` (`.forgejo/document.json`); it is not committed.
