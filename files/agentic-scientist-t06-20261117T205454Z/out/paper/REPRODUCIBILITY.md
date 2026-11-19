# Reproduction and provenance

## Scope and known gap

This package regenerates all reported quantitative plots and tables from the sealed
observations in `paper_data.json`. It contains readable evaluated selector and evaluator
snapshots under `source_evidence/`, including descriptive development comparators.
The workspace's `task/resources/{search,final}` contains normalized observations and
manifests. The `task` and `results` links point to staged run artifacts, not public
repositories. Do not interpret those links as a complete standalone data release.

A complete raw-source-to-normalized-partition builder and the original downloaded
archives were not staged. End-to-end raw reconstruction therefore remains incomplete.
The manuscript explicitly preserves this limitation. No new scientific evaluation,
optimizer experiment, bootstrap draw, or comparison condition was run during writing.

## Environment

The evaluated CPU analysis declares `numpy==2.2.6` and `scipy==1.15.3` in
`source_evidence/requirements.txt`. Use a Python environment with those requirements
for scientific reruns. The evaluator sets BLAS/OpenMP-related thread counts to two.
Its source requires Linux process isolation/resource controls and checks those controls;
do not remove them to obtain a nominally successful result.

Manuscript plotting additionally needs matplotlib, Pillow, and NumPy. During writing,
auxiliary packages were installed in `/tmp/paper-tools`, outside the manuscript tree.
`paper-tools-versions.txt` records the actual installed manuscript-tool versions.
The presentation-only repair regenerated plots with the preinstalled
`/opt/autoillustrate-venv/bin/python` (matplotlib 3.10.9, Pillow 12.2.0, NumPy 2.4.6);
the derived numeric summaries and tables remained byte-identical.
Compilation requires pdflatex, BibTeX, the installed LaTeX packages used in `paper.tex`,
and Poppler utilities for rendered validation. The selected local ICLR style has a
5.5-inch text width and 9-inch text height; no geometry settings were changed.

## Public data acquisition

Download originals to a private `data/` directory, not into a distributable code tree.
These commands specify the upstream inputs only; they do **not** replace the missing
normalization builder.

```sh
mkdir -p data
curl -L --fail \
  https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv \
  -o data/arena_train.csv
curl -L --fail \
  https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv \
  -o data/nbaallelo.csv
sha256sum data/arena_train.csv data/nbaallelo.csv
```

Expected SHA-256 values are:
- Arena: `0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2`
- NBA: `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc`

Sources declare Apache-2.0 and CC-BY-4.0, respectively. Consult upstream terms before
redistributing data. The pinned NBA README was consulted at `literature/NBAdata.md`.
The manifests in `source_evidence/manifests/` record the original and normalized
payload hashes, normalization, grouping, component filtering, and overlap audit.
No source hash is offered as substantive support for an implementation claim.

## Regenerate paper artifacts (no experimental rerun)

```sh
python build_paper_artifacts.py
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
```

In the writing environment, invoke `/tmp/paper-tools/bin/python` for plotting.
The plotting command took seconds locally; elapsed values are recorded in
`paper_validation_report.json`, not presented as a scientific runtime comparison.

Artifact mapping:
- Figure 1 (`figures/audit_overview.png`): synchronous concept-figure renderer owned
  by the parent workflow; the guarded placeholder is deliberately not a result plot.
  The plotting script never overwrites a completed render.
- Figure 2 (`figures/dataset_budget_comparison.{pdf,png}`):
  `build_paper_artifacts.py`, unpermuted final curves, random means over recorded seeds.
- Figure 3 (`figures/conditional_resampling_contrasts.{pdf,png}`): same script, one
  unique stored conditional group-weight block; display jitter seed 41.
- Table 1 (`results_table.tex`): same script, stored curves and floored mask lengths.
- Development table: direct registry values embedded in `paper.tex`, mapped in
  `claims_grounding.json` to the three development source IDs.
- Complete conditional table (`bootstrap_table.tex`, embedded verbatim in the
  supplementary manuscript to satisfy source validation): same script, stored gains
  converted to percentage points, without new resampling.
- `analysis_summary.json`: same extraction, including unrounded values.

Quantitative PDFs remain vector graphics; PNG exports use 450 DPI and are at least
2400 pixels wide. Adjacent provenance
sidecars link the derived artifacts to the immutable evidence registry and script.

## Scientific rerun from staged normalized inputs (not executed during writing)

```sh
TASK_SOURCE_DIR="$PWD/task" AGENTIC_TASK_QUALIFICATION=1 \
  python source_evidence/evaluate_final.py \
  --program_path "$PWD/source_evidence/selector.py" \
  --results_dir /tmp/ranking-final-rerun
```

This command requires staged resources and the declared evaluator environment.
The evaluator internally uses seeds 1009, 2027, 4051, 8089, and 16127, with canonical
and reversed rows for both datasets. Its conditional uncertainty RNG seed is 709237;
the clean and high-loss procedures are deterministic. Wall limits are source-defined
limits, not measured expected runtime. The original final manifest records elapsed
evaluation time of about 208 seconds on the original environment; hardware portability
and rerun time have not been measured here. A writing-time rerun was deliberately not
performed. Scientific reruns must not overwrite `paper_data.json` or its final sources.

## Literature access and exclusions

Existing retrieval output contained irrelevant matches and duplicate records. It was
replaced by exactly identified foundational ranking, influence, and resampling works,
the explicitly allowed Arena/influence/removal/vote-rigging identities, and the pinned
NBA documentation. `references_provenance.json` records exact endpoints and consulted
local files. Where no abstract was available (Bradley--Terry, Zermelo, Kendall), only
the bibliographic record was consulted; no detailed external result is attributed to
these records. Other references were consulted at abstract or documentation level,
not claimed as fully read papers. A wrong DOI for Ford and one for Field were rejected
by title and resolved with exact-title queries. A guessed Maystre arXiv identifier
resolved to an unrelated spinor paper; its abstract was seen and excluded, and that
identity is not cited. The final bibliography uses the exactly identified Rank
Centrality work instead. The PMLR endpoint was unavailable. These were unrelated
identity mismatches, not encounters with the prohibited study. No prohibited-study
page was knowingly accessed, no title/authors/results of it were inferred, and no
citations, related-paper lists, or derivatives were traversed.

## Checks

```sh
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
python .codex/skills/validate-paper/scripts/validate_figures.py --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
```

The last command additionally audits compilation inputs and rendered supplementary
content. `paper_validation_report.json` distinguishes successful checks from any
environment-specific tool limitation; no failed gate is represented as passed.

In this container, Poppler packages and libraries were extracted under
`/tmp/paper-tools` rather than installed in the manuscript tree. The compile wrapper
used `PATH=/tmp/paper-compile-bin:/tmp/paper-tools/usr/bin:$PATH` and
`LD_LIBRARY_PATH=/tmp/paper-tools/usr/lib/x86_64-linux-gnu`. Its pdflatex shim selects
the installed canonical TeX configuration directories
`/usr/share/texlive/texmf-dist/web2c:/etc/texmf/web2c` before invoking
`/usr/bin/pdflatex`. This resolves the system TeX-config symlink rejected by the
input auditor; the unchanged canonical compile and rendered-SI validators then pass.
The figure-validation launcher imports an unstaged `src.orchestrator` module and
cannot run in this container. Local checks instead validate the canonical figure
JSON schema, strategy density budgets, source IDs, referenced paths and PDF geometry;
the parent workflow retains authority for its integrated figure audit.
