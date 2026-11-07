# Task investment and multi-task leaderboard aggregation

The manuscript measures the minimum number of task scores that must improve for a target evaluation to reach first place under five aggregation rules. Investment is a score-space task count, conditional on a stated improvement law; no model is trained.

The research delivery is `paper.pdf`, with LaTeX source `paper.tex` and `manuscript/`. Build with `make paper` using TeX Live, latexmk, Latin Modern (`lmodern`) fonts and the official NeurIPS 2026 style delivered under `venue/official/`. The equivalent direct command is `TEXINPUTS=.:venue/official//: latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex`. The paper uses the official public preprint mode and the nine-page content limit.

Analysis acquisition, environments, seeds, commands, measured runtimes and data-rights notes are in `reproduction/README.md`. Input sources and SHA-256 hashes are in `data/manifest.json`; audited matrices are under `data/processed/`. Exact per-target outcomes, subsets, diagnostics and sensitivity results are under `results/`. Numerical claim-to-file mapping is also included in the paper's reproduction appendix. Figure/table generation and per-display provenance are under `presentation/`.

The two primary snapshots are HELM MMLU v1.13.0 and Open LLM Leaderboard contents commit `9c09a7cae43334062a82cb164f2ef255013dafa2`. The primary paired analysis uses the common cohort that is not already a winner under any rule; bounded-gain reachability retains fixed full cohorts including infeasible targets. Monte Carlo intervals describe random task-order sampling, and task composition ranges describe sensitivity; neither estimates uncertainty in the published scores.
