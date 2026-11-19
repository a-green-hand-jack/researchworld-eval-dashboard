# Third-party assets and attribution

The original code in `src/` is supplied under the MIT license in `LICENSE`. That license does not override third-party data or template terms.

- **Arena**: lmarena-ai/LMSYS, `arena-human-preference-55k`, Apache-2.0 as declared by the frozen dataset card. Credit Chiang et al., *Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference* (2024). The original card is `data/arena_README.md`; exact download metadata are in `data/manifest.json`.
- **MT-Bench**: LMSYS, `mt_bench_human_judgments`, CC-BY-4.0. Credit Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (2023). Card: `data/mt_README.md`. The analysis transforms preference labels and aggregates/refits scores; it does not redistribute conversations.
- **NBA**: FiveThirtyEight, historical NBA Elo data, CC-BY-4.0, with game information credited in its README to Basketball-Reference.com. Readme and original license: `data/nba_README.md`, `data/nba_LICENSE`. We deduplicate game rows, select seasons/regular-season games, and fit a different model; archived Elo estimates are not used. No endorsement by these creators is implied.
- **NeurIPS 2026 template and checklist**: downloaded from the official 2026 formatting ZIP linked by the official call. The style credits Roman Garnett and prior style authors. Original headers are preserved under `paper/vendor/`. The official archive does not include a separate license file; this artifact does not relicense these template assets under MIT. The style is unmodified; only the manuscript and checklist answers are filled as instructed.
- **Dependencies**: exact Python package versions are in `requirements.txt`, and each retains its own upstream license. No library source is vendored.
- **Literature**: only permitted starting references were downloaded/read; bibliographic attribution is in `paper/references.bib`. Downloaded PDFs are excluded from the submission archive.
