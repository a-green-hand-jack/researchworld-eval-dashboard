# Reproducibility

## Scope and frozen evidence

This package describes a completed, CPU-only retrospective English embedding-model study. It does not report a newly executed benchmark evaluation. `paper_data.json` is an immutable supplied evidence registry. Final qualification is independently recorded as completed/qualified; that operational status does not establish a generalization or superiority claim. `derived_results.json` is a deterministic reaggregation of retained final records, not a new experiment. All original cases are retained, including the adverse family-disjoint split at seed 4021. No component-specific causal attribution is made. Unverified internal fitting diagnostics are not treated as measurements.

There is no downstream-study object, no additional task name list, no external component ablation bundle, and no posthoc analysis bundle in these inputs. Both evaluated holdout conditions are covered. Search scores are not mixed into final measurements.

## Files and source identity

- `source_evidence/latent/program_spec.toml` identifies the entrypoint `program.py`; `program.py`, `covariance.py`, and `mixture.py` are readable copies of the selected latent-mixture implementation, not the separate quadrature extension.
- `source_evidence/protocol/selection_manifest.json` preserves the supplied selected-source linkage. `evaluation_manifest.json` preserves final provenance and qualification. `source_evidence/manifest.json` records local file checksums. These identify provenance; implementation claims rely on the code itself.
- `source_evidence/protocol/evaluate_final.py` preserves the complete evaluator, native baseline fitting, scoring, permutation and replay logic.
- `source_evidence/protocol/resources/final/{dataset,manifest}.json` are exact copies of the supplied frozen final source documents and split specification. The duplicate `data_manifest.json` is a convenient readable protocol anchor. The source documents retain original source paths, raw checksums, normalized content and missingness.

The original MTEB data are public at `https://github.com/embeddings-benchmark/results`, revision `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383` (CC0-1.0 per supplied task metadata). For independent access, clone that named repository and check out exactly this revision. The frozen document subset and benchmark-context identities are recorded in the included dataset and manifest. Do not scrape a changing leaderboard or infer missing targets from aggregates. Signed correlations use fixed declared bounds; all other retained metric normalization is implemented in `score_cells`. Only recorded target cells are scored.

## Environment

Inference: Python 3.12 and NumPy 2.2.6, CPU only. The native isolated evaluator requires Linux x86-64, at least four assigned CPU cores, Landlock ABI 3 and seccomp support; its budget constants and operating-system restrictions are preserved in source. They are not benchmark-specific predictive inputs. The original supplied dependency specification is `source_evidence/protocol/requirements.txt`.

Manuscript environment versions are recorded in `manuscript_environment.json`. Additional plotting/validation packages are installed in a private environment outside the manuscript workspace. A reproducible setup is:

```sh
python3.12 -m venv /tmp/embedding-paper-env
/tmp/embedding-paper-env/bin/pip install -r requirements-paper.txt
```

No GPU or paid inference API is required to regenerate numeric figures and tables. Optional concept rendering belongs to the orchestration workflow; the guarded placeholder is not a measured result. The writer does not invoke that workflow or modify its completion marker.

## Regenerating manuscript artifacts

```sh
/tmp/embedding-paper-env/bin/python build_paper_figures.py
/tmp/embedding-paper-env/bin/python build_claim_mapping.py
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
```

Plot generation reads final episode records and asserts agreement with final scalar aggregates. No seed needs to be sampled again: the evaluated split seeds are 4001, 4009 and 4021; query budgets are 1, 2, 4 and 8. Per-row and per-family weighting, zero replay weight and the original/permuted distinction are implemented explicitly. Generating these small plots should take seconds to minutes depending on the machine; this is an expectation, not a measured resource saving. The recorded evidence does not measure benchmark execution costs. Complete evaluation timeouts are source constraints, not runtime estimates.

`finalize_references.py` assembles the bibliography from cached, consulted records. Running it with the manuscript environment additionally requires Beautiful Soup, specified below. It only retrieves the three explicitly named original arXiv records if absent. The earlier retrieval scripts document exact-source acquisition, but their partial/mismatched records must not be reintroduced into the final bibliography. `literature/reading_notes.md` records the consultation scope, rejected DOI match, rejected unrelated provider abstract and source-access failures. No prohibited source was searched for or encountered.

The ICLR 2026 official template archive was downloaded directly from `https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2026.zip`. `paper.sty` matches its official style after restoring the two conference header strings omitted by the initially supplied copy; `paper.bst` matches the archive bibliography style. Geometry is unchanged: 5.5-inch single text column, 9-inch text height. The submission remains anonymous and uses the review format, without acknowledgements or funding information. No additional ICLR checklist form is supplied by this template; limitations, reproducibility and LLM Usage disclosures are explicit in the manuscript.

## Figure and table mapping

| Manuscript object | Reproduction input and code |
|---|---|
| Figure 1, conceptual overview | Strategy diagram specification and manuscript; rendered by orchestrator. `build_paper_figures.py` only creates an idempotent reservation image if no completed render exists. No numerical cells are invented. |
| Figure 2, fixed-audit budget curves | `build_paper_figures.py`, final original non-replay `observations[*].audit_mae` and baseline checkpoint records; `derived_results.json.audit_budget_curves`. |
| Figure 3, historical-alignment control | Same script, original/permuted `case.audit_mae` and `case.baseline_audit` in order random-lowrank/ridge; `derived_results.json.cases`. |
| Table 1, aggregate accuracy | `derived_results.json.aggregate_original`; remaining means assert agreement with authoritative final scalars; historical-mean audit errors derive from `mean_audit_mae`. Values are rounded to five decimals in `paper.tex`. |
| Table 2, original split summaries | `derived_results.json.cases`, restricted to original arms; direct case loss and audit summaries, rounded to five decimals. |

All quantitative panel exports are vector PDF and 300-DPI PNG from one source. LaTeX includes the PDF files. One two-panel group occupies the full text width; individual panel width is 0.487 of that span, retaining roughly 9.4-point minimum labels. Raw split points are descriptive, not independent population samples or confidence intervals.

## Optional future evaluator replay (not executed for this manuscript)

In an environment satisfying the native isolation prerequisites:

```sh
python3.12 -m venv /tmp/embedding-inference-env
/tmp/embedding-inference-env/bin/pip install -r source_evidence/protocol/requirements.txt
/tmp/embedding-inference-env/bin/python source_evidence/protocol/evaluate_final.py \
  --program_path source_evidence/latent/program.py \
  --results_dir /tmp/embedding-final-replay
```

This command would rerun the supplied evaluator. It was **not** run by the paper-writing step, is not needed to regenerate manuscript figures, and does not overwrite or replace the sealed final evidence. The evaluator allows a final workload wall limit of 1800 seconds; this is not a promised runtime. Exact runtime depends on isolation support, hardware and numerical environment. An unsupported operating-system sandbox is a replay-environment failure, not measured predictive inferiority.

## Validation

Run the provided `validate-paper` section/reference checks, claim validator, figure validator, compilation and `scientific-evidence` verifier. Keep `.prov.json` files adjacent to derived artifacts. Validation results and any local toolchain adaptations are recorded in `validation_summary.json`. The authoritative report for evidence links is `scientific-evidence/verification-report.json`, which must have zero dangling references. The final concept image and prompt log remain an explicit downstream orchestration dependency rather than a claimed completed writer-produced figure.
