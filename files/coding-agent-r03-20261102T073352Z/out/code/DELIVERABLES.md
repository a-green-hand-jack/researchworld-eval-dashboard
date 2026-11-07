# Deliverables

- Paper PDF: `paper/main.pdf` (23 total pages; 8 content pages, within the official NeurIPS 2026 nine-page limit).
- Complete LaTeX: `paper/main.tex`, `paper/references.bib`, `paper/checklist.tex`, `paper/generated/`, `paper/vendor/` and `figures/`.
- Research code: `scripts/`, exact environment `requirements.txt`, entry point `run_all.sh`.
- Reproduction and data details: `README.md`; fixed raw sources under `data/raw/`; analysis matrices and cell-level provenance under `data/processed/`.
- Executed outputs: `results/`, including per-model losses, selection orders, split memberships, tuning records, bootstrap summaries and resource records.
- Transparency: `PROTOCOL.md` (local initial design), `RESEARCH_LOG.md` (adjustments, failures and corrections), `logs/` (executed logs).
- Final audit: `results/audit.json`; all recorded checks pass, including 196 split/query records, 28,969 recomputed model predictions, full MTEB cell provenance, finite outputs, theory bound, official-style identity and page limit.
- Portable bundle: `research_bundle.tar.gz` contains all authored code, paper source/PDF, figures, processed matrices, outputs and reproduction documentation. The local environment, raw MTEB archive, raw OLL parquet and downloaded reference PDFs are omitted; acquisition URLs and checksums are included.
- File hashes: `MANIFEST.sha256` covers the portable bundle's source/output files; `research_bundle.tar.gz.sha256` hashes the archive itself.

The study is complete as documented, with restricted conclusions rather than a universal budget guarantee. No conference submission, public upload, or communication to third parties was performed.
