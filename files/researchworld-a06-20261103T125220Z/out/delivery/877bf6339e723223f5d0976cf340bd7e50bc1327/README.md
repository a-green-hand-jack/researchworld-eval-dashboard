# Benchmark scores after prompt selection

The research paper and reproduction package are integrated in this repository. Read [paper.pdf](paper.pdf), with source [paper.tex](paper.tex). **Status: complete paper and evidence package prepared for independent final review. Final release requires approval and merge of the final pull request.**

The study combines 288 controlled simulation settings with newly generated Qwen2.5-1.5B-Instruct answers on pinned MMLU-Pro. The real winner scores 36.72% on reused search questions versus 25.39% on a disjoint audit, but the default also has a substantial search–audit gap. The real-cache calibration finds positive bias without observed nominal interval undercoverage in this small bank. The paper distinguishes these findings from synthetic large-bank failures.

## Build and verify

The build uses the unmodified official ICLR 2027 anonymous initial-submission template, with a nine-page main-text limit. This is a research-report format, with no claim of conference submission or acceptance. [Venue requirements](venue/venue-requirements.md) records official sources and required statements. TeX Live with pdfLaTeX/latexmk/BibTeX, GNU Make, Python and PyMuPDF are required; [build versions](docs/build-environment.json) are recorded.

```sh
make paper
make check
```

`make check` verifies analysis SHA/size manifests, plotting inputs against analysis outputs, all 18 synthetic/real plotting inputs and eleven real output routes, local manuscript/README references, unchanged official assets, US Letter dimensions, references, overflow, required statements and the main-text page boundary including deferred floats. Scientific validity and visual legibility require separate review.

## Reproduce without inference

The repository contains all 6,144 actual main responses, the retained 768×4 binary matrix, completed synthetic/real analyses, provenance, code, environments, failure records and seeds. The original model/data bytes are acquired separately from pinned public URLs. Cached statistics and rendering require no model download or new inference.

From the root, install `analysis/requirements-analysis.txt` if needed. Run validation from `analysis/`:

```sh
cd analysis
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/validate_real.py
python3 tests/check_fetch_inputs.py
```

The measured-result check verifies the full 15-cell grids, primary counts/target transformations, 210 probability/MCSE identities, mixture weights/candidate axes, and 2,000 bootstrap records. Acquisition-choice checks make no downloads. The parser/assembly checks require the separately built native inference dependency; upstream complete-environment passes are recorded, while the report environment's cached checks do not claim a new native-backend run.

For the full simulation, from `analysis/`:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 tests/check_synthetic.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/run_synthetic.py --reps 20000 --out results/synthetic-main.jsonl
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/exact_null_reference.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/summarize_synthetic.py
```

The main synthetic run used master seed 20261103, 20,000 repeats per 288 cells and took 89.881 seconds excluding startup/imports. [Real reproduction commands](analysis/docs/real-reproduction.md) specify cached assembly, conditional reselection, empirical-cache calibration, summaries, paired bootstrap and diagnostics. The completed real statistics took 2.697, 1.971 and 36.471 seconds for conditional selection, calibration and bootstrap, excluding imports. Main seeds are 20261107, 20261106 and 20261108, with primary tie seed 20261109. These are resampling computations, not additional model runs.

Install `presentation/requirements.txt` if needed, then from the root run:

```sh
python3 presentation/render.py
python3 presentation/render_real.py
```

[Presentation documentation](presentation/README.md) maps the current figures/tables to scripts, inputs and captions, with recorded hashes and native artwork dimensions. [Real rendering instructions](presentation/REAL-README.md) cover its seven figures/four tables. Each renderer takes roughly 10–15 CPU wall seconds here and performs no statistical experiment. [Paper figure/table map](docs/figure-table-map.md) gives the final numbering, location and generator for every display.

## Acquire inputs or regenerate responses

The pinned MMLU-Pro revision is `b189ec765aa7ed75c8acfea42df31fdae71f97be`; loaded counts are 12,032 test/70 validation items, 14 categories and 3–10 answer options. Model/data source revisions, URLs, sizes and SHA-256 values are in `analysis/provenance/downloads.json`. From `analysis/`, `python3 scripts/fetch_inputs.py --model 1.5B --list` lists exact inputs; remove `--list` to acquire them. The model is Qwen2.5-1.5B-Instruct Q4_K_M. Native CPU generation requires llama-cpp-python 0.3.18 and the documented compiler/CMake build; exact original environments and working build flags are retained. See the linked real reproduction instructions before regenerating.

The delivered primary design is the prespecified Tier C fallback: four candidates `[0,10,14,13]`, search 256/audit 512, 3,072 analyzed answers. The completed parent shard generated eight candidates on these 768 questions: **all 6,144 calls are preserved and charged**, including excluded candidates. Regeneration uses historical Tier B shard **0 only**, followed by the frozen Tier C subset assembly. **Do not generate shard 1 for this study.** Original larger-design manifests are historical records; the current plan is [study/plan.md](study/plan.md) and the gate is [study/real-scope-decision.md](study/real-scope-decision.md).

Actual main timing is 75.66 hours process elapsed, 15.58 hours process CPU and 7.63 hours resource active wall; the accounting discrepancy is unresolved. A regeneration forecast should not replace these measurements. Main prompt/completion tokens are 1,424,801/13,785; both validation pilots bring cumulative successful inference to 6,258 calls. The compute ledger and failures include build/setup, failed wheels, interrupted download, backend cap behavior, every main response and all pilot costs. No GPU, paid API or training was used.

Primary exact finite-population inference concerns the 11,776 benchmark items outside the retained search reservoir. Runtime-chosen B/C designs receive error .025 each, plus within-design multiplicity where needed, giving at least 95% coverage unconditionally over partition/design choice separately per endpoint family. No runtime-trigger-conditional coverage or unbiasedness is asserted. The separate 768-row empirical-cache iid calibration retains nominal 95% binomial methods. [Measured handoff](analysis/docs/real-handoff.md) and [statistical guarantees](analysis/docs/statistical-guarantees.md) give exact target distinctions.

## Layout, provenance and access record

| Material | Location |
|---|---|
| Manuscript/PDF and build checks | `paper.tex`, `paper.pdf`, `sections/`, `references.bib`, `docs/` |
| Settled questions, scope, comparison and ownership | `study/`, `.forgejo/CODEOWNERS` |
| Analysis, all raw responses/matrices/results, environments and provenance | `analysis/`; 119 source files identified in `source-manifest.json` |
| Figures, numerical tables, rendering inputs/code and mappings | `figures/`, `tables/`, `presentation/` |
| Official ICLR 2027 assets and captured requirements | `venue/` |
| Historical working prose and checks | `working/`; superseded by root manuscript |

The organization consulted the permitted primary sources at versions recorded in the bibliography/source notes. The manuscript owner read the supplied notes and frozen task materials and does not claim independent reading of every cited primary PDF. [Literature provenance](docs/literature-source-provenance.json) and [access record](docs/literature-access-record.md) state actual scope. No attempt to identify the withheld related paper was made, and no prohibited-material encounter was observed by this role.

[Integration state](docs/integration-state.md) records current checks and remaining gates. The complete paper has eight main-text pages and 29 pages including statements, references and appendices. All 13 figures and five numerical tables are integrated at native sizes. Independent internal approval of the complete final pull request and its merge are required for final delivery.
