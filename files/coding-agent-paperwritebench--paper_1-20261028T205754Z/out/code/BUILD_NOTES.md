# VL-Rethinker manuscript

Build the manuscript with:

```sh
python3 build_paper.py
```

The source is `template.tex`; the output is `template.pdf`. The manuscript uses
an external `references.bib` and `unsrtnat`, and retains the template's
AI-Generated watermark. It includes all seven supplied figure assets (the
qualitative example shows the reasoning panel only) and all three supplied tables.

## Formatting dependency

The supplied template requests `neurips_2025.sty`, but that file was not provided
and is not installed. Attempts to obtain the official style were rejected by the
network service with HTTP 403, `blocked by time shielding`. The source preserves
`\usepackage[preprint]{neurips_2025}` when that file is available and otherwise
loads the clearly identified `paper_preview.sty`. The latter is a local preview,
not an official conference style or a claim of submission-format compliance.
It uses 10-point Times, a 5.5-by-9-inch text block, and the explicitly requested
two-column layout. The supplied NeurIPS template normally uses a single column;
conference compliance and final pagination must be checked with the official
style before submission. No official style file has been fabricated or modified.
The missing Inconsolata package similarly falls back to Courier.

## External bibliography

`references.bib` has not been edited. Its SHA-256 is:

```
98854ecb5af941f875052896dfc663e87b1ce91212832829d7ad58a6e648cd62
```

The original database contains 34 BibTeX syntax errors in uncited entries,
primarily duplicated field separators. A direct `latexmk`/BibTeX run therefore
returns an error. `build_paper.py` streams the original database, copies only the
27 cited entries **verbatim** into a temporary external file also named
`references.bib`, invokes BibTeX there, and builds the PDF from the resulting
bibliography. It changes no citation keys, fields, or bibliography metadata.
It checks for missing citation keys, unresolved references, and any change to the
original bibliography. The generated `.bbl` is also included in the workspace.

## Evidence corrections

The immutable files under `tables/` remain untouched. The manuscript includes
presentation copies under `writeup_tables/`. All underlying model scores are
preserved, with corrected best-score formatting and these corrected deltas:

- 7B MathVista: 74.9 - 73.0 = **1.9**, rather than 4.7.
- 7B MathVerse: 54.2 - 50.3 = **3.9**, rather than 6.3.
- 72B MathVision versus the strongest listed external open model:
  44.9 - 38.4 = **6.5**, rather than 6.8 (which compares only with the 72B backbone).
- 72B MMMU versus the strongest listed external open model:
  68.8 - 70.3 = **-1.5**, rather than -1.4.

Bold marks the best score across each table, including proprietary models.
Reported results are not claimed as independently reproduced experiments.
The paper distinguishes the roughly 39K released dataset pool from the 16K
ablation mixture, and retains the 32B results and negative comparisons.

## Implementation findings reflected in the paper

- `group`/`group_sft` use mean-centered advantages, not group-standardized ones.
- The training reward includes validity and checking-marker shaping; the
  binary-reward derivation is explicitly a simplified analytical case.
- `ppo_train` omits `do_filter` when calling `active_sampling`, whose false default
  bypasses the SSR/filter branches. This snapshot cannot by itself reproduce the
  reported SSR experiment. The research code has not been altered.
- The actual policy loss clips ratios to [0.8, 1.35] and uses a token-level mean.
- The auxiliary likelihood predicate is a positive advantage plus a checking
  marker, not an explicit correctness test.
- Single-sample evaluation uses greedy decoding, despite other launcher defaults.
- The plotted rethinking bound uses answer correctness and is described as an
  oracle diagnostic. Figure/table precision discrepancies are retained explicitly.
- No speedup, confidence intervals, per-class findings, or unlogged experiments
  are invented. The qualitative example is not counted as a verified success.

## Final validation

The local preview compiles to **11 double-column pages including references**.
The method overview is on page 2. All 27 citation keys resolve, all labels are
unique, and all cross-references and figure paths were checked. The final LaTeX
log contains no errors, unresolved references, or overfull boxes. Some ordinary
underfull-box warnings remain. Model-score rows in the presentation tables were
checked against the originals after stripping only emphasis commands; only the
explicit delta rows and presentation were changed. PDF text was extracted to
check pagination and content placement; a full rendered-page visual inspection
was unavailable in this environment.
