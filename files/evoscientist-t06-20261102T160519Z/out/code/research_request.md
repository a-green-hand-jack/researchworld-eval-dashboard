# Original supplied research brief

The following is the original substantive proposal supplied by the user, preserved for coverage verification. Execution context: unattended; no human is available to answer questions or choose options. Decide autonomously and continue until deliverables exist. Working directory is the workspace root; everything delivered must be saved there.

## TASK.md — 研究任务：成对比较排行榜的稳定性

### 问题与动机
许多公开的模型评测排行榜（例如基于用户投票的大模型竞技场）通过聚合大量「A 与 B 比较，谁更好」的成对偏好数据，用 Bradley-Terry 等成对比较模型拟合每个参赛者的分数，再据此给出排名与置信区间。这些排名常被用于选型、发布宣传和研究比较，但它们对底层比较数据的依赖程度并不清楚。

本任务研究：这类排行榜的排名对底层比较数据的小幅改动有多敏感（改动可能来自数据噪声，也可能来自有人有意为之），以及这种敏感性在不同数据集、不同评测设计（例如众包投票、专家标注、模型裁判、体育比赛）之间是否不同。

### 要求与证据标准
请自行界定可操作的研究问题，选择数据集和评价指标，设计并实现分析方法，用实验给出有证据支持的结论。方法路线与对比基线由你自选。结论应基于至少两类不同评测设计的真实数据；改动的规模如何度量、不同数据集之间如何比较，由你定义并说明理由。结论须说明适用条件与局限，而不只是给出单一数字；"敏感性很小""视条件而定""与预期不同"同样是可以接受的结论。

### 约束
仅用 CPU、时间约一周、使用公开数据（见 data.md、resources.md）；产出为一篇研究论文及复现代码（见 deliverable.md）。

## starter_literature.md — 起步文献
以下文献供背景知识参考；链接于 2026-10-26 核对可访问。

1. Bradley, R. A., Terry, M. E. (1952). Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons. Biometrika 39(3/4). DOI https://doi.org/10.2307/2334029 。提出 Bradley-Terry 模型的原始论文。
2. Chiang, W.-L. et al. (2024). Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference. ICML 2024. https://arxiv.org/abs/2403.04132 （v1: 2024-03-07）。介绍匿名模型投票平台和数据。
3. Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023 Datasets & Benchmarks. https://arxiv.org/abs/2306.05685 （v1: 2023-06-09）。MT-Bench 问题集及人类专家和 GPT-4 成对判断数据。
4. Koh, P. W., Liang, P. (2017). Understanding Black-box Predictions via Influence Functions. ICML 2017. https://arxiv.org/abs/1703.04730 （2017-03-14）。影响函数分析。
5. Broderick, T., Giordano, R., Meager, R. (2020). An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference? https://arxiv.org/abs/2011.14999 （2020-11-30）。小比例数据删除的稳健性度量。
6. Min, R. et al. (2025). Improving Your Model Ranking on Chatbot Arena by Vote Rigging. ICML 2025. https://arxiv.org/abs/2501.17858 （v1: 2025-01-29）。投票操纵策略及排名影响。
7. Singh, S. et al. (2025). The Leaderboard Illusion. https://arxiv.org/abs/2504.20879 （2025-04-29）。平台评测实践分析。
8. Huang et al. (2025). Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings. https://arxiv.org/abs/2508.11847v1 （v1: 2025-08-16）。人类偏好排行榜排名敏感性。

Listed sources are permissions, not a claim that all were read. Actual consulted works/read extent are recorded separately in artifacts/literature_notes.md.

## data.md — 公开数据与获取方式（取证日期 2026-10-27）
所有条目于 2026-10-27 核实页面可访问；版本列为固定 Hugging Face 或 GitHub commit。

