# Third-party assets and responsible reuse

## Datasets (not redistributed in the code archive)
- **Arena human preference 55k**: lmarena-ai/LMSYS; Apache-2.0 as pinned README metadata. Version, exact URL and SHA256 in `data/manifest.json`; associated paper Chiang et al., arXiv:2403.04132 (consulted). Local compliance copy: `artifacts/compliance/arena_readme.txt`.
- **MT-Bench human / GPT4 pair judgments**: LMSYS; CC-BY-4.0 as pinned README metadata. Associated work Zheng et al., arXiv:2306.05685 (consulted). Files and checksums in manifest; local README `artifacts/compliance/mt_readme.txt`.
- **NBA Elo source game table**: FiveThirtyEight, fivethirtyeight/data; CC-BY-4.0 as pinned repository LICENSE. Attribution must be retained on reuse; source repo `https://github.com/fivethirtyeight/data`, fixed commit and raw URL in manifest. Analysis filters season year IDs 2013–2015, `_iscopy==0`, maps results to binary outcomes; does not modify original data. License copy `artifacts/compliance/nba_license.txt`.
- Dataset source URLs are publicly accessible without accounts at retrieval. Public availability is not a warranty of original consent or label correctness. No new data collection, deanonymization, or live voting was performed. Download original assets separately under their licenses. Derived aggregate outputs and witness row references are supplied with attribution; no prompt/answer text is included in the archive.

## Official template
`paper/template/neurips_2026.sty`, the official example `.tex` and `checklist.tex` are unchanged conference-supplied assets, obtained through the official 2026 CFP. Original copyright/header and checklist guidance are preserved. They are not covered by the original-code MIT grant. See `paper/template/PROVENANCE.md` for official archive, hashes, and page rules. Filled checklist and manuscript are original documentation using those assets.

## Dependencies
Dependencies are installed by package manager, not vendored or redistributed. Numerical/plotting packages retain original copyrights and licenses (NumPy/SciPy/pandas BSD-family; matplotlib PSF-based; requests Apache-2.0; pyarrow Apache-2.0; pytest MIT; pypdf BSD-3-Clause; threadpoolctl BSD-3-Clause). Full installed versions are recorded in requirements and environment freeze; transitive packages retain their own terms. This is asset attribution for this release, not a legal opinion or a certification of all upstream practices.

## Literature and independence
Research citations are only the five actually read, user-authorized papers in `paper/references.bib`; detailed reading extents are in `artifacts/literature_notes.md`. Source PDFs/HTML were obtained directly, not through broad search or citation-following. Downloaded paper files are excluded from the code archive. No attempt was made to identify the unspecified prohibited paper. No prohibited-source incident was identified. The local audit's mandatory memory preflight encountered a project-summary snippet, not a new retrieved paper; it was not used as audit evidence. Official ethics policy (`https://neurips.cc/public/EthicsGuidelines`) and pinned data READMEs/LICENSE were additionally directly retrieved for the required checklist/license assessment; no links in further-reading lists were followed.

## Intended use and limits
Offline statistical auditing and reproducibility only. Do not claim these witnesses establish actual errors, judge bad faith, attack feasibility, global minimum budgets, causal evaluation-design effects, or production leaderboard ranks. Potential misuse for vote manipulation and misleading rank publicity is discussed in the paper. No security vulnerability in a live service was discovered or exploited, so this release is not a vulnerability disclosure or a validated defense.
