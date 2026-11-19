# Reproduction and evidence boundaries

## Scope

The manuscript analyzes an existing, completed evaluation. No new scientific
replications, benchmark evaluations, or controlled ablations were run while
writing it. `paper_data.json` is read-only and is the authoritative quantitative
registry. The final outcome is **qualified**, independently of the absent
`downstream_study`; this is operational qualification, not scientific coverage
certification. The conservative scientific-validity field does not diagnose a
coverage or adaptivity failure. All six non-benefits against PPI++ are retained.

The selected source is copied into `source_evidence/`. Its identity is associated
with the selected development record, but the final frozen tree hash has not
been independently reconstructed. No byte-identity claim is made. The method
description is grounded in readable source, not hashes or prior audit verdicts.

## Artifact-only build (performed)

Auxiliary Python packages are installed outside this workspace, in
`/tmp/paper-tools`. The figure environment uses Python 3.12, NumPy 1.26.4,
SciPy 1.12.0, and Matplotlib 3.8.4. Optional validation uses jsonschema and
PyMuPDF. To recreate this environment without polluting the manuscript:
<!-- @evidence[[source_evidence/requirements.txt]] -->
<!-- @evidence[[build_artifacts.py]] -->

```sh
python -m venv /tmp/paper-tools
/tmp/paper-tools/bin/pip install numpy==1.26.4 scipy==1.12.0 matplotlib==3.8.4 jsonschema pymupdf
/tmp/paper-tools/bin/python build_artifacts.py
python build_claims.py
python record_artifact_provenance.py
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py --paper-data paper_data.json --references references_provenance.json --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
```

The figure build requires no additional experiment and uses the stored
uncertainty intervals rather than generating new bootstraps. It verifies every
stored mean width against the 400 paired endpoint records. Runtime for this
artifact-only build is short; no prospective runtime guarantee is asserted.
Actual timing, compilation and validation status are recorded in
`validation_report.json` after verification.

Two canonical wrapper limitations were encountered: the compile wrapper rejects
a system TeX symlink into another approved TeX root, and the figure validator
imports an unstaged `src.orchestrator` module. Sanitized direct LaTeX/BibTeX
commands, a resolved-path dependency audit, the canonical figure JSON schema,
strategy density budgets, and the rendered-SI validator were checked instead.
The wrappers themselves were not modified. `audit_artifacts.py` records these
limitations and independently verifies the nine-body-page PDF, citation keys,
standalone language, figure paths/budgets and evidence report. This independent
audit is not represented as a pass of the unavailable orchestrator validators.

### Figures and tables

- Main Table 1: `build_artifacts.py` produces `analysis_summary.json` from final
  endpoints; the rounded table is embedded in `paper.tex`.
- Coverage and width-difference supplementary tables: same script and existing
  first-episode `solution.summary` uncertainty records.
- Figure `paired_width_comparison`: `build_artifacts.py`, vector PDF and 300-DPI PNG.
- Figure `coverage_with_uncertainty`: same script and formats.
- Figure `fixed_resource_overview`: orchestrator-owned conceptual rendering
  following the strategy, not an experimental measurement. The draft contains
  an explicitly temporary placeholder and `{}` prompt-log stub. The build script
  is self-guarding: it skips an existing image, nonempty prompt log or completion
  marker. It cannot overwrite the orchestrator's rendering. No paid image-model
  enhancement is authorized. The final orchestrator is responsible for replacing
  this placeholder and recompiling.

Every derived quantitative artifact has an adjacent `.prov.json`. Inline
evidence references are LaTeX comments so they are machine-checkable without
appearing as internal metadata in the rendered manuscript.

## Existing experimental code and resources (not rerun)

`source_evidence/program.py` is the selected CPU-only JSON-line inference entrypoint.
It accepts labels, their frozen scores and unlabeled scores; it has no training
or data acquisition API. `source_evidence/test_controls.py` provides algebra and
interface unit tests. These were not run during writing. A focused test command
is `python -m unittest discover -s source_evidence -p test_controls.py`.

`source_evidence/evaluate_final.py` preserves the evaluator. The complete local
task is available under `task/`. The original declared dependencies are preserved
in `source_evidence/requirements.txt`; this is a declaration, not a claim that
all its versions were independently resolved in the artifact-only environment.
The evaluator expects its original task directory and worker setup, not a copy
with only the entrypoint moved. A full replay command, **not executed here**, is:

```sh
python task/evaluate_final.py \
  --program_path "$PWD/source_evidence/program.py" \
  --results_dir /tmp/replayed-final-results
```

