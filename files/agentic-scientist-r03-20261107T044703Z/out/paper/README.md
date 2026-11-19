# Variance-guided benchmark reconstruction: paper artifacts

This directory contains `paper.tex`, `paper.pdf`, `claims_grounding.json`, the inspectable retained implementation in `source_evidence/downstream/program/`, and saved evaluator evidence in `paper_data.json`. Performance measurements are frozen; manuscript preparation does not rerun them. Final qualification is **completed / qualified**, independently of the selection outcome. Three alternative evaluations have missing scores, not measured losses. The selected source is unchanged from the original reference. Exact final-snapshot byte identity is not certified: final and selection tree digests differ and a separate archived final source tree is unavailable.

## Evidence and data

- Model regimes: MTEB embedding models and Open LLM generative models, fitted independently.
- MTEB: https://github.com/embeddings-benchmark/results at `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`.
- Open LLM: https://huggingface.co/datasets/open-llm-leaderboard/contents at `9c09a7cae43334062a82cb164f2ef255013dafa2`.
- `task/resources/final/audit.json` specifies extraction, normalization, deduplication, source archive/table hashes, and license caveats. `task/resources/final/plan.json` specifies splits, frozen rosters, budgets, aggregation, uncertainty, and runtime.
- MTEB uses original bounded test main scores, default/English subsets, distinct task/revision/subset columns, and lexicographic revision tie-breaking. Open LLM uses six Raw columns. Follow the audit, not a current leaderboard or normalized score columns.
- Reacquire the MTEB archive via `https://github.com/embeddings-benchmark/results/archive/6dabbcc68c28ea5f180ce7df79347b3ca9cc6383.tar.gz`. For Open LLM, enumerate files via `https://huggingface.co/api/datasets/open-llm-leaderboard/contents/tree/9c09a7cae43334062a82cb164f2ef255013dafa2?recursive=true` and download the parquet using its revision-specific `/resolve/` URL. Compare SHA256 with the audit before extraction. No new acquisition is necessary to regenerate manuscript figures from the frozen summaries.
- Open LLM has an undeclared dataset license. Public access is not a redistribution license. The supplied extracted pool is a private research artifact; obtain source authorization before redistribution. Independently reacquire the pinned table.
- `task/` and `results/` are staged links to the accompanying run artifacts, not self-contained downloads. Preserve these directories alongside this manuscript when packaging the deliverables. All code used for this paper is present in the staged workspace, but this is not an assertion of public redistribution rights.

## Regenerate static figures and tables

Keep tools outside the manuscript tree, for example:

```sh
python -m venv /tmp/paper-tools
/tmp/paper-tools/bin/pip install -r paper_build_environment.txt
/tmp/paper-tools/bin/python build_paper_artifacts.py
```

The exact versions actually used are recorded in `paper_build_environment.txt` (prefer that snapshot over example commands if versions differ). No benchmark evaluation is run by this script. It reads numerical values from `paper_data.json`, excludes replay, exports vector PDF and 300-DPI PNG, and writes provenance sidecars. Approximate figure-generation time on this writing host is seconds; no portable runtime or peak-storage bound was measured.

| Manuscript artifact | File / generator |
| --- | --- |
| Figure 1, conceptual overview | `figures/concept_overview.png`; orchestrator-owned `generate-concept-figure` workflow; draft placeholder is guarded against overwriting a finished render |
| Figure 2, six-policy source/split comparison | `figures/main_comparison.pdf`; `build_paper_artifacts.py` |
| Figure 3, paired historical-column control | `figures/historical_dependence_control.pdf`; same script |
| Figure 4, supplementary checkpoint curves | `figures/budget_sensitivity.pdf`; same script |
| Table 1, pooled score and MAE | `tables/pooled.tex`; same script, included directly by LaTeX |
| Table 2, all primary seed scores | `tables/seed_scores.tex`; same script, its contents embedded in Supplementary Information for strict source validation |
| Table 3, all paired controls | `tables/controls.tex`; same script, contents embedded in Supplementary Information |

`derived_results.json` holds unrounded descriptive means, standard deviations and individual saved scores. These are summaries of existing results, not new experiments. The supplied bootstrap interval is not recomputed from the three seed means.

## Independent evaluation reproduction (not executed during writing)

The recorded environment is CPython 3.12.15, NumPy 1.26.4, SciPy 1.12.0, PyArrow 16.1.0; see `task/requirements.txt`. A supported Linux x86-64 kernel with Landlock/seccomp and the trusted broker is required for the production isolation protocol. The native evaluation entrypoint accepts a **Python source file**, not a directory:

```sh
python task/evaluate_final.py \
  --program_path source_evidence/downstream/program/src/program.py \
  --results_dir /tmp/reproduced-final
```

This native invocation needs an appropriately isolated supported host; production used the broker-mediated interface. It is not a recipe for bypassing isolation. Fixed seeds are 1009, 1013, 1019; budgets are MTEB 1/2/4/8 and Open LLM 1/2/3. The final evaluator's wall limit is 3600 seconds; the saved seed durations are about 24.08, 22.89, and 23.08 seconds on the original host, not a prediction for other machines. Source acquisition is additional. Reruns should not overwrite `paper_data.json` or the original final evidence. Missing baseline checkpoint arrays cannot be reconstructed from saved baseline averages.

## Literature and manuscript build

The 25 active references were restricted to exact allowed starter identifiers and foundational-method DOIs/titles. `references_provenance.json` records consulted abstracts and one full factorization paper. `literature/READING_NOTES.md` records rejected metadata and scope. No citation graph was expanded and no prohibited-material encounter was identified in this writing step. Re-retrieval is optional and does not affect frozen results:

```sh
/tmp/paper-tools/bin/python retrieve_allowed_references.py
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
```

The last command needs `pdflatex`, `bibtex`, and `pdftotext`. Use the supplied single-column ICLR review style without altering its geometry. Canonical system-root validation and figure validation may depend on orchestration modules absent in a minimal container; `validation_report.json` records actual checks and environment limitations rather than asserting unchecked success. Figure 1 remains a deliberately reserved placeholder until the orchestrator's synchronous render; the paper's quantitative figures and results are complete independently of it.

The study compares changing-remainder policies, not fixed-target prediction, and does not establish response-adaptive acquisition, calibrated uncertainty, universal budget sufficiency, or speed superiority. Read the manuscript limitations before reusing inferred model scores.
