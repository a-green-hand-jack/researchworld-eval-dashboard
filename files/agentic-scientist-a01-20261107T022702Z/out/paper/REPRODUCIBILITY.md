# Reproducing the score-space study

## Scope

The manuscript analyzes immutable final records, not the development search trajectory. The three final seeds repeat a fixed target panel. No training, new experiment, or evaluator rerun was performed during paper preparation. `scripts/reproduce_allocations.py` only recomputes arithmetic on existing selected subsets and all-task endpoints. It does not establish optimality independently of the recorded reference bounds.

The separate development comparison had zero score difference from the original baseline. The final assessment is independently completed and qualified. Development and final weighted scores have different scopes and are not subtracted. These facts are preserved in `claims_grounding.json`.

## Files and versions

- `paper_data.json`: read-only host evidence registry, including all original and control records and final qualification.
- `data/helm.json`, `data/openllm.json`, `data/protocol.json`: byte-identical local copies of the supplied frozen final resources. Local byte hashes are in `derived/checksums.json` and the adjacent provenance sidecars.
- HELM MMLU release **v1.13.0**, obtained through the public bucket's subject JSON files.
- Open LLM contents commit **9c09a7cae43334062a82cb164f2ef255013dafa2**, parquet file `data/train-00000-of-00001.parquet`. The separate per-model results dataset is not used.
- Historical acquisition date: **2026-11-07**, recorded in the frozen resources. `derived/upstream_provenance.json` lists every used upstream URL and SHA-256. Source-row indices and aliases remain in the resources.
- Scores use the published higher-is-better scales: HELM divided by 1; the six normalized Open LLM leaderboard columns divided by 100. Raw columns are not additional tasks. Scores and response endpoints round to ten decimals; co-first tolerance is `1e-10`.
- Known aliases and exact raw-score content are clustered before the frozen split; the content split seed is `20261027`. Targets are mean-rank-spaced nonwinners in fixed row order. Runtime seeds are `42011`, `42013`, `42017`.

`requirements-evaluated.txt` records the supplied evaluation dependencies. `requirements-paper.txt` pins the actual extraction/plotting environment used here; `derived/environment.json` records its interpreter and platform. These environments are explicitly distinct. The retained final evaluator source matches the final manifest's evaluator digest. The selected entry-point file matches the retained downstream source file; tree hashes in the selection and final records have distinct scopes and are not silently equated.

## Rebuild the existing analysis and document

Use a private environment outside the manuscript tree:

```sh
python3.12 -m venv "$TMPDIR/paper-reproduce"
"$TMPDIR/paper-reproduce/bin/pip" install -r requirements-paper.txt
export PATH="$TMPDIR/paper-reproduce/bin:$PATH"
python scripts/build_results.py
python scripts/reproduce_allocations.py
python scripts/build_claims.py
python scripts/build_provenance.py
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
python scripts/build_provenance.py
python scripts/audit_paper.py
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
```

Compilation requires a TeX Live installation with the packages in `paper.tex`, BibTeX and Poppler's `pdftotext`. The official unmodified ICLR 2026 style and bibliography style are bundled. `template_provenance.json` records the official ICLR repository, download path, file checksums and geometry. The paper keeps review mode, with no identifying author block. The official template does not supply a separate conference checklist; disclosures are included in the supplement, including LLM Usage.

This container lacked Poppler utilities and exposed an approved-to-approved TeX configuration symlink rejected by the strict input validator. Poppler binaries and required libraries were extracted privately under `$TMPDIR`; a private `pdflatex` wrapper uses only `/etc/texmf/web2c` and `/usr/share/texlive/texmf-dist/web2c` for configuration. No validator was modified and no manuscript dependency was hidden. A normal complete TeX/Poppler installation does not require these container-specific wrappers.

The staged `validate_figures.py` imports an unavailable parent `src.orchestrator` module. `scripts/audit_paper.py` therefore directly validates the same canonical JSON schema, strategy density limits, actual files, evidence JSON pointers, embedded tables and local rendered geometry. The parent orchestrator's final readability/page validation remains authoritative.

