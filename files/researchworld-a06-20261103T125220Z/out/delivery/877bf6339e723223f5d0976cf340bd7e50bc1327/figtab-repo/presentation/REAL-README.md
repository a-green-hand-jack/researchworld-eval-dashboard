# Reproduce measured real-model presentation

From the delivery root, use the same pinned Python environment as the synthetic package (`presentation/requirements.txt`):

```bash
python3 presentation/render_real.py
```

The CPU render takes roughly10–15 seconds here. It reads only16 small, hash-verified committed inputs under `presentation/inputs/real/` and runs no LLM inference or statistical resampling. It exports seven vector PDFs and PNG previews in `figures/`, four booktabs LaTeX tables and full-precision derived CSVs in `tables/`, and previews compiled from those actual table sources. `pdflatex`, `booktabs`, `geometry` and Poppler `pdftoppm` are required for table previews. Preview TeX sources are retained in `presentation/real-*-preview.tex`.

Upstream repository/revision, exact input paths, SHA-256 hashes, versions and real interval guarantees are in `presentation/real-provenance.json`. The analysis owner supplies its full raw outputs, model/data acquisition, code, seeds, manifests, diagnostics and costs separately under `analysis/` in paper. This package copies approved main aggregate inputs, not pilot values or artificial fixtures. Original full inference is6144 generated main answers, of which3072 are analyzed; validation adds114 successful calls. Rendering incurs no new inference.

The primary target is question-weighted accuracy on11776 benchmark questions outside the entire retained256-item reservoir, audited on512 questions. Exact real intervals allocate alpha .025 per possible B/C design plus the exported within-design adjustments; their guarantee is at least95% unconditional over partition and runtime tier choice, separately per endpoint family. No conditional-on-trigger or joint-all-endpoint guarantee is asserted. The separate known-cache calibration uses768 retained paired rows/four candidates, iid replacement draws and original nominal95% methods.

All figures are native5.5-inch width with at least8pt plot text. Use full linewidth without further shrinkage. Table sources require `booktabs` and fit the5.5-inch text area at8pt. `presentation/real-captions.md` supplies complete claim/target/uncertainty/cost captions and suggested placement. `presentation/real-output-map.json` gives machine-readable script/input/setting mapping. The displayed n256/K4 table is a declared presentation slice, not a preregistration claim.

| Output | Inputs / setting |
| --- | --- |
| real-cache-main | Cache summary; compact main optimism for all K and coverage for three methods at K4, all n |
| real-primary | Primary result, candidate audit, primary gap decomposition; n256/K4 |
| real-cache | Cache summary; optimism all K, reporting/quality at K4; all n |
| real-conditional | Conditional-selection summary and selection frequencies; complete15-cell grid |
| real-cache-coverage-grid | Coverage for all five methods and all15 cells |
| real-cache-mse | Score MSE for all point-estimate protocols and all15 cells |
| real-diagnostics | Retained format counts and mapped paired-row correctness correlation |
| real-reporting table | Primary scores/intervals/decisions and logical comparison calls |
| real-cache-methods table | All five protocols at declared n256/K4; bias/coverage/width/quality/cost |
| real-bootstrap table | Original conditional means and completed1000x2000 bootstrap sensitivity at n64/256,K4 |
| real-cache-decisions table | All15 cells; known-cache false-superiority counts with full MC intervals in CSV |

MC bands in cache figures are marginal exact95% binomial intervals for probability metrics and mean±1.96MCSE otherwise. MSE is multiplied by10000 for squared percentage points. These quantify computational uncertainty conditional on the empirical cache, not independent model/audit replications. Exact finite-audit bounds and approximate bootstrap ranges have separate labels and inputs. Displayed rounding never changes source values; table CSVs retain full precision.

The rendered claims preserve the material qualifications: the full11.33pp winner gap is not selection-only optimism (default gap8.59pp); empirical-cache point optimism coexists with no observed naive undercoverage across this small heterogeneous bank; and the primary audit supports improvement that the conservative reuse rule does not declare. No population false-positive reuse decision was demonstrated. The single model/cache/partition, prompt format failures and runtime-driven fallback limit generalization.

Optional inspection aid (PyMuPDF/Pillow versions are recorded in the provenance):

```bash
python3 presentation/check_real_layout.py --output-directory /tmp/real-layout-check
```

This uses `venue/official/iclr2027` from the paper delivery by default; when checking the figure-only source repository, pass `--style-directory` pointing to those unmodified official assets. It compiles the retained seven-page diagnostic, rasterizes every exported PDF, checks native widths/fonts/text bounds, and records `presentation/real-render-check.json`. Open its contact sheets for human inspection; the checks do not establish scientific validity.

Compact main allocation (paper request figtab#6): use real-primary at its native5.5×3.65in and real-cache-main at5.5×2.65in; concise checkable captions are in real-captions.md. These two figures total6.30in of artwork before captions. All four numerical tables and the complete four-panel real-cache display remain available for appendix placement. Cache x-axes and budgets count **question draws**, with replacement, rather than distinct question identities. real-reporting explicitly separates selected-accuracy calls (s) from paired-comparison calls (p); its full-precision CSV retains both columns. The original logical_calls_for_comparison column remains compatible.

The additional `presentation/real-main-layout-check.tex` compiles both compact main figures with the supplied concise captions, using the same unmodified official style. Its two default float pages include unused whitespace and are a readability check, not a claim about final manuscript page consumption. The root manuscript remains the authority for final placement.
