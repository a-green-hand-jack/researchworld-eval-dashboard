# Goal

**研究任务：用少量基准预测大模型在其余基准上的表现**
**问题与动机**
评估一个大语言模型通常要在几十乃至上百个基准（或子任务）上逐一运行，每个基准都消耗算力、时间和人力。
与此同时，公开榜单积累了大量"模型 × 基准"的得分记录，不同基准的得分之间是否相关、相关到什么程度，是需要用数据回答的问题。

设想一位评测者面对如下情形：

- 手头有一张历史得分矩阵：M 个已评测模型、N 个基准，部分格子缺失（并非每个模型都跑过每个基准）；
- 来了一个新模型，评测预算只允许在其中 k 个基准上实际运行（k 远小于 N）；
- 评测者希望用这 k 个基准上的实测得分，尽可能准确地推断该模型在其余 N−k 个基准上的得分。

**核心问题：在只能运行 k 个基准的预算下，应当如何选择这 k 个基准，并据此推断新模型在其余基准上的得分，才能使推断最准？需要多大的 k 才够用？**

请你作为独立研究者：

1. 梳理已有的相关做法与局限，明确你要回答的具体研究问题与假设；
2. 提出并实现一套选择基准、并据此推断其余基准得分的方法，说明其适用条件与代价；
3. 在公开榜单构成的真实得分矩阵上设计并运行实验：说明你的评估协议为什么能回答研究问题，与合适的基线对照，并说明结论在哪些数据条件下成立；
4. 如能给出理论分析，请给出推导并用实验核对。

**成功的衡量：** 以对新模型在未运行基准上的得分推断与其实测得分的接近程度来衡量。结论可以是你的假设得到支持、被反驳，或仅在部分数据条件下成立，均以实验证据为准。

**约束：** 仅用 CPU 即可完成，时间上限一周，存储 < 5 GB；数据来自公开榜单（见 `data.md`）；产出为一篇研究论文及全部代码（见 `deliverable.md`）。

以研究问题和实验证据为主线，自行决定具体路线。

**起步文献清单**
取证日期：2026-10-26。括号内为各条的首次提交日期。

1. Hendrycks et al. *Measuring Massive Multitask Language Understanding.* arXiv:2009.03300（2020-09-07 首次提交）。https://arxiv.org/abs/2009.03300 。说明：提出覆盖 57 个学科（含初等数学、美国历史、计算机科学、法律等）的多选题基准，用于衡量文本模型的多任务准确率。
2. Muennighoff, Tazi, Magne, Reimers. *MTEB: Massive Text Embedding Benchmark.* arXiv:2210.07316（2022-10-13）。https://arxiv.org/abs/2210.07316 。说明：提出覆盖 8 类嵌入任务、58 个数据集、112 种语言的文本嵌入评测基准，评测了 33 个模型，附开源代码和公开榜单。
3. Liang et al. *Holistic Evaluation of Language Models.* arXiv:2211.09110（2022-11-16）。https://arxiv.org/abs/2211.09110 。说明：提出在多种使用场景、多项指标下对语言模型做统一评测的框架，并公开了对 30 个模型的评测结果以及原始提示与输出。
4. Zheng et al. *Judging LLM-as-a-judge with MT-Bench and Chatbot Arena.* arXiv:2306.05685（2023-06-09）。https://arxiv.org/abs/2306.05685 。说明：研究用强语言模型作评判者评估对话助手，提出 MT-bench（多轮问题集）和 Chatbot Arena（众包对战平台），并考察评判者与人类偏好的一致程度。
5. Polo et al. *tinyBenchmarks: evaluating LLMs with fewer examples.* arXiv:2402.14992（2024-02-22）。https://arxiv.org/abs/2402.14992 。说明：研究如何用更少的评测样本估计语言模型在单个基准上的表现，并发布了若干常见基准的精简版本和评测工具。
6. Kipnis et al. *metabench -- A Sparse Benchmark of Reasoning and Knowledge in Large Language Models.* arXiv:2407.12844（2024-07-04）。https://arxiv.org/abs/2407.12844 。说明：利用 5000 多个模型的评测数据，把 ARC、GSM8K、HellaSwag、MMLU、TruthfulQA、WinoGrande 六个基准提炼成一个不足原规模 3% 的稀疏基准，并检验它对原基准得分的还原程度。
7. Perlitz et al. *Do These LLM Benchmarks Agree? Fixing Benchmark Evaluation with BenchBench.* arXiv:2407.13696（2024-07-18）。https://arxiv.org/abs/2407.13696 。说明：分析 40 多个基准，讨论基准一致性检验中各项方法选择对结果的影响，提出一组实践建议，并发布 Python 包 BenchBench 和对应的榜单。
8. Ruan, Maddison, Hashimoto. *Observational Scaling Laws and the Predictability of Language Model Performance.* arXiv:2405.10938（2024-05-17）。https://arxiv.org/abs/2405.10938 。说明：提出不训练新模型、而用约 100 个公开模型的已有评测结果来建立缩放规律的观测式方法，并用它研究若干复杂现象的可预测性。
9. Polo et al. *Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families.* arXiv:2412.06540（2024-12-09）。https://arxiv.org/abs/2412.06540 。说明：提出一种缩放规律（Skills Scaling Laws），利用公开的基准数据预测不同模型家族在多个基准上的表现，并在 Open LLM Leaderboard 的 12 个基准上做了评估。
10. Zhuo et al. *BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions.* arXiv:2406.15877（2024-06-22）。https://arxiv.org/abs/2406.15877 。说明：提出含 1,140 个任务、涉及 139 个库和 7 个领域的代码生成基准，并评测了 60 个模型。

