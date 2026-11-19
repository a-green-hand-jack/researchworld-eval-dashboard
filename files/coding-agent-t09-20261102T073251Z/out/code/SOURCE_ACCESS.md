# Source access and restriction record

Access date: 2026-11-02 UTC. No general web/literature search, citation-following,
related-paper browsing, title guessing, or prohibited-work identification was done.
Only exact starter-paper identifiers, the supplied public-data URLs, and exact
official conference-format URLs were requested. No prohibited-work encounter was
observed. This describes observed access; it does not claim a comprehensive
literature or priority search.

## Consulted research sources

The following five papers are explicitly on the supplied allowed starter list.
PDFs were downloaded directly, without fetching abstract or aggregator pages.
Cached PDFs and extraction files are in `/work/sources/`; third-party paper PDFs
are not copied into the distributable research archive.

| Source | Exact URL | What was consulted |
|---|---|---|
| Chin, 2019 | https://arxiv.org/pdf/1808.08683 | Abstract and introduction excerpt; first-eight-page extraction and selected model/regression/exogeneity passages. This was not a full 38-page read. |
| Aronow and Samii, 2017 | https://arxiv.org/pdf/1305.6156 | Abstract and opening introduction from the first-eight-page extraction; exposure/design framework and inverse weighting described there. |
| Eckles, Karrer, Ugander, 2017 | https://arxiv.org/pdf/1404.7530 | Abstract and opening introduction from the first-eight-page extraction; design/analysis bias reduction and GATE framing. |
| Han and Ugander, 2023 | https://arxiv.org/pdf/2302.04997 | Abstract, opening introduction, and selected linear-interference, uniform assignment, feature-generation and bootstrap passages from first-eight-page extraction. Not the full paper. |
| Ugander et al., 2013 | https://arxiv.org/pdf/1305.6979 | Abstract and opening introduction from first-five-page extraction; full-exposure inverse weighting and variance motivation. |

No claim about these papers' empirical numerical results or detailed proof
assumptions is made beyond the material actually consulted. Publication metadata
also uses the user-supplied starter list. Their reference lists were not used to
expand the literature set.

## Official format and data sources

- https://icml.cc/Conferences/2026/AuthorInstructions : searched page text for
  the 8-page submission-body limit, official style link, impact statement,
  appendix/reference rules, and checklist. Archived as
  `sources/icml_author_instructions.html`.
- https://icml.cc/Conferences/2026/CallForPapers : consulted format, impact
  statement and generative-AI responsibility/authorship provisions; no papers
  or conference research listings were followed. Archived as `sources/icml_call.html`.
- https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip : downloaded
  official style ZIP, SHA-256
  `8b29290f5828e176debb57ea9cc00252502973d55ea561a2f18a7f0a326bfc6c`.
  Read official example source sections for usage and impact statement. Copied
  the original `icml2026.sty`, `.bst`, and `fancyhdr.sty` without modification.
  ICML 2026 is the most recent held ICML edition as of this study; these are its
  official year-specific files. No separate paper checklist was present in the
  downloaded template or consulted instructions. We supply an additional
  explicitly nonofficial completed reproducibility checklist in the appendix.
- https://snap.stanford.edu/data/ego-Facebook.html : consulted graph counts,
  description as combined ego networks, file link, and source citation. This
  is the cited SNAP data page, not a claim to have read the source research paper.
- https://snap.stanford.edu/data/facebook_combined.txt.gz : downloaded the
  exact supplied public graph, verified bytes/hash in `data/manifest.json`.

## Failed access

The source-paper link on the allowed SNAP data page was requested over HTTPS:
https://i.stanford.edu/~julian/pdfs/nips2012.pdf . The request returned HTTP 502.
No paper contents were read, no follow-up search was done, and this underlying
paper is not cited as a consulted paper. Its authors/title are only acknowledged
as the dataset page's supplied credit. The failed `curl --fail` request produced
no usable PDF. This was an ordinary allowed-source retrieval failure, not an
encounter with prohibited material.

Python packages were installed from the configured public package index using
`uv`; this fetched software distributions, not research search results.
