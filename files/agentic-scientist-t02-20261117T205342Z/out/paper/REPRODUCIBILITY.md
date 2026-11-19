# Reproduction and evidence boundaries

## Scope

This bundle analyzes the retained final evaluation. It does not rerun training or
evaluate a new controller. The central result is finite-horizon memorization
without observed sustained generalization, not a generalization-time or mechanism
claim. `paper_data.json` is the unchanged host evidence registry.

The final qualification sources independently report completed/qualified/true.
Acceptance does not imply generalization, superiority, or comprehensive validity
certification. The diagnostics trust flag remains unverified. The original
lower-rate configuration has no matched final evaluation here.

## Neural training

- Dependencies: `source_evidence/requirements.txt` pins NumPy and CPU PyTorch.
- Training implementation: `source_evidence/evaluate_final.py:789` owns feature
  construction, initialization, AdamW, full-batch cross-entropy, and checkpoints.
- Controller: `source_evidence/controller/program_spec.toml` points to
  `source_evidence/controller/src/program.py`. It returns a shared constant rate.
- Seeds: read the three seed entries in
  `paper_data.json#/final_evaluation/evaluation_evidence/episodes`.
- Data: `source_evidence/resources/final/benchmark.json` is retained. The exact
  generation and partition code is at `source_evidence/evaluate_final.py:588`.
  Data are synthetic and require no downloads, accounts, or third-party licenses.
- Measurements: `source_evidence/evaluation_evidence.json` and the corresponding
  embedded final records in `paper_data.json` are the retained observations.

The original evaluator accepts `--program_path` and `--results_dir`, but depends
on an external RPC broker. A complete standalone broker launcher is not supplied.
These flags alone are not a working independent training reproduction command.
The source snapshots make the neural computation inspectable; replaying the full
execution context requires the original orchestration infrastructure. No new
training command or unmeasured runtime is invented to conceal this limitation.

The recorded seed-evaluation durations are available in `analysis/derived_results.json`.
They are actual durations, not portable hardware/runtime estimates.

## Recompute tables and quantitative figures

Create analysis dependencies outside the manuscript tree:

```sh
python -m venv /tmp/paper-analysis
/tmp/paper-analysis/bin/pip install -r analysis/plotting_requirements.txt
/tmp/paper-analysis/bin/python build_artifacts.py
```

This reads final records, checks the event and lag computations against stored
values, and writes the following artifacts without training:

| Paper artifact | Output | Source |
|---|---|---|
| Main event table | `tables/events.tex` | final observations, memorization/generalization fields |
| Complete seed table | `tables/full_observations.tex` | final traces and event fields |
| Endpoint diagnostics table | `tables/diagnostics.tex` | final checkpoint losses and parameter norms |
| Width/decay outcome figure | `figures/width_decay_outcomes.pdf`, `.png` | final five trace checkpoints |
| Censoring audit figure | `figures/censoring_audit.pdf`, `.png` | observed events and capped lags |
| Machine-readable derived results | `analysis/derived_results.json` | same final observations |

All are produced by `build_artifacts.py`. Quantitative PDF exports are vector
graphics; PNGs are generated directly at 300 DPI on an 8.25-inch-wide canvas.
The concept overview is orchestrator-owned and initially contains a deliberately
labeled placeholder. The build script never overwrites a completed concept
figure or a figure with a nonempty rendering log. No artificial trajectories
or synthetic measurements are used.

## Compile and check

```sh
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
```

Compilation requires LaTeX, BibTeX and Poppler `pdftotext`. The official ICLR 2026
style and bibliography style were retrieved from the exact official template
directory; URLs and file hashes are retained in
`source_evidence/template_provenance.json`. Review mode remains anonymous.

The bundled figure validator imports parent-only orchestration code. Where that
module is unavailable locally, schema/density checks are recorded separately and
the parent must run its authoritative figure and page-occupancy validator.

## Literature safety and unmet reference quota

Only the eight exact source identities approved by the strategy were retrieved
and consulted, at title/author/abstract scope. `literature/retrieve_approved.py`
contains that allowlist; `references_provenance.json` identifies the consulted
files and their provenance. No citation graphs, recommendations, or broad
width/grokking searches were consulted. Off-target metadata in the initial
retrieval was not used as substantive evidence. No prohibited identity was
inferred or intentionally accessed.

The requested minimum of 25 references cannot be met under the strategy's
eight-identity safety boundary. The manuscript cites eight real consulted
sources rather than padding the bibliography with unrelated or unconsulted
entries. This is an explicit unresolved submission requirement, not a successful
reference-count validation. See `submission_readiness.json` for final status.