**数据与获取方式**
取证日期：2026-10-27。你也可以使用其他公开榜单或数据；以下是已核实可无账号获取的起点，并给出固定的版本，请按所列版本取数，以保证可复现。其中标"主"的是推荐的主数据，标"可选"的是补充。

| 数据 | 获取 | 许可/账号 | 备注 |
| --- | --- | --- | --- |
| **主** MTEB 嵌入榜单结果（模型 × 任务得分，每个任务一个 JSON） | https://github.com/embeddings-benchmark/results （HTTP 200）；固定到提交 `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`（2026-03-31）：克隆后 `git checkout 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383` | 许可 CC0-1.0（GitHub API 核实）；无需账号 | 目录结构 `results/<模型>/<版本>/<任务>.json`；该提交下 `results/` 有 548 个模型目录，单个模型目录约百个任务文件；完整仓库历史约 0.6 GB（GitHub 显示 626,583 KB）；各任务 JSON 内含该任务的得分；榜单上的模型是文本嵌入模型，基准是嵌入任务，不是生成式大模型 |
| **可选** Open LLM Leaderboard 模型得分表 | https://huggingface.co/datasets/open-llm-leaderboard/contents （HTTP 200）；固定到数据集提交 `9c09a7cae43334062a82cb164f2ef255013dafa2`（最后修改 2025-03-20） | 数据集卡没有声明许可证（表内"Hub License"列是各模型自己的许可，不是数据集许可）；无需账号 | 单个 parquet 文件（约 1.1 MB），4,576 行；包含 6 个基准（IFEval、BBH、MATH Lvl 5、GPQA、MUSR、MMLU-PRO）各自的原始分与归一化分，以及模型元数据列 |
| **可选** HELM Lite 榜单 | https://crfm.stanford.edu/helm/lite/v1.13.0/ （HTTP 200）；数据文件 https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0/ （例如 `groups/core_scenarios.json`，HTTP 200）；固定到发布版本 v1.13.0（2025-01-10） | 评测代码仓库 stanford-crfm/helm 为 Apache-2.0；榜单数据按各评测场景的来源数据各有许可，未逐项核实；无需账号 | 该版本核心场景表有 91 个模型 × 10 个场景（外加平均胜率列） |
| **可选** LiveBench 判分记录 | https://huggingface.co/datasets/livebench/model_judgment （HTTP 200）；固定到数据集提交 `9704e5da7bfbefe75ac1482a13de827127295993`（最后修改 2025-04-07） | 数据集卡没有声明许可证（GitHub 仓库 LiveBench/LiveBench 的许可为 NOASSERTION），均未核实；无需账号 | 单个 parquet 文件（约 0.7 MB），60,372 行判分记录 |
| **可选** BigCodeBench 榜单与结果 | https://github.com/bigcode-project/bigcodebench （HTTP 200）；固定到提交 `09dd993f46c3fbf3a799465bb96d524edcb0b199`（2025-10-15） | Apache-2.0（GitHub API 核实）；无需账号 | 代码类，多子任务 |
| **可选** AlpacaEval 榜单 | https://github.com/tatsu-lab/alpaca_eval （HTTP 200）；固定到提交 `cd543a149df89434d8a54582c0151c0b945c3d20`（2025-08-09） | Apache-2.0（GitHub API 核实）；无需账号 | 对话类胜率 |
| **可选** 合成数据 | 自行生成"模型 × 基准"得分矩阵 | 无 | 无需下载 |

注意：不同榜单的模型命名不一致；各榜单覆盖的基准不同，合并后的得分矩阵会有缺失；得分量纲各异（准确率、胜率、1–10 分评分等）。

**资源与预算**
- 计算：仅 CPU 即可完成（4 核以上、16 GB 内存为宜）；不需要 GPU，不需要付费 API。
- 估算依据（未实测，按数据量级估计）：data.md 中各数据源的得分表规模为数百个模型 × 数十至数百个基准（固定版本的 MTEB 结果有 548 个模型目录；Open LLM Leaderboard 表为 4,576 行 × 6 个基准），表格规模小，单次数据处理与计算预计为秒到分钟级，整项研究的总算力预计在数十 CPU 小时以内，不需要 GPU。
- 时间上限：一周（含阅读、数据整理、实现、实验、写作）。
- 存储：< 5 GB（含数据下载与中间文件）。
- 联网：可访问公开文献与数据下载；不得访问 deliverable.md 中列出的禁止内容。

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
