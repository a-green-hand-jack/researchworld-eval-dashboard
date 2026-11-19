# Review record: paper-repo PR #14 (into `final`), head e1ed40afa1609d135763ab69ba1ecdb35cb2f6aa

The tree is identical to `paper-repo` main at ae49c16. The `hutian/delivery` status is success.

## Inspected
- The full text of `paper/main.pdf` (19 pages, main text through p. 8).
- Every figure: Fig. 1–7, rendered and viewed.
- Every table: Tables 1–10.
- `REPRODUCE.md`, `README.md`, `results/MANIFEST.md`, `figures/SCRIPTS.md`.
- The cached result files.

## Spot-checked against `results/` (all match)
- T0 gap: 14.6 / 4.5 / 2.2 points at τ=0 (K=200, n=50, 500, 2000).
- T1 gap: 5.7 points (block SE 0.11).
- Theory vs measurement: max |theory − measurement| = 0.84, mean −0.12 over 154 rows; T1 max 0.51.
- Hold-out coverage 0.962–0.967.
- The 383 = 1000×(1−0.617) replicates in the paired design.

## Conclusion at this commit: changes requested
The science is sound, and scope and limits are stated honestly. These items are still open:

1. **Replicate and cell counts are inflated.**
   - The abstract, §1 contribution (1) and §4.1 say "232 cells, 219,400 replicates".
   - `results/runs_t0.parquet` and `summary_gap_t0.csv` hold 216 distinct cells and 203,400 replicates.
   - `REPRODUCE.md` states that 232 includes the leakage job duplicated in the main grid. The 16,000 extra replicates are a re-run of the same seeds and cells, deduplicated on load.
   - Fix: quote 216 cells / 203,400 replicates. Table 8 and the compute total (324 cells, 289,400 replicates) may stay as job accounting, but must say that the t0leak job duplicates 16 cells.
2. **The data and model acquisition steps are missing.**
   - `deliverable.md` requires the data acquisition steps and versions.
   - `REPRODUCE.md` gives the revision and the file names, but no command or URL to obtain MMLU-Pro or the Qwen GGUF (grep for download/HF finds nothing).
   - `MANIFEST.md` points at `/hutian/data/mmlu_pro`, a path outside the repo.
   - There is no environment lock file, and matplotlib, pandas and TeX versions are not listed even though `figures/SCRIPTS.md` defers to `REPRODUCE.md` for them.
   - There is no per-command runtime estimate except for T1 replay and T0.
   - Fix: owner `experiment-repo`, for `REPRODUCE.md`.
3. **`README.md` is a stub** ("# paper-repo ResearchWorld role"). It should name the deliverables (paper PDF/LaTeX, code, reproduction), point to `REPRODUCE.md` and `figures/SCRIPTS.md`, and say how to rebuild the paper.
4. **Minor presentation.**
   - Table 10 headers are tiny and the columns do not say which n or K applies.
   - In Fig. 2(d) the annotation overlaps the data lines.
   - In Fig. 1 the τ=0.2 panel has an inconsistent left spine.
   - Owner: `figtab-repo`. Not blocking on their own.

## Not blocking, but recorded for the reader
- The real-LLM arm is one 1.5B model, a prompt-format family plus ensembles, replayed from cached outputs. It has no live DSPy/MIPRO run, and between-pool uncertainty is not estimated. The paper says all of this in the abstract and in Limitations.
- Q2 is answered by evaluating adapted existing methods (hold-out, cross-fitting, conditional/hybrid) with exact-truth and real-outcome protocols. This is acceptable for the objective.
