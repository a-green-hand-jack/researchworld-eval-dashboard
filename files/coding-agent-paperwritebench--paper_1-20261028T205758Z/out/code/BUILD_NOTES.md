# Manuscript and build

`template.tex` is the completed double-column manuscript. It preserves the supplied NeurIPS preprint package, watermark, `unsrtnat` bibliography style, and external `references.bib` interface. It includes three tables and seven supplied image assets, with related training plots combined and the qualitative image cropped to its reasoning trace. The overview is scheduled on page 2. The original tables, figures, code, and bibliography are unchanged; corrected table presentations are embedded in the manuscript.

## Build

The official `neurips_2025.sty` was absent from the workspace and TeX installation. Attempts to retrieve it were blocked by the environment's network proxy. No replacement conference style is shipped. Once the official package is installed, run:

```bash
python3 build_paper.py
```

Or supply its directory:

```bash
python3 build_paper.py --style-dir /path/to/official/style
```

The helper builds `template.pdf`, `template.log`, and `template.bbl`. The supplied optional Inconsolata font package is loaded only if installed.

The original `references.bib` has 34 redundant comma separators that cause BibTeX parsing errors. The helper removes only those redundant separators in a temporary external bibliography copy; it never changes the source database. `template.bbl` has already been generated successfully from this process. To regenerate just the bibliography:

```bash
python3 build_paper.py --bibliography-only
```

## Verification and scope

A temporary, explicitly unofficial style shim was used outside the workspace to check LaTeX syntax and provisional double-column layout. That check produced **11 pages including references**, with the overview on page 2, no undefined citations or references, no duplicate labels, and no overflowing boxes. It does **not** establish final pagination or visual conformity under the unavailable official style. No PDF made with the shim is presented as the conference paper.

All 29 citation keys were checked against entry keys in the original database. All measured model and ablation table rows were checked against the supplied tables. Seven image paths and 34 unique labels were verified.

Corrected comparisons include:

- 7B MathVista: +1.9 points against the listed MM-Eureka score of 73.0.
- 7B MathVerse: +3.9 points against the listed MM-Eureka score of 50.3.
- 72B MathVision: +6.5 points against the strongest external open score of 38.4; +6.8 is specifically the gain over the 72B backbone's 38.1.
- 72B MMMU: -1.5 points against QvQ's 70.3.

Bolding marks the best listed score, including proprietary models in the large-model table. The text reports the 32B results, negative comparisons, imperfect qualitative correction, non-factorial ablations, and absence of measured latency or token savings. It distinguishes binary answer correctness from shaped training reward, standardized GRPO from the code's mean-centered estimator, and the intended SSR algorithm from the supplied trainer call that bypasses resampling. No new experiments were run or claimed.
