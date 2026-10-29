# Research request (verbatim copy of the task brief, saved 2026-10-28)

## TASK.md — 研究任务：成对比较排行榜的稳定性

### 问题与动机
许多公开的模型评测排行榜（例如基于用户投票的大模型竞技场）通过聚合大量「A 与 B 比较，谁更好」的成对偏好数据，用 Bradley-Terry 等成对比较模型拟合每个参赛者的分数，再据此给出排名与置信区间。这些排名常被用于选型、发布宣传和研究比较，但它们对底层比较数据的依赖程度并不清楚。

本任务研究：这类排行榜的排名对底层比较数据的小幅改动有多敏感（改动可能来自数据噪声，也可能来自有人有意为之），以及这种敏感性在不同数据集、不同评测设计（例如众包投票、专家标注、模型裁判、体育比赛）之间是否不同。

### 要求与证据标准
请自行界定可操作的研究问题，选择数据集和评价指标，设计并实现分析方法，用实验给出有证据支持的结论。方法路线与对比基线由你自选。结论应基于至少两类不同评测设计的真实数据；改动的规模如何度量、不同数据集之间如何比较，由你定义并说明理由。结论须说明适用条件与局限，而不只是给出单一数字；"敏感性很小""视条件而定""与预期不同"同样是可以接受的结论。

### 约束
仅用 CPU、时间约一周、使用公开数据（见 data.md、resources.md）；产出为一篇研究论文及复现代码（见 deliverable.md）。

## starter_literature.md (summary)
1. Bradley & Terry 1952 (BT model). 2. Chiang et al. 2024 Chatbot Arena (arXiv 2403.04132). 3. Zheng et al. 2023 MT-Bench / LLM-as-a-judge (arXiv 2306.05685). 4. Koh & Liang 2017 influence functions (arXiv 1703.04730). 5. Broderick, Giordano, Meager 2020 AMIP (arXiv 2011.14999). 6. Min et al. 2025 vote rigging (arXiv 2501.17858). 7. Singh et al. 2025 Leaderboard Illusion (arXiv 2504.20879). 8. Huang et al. 2025 "Dropping Just a Handful of Preferences Can Change Top LLM Rankings" (arXiv 2508.11847v1).

## data.md (summary of permitted data, snapshot 2026-10-27)
- lmarena-ai/arena-human-preference-55k @ 18c298340948c0e7f7727399fd459cca6ce0ca6f, train.csv sha256 0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2 (apache-2.0)
- lmarena-ai/arena-human-preference-140k @ 6322995ab34d7c2693e3f47dd13fa5caa0789a74 (cc-by-4.0, optional)
- lmsys/mt_bench_human_judgments @ f7d2896d2cc5d80f8b55c2bbc722613555233c25 (human parquet sha256 4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769; gpt4_pair parquet) (cc-by-4.0)
- potsawee/chatbot-arena-llm-judges @ 638a7e3be3078e55d2eb0b789d34749747822c49 (license undeclared; derived from Kaggle LMSYS arena data) optional
- lmarena-ai/webdev-arena-preference-10k @ 7c397e652ffb8c2384e6d71d21d8388c19365fdc (other licence, agreement) optional
- fivethirtyeight nba-elo @ 4c1ff5e3aef1816ae04af63218015066e186c147, nbaallelo.csv sha256 d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc (CC-BY-4.0) optional
- Raw data goes to data/ (not to be shipped); record source/version/checksums.

## resources.md (summary)
CPU only (~4 cores reference), 8 GB RAM, <=3 GB data, one week, no paid APIs; LLM assistance must be disclosed. Network only for listed data, literature, dependencies.

## deliverable.md (summary)
1. Full research paper (PDF + LaTeX) using the latest official template of ICML/ICLR/NeurIPS, respecting page limit, including the venue's required checklist; must have abstract, intro, related work, method, experiments, discussion & limitations, references.
2. All code + reproduction notes: environment & versions, data acquisition & versions, seeds, commands & runtimes, mapping of every table/figure to the script producing it.
Review criteria: novelty/positioning, rigor (baselines, controls, ablations, uncertainty), sufficiency of evidence, clarity/reproducibility, honest limitations.
No fabrication; report failures. Only cite literature actually consulted.
FORBIDDEN: a published paper that already studied this question, its mirrors/preprints/code/talks, and anything citing/discussing/reproducing it. Do not try to guess or search for its title/authors/results. If encountered accidentally, stop and record in reproduction notes.
