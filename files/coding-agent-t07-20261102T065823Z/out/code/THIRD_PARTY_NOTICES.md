# Third-party materials

- `upstream/` is a checkout of `socialfoundations/benchmark-prediction` at
  `55faff496947789f94e6b5908c77cbc3e84f81ad`. Its packaged matrices and code
  are covered by its MIT license; preserve `upstream/LICENSE.txt` (copyright
  2024 Guanhua Zhang and Moritz Hardt). The task identifies these assets as
  usable under that license. Our baseline descriptions credit the source;
  the implementation here is separate except for matching documented formulas.
- Upstream evaluations were assembled from Open LLM Leaderboard and HELM.
  HELM's toolkit is Apache-2.0. We do not infer a new license for original
  benchmark question text, model weights or live Hugging Face details and do
  not download or redistribute those objects. Data slots retain original weights.
- `paper/neurips_2026.sty` is the official, unmodified NeurIPS 2026 style from
  `https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`.
  `paper/checklist.tex` keeps the official questions and guidelines and fills
  answers. Original template sources are in `references/template/`.
- `references/` stores the explicitly permitted research PDFs and extraction
  records used for consultation; those papers retain their authors' licenses
  and copyrights. They are not relicensed by this project's code license.
- Installed Python packages retain their own licenses; `requirements.lock.txt`
  records exact installed versions. No external language model was re-evaluated.

New code in `src/`, `build.sh`, `reproduce.sh`, and documentation written for
this project are under the separate MIT license in `LICENSE`.
