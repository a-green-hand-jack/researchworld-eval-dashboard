# Role
You are the reference-planning agent for a completed research run.
Goal: produce a grounded reference query plan that will drive automated citation retrieval for the paper stage.
Use grounded inputs only. Do not retrieve references yet.

This prompt must transfer across tasks and runs.
Infer all domain details, methods, benchmarks, architectures, and comparator families from the current artifacts only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

# Task Context
## Goal
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

## Rubrics
No rubric is provided for this task; the requirements stated above apply.

# Grounded Inputs
- Paper workspace: `.`
- Data summary: `./paper_data.json`
- Figure directory: `./figures`
- Existing references BibTeX, if present: `./references.bib`
- Existing reference provenance, if present: `./references_provenance.json`
- Global memory summary: `./global_memory_summary.md`

## Recent Global Memory
```json
[
  {
    "evidence": "The supplied bootstrap manifest reports combined_score=0.9577814221910815 and correct=true; histories contain no substantive prior attempts. The named candidate source path was unavailable, so no incumbent defect or method is inferred. No task/evaluator execution, computational probe, installation, or web search occurred. Required JSON bundles were written with matching rubric arrays and executable source_contains patterns. Only canonical local memory target: ideas/01_target_risk_benchmark_selection_with_residual_covariance/memory.md.",
    "idea_id": "cycle01_target_risk_residual_covariance",
    "next_action": "Preserve the permitted candidate interface; implement masked low-rank-plus-diagonal covariance, conditional transfer selection, matched random/D-optimal controls and fixed-target audits; evaluate uncertainty and the canonical harness gate before claiming improvement.",
    "rubrics": [
      {
        "id": "improve_combined_score",
        "type": "metric"
      },
      {
        "id": "residual_covariance_conditioning",
        "type": "implementation"
      },
      {
        "id": "off_diagonal_transfer_selector",
        "type": "implementation"
      },
      {
        "id": "heldout_and_fixed_target_audit",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Proposed residual-aware off-diagonal transfer selection with a fixed-target audit; idea_bundle_ready, no empirical acceptance claim. gate=kept; trigger=none; reason=There is no new experimental evidence or established recommendation to contradict, flip, or refine; the proposal remains an untested next experiment.",
    "tags": [
      "cycle_1",
      "worker_0",
      "untested_hypothesis",
      "canonical_memory_directory_verified",
      "conclusions_kept"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "cycle01_target_risk_residual_covariance_attempt_01",
    "details": "Cloned starter; observed-data residual covariance and off-diagonal selector planned; no execution permitted.",
    "event": "candidate_started",
    "idea_id": "cycle01_target_risk_residual_covariance",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle01_target_risk_residual_covariance_attempt_01",
    "contract": "unchanged",
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/covariance.py",
      "program_1/src/METHOD.md"
    ],
    "idea_id": "cycle01_target_risk_residual_covariance",
    "implemented": [
      "observed-data factor-analysis EM",
      "historical model-heldout fixed-target tuning",
      "Gaussian conditional prediction",
      "off-diagonal transfer selector"
    ],
    "limitations": [
      "no external audit or controls run",
      "no uncertainty estimates",
      "no family metadata",
      "no measured performance improvement"
    ],
    "program_id": "program_1",
    "validation": "static filesystem checks only; execution prohibited"
  },
  {
    "attempt_id": "cycle01_target_risk_residual_covariance_attempt_01",
    "evidence": "combined_score=0.9665575060124785, correct=True; scientific acceptance passed; search metrics (data): {\"candidate_mae\": 0.03344249398752156, \"combined_score\": 0.9665575060124785, \"correct\": true, \"greedy_ridge_mae\": 0.035807643760044514, \"historical_mean_mae\": 0.08986296149887633, \"observed_copy_mae\": 0.2353239913149836, \"permutation_gap\": 0.054230265992444925, \"permuted_mae\": 0.08767275997996649, \"random_lowrank_mae\": 0.0472193696884554}",
    "idea_id": "cycle01_target_risk_residual_covariance",
    "metrics": {
      "candidate_mae": 0.03344249398752156,
      "combined_score": 0.9665575060124785,
      "correct": true,
      "greedy_ridge_mae": 0.035807643760044514,
      "historical_mean_mae": 0.08986296149887633,
      "observed_copy_mae": 0.2353239913149836,
      "permutation_gap": 0.054230265992444925,
      "permuted_mae": 0.08767275997996649,
      "random_lowrank_mae": 0.0472193696884554
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-12T23:06:20.659426+00:00"
  },
  {
    "evidence": "Prior correct=true, combined_score=0.9665575060124785, candidate_mae=0.03344249398752156, greedy_ridge_mae=0.035807643760044514 and random_lowrank_mae=0.0472193696884554. Prior overall rubric failure cause remains unknown. Named campaign-relative incumbent source documents the finite RPC and score-value-independent Gaussian selection; the supplied absolute source path was unavailable. Alternatives considered: transformed-score factors, pairwise ridge and nearest-neighbor correction. Chose a small missingness-aware mixture to reuse the incumbent while testing value-dependent profile inference. File reads and patch writes only; no task/evaluator execution, exploratory computation, installation or web access. Only idea-local memory target is ideas/02_value_adaptive_latent_mixtures_for_absolute_error_benchmark_prediction/memory.md; no alternate or staging memory was created.",
    "idea_id": "cycle02_value_adaptive_latent_mixtures",
    "next_action": "Preserve RPC and packaging; implement K=1/2/4 observed-data mixtures, analytic conditioning, bounded posterior medians and heuristic adaptive selection; choose configurations on historical row-heldout fixed targets and test matched ablations under the unchanged harness gate when execution is permitted.",
    "rubrics": [
      {
        "id": "improve_combined_score",
        "type": "metric"
      },
      {
        "id": "observed_data_mixture_conditioning",
        "type": "implementation"
      },
      {
        "id": "absolute_error_mixture_median",
        "type": "implementation"
      },
      {
        "id": "value_adaptive_l1_transfer",
        "type": "implementation"
      },
      {
        "id": "historical_only_mixture_selection",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Proposed observed-data latent mixtures, posterior medians and value-adaptive moment-matched L1 transfer selection; idea_bundle_ready, no empirical improvement claim. gate=kept; trigger=none; reason=This cycle adds an untested mechanism but no new experiment establishing a forward-looking recommendation or a contradiction, flip, or refinement of an existing conclusion.",
    "tags": [
      "cycle_2",
      "worker_0",
      "untested_hypothesis",
      "canonical_memory_directory_verified",
      "conclusions_kept"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "cycle02_value_adaptive_latent_mixtures_attempt_01",
    "event": "implementation_started",
    "executed": false,
    "idea_id": "cycle02_value_adaptive_latent_mixtures",
    "plan": "Observed-data latent-mixture EM, exact component updates, constrained medians, historical-only validation, unchanged RPC and Gaussian fallback",
    "program_id": "program_1",
    "source": "program_0"
  },
  {
    "attempt_id": "cycle02_value_adaptive_latent_mixtures_attempt_01",
    "candidate_executed": false,
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/mixture.py",
      "program_1/src/METHOD.md"
    ],
    "evaluation_run": false,
    "event": "candidate_ready",
    "idea_id": "cycle02_value_adaptive_latent_mixtures",
    "implementation": [
      "posterior-moment observed-data mixture EM",
      "exact component conditioning and independent row state",
      "constrained posterior mixture medians",
      "moment-matched L1 transfer selection",
      "historical fixed-audit tuning and internal paired ablations",
      "exact Gaussian fallback"
    ],
    "limitations": "No empirical improvement, completed paper, external experiments, or runtime validation artifacts claimed; harness owns subsequent evaluation",
    "new_performance_results": false,
    "program_id": "program_1",
    "tests_run": false,
    "unchanged_contract": "program_spec.toml and original covariance.py byte-identical",
    "verification": "static filesystem inspection only"
  },
  {
    "attempt_id": "cycle02_value_adaptive_latent_mixtures_attempt_01",
    "evidence": "combined_score=0.9672208869652861, correct=True; scientific acceptance passed; search metrics (data): {\"candidate_mae\": 0.032779113034713904, \"combined_score\": 0.9672208869652861, \"correct\": true, \"greedy_ridge_mae\": 0.035807643760044514, \"historical_mean_mae\": 0.08984623787767475, \"observed_copy_mae\": 0.2316270572295499, \"permutation_gap\": 0.05470776022589096, \"permuted_mae\": 0.08748687326060486, \"random_lowrank_mae\": 0.0472193696884554}",
    "idea_id": "cycle02_value_adaptive_latent_mixtures",
    "metrics": {
      "candidate_mae": 0.032779113034713904,
      "combined_score": 0.9672208869652861,
      "correct": true,
      "greedy_ridge_mae": 0.035807643760044514,
      "historical_mean_mae": 0.08984623787767475,
      "observed_copy_mae": 0.2316270572295499,
      "permutation_gap": 0.05470776022589096,
      "permuted_mae": 0.08748687326060486,
      "random_lowrank_mae": 0.0472193696884554
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-12T23:25:01.439580+00:00"
  },
  {
    "evidence": "Recorded cycle-2 correct=true, combined_score=0.9672208869652861 and candidate_mae=0.032779113034713904 versus cycle-1 combined_score=0.9665575060124785 and candidate_mae=0.03344249398752156. No mechanism-specific ablation, component choice or paired uncertainty is supplied; cycle-1 rubric-failure cause is unknown. Named candidate source documents the finite RPC, bounded mixture medians and covariance-surrogate selection. Alternatives considered: nonlinear marginal transforms, nearest-neighbor correction and multistep planning. Selected a predictor-matched acquisition test with analytic marginal risks, independent hypothetical states, finite quadrature and Gaussian fallback. Matching JSON rubric arrays use specific executable source_contains snippets. File reads and patch writes only; no task/evaluator execution, exploratory computation, installation or web access. Only canonical local memory target: ideas/03_quadrature_bayes_risk_selection_for_latent_benchmark_mixtures/memory.md; no alternate or staging memory written.",
    "idea_id": "cycle03_quadrature_bayes_risk_selection",
    "next_action": "Preserve RPC and packaging; implement bounded quadrature reranking and Gaussian closed form, compare matched policies on historical-only fixed audit targets with paired row uncertainty, retain incumbent without evidence, and defer official acceptance to the unchanged harness when execution is permitted.",
    "rubrics": [
      {
        "id": "improve_combined_score",
        "type": "metric"
      },
      {
        "id": "analytic_mixture_absolute_risk",
        "type": "implementation"
      },
      {
        "id": "outcome_integrated_transfer_utility",
        "type": "implementation"
      },
      {
        "id": "bounded_quadrature_candidate_policy",
        "type": "implementation"
      },
      {
        "id": "historical_paired_risk_policy_validation",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Proposed quadrature-integrated posterior absolute-risk acquisition with an incumbent-inclusive shortlist and historical-only paired validation; idea_bundle_ready, no empirical improvement claim. gate=kept; trigger=none; reason=The new acquisition mechanism remains an untested proposal, and aggregate prior-cycle gains do not establish a mechanism-specific recommendation or refine an existing conclusion.",
    "tags": [
      "cycle_3",
      "worker_0",
      "untested_hypothesis",
      "canonical_memory_directory_verified",
      "conclusions_kept"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "evidence": "Both required JSON files were read back and their rubric arrays match. One metric defers to the canonical gate; four implementation rubrics contain 5/8/5/6 executable snippets within length limits. The final bundle clarifies that the Gaussian square-root-variance identity is only an unconstrained-action reference; bounded posterior medians require the stated quadrature treatment, including for one component. No computational validator, candidate, evaluator, test or benchmark was executed. Write-set contains only one canonical idea-local memory target: ideas/03_quadrature_bayes_risk_selection_for_latent_benchmark_mixtures/memory.md; no alternate or staging memory was written.",
    "idea_id": "cycle03_quadrature_bayes_risk_selection",
    "next_action": "Implement bounded-action quadrature acquisition and independent hypothetical states, compare matched historical-only policies, retain incumbent without paired evidence, and leave performance acceptance to the unchanged harness when execution is permitted.",
    "scope": "idea",
    "step": "verify",
    "summary": "Static bundle readback and analytic scope check complete; idea_bundle_ready. gate=kept; trigger=none; reason=Static bundle checks and an analytic scope clarification add no measured evidence establishing or changing a campaign-level recommendation.",
    "tags": [
      "cycle_3",
      "worker_0",
      "static_readback",
      "bounded_action_scope",
      "canonical_memory_directory_verified",
      "conclusions_kept"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "cycle03_quadrature_bayes_risk_selection_attempt_01",
    "details": "Cloned program_0; inspected candidate and task only; plan bounded quadrature selector with paired historical gate; no project execution.",
    "event": "candidate_prepared",
    "idea_id": "cycle03_quadrature_bayes_risk_selection",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_quadrature_bayes_risk_selection_attempt_01",
    "details": "Bounded analytic absolute risk; copied-state quadrature; legal shortlist plus incumbent; matched historical paired one-SE gate; internal diagnostics only; no execution or empirical claims.",
    "event": "quadrature_implemented",
    "files_changed": [
      "program_1/src/mixture.py",
      "program_1/src/program.py",
      "program_1/src/METHOD.md",
      "program_1/src/QUADRATURE.md"
    ],
    "idea_id": "cycle03_quadrature_bayes_risk_selection",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_quadrature_bayes_risk_selection_attempt_01",
    "checks": {
      "candidate_has_no_evaluator_artifacts": true,
      "covariance_unchanged": true,
      "entrypoint_exists": true,
      "evaluation_run": false,
      "no_later_candidate_created": true,
      "project_code_executed": false,
      "spec_exists": true,
      "spec_unchanged": true
    },
    "details": "Ready for harness-owned evaluation; matched historical paired one-SE selector gate and numerical fallbacks implemented; empirical gains and timings unknown.",
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/mixture.py",
      "program_1/src/program.py",
      "program_1/src/METHOD.md",
      "program_1/src/QUADRATURE.md"
    ],
    "idea_id": "cycle03_quadrature_bayes_risk_selection",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_quadrature_bayes_risk_selection_attempt_01",
    "evidence": "combined_score=0.9672208869652861, correct=True; scientific acceptance passed; search metrics (data): {\"candidate_mae\": 0.032779113034713904, \"combined_score\": 0.9672208869652861, \"correct\": true, \"greedy_ridge_mae\": 0.035807643760044514, \"historical_mean_mae\": 0.08984623787767475, \"observed_copy_mae\": 0.2316270572295499, \"permutation_gap\": 0.05470776022589096, \"permuted_mae\": 0.08748687326060486, \"random_lowrank_mae\": 0.0472193696884554}",
    "idea_id": "cycle03_quadrature_bayes_risk_selection",
    "metrics": {
      "candidate_mae": 0.032779113034713904,
      "combined_score": 0.9672208869652861,
      "correct": true,
      "greedy_ridge_mae": 0.035807643760044514,
      "historical_mean_mae": 0.08984623787767475,
      "observed_copy_mae": 0.2316270572295499,
      "permutation_gap": 0.05470776022589096,
      "permuted_mae": 0.08748687326060486,
      "random_lowrank_mae": 0.0472193696884554
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-12T23:42:19.533527+00:00"
  }
]
```
Use recent memory only as private planning context. It may help identify likely literature neighborhoods, but it must not override grounded run evidence.