Use the original task execution environment for this command; retain
`task/resources/final/`, its manifest, and its worker dependencies. The final
archives are already present locally and need not be downloaded to replay the
recorded inputs. The preserved final manifest reports 3340.755 seconds elapsed
for the original evaluation; this is not a newly measured writing-stage runtime
or a guarantee on another CPU. Source tests and replay can be run independently;
neither is claimed as completed in this paper-writing step.
<!-- @evidence[[source_evidence/final_manifest.json#compute_usage/elapsed_seconds]] -->

### Data versions and acquisition

`source_evidence/resource_manifest.json` records the exact hashes, sampling,
normalization, seed list, and empirical-source origin. The final data are at
`task/resources/final/{linear,nonlinear,uninformative,rare_outcome,gene_expression}.npz`.
Synthetic draws are archived for seeds 1000--1399; the stored generation
description states uniform scalar scores and Bernoulli outcomes but does not
supply all conditional functions. Replaying the archived inputs is supported;
reconstructing missing functions from condition names is not.

The upstream gene-expression example comes from `ppi-python==0.2.3`, repository
revision `6b8475b53f0303e4abc4d1eb0b94aa8052f9b940`. Acquisition in an original,
separate environment is:

```python
from ppi_py.datasets import load_dataset
data = load_dataset('./data/', 'gene_expression')
```

This resolves the Google Drive URL recorded in the manifest. The downloaded
archive checksum is
`72565d2d88ed6a16331b3423da5dee036e97f2220fad054eb139ced1942e3303`.
The existing final unique-record table, not this full upstream archive, defines
the empirical-source target. Normalization and duplicate grouping precede a
hash-sorted development/final split. The precise original preprocessing code is
not supplied in this workspace; no replacement reconstruction is claimed.
Underlying promoter strings are not available. Independent data redistribution
rights are undeclared; do not infer them from the code's MIT license.
<!-- @evidence[[source_evidence/resource_manifest.json]] -->

### Randomness and uncertainty

- Final statistical seeds: 1000--1399, 400 repetitions per condition.
- Synthetic resource RNG: PCG64, `SeedSequence([seed, case_index, 17923])` as
  documented in the resource manifest.
- Empirical sampling: `SeedSequence([seed, 4, 17923])`, with replacement.
- Permutation control: `SeedSequence([seed, 991])`, separate permutations in
  the two prediction pools; outcomes unchanged.
- Inference seed: for each condition, the evaluator cycles through the first
  64 statistical seeds (1000--1063), using `reset_seeds[index % 64]` for
  repetition index 0--399. Selection uses outer and inner permutations. This
  reset seed is distinct from the statistical sampling seed after index 63.
  No cross-episode state is retained.
- Coverage intervals: Clopper--Pearson with tails `0.05/(7*4*2)`.
- Width intervals: existing paired bootstrap, 512 resamples, RNG 79231, tail
  `0.05/42`. This budget gives limited extreme-tail resolution. We do not
  describe the percentile intervals as exact simultaneous confidence sets.
<!-- @evidence[[source_evidence/evaluate_final.py#L920-L974]] -->
<!-- @evidence[[source_evidence/evaluate_final.py#L1001-L1023]] -->

## Literature and venue

`retrieve_screened_references.py` retrieves exact permitted works and dated
historical foundations only. It uses direct DOI lookups or exact-title lookup;
arXiv metadata overrides ambiguous bibliographic search matches for the three
exact permitted preprints. Metadata and available abstracts are saved in
`reference_evidence/`; no citation graph is followed. Some books and historical
works lack an API abstract; their consultation is metadata-only, and related
citations are topic attribution rather than claims to have checked a theorem.
Initially supplied unscreened modern entries were quarantined and never used.
No prohibited-work encounter was identified during writing. No inference about
the prohibited work's identity, title, authors or conclusions was made.

The ICLR 2026 official style, bibliography style and original template were
retrieved from `ICLR/Master-Template/iclr2026`; checksums and exact URLs are in
`source_evidence/template_provenance.json`. Venue year follows `VENUE.md`.
The source is double-blind and includes LLM Usage disclosure. The official
template does not contain a separate checklist; none is fabricated.

## Unresolved scientific requirements

The returned interval is not a finite-sample certificate. The exact fallback
does not certify the outcome-dependent combined rule. The nonlinear headroom
identities do not imply realized gains or identify a component's effect.
Independent final byte identity, a full preprocessing reconstruction, code/data
redistribution rights, controlled component ablations, other sample-size
regimes, and external biological generalization are not established.
