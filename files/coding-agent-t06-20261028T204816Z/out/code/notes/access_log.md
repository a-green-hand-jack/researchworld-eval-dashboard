# Restricted literature access log

Date: 2026-10-28 UTC. No open-ended literature search, title/author guessing,
citation following, or prior ranking-robustness repository access was performed.
Only the task's explicitly allowed starter-paper URLs were requested. The six
PDFs below were downloaded directly and locally text-extracted. Reading scope
is described rather than claiming that every reference or appendix was read.
A latest-version URL was used except where the task pinned Huang v1. Version
markers in the retrieved PDFs identify Chiang v1, Broderick v5, Koh v3, Min v2;
Huang is explicitly v1. These are the only papers cited in the manuscript.

| Local ID | Exact requested PDF URL | Actual SHA-256 | Material consulted |
| --- | --- | --- | --- |
| `chiang2024` | https://arxiv.org/pdf/2403.04132 | 039bccd60a7d49bfda80ce17ea627654736928eee9a7ee75767a38d04a01562f | abstract and introduction; Arena collection and BT design discussion |
| `zheng2023` | https://arxiv.org/pdf/2306.05685 | 1574982845157569b85c1214bfa9987000384d7a5e3b5fbdcc5a29afec59cb81 | abstract, benchmark construction, judging methods, and position/verbosity bias discussion |
| `koh2017` | https://arxiv.org/pdf/1703.04730 | 4ac350d88d44fff186b89e96048306c702d09eaac812303f12220c012e00badc | abstract, introduction, and influence-function setup |
| `broderick2020` | https://arxiv.org/pdf/2011.14999 | b25d1b808fd68bc283c69694dd069b13c95259a762af40e92f4300bb4183ed4a | abstract, introduction, finite-sample removal metric and verification setup |
| `min2025` | https://arxiv.org/pdf/2501.17858 | 90d2df39bab4b94ddbd19633af368fdf265db6fd73e39c5fc88b10b08ae85ae6 | abstract, introduction, and attack/threat-model setup |
| `huang2025` | https://arxiv.org/pdf/2508.11847v1 | 3539869811b8dc60da3ebb0486127b5aca1a00b5e0bc468c0813ba1dd4a0f3ef | abstract, introduction, BT/removal setup, influence/refit method, tie convention, experimental setup and results, and discussion |

The literature includes Huang et al. because it is explicitly allowlisted in
`starter_literature.md`; no linked sources or repository were opened. The paper
is credited as the direct prior deletion-ranking study. Local text extraction
included reference text, but no references outside the allowlist were pursued.
No prohibited work was deliberately sought or identified, and there was no
known accidental encounter with prohibited material. We do not infer its
identity from the task or enumerate guesses.

The direct DOI URL `https://doi.org/10.2307/2334029` was requested for the allowed
Bradley--Terry original. Its returned content was an automated verification page,
not an article. Only its beginning was inspected to recognize the failure; it
was not cited as a read source. We did not search for alternate mirrors.

Official conference materials consulted:

- `https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip`
  (actual SHA-256: `8b29290f5828e176debb57ea9cc00252502973d55ea561a2f18a7f0a326bfc6c`). The official example source and style were
  inspected for page limit, author/anonymization fields, fonts, and impact rules.
- `https://icml.cc/Conferences/2026/CallForPapers`: read main-paper page rule,
  required impact statement, and generative-AI disclosure guidance. Linked
  external discussion pages were not opened. The page and locally extracted
  text are retained under `notes/`.

The official materials specify eight main-text pages, excluding references,
impact statement, and appendices. They do not specify a NeurIPS-style paper
checklist inside the manuscript. A completed project-specific reproducibility
checklist is included. The official style files are unmodified.

Dataset endpoints and revision metadata were also accessed for the four task-
listed datasets; exact URLs are in `data/manifest.json`. Hugging Face's fixed-
commit file-tree API was used solely to resolve the two named MT parquet files.
Network access otherwise served dependency installation. No live voting service,
communication tool, or external experiment API was used.
