# Outcome-Flip Sensitivity of Pairwise Leaderboards

The research delivery is [paper.pdf](paper.pdf), with [LaTeX source](paper.tex), [manuscript sections](manuscript/) and [bibliography](references.bib). It audits retrospective decisive-outcome reversals in pinned public Arena preferences, human and GPT-4 MT-Bench judgments, and ten NBA seasons. Found edit counts are successful heuristic upper bounds; they are not minimum budgets or operational vote-injection attacks.

## Build the paper

With TeX Live, latexmk and BibTeX installed, run from the repository root:

```sh
make paper
```

Install GNU Make if needed, or run `TEXINPUTS=.:venue//: latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build paper.tex` and copy `build/paper.pdf` to `paper.pdf`. The build uses the official unmodified style files under `venue/`; their provenance and applicable formatting requirements are documented there. The built `paper.pdf` is kept at the delivery root for inspection. Local intermediates go to ignored `build/`.

## Reproduce the evidence

Read [analysis/README.md](analysis/README.md) for pinned dependency versions, data acquisition, seeds, complete CPU commands and measured runtimes. Raw inputs are downloaded into ignored `analysis/data/raw/`; they are not part of the submission. [analysis/results/provenance.json](analysis/results/provenance.json) records exact URLs, versions, licenses and SHA-256 values.

Read [presentation/README.md](presentation/README.md) for the script and source data corresponding to every figure and table. The manuscript appendix describes the source-to-claim chain, exact witness replay, bootstrap estimands, post-hoc control and research assistance. Numerical outputs are included for inspection without downloading raw data; refitting requires the pinned inputs.

The analysis preserves fixed comparison schedules and ties, flips distinct decisive outcomes, and measures effects with full refits. Its random-edit Monte Carlo variation, unedited-data cluster bootstraps, human-annotation selection, and convention checks answer separate uncertainty questions. Cross-dataset contrasts are descriptive.

## Research record

The [planning/](planning/) materials record the objective coverage and ownership split. The [venue/](venue/) materials record the official conference format and page rules. Public-source consultation follows the supplied independent-research restriction; the context literature record and manuscript appendix disclose its limits. AI assistance was used in the research workflow; no model was queried to create experimental judgment labels.
