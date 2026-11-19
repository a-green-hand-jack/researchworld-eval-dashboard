# Reproduction

## Scope

This package separates an existing, completed scientific evaluation from manuscript-time reaggregation. No estimator evaluation was rerun to write the paper. `paper_data.json` is the unchanged authoritative registry. The final qualification is completed/qualified; this is not a superiority result. The negative comparison to one-hop OLS is retained.

## Contents and exact inputs

- `source_evidence/estimator.py`: readable snapshot of the selected estimator source associated by the selection manifest; an independent reconstruction of the final executable-tree hash has not been performed.
- `source_evidence/evaluate_final.py`: evaluator, all three scientific baseline implementations, outcome construction, behavioral controls and replay logic.
- `reproducibility/resources/final/`: physical copies of the archived benchmark, manifest, and Stanford3 graph archive. The raw input generator is not supplied; exact archived-input replay is supported, not a claim of regenerating all raw inputs from a documented independent generator.
- `analysis/observations.csv`, `analysis/summary.json`: recorded case estimates and derived summaries. Every statistic uses the recorded final cases, not development scores.
- `build_paper_artifacts.py`: reaggregates errors, computes paired seed-block intervals, generates Figures 2–3 and the numeric sources for Tables 1–4. Table 1 uses the readable evaluator/manifest; the remaining tables transcribe the saved summaries. The overview is owned by the orchestrator; its placeholder is guarded against overwriting a completed render.
- `map_claims.py`: creates the claim map, including individual condition rows and support summaries.
- `reference_evidence/`: bounded direct literature records and original-document excerpts. Exact-title lookups only; no citation-graph traversal.

## Environment

Declared original evaluator dependencies: Python 3.11 or 3.12, NumPy 1.26.4, SciPy 1.13.1, NetworkX 3.3. Linux native replay requires Landlock ABI >=3 and libseccomp.so.2; the evaluator limits each role to two CPU cores and 8 GiB, with single-threaded numerical libraries. The wall allowance is 7200 seconds. The existing final evaluation recorded approximately 629 seconds elapsed for the complete workload, not a speed benchmark.

Manuscript-time analysis used Python 3.12, NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2, requests 2.34.2 and jsonschema 4.26.0, installed in `/tmp/paper-tools`, outside this package. The source evaluator was not executed under that analysis environment. For exact final-input replay install `source_evidence/requirements.txt` in a separate environment.

```sh
python3.12 -m venv /tmp/gate-evaluator
/tmp/gate-evaluator/bin/pip install -r source_evidence/requirements.txt
TASK_SOURCE_DIR="$PWD/reproducibility" \
  /tmp/gate-evaluator/bin/python source_evidence/evaluate_final.py \
  --program_path "$PWD/source_evidence/estimator.py" \
  --results_dir /tmp/gate-replay
```

This replay command is documented from the inspected entrypoint and was not run for this manuscript. Do not replace the authoritative final results with a replay result. The `program_path` flag is a literal evaluator API identifier, not a scientific variable.

For derived analysis, using a separate environment with the analysis dependencies:

```sh
python build_paper_artifacts.py
python map_claims.py
```

These two commands were run. Summary bootstrap seed: 20261107; 10000 resamples; 95% percentile intervals. The resampling unit is the entire statistical seed block jointly across all graph families, conditions, and methods. Intervals are Monte Carlo summaries, not causal confidence intervals or graph-population uncertainty. Small-sample bias of percentile intervals and absolute-value bias summaries is not corrected. Figures export vector PDF and 300-DPI PNG. The conceptual placeholder is replaced separately by the orchestrator, not treated as a finished scientific illustration.

## Data

Stanford3 is from `https://nrvis.com/download/data/socfb/socfb-Stanford3.zip`, with provenance page `https://networkrepository.com/socfb-Stanford3.php`. Attribute Traud, Mucha and Porter (2012), and Rossi and Ahmed (2015). Network Repository states CC BY-SA: retain attribution and share-alike obligations on redistribution. The study uses synthetic experimental outcomes, no real platform outcomes or user attributes.

Archive SHA256: `b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d`.
Exact benchmark NPZ SHA256: `ba5ae5cd05e4b310a1c0dd40bf15568fd489c35704cb5812642de117fe878832`.
The manifest lists each graph and raw-row hash and all statistical seeds. It records the deterministic cluster rule and normalization. The evaluator verifies archives and dimensions before fitting. The listed download URL is for acquisition; copying the supplied archive requires no new download.

## Literature, anonymity and disclosure

Semantic Scholar direct permitted-source access returned HTTP 429; exact-title OpenAlex records were used instead. Incorrect retrieval years were checked against Crossref print metadata. The original unrelated retrieval hits were replaced with relevant, directly inspected sources, leaving 25 references. Reading scopes are explicit in `references_provenance.json`. The unavailable original blockmodel abstract was not cited; a readable blockmodel source was substituted. No prohibited paper was searched for or identified, no citation graph or related-content pages were traversed, and no prohibited material was knowingly encountered in this writing step.

The ICLR 2026 official style and bibliography style were downloaded directly from `ICLR/Master-Template`, directory `iclr2026`; their single-column text block is 5.5 by 9 inches. The required watermark is preserved unchanged. The manuscript is anonymous and includes an LLM Usage subsection inside Supplementary Information.

## Validation

Run the supplied skill validators for sections/citations, claim mapping, figure schema, scientific-evidence links, and compilation. The final local validation report records exactly which checks passed and any environment limitations; it does not substitute a word-count proxy for rendered page occupancy.

The local PDF compiles with the official style and all 25 bibliography entries. The canonical geometric helper measures eight body pages with final-page occupancy about 0.909, exceeding the required 0.75. Supplementary Information is visibly rendered after references. Full figure validation must wait for the orchestrator to replace the explicitly required empty overview prompt-log stub. The strict compile wrapper also rejects this container's system symlink `/usr/share/texmf/web2c/texmf.cnf` resolving into another approved system TeX tree; the scientific inputs and validator were not modified to bypass that check. Sanitized LaTeX compilation, BibTeX dependency checks, citation/claim checks, and scientific-evidence verification were run separately. The final report preserves these two deferred items instead of declaring full-gate success.
