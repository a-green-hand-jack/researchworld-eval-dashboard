# Document build and inspection

From the delivery root:

```bash
make paper
make audit
make inventory
```

The build uses the unchanged official `venue/official/neurips_2026.sty`, `manuscript/main.tex`, TeX Live's `latexmk`/`pdflatex` and BibTeX. Intermediate files stay in `build/latex/`; the built PDF is copied to root `paper.pdf`. The style uses anonymous review option `main`. `courier` avoids a Type 3 fallback; `xcolor` supports official checklist answers. The explicit `\input{./checklist.tex}` loads the answered manuscript checklist even though TEXINPUTS searches official assets first. No fallback paper or placeholder evidence is generated when an input is missing.

`make audit` writes `pdf-audit.json` and `checklist-audit.json`. It checks actual page/font/technical properties and preserved official checklist wording plus filled answer fields. The current paper has eight content pages, references starting on page 9, 35 total pages and 37 embedded fonts. These diagnostics do not judge scientific support, answer truth, figure readability or complete venue compliance. `make inventory` maps compiled labels/pages to all ten figure and ten table artifact hashes in `manuscript/display-inventory.json`.

`final-inspection.md` and `final-page-proof-facts.json` record the report owner's actual full-document rendering inspection. `link-audit.json` records internal destinations and external-link syntax without requesting the external targets. `manuscript/review-inventory.md` enumerates evidence and unresolved review work. Re-render display pages with:

```bash
python3 presentation/inspect_document.py --root . --output /path/to/new-proofs --dpi 144
python3 presentation/verify_manifest.py --root .
python3 code/scripts/verify_bundle.py --root . --output /path/to/new-verification.json
```

The bundle check verifies supplied file identities; it does not independently replay training. Use the complete pipeline in `reproduction/README.md` for raw/derived recomputation. [Presentation-owner inspection](../presentation/integrated-final-inspection.json) and [venue compliance](../venue/inspection/2026-11-07.md) pass for the exact current PDF; [integration checks](final-owner-integration.md) preserve their scope. [Final access consolidation](../reproduction/final-access-consolidation.md) is integrated and its [R1 response/identity checks](final-provenance-integration.md) are complete. Formal independent exact-head approval remains separate.

Historical preview and working-control inspection records retain their exact dated scope. The incomplete preview target and PDF have been retired; `make paper` builds the full document. Unanswered-checklist negative checks and original build failures are preserved as history, not final failures or extra scientific replications. Actual build tools/versions are in `environment.txt`.
