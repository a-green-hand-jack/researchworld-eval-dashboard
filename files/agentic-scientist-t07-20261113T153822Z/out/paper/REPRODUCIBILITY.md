# Reproduction scope

This package reproduces the paper's descriptive analysis of frozen evaluation records. It does not claim a fresh end-to-end evaluation or repair the failed final qualification. The host-generated `paper_data.json` is read-only. No new estimator experiments or final evaluations were run during manuscript preparation.

## Environment

The artifact-generation environment used Python 3.12.15 on Debian 13, with NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2, Pillow 13.0.0, jsonschema 4.26.0, PyMuPDF 2.1, and requests 2.34.2. The manuscript uses the supplied ICLR style, pdfLaTeX and BibTeX from TeX Live 2025/dev/Debian. These are the observed writing-environment versions, not recovered versions of the original evaluation environment. The evaluator additionally imports scikit-learn and threadpoolctl; their original versions are not established here.

Install auxiliary Python packages outside the manuscript workspace:

```sh
python -m venv --system-site-packages /tmp/paper-venv
/tmp/paper-venv/bin/pip install numpy==2.5.4 scipy==1.18.1 matplotlib==3.11.2 pillow==13.0.0 jsonschema==4.26.0 pymupdf==2.1 requests==2.34.2
/tmp/paper-venv/bin/python build_paper_artifacts.py
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
```

The transformation is deterministic and performs no random sampling or model fitting. It reads seeds and query budgets from the evidence. Original final seeds are 5003, 7001 and 9001; requested item prefixes contain 8, 16 and 32 items. The manuscript-generation runtime is recorded separately in `artifact_build_runtime.txt`; it is not an estimator or language-model inference runtime. No independently verified full-evaluation runtime estimate is available.

## Data and evaluated sources

The task specifies binary response matrices from snapshot `55faff496947789f94e6b5908c77cbc3e84f81ad`. For upstream score acquisition, download only the fixed score files from the task-provided location:

```sh
SNAPSHOT=55faff496947789f94e6b5908c77cbc3e84f81ad
mkdir -p /tmp/benchmark-score-data
for name in bbh gpqa musr openllm_math commonsense gsm legalbench math med_qa mmlu; do
  curl --fail --location "https://raw.githubusercontent.com/socialfoundations/benchmark-prediction/$SNAPSHOT/data/scores/$name.jbl" --output "/tmp/benchmark-score-data/$name.jbl"
done
```

These commands are supplied from the task's data instructions and were not executed during writing. Do not unpickle untrusted files. Raw downloads do not recreate the evaluator's staged matrices by themselves: column alignment, filtering and provenance-group construction are required. `source_evidence/final_data_manifest.json` records the actual staged case matrix hashes, normalization, split rule and limitations. The original evaluator and selected estimator are provided as readable snapshots, together with their entrypoint manifest and method notes. Local matrix resources remain under `task/resources/final/` in the supplied environment. Full reconstruction outside that environment requires those resources; the frozen prediction registry is sufficient for the manuscript's descriptive results.

For a future independent full assessment, the inspected evaluator CLI accepts the following command. It was **not executed** during writing. It requires NumPy, SciPy, scikit-learn, threadpoolctl, Linux process/resource facilities, and the original staged resources; exact original dependency versions and identical timing behavior are not established. Always write fresh output outside the sealed evidence:

```sh
TASK_SOURCE_DIR="$PWD/task" TASK_PYTHON=/tmp/paper-venv/bin/python \
  /tmp/paper-venv/bin/python source_evidence/evaluate_final.py \
  --program_path "$PWD/source_evidence/selected_method.py" \
  --results_dir /tmp/independent-few-item-assessment
```

The command does not imply that a fresh outcome would reproduce the missing-output pattern, diagnose its cause, or change the frozen qualification status used in this paper.

