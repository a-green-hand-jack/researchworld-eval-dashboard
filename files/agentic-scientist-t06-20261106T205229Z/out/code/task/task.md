# Goal

**研究任务：成对比较排行榜的稳定性**
**问题与动机**
许多公开的模型评测排行榜（例如基于用户投票的大模型竞技场）通过聚合大量
「A 与 B 比较，谁更好」的成对偏好数据，用 Bradley-Terry 等成对比较模型拟合
每个参赛者的分数，再据此给出排名与置信区间。这些排名常被用于选型、发布宣传和
研究比较，但它们对底层比较数据的依赖程度并不清楚。

本任务研究：这类排行榜的排名对底层比较数据的小幅改动有多敏感（改动可能来自数据噪声，也可能来自
有人有意为之），以及这种敏感性在不同数据集、不同评测设计（例如众包投票、专家标注、模型裁判、
体育比赛）之间是否不同。

**要求与证据标准**
请自行界定可操作的研究问题，选择数据集和评价指标，设计并实现分析方法，用实验给出有证据支持的
结论。方法路线与对比基线由你自选。结论应基于至少两类不同评测设计的真实数据；改动的规模如何
度量、不同数据集之间如何比较，由你定义并说明理由。结论须说明适用条件与局限，而不只是给出单一
数字；"敏感性很小""视条件而定""与预期不同"同样是可以接受的结论。

**约束**
仅用 CPU、时间约一周、使用公开数据（见 `data.md`、`resources.md`）；产出为一篇研究论文及复现
代码（见 `deliverable.md`）。

**起步文献**
以下文献供背景知识参考；链接于 2026-10-26 核对可访问。

1. Bradley, R. A., Terry, M. E. (1952). Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons. Biometrika 39(3/4). DOI: https://doi.org/10.2307/2334029 。说明：提出成对比较的概率模型（Bradley-Terry 模型）的原始论文。
2. Chiang, W.-L. et al. (2024). Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference. ICML 2024. https://arxiv.org/abs/2403.04132 （v1: 2024-03-07）。说明：介绍 Chatbot Arena 平台：用户对两个匿名模型的回答投票，据此估计模型排名；文中描述了平台设计与所收集的投票数据。
3. Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023 Datasets & Benchmarks. https://arxiv.org/abs/2306.05685 （v1: 2023-06-09）。说明：研究用大语言模型作评审（LLM-as-a-judge）评价对话模型，提出 MT-Bench 问题集，并发布了人类专家与 GPT-4 对模型回答的成对判断数据。
4. Koh, P. W., Liang, P. (2017). Understanding Black-box Predictions via Influence Functions. ICML 2017. https://arxiv.org/abs/1703.04730 （2017-03-14）。说明：介绍如何用影响函数分析单个训练样本对模型参数和预测的影响，并在若干模型上给出实验。
5. Broderick, T., Giordano, R., Meager, R. (2020). An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference? https://arxiv.org/abs/2011.14999 （2020-11-30）。说明：提出一个衡量统计分析结论稳健性的度量，并在多个已发表的应用研究数据上做了检验。
6. Min, R. et al. (2025). Improving Your Model Ranking on Chatbot Arena by Vote Rigging. ICML 2025. https://arxiv.org/abs/2501.17858 （v1: 2025-01-29）。说明：研究针对 Chatbot Arena 这类众包投票排行榜的投票操纵策略及其对模型排名的影响。
7. Singh, S. et al. (2025). The Leaderboard Illusion. https://arxiv.org/abs/2504.20879 （2025-04-29）。说明：分析 Chatbot Arena 的评测实践（如私有测试、不同提供方的数据访问与采样差异）及其对排行榜的影响。
8. Huang et al. (2025). Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings. https://arxiv.org/abs/2508.11847v1 （v1: 2025-08-16）。说明：一篇讨论基于人类偏好的大模型排行榜（如 Chatbot Arena）排名的论文。

**公开数据与获取方式（取证日期 2026-10-27）**
你可自行选择使用哪些数据。所有条目于 2026-10-27 核实页面可访问；版本列为 Hugging Face 数据集 commit 或 GitHub commit，均为固定快照。

