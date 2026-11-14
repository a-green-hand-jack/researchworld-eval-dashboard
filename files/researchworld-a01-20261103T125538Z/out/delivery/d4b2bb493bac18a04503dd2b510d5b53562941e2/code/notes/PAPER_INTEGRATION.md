# Analysis integration candidate, 2026-11-03

Story-repo#2 settled the scope against the frozen objective and context-v2, and paper main merged the ownership and plan PRs. `code/.* @experiment-repo` is the assigned path. The full conditional affected-task-count analysis and its exactness arguments remain in scope; no continuous score-budget extension, actual training or physical-cost calibration is required. Independent feasibility and analysis review may still identify a concrete correction.

Actual integration candidate: **world/paper-repo#10**, "Deliver exact task-investment code, public data provenance and complete evidence", paper head `c61d185b22a096dbbab0ea8fd336ec103f238547`. It is based on paper main with the settled plan and CODEOWNERS, and contains only the `code/` path. The source archive is experiment-repo `b98330c1f0d0c4ce1a1c3dd19a7e8bc5aae56692`, with an additional `code/DELIVERY.json` recording the source revision and SHA-256/size for each archived file. This note records the candidate rather than claiming it is already merged.

Relocation validation:

- Copied all60 tracked analysis files, excluding untracked raw downloads and caches; retained processed score matrices, all results, code, tests, requirements, notes, manifest and README.
- The packaged independent exhaustive tests pass in2.635seconds. The packaged output validator passes296,064 primary/sensitivity rows and completion of63,200 subset attacks.
- Every archived file still matches its SHA-256 after tests and output validation. No path-dependent result bytes changed.
- All nine source summaries frozen by figtab-repo still match their declared hashes in the package. Primary and robustness numerical results were not rerun or changed for packaging.
- Reproduction uses `cd code` from the final delivery root. The internal scripts retain their own directory-relative ROOT calculation, so standalone and integrated layouts use the same commands.

The PR supplies analysis material for paper-repo#2; it deliberately does not close the broader manuscript integration request on code merge. The report owner must still incorporate and check the ceiling-dependent reversal, infeasibility, model limits and uncertainty semantics in the built paper. The package is the analysis-owned part, not another owner's final prose or figure rendering. The report owner merges this PR; no merge is scheduled by the analysis owner into another owner's repository. Independent analysis audit remains open in internal-review-repo#2. The commitment stays open for required integration/review corrections and final delivery checks.
