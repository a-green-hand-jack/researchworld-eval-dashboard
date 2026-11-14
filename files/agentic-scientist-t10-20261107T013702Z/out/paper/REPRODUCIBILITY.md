# Reproducing the paper artifacts

## Scope

This package reproduces tables and quantitative figures from existing sealed endpoint records. It does **not** reconstruct the original scientific experiment. Condition generators, condition-specific sample sizes, raw outcome/score arrays, the evaluation dependency environment, and an independently comparable final source snapshot are unavailable. No generator, dataset identity, or missing ablation is inferred. The archived safety construction has no measured performance record.

The read-only input is `paper_data.json`, especially `final_evaluation.evaluation_evidence.episodes`. The final evaluation is independently recorded as completed and qualified; this status is not statistical certification. Candidate diagnostics remain unverified. Development selection scores are not used in the paper.

## Environment

Use Python 3.12 and the exact extraction versions recorded in `reproduction_environment.json`. The preparation environment uses CPU only. Install into a private environment outside the manuscript workspace:

```sh
python -m venv /tmp/paper-tools
/tmp/paper-tools/bin/pip install numpy==2.5.4 scipy==1.18.1 matplotlib==3.11.2 pypdf==7.0.0 pymupdf==2.1 jsonschema==4.26.0 requests==2.34.2
/tmp/paper-tools/bin/python scripts/build_artifacts.py
/tmp/paper-tools/bin/python scripts/finalize_references.py
/tmp/paper-tools/bin/python scripts/map_claims.py
```

Versions describe this manuscript-extraction environment, not the unavailable sealed evaluation environment. The derivations do not refit the evaluated method. They compute coverage, widths, pointwise exact-binomial limits, paired-t limits, and collapse counts from existing endpoints. The recorded repetition seeds are available verbatim in `analysis_results.json`; no fresh scientific seeds are introduced.

`build_artifacts.py` is deterministic apart from export metadata timestamps. It is CPU-light; allow approximately a minute including process startup and exports (an execution-time estimate, not a scientific runtime measurement). It skips an existing concept image and never overwrites an orchestrator-rendered image. The concept marker is orchestrator-owned.

## Artifact map

| Paper content | Generating source | Output |
|---|---|---|
| Main coverage table | `scripts/build_artifacts.py` | `tables/coverage.tex` |
| Main mean-width table | `scripts/build_artifacts.py` | `tables/width.tex` |
| Complete supplementary summaries | `scripts/build_artifacts.py` | `tables/complete.tex` |
| Supplementary paired differences | `scripts/build_artifacts.py` | `tables/differences.tex` |
| Coverage/width comparison | `scripts/build_artifacts.py` | `figures/coverage_width_comparison.pdf` and `.png` |
| Rare-outcome diagnostic | `scripts/build_artifacts.py` | `figures/rare_outcome_diagnostic.pdf` and `.png` |
| Concept overview | Synchronous external concept workflow | `figures/frozen_score_overview.png` and prompt log |
| Derived statistics | `scripts/build_artifacts.py` | `analysis_results.json` |
| Claim map and source-copy audit | `scripts/map_claims.py` | `claims_grounding.json`, `source_evidence/manifest.json` |

Supplementary table rows are embedded directly in `paper.tex` because the strict section validator prohibits supplementary TeX imports. They are exact copies of the generated table files. Main tables use those files directly. A source change to the table extraction requires refreshing the embedded rows through an explicit manuscript patch; no original evaluation should be rerun for manuscript repair.

## Sources and data availability

The inspectable archived method is in `source_evidence/calibration/`; the manifest records copy hashes and the mounted source locations. These files describe the archived calibration family and are not certified as byte-identical to the final evaluated executable. `program_spec.toml` declares the entrypoint; `METHOD.md` distinguishes asymptotic and safety constructions. `study.py` contains reporting helpers, not an executed end-to-end experiment runner.

No named real dataset or data-download workflow is established by the endpoint archive. The general task's permitted dataset list is not evidence that any of those datasets was evaluated. Full experimental reproduction requires the missing original workload specification and data; this guide does not fabricate them.

## References

The final bibliography contains exact-identity consulted sources only. `literature/` records metadata, abstract/publisher excerpts, and selected primary-source extracts. `scripts/finalize_references.py` rebuilds the canonical bibliography and provenance from those staged records without network access. Earlier exploratory DOI mismatches remain logged but are not in the canonical bibliography. `scripts/consult_references.py` documents initial exact-DOI retrieval, not a recommended unrestricted literature search.

Reference remediation used permitted PPI/PPI++ works and explicitly screened historical foundations. No citation graph or cited-by traversal was performed. No prohibited work was intentionally searched, identified, or read, and no accidental encounter with an identified prohibited work was observed. Primary-text access failures are recorded as failures, not as full-paper consultation.

## Validation

```sh
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py --paper-data paper_data.json --references references_provenance.json --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
/tmp/paper-tools/bin/python scripts/check_paper.py
```

The standard compilation command is provided for complete TeX installations. In this container it encounters an approved-system-root symlink check and no system `pdftotext`; those tooling limits are recorded in `local_validation_report.json`. Sanitized `pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex`, `bibtex paper`, and two further LaTeX passes produce the PDF. The local checker uses the canonical figure schema and rendered-SI checking function with independent PDF text extraction; it does not claim to replace the parent's authoritative layout validator. The scientific-evidence report must have zero dangling links.

`scripts/check_paper.py` verifies real manuscript JSON-pointer targets and source-line bounds in addition to the base verifier's path checks. It also checks figure budgets, prohibited visible vocabulary, supplementary ordering, and the body-page count. The orchestrator replaces the explicitly reserved concept image and recompiles after this writing step.