- Chatbot Arena 人类偏好55k： https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k 。commit `18c298340948c0e7f7727399fd459cca6ce0ca6f`（2024-05-17）；apache-2.0；57,477 场；train.csv 184,175,071 字节；SHA256 `0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2`；不需账号。
- 可选更大Arena140k： https://huggingface.co/datasets/lmarena-ai/arena-human-preference-140k 。commit `6322995ab34d7c2693e3f47dd13fa5caa0789a74`（2025-08-01）；cc-by-4.0；7个parquet合计约1.6GB（含对话）；不需账号。
- MT-Bench人类与GPT-4判断： https://huggingface.co/datasets/lmsys/mt_bench_human_judgments 。commit `f7d2896d2cc5d80f8b55c2bbc722613555233c25`（2023-07-20）；cc-by-4.0；human parquet 738,612 字节，SHA256 `4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769`；gpt4_pair parquet649,996字节；不需账号。
- 可选Arena对战模型裁判： https://huggingface.co/datasets/potsawee/chatbot-arena-llm-judges 。commit `638a7e3be3078e55d2eb0b789d34749747822c49`（2024-09-29）；页面与元数据未声明许可，README说明抽取自Kaggle LMSYS竞赛训练集（HF55k声明apache-2.0），使用前确认条款；train.single-turn.json约142MB，49,938条，含各裁判模型全部文件约0.58GB；不需账号。
- 可选WebDev Arena： https://huggingface.co/datasets/lmarena-ai/webdev-arena-preference-10k 。commit `7c397e652ffb8c2384e6d71d21d8388c19365fdc`（2025-03-10）；other，见LICENSE/README；data/webdev-arena-preference-10k.json149,295,752字节；匿名下载成功，许可协议约束适用。
- 可选NBA历史Elo： https://github.com/fivethirtyeight/data/tree/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo 。仓库commit `4c1ff5e3aef1816ae04af63218015066e186c147`（2025-02-25）；目录最后修改 `6d880e939a`（2022-12-16），内容相同；CC-BY-4.0；nbaallelo.csv18,173,265字节，126,313行（63,157场，每场两行，另有_iscopy）；SHA256 `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc`；不需账号。

若数据需要登录而无法获得，改用其余数据并说明。合成数据可用但必须明示。原始数据放工作目录data/，不放代码仓库或随论文提交；复现说明记录来源、版本、校验和。

## resources.md — 资源与预算
- 仅CPU（参考4核）。几千至十几万比较；参与者从个位（MT6个）至一百余（NBA历史球队）。单次拟合预计秒级但未实测。不另设CPU小时上限，受一周约束。
- 不需要GPU或付费API。允许LLM辅助，不计计算预算，但论文须披露。
- 内存8GB足够；140k只读必要列。磁盘数据合计不超过3GB。
- 时间上限一周，含调研、实验、写作、复现整理。
- 网络仅用于获取data.md列出的数据、读取文献与安装依赖。

## deliverable.md — 产出要求
### 提交物
1. 完整研究论文PDF与LaTeX。从ICML/ICLR/NeurIPS选择最新一届官方LaTeX模板，遵守正文页数上限，按规则区分参考文献与附录；填写该会议要求随文提交的checklist。至少包含摘要、引言、相关工作、方法、实验、讨论与局限、参考文献。
2. 全部代码与复现说明：环境与依赖版本、数据获取步骤及版本、随机种子、运行命令与预计耗时、每张表图对应生成脚本。

### 评审标准
按所选会议主会审稿标准，重视新颖性定位、严谨性（合理方法、基线/对照/消融、多次运行/CI/检验）、证据充分性与适用范围、清楚完整表达及复现、如实讨论局限失效。负面结果可接受，证据充分、不确定性完整更重要。

### 如实报告（禁止编造）
所有数字表图必须源于本任务实际运行且随附代码可再现，不编造、不用占位或估计/示意合成冒充实测。失败、意外、放弃方案如实报告；预算未完成者注明，不能写成完成。仅引用真实存在且确实查阅的文献。

### 不得访问的内容
已有一篇已发表论文研究过本问题。为独立性，不得检索、访问、阅读或使用那篇论文本身及任何镜像、预印本、摘要页、会议/评审页、幻灯片、海报、视频、博客、代码仓库；不得访问引用、讨论、复现它的任何页面（后续论文、综述、笔记、聚合、社交讨论等）。不要推测或检索它的标题、作者、结果。starter_literature.md中列出文献及无关其他公开资料可用。若偶然遇到上述内容，立即停止阅读并在复现说明如实记录遇到什么、何处、读到多少。

## Execution intake decisions (not part of original task)
Direct main-agent implementation avoided code-agent delegation and any unavailable code-mode clarification. Official required template/policy were obtained directly, not through paper search. Analysis protocol and deviations live in todos.md and experiment_log.md. No forbidden identity was inferred. Original task source messages remain the authoritative wording if typography/formatting differs here.