| 数据 | 获取 | 版本 | 许可 | 规模与格式 | 需账号 |
| --- | --- | --- | --- | --- | --- |
| Chatbot Arena 人类偏好（约 5.7 万场，57,477 场） | https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k | commit `18c298340948c0e7f7727399fd459cca6ce0ca6f`（2024-05-17） | apache-2.0 | `train.csv`，184,175,071 字节，sha256 `0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2` | 否 |
| Chatbot Arena 人类偏好（更大版本，约 14 万场，可选） | https://huggingface.co/datasets/lmarena-ai/arena-human-preference-140k | commit `6322995ab34d7c2693e3f47dd13fa5caa0789a74`（2025-08-01） | cc-by-4.0 | 7 个 parquet 文件，合计约 1.6 GB（含对话文本） | 否 |
| MT-Bench 人类判断与 GPT-4 判断 | https://huggingface.co/datasets/lmsys/mt_bench_human_judgments | commit `f7d2896d2cc5d80f8b55c2bbc722613555233c25`（2023-07-20） | cc-by-4.0 | 两个 parquet：`human-…parquet` 738,612 字节（sha256 `4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769`），`gpt4_pair-…parquet` 649,996 字节 | 否 |
| 模型裁判在 Arena 对战上的判断（可选） | https://huggingface.co/datasets/potsawee/chatbot-arena-llm-judges | commit `638a7e3be3078e55d2eb0b789d34749747822c49`（2024-09-29） | 页面与元数据均未声明许可；README 说明数据抽取自 Kaggle 上的 LMSYS Chatbot Arena 竞赛训练集（该竞赛数据的 HF 版本 arena-human-preference-55k 声明 apache-2.0），使用前请自行确认条款 | `train.single-turn.json` 约 142 MB（49,938 条单轮对战）；含各裁判模型输出的全部文件约 0.58 GB | 否 |
| WebDev Arena 偏好（约 1 万场，可选） | https://huggingface.co/datasets/lmarena-ai/webdev-arena-preference-10k | commit `7c397e652ffb8c2384e6d71d21d8388c19365fdc`（2025-03-10） | other（见该数据集 LICENSE 与 README 协议） | `data/webdev-arena-preference-10k.json`，149,295,752 字节 | 匿名下载可成功；页面 README 含须同意的数据集许可协议，协议约束适用 |
| NBA 历史 Elo 比赛记录（可选） | https://github.com/fivethirtyeight/data/tree/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo | 仓库 commit `4c1ff5e3aef1816ae04af63218015066e186c147`（2025-02-25）；`nba-elo/` 目录最近一次修改为 `6d880e939a`（2022-12-16），文件内容相同 | CC-BY-4.0（仓库 LICENSE） | `nbaallelo.csv`，18,173,265 字节，126,313 行数据（63,157 场，每场两行，另含 `_iscopy` 列），sha256 `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc` | 否 |

说明：
- 若数据需要登录而你无法获得，请改用其余数据，并在论文中说明。
- 你也可以使用自行生成的合成数据，但须在论文中明示为合成。
- 请把原始数据放在工作目录下的 data/ 中，不要放进代码仓库或随论文提交；复现说明里记录来源、版本和校验和。

**资源与预算**
- 计算：仅 CPU（参考配置 4 核）。数据量级为几千到十几万条成对比较，参与者个数从个位数（MT-Bench
  为 6 个模型）到一百余个（NBA 球队）不等；单次 Bradley-Terry 型模型拟合预计在秒级（按数据量级估算，
  未实测）。总算力受下述一周时间上限约束，不另设 CPU 小时上限。
- 不需要 GPU，不需要付费 API。若你选择使用 LLM 辅助（如文献阅读、代码生成），不计入上述计算预算，
  但须在论文中披露。
- 内存：8 GB 足够（读取 140k 版本时只读取所需列）；磁盘：数据合计不超过 3 GB。
- 时间上限：一周（含文献调研、实验、写作与复现整理）。
- 网络：仅用于获取 data.md 中列出的数据、读取文献与安装依赖。

**产出要求**
**提交物**
1. 一篇完整的研究论文（PDF 与 LaTeX 源文件）。从 ICML、ICLR、NeurIPS 中自选一个会议，使用该会议
   最新一届的官方 LaTeX 模板，遵守其正文页数上限（参考文献、附录是否计入页数按该会议的规定）；
   该会议要求随文提交的 checklist（例如 NeurIPS 的 paper checklist）一并填写。论文至少包含摘要、
   引言、相关工作、方法、实验、讨论与局限、参考文献。
2. 全部代码与复现说明：环境与依赖版本、数据获取步骤和所用数据的版本、随机种子、运行命令和预计
   耗时，以及论文中每张表、每张图由哪个脚本生成。

**评审标准**
论文按所选会议主会的审稿标准评审，重点看：

- 新颖性与定位：贡献是什么，与已有工作的关系和区别是否讲清楚；
- 严谨性：方法和实验设计是否合理，基线、对照和消融是否恰当，是否报告不确定性（多次运行、
  置信区间或显著性检验）；
- 证据是否充分：实验能否支撑论文的每个结论，结论的适用范围是否写清楚；
- 表达：论文是否清楚、完整，他人能否据此复现；
- 局限：是否如实讨论方法和结论的局限与失效情形。

负面结果、与预期不符的结果同样有价值；结论有充分证据、不确定性报告完整，比结论本身是正面还是
负面更重要。

**如实报告（禁止编造）**
- 论文中的每个数字、每张表和每张图都必须来自你在本任务中实际运行、随附代码可以重新产生的结果；
  不得编造数据或结果，不得用占位数字、估计值或"示意"性的合成结果冒充实测结果。
- 失败的运行、与预期不符的结果和放弃的方案如实报告；因预算没有完成的实验写明未完成，不写成
  已完成。
- 只引用真实存在、你确实查阅过的文献，不得编造引用。

**不得访问的内容**
本任务的研究问题已有一篇已发表的论文研究过。为保证研究独立，不得检索、访问、阅读或使用：

- 那篇论文本身，及其任何镜像、预印本、摘要页、会议或评审页面、幻灯片、海报、视频、博客和代码
  仓库；
- 引用、讨论或复现那篇论文的任何页面，包括后续论文、综述、论文笔记、论文聚合站点和社交媒体
  讨论。

也不要尝试推测或检索那篇论文的标题、作者或结果。`starter_literature.md` 中的文献，以及与那篇
论文无关的其他公开文献、数据和代码，可以正常使用。若在检索中偶然遇到上述内容，立即停止阅读，
并在复现说明中如实记录遇到了什么、在哪里遇到、读到了多少。

# Rubrics

No rubric is provided for this task; the requirements stated above apply.
