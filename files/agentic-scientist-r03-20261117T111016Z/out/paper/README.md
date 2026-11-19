# Reproduction package

## Scope and status

This is a retrospective embedding-score prediction study on previously observed
MTEB task/subset cells. The independent final evaluation completed and qualified.
Its retained evidence, including unfavorable historical-data controls, is preserved
in read-only `paper_data.json`. No new model experiment was run while writing the
paper. The configuration-level comparison does not isolate residual transfer.

## Environment

The evaluated task declares Python dependencies `numpy==1.26.4` and
`matplotlib==3.9.2`; Python 3.12 is available in the supplied environment.
The numeric artifacts were generated with those declared dependency versions.
TeX Live, `pdflatex`, `bibtex`, and Poppler `pdftotext` support compilation and
rendered-text checks. JSON Schema and PDF-layout checks additionally use
`jsonschema` and PyMuPDF; these validation-only packages need not enter the
scientific environment. Install environments outside this workspace:

```sh
python3.12 -m venv /tmp/embedding-paper-env
/tmp/embedding-paper-env/bin/pip install -r source_evidence/requirements.txt
/tmp/embedding-paper-env/bin/python build_paper_artifacts.py
python3 build_claims.py
```

The build script only aggregates retained arrays and reproduces the component
bootstrap. It does not fit or evaluate new models. No timing benchmark of this
artifact build was collected, so a measured regeneration runtime is unavailable.
Concept placeholders are self-guarded: the build never overwrites an orchestrator-
completed overview. Final concept rendering is a separate synchronous step.

## Data versions and checking extraction

Results repository: `https://github.com/embeddings-benchmark/results`, revision
`6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`.
Task definitions revision: `5a83aafe4e7140d0606b96f59448c704f31dbf76`.
The final manifest has 126 rows and 135 task/subset columns. The raw source JSON
documents used to construct each row are embedded in
`source_evidence/resources/final/rows.jsonl`; definitions, normalization rules,
resource fingerprints, and split assignments are bundled alongside them.
The evaluator's `extract` and `load_resources` functions re-extract scores and
check exact agreement with the stored normalized matrix, source digests, and splits.
No network is needed to reconstruct this matrix from the bundled documents.

Optional upstream checkout, not needed for manuscript regeneration:

```sh
git clone --filter=blob:none https://github.com/embeddings-benchmark/results /tmp/mteb-results
git -C /tmp/mteb-results checkout 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383
```

The bundled final plane is the authoritative reproduction input, not a fresh
selection from a current leaderboard. The original upstream subset-construction
utility is not present; the final extraction/checking code and all selected raw
documents are present. The manifest records current CC0-1.0 results-license evidence,
Apache-2.0 definitions metadata, and absence of a results license at the pinned
snapshot. Do not silently resolve that historical licensing caveat.

## Evaluated source

- `source_evidence/selected/src/program.py`: evaluated predictor, including ALS,
  acquisition, donor folds, local medians, calibration, reset, and prediction.
- `source_evidence/selected/program_spec.toml`: unchanged entrypoint specification.
- `source_evidence/selected/RESIDUAL_METHOD.md`: accompanying method note.
- `source_evidence/original/`: supplied original predictor for inspection only;
  no paired final result for this exact file is asserted.
- `source_evidence/evaluate_final.py`: complete frozen evaluator and five references.
- `source_evidence/resources/final/plan.json`: seeds 6841, 8089, 9011 and splits.
- `source_evidence_manifest.json`: copy fingerprints and original evidence locations.

For an independent future rerun, outside manuscript-only revision:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /tmp/embedding-paper-env/bin/python source_evidence/evaluate_final.py \
  --program_path source_evidence/selected/src/program.py \
  --results_dir /tmp/embedding-final-rerun
```

This command was not run during paper writing. It fits models and changes no
sealed registry entries. The evaluator imposes its own CPU/thread, resource,
message, and 7200-second wall-time limits. Recorded seed durations, including
their primary and disruption conditions but excluding reset replay, were
77.4804, 63.8990, and 61.9266 seconds. These are retained measurements, not
runtime guarantees for another environment.
<!-- @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]] -->

## Tables, figures, and claims

All numeric outputs come from `build_paper_artifacts.py`:

| Manuscript object | Output |
| --- | --- |
| Main comparison table | `tables/main_comparison.tex` |
| Supplementary budget table | `tables/budget_details.tex` |
| Supplementary seed table | `tables/seed_details.tex` |
| Figure 2: holdout/budget comparison | `figures/budget_comparison.pdf` and `.png` |
| Figure 3: history controls | `figures/history_structure_controls.pdf` and `.png` |
| All derived statistics and bootstrap bounds | `derived_results.json` |

Supplementary tables are embedded verbatim in `paper.tex` to satisfy source-only
supplement validation; their generated versions above must agree exactly.
The settings table is a transcription of the source configuration, not an
additional experiment. Figure 1 is qualitative, rendered from the strategy and
manuscript by the separate concept-figure workflow; its prompt log accompanies it.
The writing-stage PNG is explicitly a reserved placeholder until that renderer
completes. Do not treat its presence as completed visual production.
`figure_manifest.json` records paths, generators, density, and final-layout sizes.
Every quantitative plot has vector PDF and 300-DPI PNG exports.
`build_claims.py` writes `claims_grounding.json`, combining registry source IDs
with readable source locations; hashes alone never support method semantics.

## References and restrictions

`retrieve_paper_references.py` retrieves exactly identified classical references
and explicitly permitted starter papers. Semantic Scholar rate limits prompted
OpenAlex fallback. Consulted abstracts and metadata are retained under
`literature_evidence/`; no citation network was followed. One incorrect DOI was
rejected rather than cited. Publisher metadata from the original JMLR article
corrects malformed concatenated author names in its OpenAlex record; the permitted
starter title corrects the `Langauge` spelling error in another record. No
encounter with the prohibited study was identified. This is not an exhaustive
literature survey or a novelty/priority verification.

## Compilation and validation

The manuscript uses the official ICLR 2026 review template, fetched from
`ICLR/Master-Template/iclr2026`; exact URLs and repository file identities are in
`template_provenance.json`. No author identities, acknowledgements, or funding
statements are inserted. The separate LLM Usage disclosure appears in the supplement.

```sh
python3 .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python3 .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
```

If the environment-specific canonical compile-input gate rejects Debian's
system configuration symlink, `sh compile_paper_locally.sh` runs direct
`pdflatex`, `bibtex`, and two more `pdflatex` passes for diagnosis; this does not
mean that the canonical input gate passed. `local_validation_report.json` records actual checks and any unavailable
canonical checks. Quantitative source links and adjacent provenance sidecars are
checked by `scientific-evidence/verification-report.json`.
