# Artifact audit

All checks passed on 2026-11-04 UTC.

- Exactly five allowed PDF files; signatures valid and SHA256 hashes match access log.
- Exactly five BibTeX records with the expected arXiv IDs; braces balanced (structural check, not a full BibTeX compilation).
- Body-only extracts contain no References section headings.
- All three official template/style/checklist files exactly match the archived originals.
- Required source list, notes, bibliography and conference rules exist and are nonempty.
- No experiments or LaTeX compilation run. Reading and verification limitations are documented.

## Files

Paths below are relative to `/work`; this audit itself is `/work/literature/audit.md`.

- `./literature/2210.07316.body.txt`
- `./literature/2210.07316.pdf`
- `./literature/2402.14992.body.txt`
- `./literature/2402.14992.pdf`
- `./literature/2405.10938.body.txt`
- `./literature/2405.10938.pdf`
- `./literature/2407.12844.body.txt`
- `./literature/2407.12844.pdf`
- `./literature/2412.06540.body.txt`
- `./literature/2412.06540.pdf`
- `./literature/_offline_pdf_text.py`
- `./literature/_prepare_reading.py`
- `./literature/access_log.md`
- `./literature/reading_notes.md`
- `./literature/references.bib`
- `./literature/sources.md`
- `./paper/Formatting_Instructions_For_NeurIPS_2026.zip`
- `./paper/RULES.md`
- `./paper/_fetch_official.py`
- `./paper/neurips2026/checklist.tex`
- `./paper/neurips2026/neurips_2026.sty`
- `./paper/neurips2026/neurips_2026.tex`
- `./paper/neurips2026_call_for_papers.html`
- `./paper/neurips2026_call_for_papers.txt`
- `./paper/neurips2026_main_track_handbook.html`
- `./paper/neurips2026_main_track_handbook.txt`
