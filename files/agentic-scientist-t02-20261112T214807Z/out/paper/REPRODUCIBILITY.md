# Reproducibility and evidence boundaries

The manuscript reports existing observations only. It does not rerun training or
the sealed evaluation. Scientific qualification is **failed**, independently of
the manuscript's compilation or production status; its specific cause is unknown.
The read-only `paper_data.json` remains the authoritative observation registry.

## Supplied code and data

- `source_evidence/task/evaluate.py`: original development evaluator.
- `source_evidence/task/evaluate_final.py`: final evaluator, with a SHA-256 that
  matches `paper_data.json.final_evaluation.evaluator_sha256`.
- `source_evidence/task/capture.py`: evaluator subprocess capture dependency.
- `source_evidence/controllers/studied/`: inspected common configuration.
- `source_evidence/controllers/larger_init/` and `faster_update/`: sensitivity settings.
- `source_evidence/task/resources/{search,final}/dataset.json`: exact synthetic
  input/label pools, split indices, seeds, and split digests. No dataset download
  or third-party data version is involved. The two resources have disjoint inputs.
- `derived/source_manifest.json`: hashes of inspectable source snapshots.

Hashes locate source; readable code supports implementation claims. The controller
settings agree with retained evidence, but no independent reconstruction of the
entire frozen candidate tree is claimed.

## Analysis-only reproduction

Use a private environment outside the paper directory:

```sh
python3 -m venv /tmp/paper-analysis
/tmp/paper-analysis/bin/pip install -r scripts/requirements-analysis.txt
/tmp/paper-analysis/bin/python scripts/build_artifacts.py
/tmp/paper-analysis/bin/python scripts/build_overview.py
/tmp/paper-analysis/bin/python scripts/build_claims.py
```

Analysis generates `derived/observations.json`, `derived/summary.json`,
`derived/final_records.tex`, `derived/norm_loss_records.tex`,
`derived/coverage_table.tex`, `derived/development_table.tex`, source hashes,
`figure_manifest.json`, and vector PDF/450-DPI PNG quantitative plots. It reads all
numbers from recorded curves and checks recomputed onset fields. It uses sample
SD with denominator n-1 and exact beta-quantile event-count intervals, conditional
on retained records; no missing outcomes are imputed for descriptive comparisons.

The designated concept-figure workflow failed before rendering because its
configured backend lacked `RWE_CODEX_API_KEY` (see `concept_figure_run.log`).
`scripts/build_overview.py` replaces the placeholder with a grounded Matplotlib
fallback, exporting canonical PNG/PDF files. The manifest records the actual
generator, failed designated workflow, and original prompt-log path. The analysis
builder preserves this entry and any completed render; it never changes the
orchestrator-owned completion marker. The fallback script deliberately does not
modify `figures/study_overview.png.prov.json`, whose acceptance is host-owned.

## Table and figure mapping

| Manuscript item | Generator and inputs |
|---|---|
| Study overview | `scripts/build_overview.py`, inspected design + observation definitions; fallback after designated renderer failure |
| Width endpoints | `scripts/build_artifacts.py`, development/final curves |
| Fitting/generalization onsets | Same script; sustained three-checkpoint events |
| Final coverage table | Same script, `derived/coverage_table.tex` |
| Development summary table | Same script, `derived/development_table.tex`, displayed to two decimals |
| Final norm/loss diagnostics | Same script, `derived/norm_loss_records.tex` |
| Complete final table | Same script, `derived/final_records.tex` |

Generated table content is embedded in `paper.tex` to satisfy the standalone
supplement contract. Figures use vector PDF where available. The source registry,
not rounded manuscript values, is authoritative for recomputation.

## Original training reproduction (not executed during writing)

The original implementation pins NumPy 2.1.3 and PyTorch 2.5.1+cpu and uses
deterministic CPU operations with at most two worker threads. Linux resource
limits and subprocess isolation are part of the supplied evaluator. To recreate
the workload in a compatible Linux environment:

```sh
python3 -m venv /tmp/modular-addition-training
/tmp/modular-addition-training/bin/pip install numpy==2.1.3
/tmp/modular-addition-training/bin/pip install torch==2.5.1+cpu \
  --index-url https://download.pytorch.org/whl/cpu
/tmp/modular-addition-training/bin/python source_evidence/task/evaluate.py \
  --program_path "$PWD/source_evidence/controllers/studied" \
  --results_dir /tmp/modular-addition-development
/tmp/modular-addition-training/bin/python source_evidence/task/evaluate_final.py \
  --program_path "$PWD/source_evidence/controllers/studied" \
  --results_dir /tmp/modular-addition-final
```

Do not replace `paper_data.json` with new outputs. These commands rerun an
evaluation, not merely the analysis, and are not a guarantee of full grid
completion or qualification on different hardware. Inspect isolation prerequisites
in the supplied sources before execution. Development seeds are 101 and 211;
final seeds are 60613, 70717, 80821. Initialization is paired across widths and
the stored split is shared by conditions within a seed. Recorded selected
development evaluation times were 981.221 and 754.246 seconds; final seed totals
were 3198.605, 2793.934, 3487.684 seconds. The latter include missing cells and
overhead and are not completion-time estimates for the entire grid.

## Compilation and evidence checks

Use a TeX Live installation with `pdflatex`, `bibtex`, and Poppler `pdftotext`:

```sh
python .codex/skills/validate-paper/scripts/validate_tex_refs.py \
  --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
```

The local dependency guard rejects this container's normal TeX configuration
symlink, which resolves outside its enclosing approved directory. The canonical
figure checker also imports an unavailable host `src.orchestrator` module.
These limitations are documented in `validation_report.json`; no validator was
modified. Direct sanitized LaTeX/BibTeX compilation and rendered-supplement checks
are recorded separately, not represented as a canonical full validation pass.

## Literature access and unresolved reference quota

Only the eight exact starter originals in the framing contract were downloaded
from their exact arXiv PDF addresses. Their abstracts and opening first-page text were consulted for
the specific claims used; extracts retain the first two pages for context, and
provenance distinguishes extraction from consultation. Full-paper review is not claimed.
No recommendations or citation networks were followed. Unrelated supplied
retrieval records were excluded rather than cited. No prohibited work was
intentionally sought or identified, and no known prohibited encounter is claimed.
This restricted bibliography has eight references and cannot satisfy the requested
25--30 range without relaxing the framing contract. That requirement remains
unmet; no unconsulted, irrelevant, or fabricated references were added to hide it.

The prior reference-query and strategy files remain unchanged. Provenance and
claim validation do not upgrade the failed final scientific qualification.