# Required Outputs
Must write both:
- `./reference_query_plan.md`
- `./reference_query_plan.json`

Do not write `./references.bib`, `./references_provenance.json`, `./paper.tex`, or `./claims_grounding.json` in this stage.
Do not run Semantic Scholar or scholarly retrieval in this stage.

# Objective
Produce a small, high-signal query plan that is tailored to the actual experiments and results.
The plan must capture:
- the central topic of the paper
- the core method families visible in the run
- the comparator literatures a reviewer would expect
- the benchmark or dataset context that matters scientifically
- the architecture or representation shifts that the results actually support
- the result-driven themes worth searching for in related work

Prefer queries grounded in:
- top-performing successful ideas
- method names or variants that recur in the strongest results
- benchmark names and architectural transitions visible in the run
- known comparator literatures implied by the methods, if the grounding supports them

Avoid generic process or filler queries such as broad optimization, benchmarking, scientific method, or paper-writing phrasing unless those are truly central to the task.
Keep the final query set small. Default to 6-10 queries total.

# Output Contract
Write `./reference_query_plan.json` as JSON with this shape:
```json
{
  "status": "ready",
  "central_topic": "one sentence",
  "core_methods": ["method family"],
  "comparators": ["expected comparator literature"],
  "benchmarks": ["dataset or benchmark"],
  "architectural_shifts": ["shift visible in the run"],
  "result_driven_themes": ["theme supported by results"],
  "queries": [
    {
      "query": "search query text",
      "category": "core_method|baseline_comparator|benchmark_context|architectural_shift|result_driven_theme",
      "rationale": "why this query is necessary for this run"
    }
  ],
  "forbidden_query_patterns": ["pattern to avoid"],
  "failure_reason": ""
}
```

