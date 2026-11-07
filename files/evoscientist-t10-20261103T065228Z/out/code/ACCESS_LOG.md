# Information access ledger and exclusion boundary

Task date: 2026-11-03 (UTC). This is an access-restriction report, not an exhaustive related-work search. The prohibited work's identity was neither guessed nor searched.

## Procedure
No open-ended search, citation chasing, recommendation feeds, academic aggregators, repository README browsing, or external discussions were used. Direct starter-paper PDFs were expressly permitted. Their reference lists were not pursued; incidental reference text inside permitted PDFs is noted in actual-read notes, without investigating identities. No suspected prohibited encounter occurred, so there is no hidden accidental-access content to report. If that assessment is wrong, source URLs and downloaded versions remain available for independent audit.

## Actual methodological sources

Exact download timestamps, byte sizes, hashes, headers, versions and read extents are recorded in `literature/access.tsv`, `pdf_versions.tsv`, `allowed_methods.md` and `scope_notes.md`. The following direct URLs were used:

1. `https://arxiv.org/pdf/2301.09633` → retrieved v4; mean setup, asymptotic and bounded-data finite-sample construction, selected proofs/appendices. Read ledger in allowed_methods.md.
2. `https://arxiv.org/pdf/2311.01453` → retrieved v2; mean tuning, finite-ratio lambda, pooled variance convention, theorem assumptions, selected experiment protocol.
3. `https://arxiv.org/pdf/2406.04291` → retrieved v2; designed stratification, known weights, assumptions, limitations, selected proofs. No links followed.
4. `https://arxiv.org/pdf/2309.16598` → retrieved v3; pages 1–8 only, training-vs-inference resource distinction. No citations followed.
5. `https://arxiv.org/pdf/2403.03208v2` → v2; pages 1–8 only, prospective label-allocation distinction. No citations followed.
6. `https://arxiv.org/pdf/0907.3740` → v1; title/abstract, Theorems 1 and 4 and associated variance definitions on first two pages actually read, for empirical-Bernstein constants. This 2009 concentration source is unrelated to the excluded contemporary PPI work; no references followed. Its exact-byte SHA is included in final artifact checks.

All six citations correspond to actual downloaded/read material. Full PDFs are local research reading records, not a claim of independent publication rights. Optional DML, Wine, ACS, Galaxy Zoo original articles were not accessed and are not cited as read.

## Data and packages

- `pip download --no-deps ppi-python==0.2.3`: pinned PyPI wheel. Only `ppi_py/datasets/datasets.py` was extracted/read to locate the expressly allowed example datasets; no upstream repository or README was browsed. Wheel in `vendor/` and hash in `artifacts/source_hashes.json`.
- Direct data downloads: `https://drive.google.com/uc?id=1pDLQesPhbH5fSZW1m4aWC-wnJWnp1rGV` and `https://drive.google.com/uc?id=1Vqi1wSmVnWh_2lLQuDwrhkGcipvoWBc0`. Success; sizes/hashes/license caveat in data provenance.
- pip installed `gdown==5.2.0`, `pypdf==6.1.3`, `pytest==8.3.5` and their dependencies for download, extraction, testing. The numerical stack was already installed. Package-download metadata is not used as literature evidence.

## Official conference template access

- Attempt `https://media.neurips.cc/Conferences/NeurIPS2026/Styles/neurips_2026.sty`: HTTP 404, no paper content.
- Attempt `https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles`: HTTP 404, no paper content. The first failed Python batch stopped at its initial URL; other planned URLs in that batch were not fetched.
- Success `https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip`: official template archive. Read its `example_paper.tex` formatting instructions, including 8-page initial main-text cap, references/appendix exclusions, Impact Statement guidance; used official style/bst unchanged. This is formatting guidance, not a conference proceedings/paper search.

No paid API or GPU endpoint was used. Independent subagents received the same access boundary and report no forbidden exposure. Local file/command inspection and numerical verification are not web discovery.