`source_evidence/selected_method.py` is copied byte-for-byte from the selected delivered source identified by the registry. `source_evidence/evaluate_final.py` is copied from the supplied evaluator; its SHA-256 equals the evaluator hash recorded in `paper_data.json.final_evaluation`. Inspect the source files for implementation details. Hashes alone are not substantive support for those details, nor proof of every execution path.

## Figure and table map

| Paper artifact | Producer | Input and interpretation |
| --- | --- | --- |
| Figure 1, `figures/method_and_evidence_overview.png` | Orchestrator-owned `generate-concept-figure` workflow | Grounded strategy plus manuscript. A guarded draft placeholder and `{}` prompt-log stub are supplied until synchronous rendering. |
| Figure 2, `figures/available_pair_method_comparison.pdf` | `build_paper_artifacts.py` | Final target means and primary/fitted-uniform/anchor/IRT predictions; common available pairs only. |
| Figure 3, `figures/budget_accuracy_and_ranking.pdf` | `build_paper_artifacts.py` | Same evidence, with primary/fitted-uniform/selected-mean/uniform-mean comparisons on a shared support mask. |
| Main aggregate table | Transcribed in `paper.tex` | Frozen `final_evaluation.metrics`, including evaluator defaults. |
| Main audit table | `derived_results.json` plus evaluator inspection | Missing primary/reference records, failed structural checks, paired fallback and replay diagnostic. |
| Supplementary source-location table | Source inspection | Readable line locations in `source_evidence/`. |
| Supplementary case table | `build_paper_artifacts.py`, `tables/case_mae.tex` | Available matched MAE, equal budget and target weights within seed. |
| Supplementary budget table | `build_paper_artifacts.py`, `tables/budget_metrics.tex` | Equal source-domain mass, equal case mass within source, equal available-seed mass within case. |
| Supplementary primary seed table | `build_paper_artifacts.py`, `tables/primary_seed_metrics.tex` | Every recorded primary case-seed result, including missing rows and realized target/group counts. |
| Exhaustive numerical ledger, `complete_metrics.csv` | `build_paper_artifacts.py` | All recorded conditions/references, four metrics per case/seed/budget, with separate availability and structural status; null predictions remain blank. |

Generated numerical rows are embedded between markers in `paper.tex`, rather than imported as unchecked supplementary TeX. Rebuilding refreshes those rows. Quantitative figures are exported as vector PDF and 300-DPI PNG; the manuscript uses PDF. The script never overwrites an existing overview or an orchestrator completion marker. Per-case/seed inputs to the plots are retained in `derived_results.json`; null entries identify unavailable records, not measured losses. Rank correlations use the evaluator's zero convention for exactly constant truth or prediction vectors, checked by peak-to-peak range rather than floating-point standard deviation.

## Evidence boundaries

The final evaluation completed and did not qualify. Commonsense primary and reference predictions are missing at seeds 5003 and 9001; matched structural failures are recorded there. The precise underlying exception is not recorded. Conditional plots use 28 common case-seed pairs, not an imputation or repaired evaluation. Seed partitions overlap; dots are descriptive, not independent confidence replicates. The reported paired interval endpoints are fallback values. No profile-only benefit, fixed-predictor selector-only effect, calibrated uncertainty or overall superiority is established.

## References and access restriction

The supplied bibliography contained unrelated retrieval hits; they were discarded. Exact permitted starter DOI/arXiv identifiers and classical methodology DOIs were queried without broad literature search, citation-graph traversal or identification of the prohibited unnamed paper. Semantic Scholar exact-ID requests returned HTTP 429; OpenAlex exact-DOI retrieval was used as the documented fallback. `reference_consultation.md` records the returned metadata/abstracts that were inspected. Where no abstract was returned, citations provide bibliographic context only, not claims about uninspected experiments. A mistaken classical DOI returning an unrelated historical statistics title was rejected and replaced with the verified equivalence-of-design-problems citation. No prohibited source was identified or deliberately accessed; no citation graph or upstream research code repository was read during this paper step. The task's explicitly permitted starter references were used within their stated scope.