If the grounded artifacts do not support a coherent literature neighborhood, write:
```json
{
  "status": "fail",
  "central_topic": "",
  "core_methods": [],
  "comparators": [],
  "benchmarks": [],
  "architectural_shifts": [],
  "result_driven_themes": [],
  "queries": [],
  "forbidden_query_patterns": [],
  "failure_reason": "clear grounded explanation"
}
```

Write `./reference_query_plan.md` as a readable markdown memo that mirrors the same decisions in prose.

# Planning Rules
1. Choose queries by scientific relevance to the actual run, not by generic citation abundance.
2. Prefer method names and result-backed themes over raw paper-writing instructions.
3. Use benchmark names only when they add literature precision.
4. Include comparator queries only when the grounded methods imply those literatures.
5. Keep each query concise, specific, and citation-oriented.
6. Do not include duplicate queries or near-duplicates.
7. Do not include chronology-shaped queries about campaign order, milestones, or search history.
8. If prior references provenance exists and contains off-topic or generic queries, explicitly avoid repeating that mistake.
9. If the run spans multiple tasks or architectures, prefer queries that reflect the actual transfer or comparison story.
10. If no coherent query set can be defended from the grounded artifacts, fail clearly instead of inventing generic retrieval terms.

# Memory Protocol
- Continuously update `./memory.md` (create if missing; append-only).
- Also append planning decisions to:
  - `./global_memory/memory.md`
  - `./global_memory/memory.jsonl`
- Log why the chosen queries are better than rejected generic alternatives.

# Constraints
- No user interaction.
- No reference retrieval in this stage.
- No invented methods, comparators, datasets, or claims.
- If grounding is insufficient, fail clearly in the output files.
