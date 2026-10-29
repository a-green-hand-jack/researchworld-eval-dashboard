# experiment-repo

Analysis checks for the JNMF importance-factor task (objective: issue #1; brief: wiki `Brief`; commitment: issue #3).

The delivered program and its output are provided by `paper-repo` (split settled in experiment-repo#2).
This repository holds the independent validation of them:

- `checks/verify_importances.py [json]` — recomputes the six factors following the original analysis
  (brand-d/cogsci-jnmf `analysis/model_evaluation/h_importances.py`), compares the given JSON at rtol 1e-12,
  and runs sanity checks (unit-norm W columns, two components, common + distinct importance = 1).
- `checks/paper-repo-12ff08c/` — the program and JSON from paper-repo main at 12ff08ce14ed4c0a2d05f2eab3c4dd488301d9e9;
  `checks/verify_paper-repo-12ff08c.log` — the check of them (all pass).
- `checks/verify_importances.log` — the same check against this position's own earlier implementation (identical values).
