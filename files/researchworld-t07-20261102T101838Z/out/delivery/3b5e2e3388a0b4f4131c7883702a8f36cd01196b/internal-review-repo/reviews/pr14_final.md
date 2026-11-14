# Review of paper-repo PR #14 (merge into `final`)
Head inspected: 8a3aa7e5ca75b80c85170efc96b58a42862068f8.

`git diff 29ef145 8a3aa7e` is empty: the tree of this head is identical to the head I inspected and approved in #9 (29ef1451; record reviews/pr9_review_round3.md), whose paper.pdf I rebuilt from source and whose numbers I checked against results/predictions/tier1.parquet and results/tables/review/. The earlier findings F1-F10 and N1-N4 were verified resolved there; the figures and tables were opened and are readable.

Against the objective: question answered under two protocols on 13 matrices with 11 pipelines (existing methods, simple baselines, a design with ablations), MAE/RMSE/Spearman/Kendall, paired and target-model bootstrap uncertainty, a negative/conditional conclusion with its scope, reproduction guide with pinned data commit, seeds, commands and run times, forbidden-content disclosure, NeurIPS 2026 template with checklist, 9/9 main pages.

Residual limitations, all stated in the paper (not hidden): re-implemented anchor-point/IRT methods (original packages not run), Active Evaluation Acquisition and metabench GAM absent, further analyses on 4-7 benchmarks and 20 repetitions, organisation hold-out rather than size/date family shift. Minor: code/bpx/__pycache__ still tracked in this tree (fix already on experiment-repo main, 1a18f297).

Conclusion: supported; approve.

## Update: head 861dbe93d20d3a148ec8948910c08a0c80706d5c
Diff to the approved 8a3aa7e5: only removes code/bpx/__pycache__/*.pyc and adds code/.gitignore (experiment-repo#7). No paper, result or script change; approval carries over.
