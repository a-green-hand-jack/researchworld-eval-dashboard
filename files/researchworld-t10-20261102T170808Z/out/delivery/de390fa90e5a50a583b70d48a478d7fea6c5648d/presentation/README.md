# Delivered figures and tables

Two main displays pair validity and precision: `figures/main_comparison.pdf` and `figures/finite_comparison.pdf`. Five appendix figures expose sample-size effects, archived-population behavior, failure regimes, finite-sample costs and the finite-N theory check. `tables/main_results.tex` is a compact optional main table. Other tables include all **405** completed method/setting cells, exact binary comparisons, width tails, analytical ratios and verified method assumptions. [captions.md](captions.md) contains final captions and an exact input/output/function map.

All numeric inputs are committed experiment-repo results at revision **317d3f6eb010c335540a0d685581f17554fa812e**. Their exact snapshots are retained in `presentation/source/` and their SHA-256 hashes in `render_manifest.json`. These are copies for presentation reproducibility, not newly computed analysis. The underlying draws and analysis generators are delivered separately under results/ and code/.

From the delivered paper root, regenerate every figure and table:

```sh
python3 presentation/render.py --results results --out . --source-revision 317d3f6eb010c335540a0d685581f17554fa812e --width 5.5
```

Use `--results presentation/source` to regenerate from the included exact snapshots instead. The snapshot rerender was run and reproduced every numeric artifact and figure byte for byte. A complete rendering took **11.4 seconds** in this two-CPU sandbox, excluding package setup; time depends on the machine. `--theory-only` regenerates only the analytical table and its manifest, so use a separate output directory for partial inspection if preserving the full manifest.

`presentation/requirements.txt` pins the rendering and PDF-inspection packages actually used; `render_manifest.json` records the numeric/rendering environment. Python was 3.11. TeX Live 2022 / pdfTeX 1.40.24 and Poppler pdffonts 22.12.0 supplied the table/font checks. No random seed is needed for deterministic rendering; the experiment seeds and repetition design are recorded in the analysis delivery.

Inspect tables in the official NeurIPS style from the paper root:

```sh
mkdir -p presentation/check-build
TEXINPUTS="$PWD/venue/official:$PWD/presentation:" pdflatex -interaction=nonstopmode -halt-on-error -output-directory=presentation/check-build presentation/inspect_tables.tex
TEXINPUTS="$PWD/venue/official:$PWD/presentation:" pdflatex -interaction=nonstopmode -halt-on-error -output-directory=presentation/check-build presentation/inspect_tables.tex
python3 presentation/check_artifacts.py --root . --table-pdf presentation/check-build/inspect_tables.pdf --table-log presentation/check-build/inspect_tables.log
```

Use booktabs and longtable in the manuscript. The complete-results input supplies its own longtable captions and repeated regime headings; do not wrap it in a floating table. Other table files are tabular bodies, with captions supplied in captions.md. Main/appendix figures must be included at their native 5.5-inch width, using width=linewidth. Preserve their aspect ratios.

All seven figures were opened individually, their PDFs reopened/rendered, and all 12 pages of the compiled seven table outputs inspected. The PDFs fit the selected venue width, have embedded outline fonts and no Type 3 fonts; tables compile without overfull boxes. `inspection.json` records the checks. Every source cell remains in full_results.tex and all_cells.csv; all paired comparisons remain in all_paired.csv. Small nonzero Monte Carlo errors use significant digits/scientific notation and are not rendered as zero. Final integrated root-PDF inspection remains a handoff check after the report owner incorporates these files.

Statistical claims remain analysis-owned. Captions distinguish asymptotic coverage evidence, theorem-backed bounded/CP guarantees, Monte Carlo uncertainty and archived-record empirical-population sampling. No prohibited literature was accessed in presentation work.