## Validation

### Targeted citation enrichment

The post-draft citation pass added only `Baker2001` and `OpenLLMLeaderboard` and reused `Liang2023`. `reference_consultation.md` records the exact official destinations, inspected book pages and collection metadata; `references_provenance.json` stores the two new records and consulted-file hashes. Baker's scanned source was read visually, including the Rasch/2PL definitions and item-information formula. The living collection page is undated, not represented as a frozen historical version. These citations supply background only; all staged-data and performance claims retain their artifact grounding. No experiments or evaluation reruns were performed.

The base `retrieve_vetted_references.py` recreates the original exact-DOI bibliography, not the two manually curated additions. Preserve the final `references.bib` and `references_provenance.json` for exact manuscript reproduction; to rebuild references independently, append the two documented records after running the base retriever. Two exact official blog URLs returned HTTP 404; the permitted collection homepage was used instead. No restricted source was identified or encountered.

During this targeted pass, the standard compile/rendered-SI wrappers additionally lacked `pdftotext`. Direct pdfLaTeX/BibTeX compilation succeeded, and the PyMuPDF-based local verifier checked actual rendered body geometry and references/Supplementary Information ordering. Canonical figure validation still requires the absent `src.orchestrator` package, and the canonical recorder rejects a standard TeX configuration symlink. These are validation-environment limitations, not passed canonical checks. The overview remains the guarded orchestrator-owned placeholder pending its synchronous render.

```sh
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py --paper-data paper_data.json --references references_provenance.json --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
/tmp/paper-venv/bin/python verify_paper_artifacts.py
python .codex/skills/validate-paper/scripts/validate_rendered_si.py --pdf paper.pdf
```

The local verifier checks actual JSON-pointer paths, manifest schema, numerical reaggregation, figure paths, standalone language, rendered references/Supplementary Information ordering, body-page count and geometric last-page fill. The base scientific-evidence verifier reports unsupported locator grammars as anchored; the local pointer checks supplement it.

Two canonical wrapper limitations are documented, not hidden: `validate_figures.py` cannot import the absent `src.orchestrator` package, and the compile recorder rejects `/usr/share/texmf/web2c/texmf.cnf` because its standard symlink resolves into a different approved TeX root. Direct no-shell-escape pdfLaTeX/BibTeX compilation and rendered Supplementary Information validation succeed. Figure schema/readability and body-layout checks are performed locally; the parent orchestrator must rerun its complete checks after replacing the overview placeholder. These wrapper errors are not scientific qualification diagnostics.

## Figure-validation repair

The quantitative strategy used the descriptive type `grouped_dot_plot`, which is not a canonical schema value. Its two quantitative type fields and the corresponding manifest fields now use `scatter`; the grouped-dot presentation, data, panels, placement, and captions are unchanged. The builder copies the strategy type rather than substituting `composite`, and preserves the existing orchestrator-owned overview record. Larger source canvases with proportionally scaled typography regenerate the quantitative PNGs at 300 DPI and at least 2400 pixels wide, without upscaling existing rasters. PDF remains the manuscript's quantitative-figure format. The local verifier now enforces strategy/type agreement and PNG resolution.

During repair, the installed orchestrator package was located outside the manuscript at `/workspace/task/.venv/lib/python3.12/site-packages`. With that directory on `PYTHONPATH` and validator dependencies in `/tmp/paper-repair-venv`, canonical figure validation passed for all three figures without warnings. This supersedes the earlier figure-wrapper import limitation only; it does not establish that the complete canonical compilation gate passed. Direct compilation and local rendered-layout checks passed again. The overview pipeline's failed-render record and placeholder remain orchestrator-owned and unchanged. No evaluation, measured result, manuscript claim, reference, or scientific qualification was changed.
