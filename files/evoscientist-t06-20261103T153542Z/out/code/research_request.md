# Original task brief (provided in Chinese)

研究任务：成对比较排行榜的稳定性。研究 Bradley–Terry 等排行榜对小幅底层比较数据改动（噪声或定向行为）的敏感性，至少两类不同评测设计的真实数据；自主界定研究问题、预算与跨数据比较；CPU only，约一周，公开数据，不超过 3GB。产出：最新一届 ICML/ICLR/NeurIPS 官方模板、页数合规的完整论文 PDF 与 LaTeX，以及全部复现代码、版本、种子、命令、预计耗时与逐图表来源。所有数字须来自实际运行；失败与未完成实验如实报告；仅引用实际查阅的真实文献。不得寻找、推测、访问任务未公开指明的已发表相关论文或其任何衍生内容；起步文献允许。

## Authorized fixed sources (verbatim identifiers from brief)
- Arena 55k: lmarena-ai/arena-human-preference-55k @ 18c298340948c0e7f7727399fd459cca6ce0ca6f; train.csv; expected SHA256 0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2; apache-2.0.
- MTBench: lmsys/mt_bench_human_judgments @ f7d2896d2cc5d80f8b55c2bbc722613555233c25; human parquet expected SHA256 4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769; CC-BY-4.0.
- NBA: fivethirtyeight/data @ 4c1ff5e3aef1816ae04af63218015066e186c147 /nba-elo/nbaallelo.csv; expected SHA256 d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc; CC-BY-4.0.
- Optional datasets not required or selected: Arena140k, other LLM judges, WebDev.

## Authorized starter references
Bradley & Terry 1952 doi:10.2307/2334029; Chiang et al. arXiv:2403.04132; Zheng et al. arXiv:2306.05685; Koh & Liang arXiv:1703.04730; Broderick et al. arXiv:2011.14999; Min et al. arXiv:2501.17858; Singh et al. arXiv:2504.20879; Huang et al. arXiv:2508.11847v1.

## Independence
Read only exact allowed papers (no citation following) and exact data manifests. Official conference template retrieval is necessary to satisfy deliverables; no topical search. If any prohibited content is incidentally encountered, immediately stop and log URL/content extent in README. Do not infer prohibited paper identity.
