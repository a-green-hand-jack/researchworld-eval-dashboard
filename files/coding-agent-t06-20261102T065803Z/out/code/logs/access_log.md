# Access and independent-research log

Date: 2026-11-02 UTC. Work began in the empty `/work` directory at approximately 06:58 UTC. No general web-search or literature-search tool was called. The prohibited work was not identified, guessed, searched for, or knowingly accessed. No known prohibited material was encountered. This statement does not assert an exhaustive audit of all possible citations in permitted documents.

## Permitted starting papers directly consulted

Only these five entries from the supplied starting list were downloaded. PDFs were parsed locally to text. Reading focused on the abstract/introduction, relevant method definitions, dataset collection and uncertainty, influence/deletion interpretation, and new-vote versus historical-edit scope. Some local keyword-search outputs also contained reference-list matches; no citation links were followed and no additional literature was downloaded from those matches.

| Direct request | Observed version in downloaded PDF | Used reading |
|---|---|---|
| `https://arxiv.org/pdf/2403.04132` | v1, 2024-03-07 | Arena collection, BT estimation, sampling and uncertainty background |
| `https://arxiv.org/pdf/2306.05685` | v4, 2023-12-24 | MT-Bench human/model judgments, order-inconsistent ties, bias, shared questions and collection process |
| `https://arxiv.org/pdf/1703.04730` | v3, 2020-12-29 | Influence differentiation and Hessian approximation, especially Section 2 |
| `https://arxiv.org/pdf/2011.14999` | v5, 2023-07-19 | Finite-sample deletion sensitivity, approximate influence versus refitted evidence, uncertainty distinction |
| `https://arxiv.org/pdf/2501.17858` | v2, 2025-08-10 | New-vote manipulation, target-only and omnipresent scope, BT setup; no code repository accessed |

The other starting references, including the original BT paper, were not downloaded. The paper does not cite an unconsulted original paper merely to increase its reference count. It cites the consulted Arena reference for the ranking model and gives its own complete mathematical derivation. No inference about the unknown excluded paper's identity was made.

## Fixed public datasets

Exact raw URLs, commits, checksums and observed sizes are in `data/manifest.json`, generated and verified by `src/download.py`. All four files match the task's specified digests (the GPT-4 digest was also available in the frozen Hugging Face file metadata). Dataset conversation columns were inspected only as schema; the experimental loaders use identifiers and judgment labels, not conversation content.

One fixed-revision Hugging Face tree request was used to discover the two MT-Bench parquet filenames:

`https://huggingface.co/api/datasets/lmsys/mt_bench_human_judgments/tree/f7d2896d2cc5d80f8b55c2bbc722613555233c25?recursive=true`

Dataset documentation requests:

- `https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/raw/18c298340948c0e7f7727399fd459cca6ce0ca6f/README.md`
- `https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/raw/f7d2896d2cc5d80f8b55c2bbc722613555233c25/README.md`
- `https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/README.md`
- `https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/LICENSE`

No links from those cards to leaderboard analyses, notebooks, competition discussion, repositories other than the named NBA data files, or other studies were followed.

## Conference formatting and ethics

- `https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles`: HTTP 404, no substantive content read.
- `https://media.neurips.cc/Conferences/NeurIPS2026/Styles.zip`: HTTP 404, no substantive content read.
- `https://neurips.cc/Conferences/2026/CallForPapers`: successful official call, read formatting link and submission instructions only; no paper/proceeding pages followed.
- `https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`: successful; original style, sample manuscript and checklist saved in `paper/vendor/`. The sample gives the nine-page main-text limit, with references/checklist/appendices excluded.
- `https://neurips.cc/public/EthicsGuidelines`: successful; ethics guidance reviewed, particularly public data, privacy, attribution, impact and reproduction.

Original HTML/archive files are under `logs/` locally. The submission includes this log and vendor template files, not the HTML site captures.

## Package access

Only Python dependency installation used package-index network access. The first PDF-rendering installation selected PyMuPDF 2.0 with unnecessary layout/inference dependencies; it was replaced by pinned PyMuPDF 1.26.6 before rendering. The renderer was used only for visual manuscript inspection. No remote model weights, LLM evaluation APIs, GPU services, or other datasets were requested.

## LLM assistance

An OpenAI Codex assistant performed the research workflow, code generation, derivation, analysis and drafting. LLM assistance is disclosed in the manuscript. There was no second model judging experiment, paid API use, synthetic replacement of real outcomes, participant messaging, or live leaderboard manipulation.