The extraction, plotting and arithmetic checks are CPU-only. Recorded local wall times for document rebuild commands are in `derived/rebuild_times.json`; they are not solver benchmarks or estimates of training cost. A fresh upstream download depends on network availability and is not included in those local times. No GPU or paid API is required for numerical reproduction.

## Regenerate public score resources separately

The exact supplied acquisition code is retained as `scripts/acquire_scores.py`. To avoid modifying the frozen manuscript evidence:

```sh
python scripts/acquire_scores.py \
  --cache "$TMPDIR/leaderboard-source-cache" \
  --output_root "$TMPDIR/reacquired-leaderboard-resources"
```

This code downloads only the pinned Open LLM contents parquet and HELM release subject summaries, canonicalizes content, clusters known aliases, partitions raw content before feature scaling, and writes both partitions. It has a frozen historical acquisition-date field; running it later does not establish that historical download time. Compare source-byte hashes and final output hashes with `derived/upstream_provenance.json` and `derived/checksums.json`. If upstream bytes differ or access fails, stop and report the mismatch rather than silently substitute another release. Final protocol parameters are retained separately in `data/protocol.json`.

The code license and per-model license fields do not license the score tables. The public score sources have no separately declared score-data license in the supplied provenance. These local copies are retained for isolated research reproduction, not a statement of redistribution permission. Reacquire with attribution and review rights before public redistribution.

## Figure and table generation map

| Artifact | Source and command |
|---|---|
| Main complete budget table | `scripts/build_results.py` → `tables/budgets.tex`, from first-seed original records, validated against all seeds |
| Paired mean/median figure | Same script → `figures/paired_mean_median_budgets.pdf` and 300-DPI PNG |
| Reachability figure | Same script → `figures/cap_conditioned_reachability.pdf` and 300-DPI PNG |
| Complete supplement tables | Same script → `tables/helm_complete.tex`, `tables/openllm_complete.tex`; their exact contents are embedded in `paper.tex` to satisfy strict supplement validation |
| Full selected task indices and comparator records | Same script → `derived/allocations.csv`, `derived/original_records.json` |
| Recorded-witness arithmetic verification | `scripts/reproduce_allocations.py` → `derived/witness_verification.json` |
| Conceptual overview | `generate-concept-figure` pipeline owned synchronously by the parent document orchestrator, using `paper_strategy.json` and `paper.tex`; canonical path `figures/score_space_overview.png` |

The overview's blank, high-resolution reserved footprint and empty prompt log are placeholders only until orchestration. They contain no synthetic measured results. `build_results.py` never overwrites an existing overview and also honors the completion marker and nonempty prompt log. The numerical plots are vector PDFs in LaTeX; all numeric plot inputs come from original final records. NA rails mean certified unattainability, not missing observations. An out-of-range reference sentinel is never interpreted as investment.

## Literature and exclusion boundary

`references_provenance.json` contains 25 exact, consulted references and records whether the abstract or opening pages were read. The research-task seeds were accessed by exact allowed identifiers. Additional foundational references were retrieved by exact DOI, with historical exact-title queries used only to repair three incorrect identifiers. No related-content or citation-graph traversal was used. An incorrect candidate DOI returned unrelated machine-translation metadata; it was rejected, not cited. Initial off-topic bibliography matches were also rejected. No prohibited work was intentionally retrieved or identified; no inference about its title, authors or findings was made. No citations or links from the allowed seed papers were followed.

`scripts/fetch_exact_references.py` and `scripts/assemble_references.py` preserve the bounded retrieval procedure. Network retrieval is not needed to rebuild the paper. Cached consulted PDFs/opening text or substantive abstracts and metadata are in `literature/`. Reading scope is not upgraded to a full-text review where only an abstract was consulted.

## Evidence and limitations

Every original budget has a claim mapping and episode/case/observation pointers. The scientific-evidence bundle verifies target existence and sidecar trails; the local audit additionally resolves JSON pointers. A resolved path alone does not prove the substantive claim. The extractor asserts independent reference closure and agreement, and arithmetic checking validates selected witnesses and full-cap failures. No code component ablation, training-response experiment, model-population confidence interval, composition sensitivity, or strict-victory analysis is supplied. These are limitations, not unreported positive findings.
