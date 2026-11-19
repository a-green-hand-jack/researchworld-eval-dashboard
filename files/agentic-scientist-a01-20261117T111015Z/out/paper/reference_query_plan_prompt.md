# Role
You are the reference-planning agent for a completed research run.
Goal: produce a grounded reference query plan that will drive automated citation retrieval for the paper stage.
Use grounded inputs only. Do not retrieve references yet.

This prompt must transfer across tasks and runs.
Infer all domain details, methods, benchmarks, architectures, and comparator families from the current artifacts only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

# Task Context
## Goal
**研究任务：多任务排行榜的聚合规则与针对性投入**
**背景与动机**
多任务基准（multi-task benchmark）已成为评估机器学习模型的核心基础设施：一个排行榜由多个子数据集组成，每个模型在各子数据集上得到分数，再通过某种聚合规则（例如取平均、取中位数等）得到总排名。排行榜名次影响模型的采用、论文发表与资金，因此开发者有动机采取策略性行动，使某个特定模型的名次上升。其中一类行动是：把部分子数据集的相关数据纳入自己模型的训练，从而提高目标模型在这些子数据集上的得分。

这类针对性投入在多大程度上能改变排行榜名次，以及这与所采用的聚合规则有何关系，目前缺少系统的分析。

**研究问题**
在公开的多任务排行榜上，开发者要通过上述针对性投入使某个目标模型排到第一，需要怎样的投入？这种投入如何随聚合规则变化？请自行界定"投入"的含义和度量方式，并给出你的结论。

结论可以是支持、反驳或视条件而定的。能回答这一问题的证据应当：对所用概念和假设给出清晰定义；有可检验的论断；在公开榜单数据上得到可复现的实证支持；并说明结论在什么条件下成立、在什么条件下不成立。

**范围说明**
- 聚合规则有哪些、研究哪些，由你自行界定。
- 你需要自行选择并明确论证所需的建模假设，说明其合理性与局限。
- 研究方式（理论分析、实证分析或二者结合）由你自行选择；无论采用哪种方式，所用的榜单数据必须公开，结论所依据的结果须可复现。
- 不要求也不鼓励实际训练大模型；所需数据均为已公开的评测结果。

**约束与产出**
- 数据：公开的多任务评测榜单得分（来源见 `data.md`），无需账号。
- 资源与时间：仅 CPU，不需要 GPU；时间上限一周（细节见 `resources.md`）。
- 产出：一篇完整的研究论文及可复现的代码（要求见 `deliverable.md`）。

**起步文献**
以下均为较早的公开工作，仅供入门，请自行扩展检索。取证日期 2026-10-27。

1. Hendrycks et al. "Measuring Massive Multitask Language Understanding." arXiv:2009.03300 (2020-09). https://arxiv.org/abs/2009.03300 —— 说明：提出覆盖 57 个学科的多项选择问答评测集，用于衡量语言模型的多任务知识水平。
2. Suzgun et al. "Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them." arXiv:2210.09261 (2022-10). https://arxiv.org/abs/2210.09261 —— 说明：从 BIG-Bench 中筛选出一组此前语言模型表现未超过人类平均水平的困难任务（BBH），并研究思维链提示对这些任务的影响。
3. Liang et al. "Holistic Evaluation of Language Models." arXiv:2211.09110 (2022-11). https://arxiv.org/abs/2211.09110 —— 说明：提出覆盖多种使用场景和多项指标的语言模型评测框架，对 30 个模型做了大规模评测，并公开了原始提示与模型输出及评测工具包。
4. Dehghani et al. "The Benchmark Lottery." arXiv:2107.07002 (2021-07). https://arxiv.org/abs/2107.07002 —— 说明：提出"基准彩票"概念，讨论基准测试中的任务选择等因素如何改变不同方法之间的相对比较，并在若干常见基准设置上给出实例。
5. Lanctot et al. "Evaluating Agents using Social Choice Theory." arXiv:2312.03121 (2023-12). https://arxiv.org/abs/2312.03121 —— 说明：将社会选择（投票）理论用于智能体的多任务评测，并在强化学习、大语言模型等场景中做了实验。
6. Singh et al. "The Leaderboard Illusion." arXiv:2504.20879 (2025-04). https://arxiv.org/abs/2504.20879 —— 说明：对 Chatbot Arena 排行榜的分析，讨论私下测试、数据采样不均等做法对榜单结果的影响，并给出改进建议。
7. Zhou et al. "Don't Make Your LLM an Evaluation Benchmark Cheater." arXiv:2311.01964 (2023-11). https://arxiv.org/abs/2311.01964 —— 说明：讨论评测数据被用于模型训练（基准泄漏）带来的问题，通过实验考察其对评测结果的影响，并给出使用基准时的建议。
8. Yang et al. "Rethinking Benchmark and Contamination for Language Models with Rephrased Samples." arXiv:2311.04850 (2023-11). https://arxiv.org/abs/2311.04850 —— 说明：指出对测试数据做改写后可绕过常见的去污染方法，并提出基于大语言模型的污染检测方法。
9. Chen et al. "Leaderboard Incentives: Model Rankings under Strategic Post-Training." arXiv:2603.08371 (2026-03). https://arxiv.org/abs/2603.08371 —— 说明：用博弈论模型刻画基准设计者与多个模型开发者之间的互动，并给出了关于开发者策略均衡的理论结果。
10. Gao et al. "A framework for few-shot language model evaluation" (EleutherAI lm-evaluation-harness), Zenodo DOI 10.5281/zenodo.10256836 (2023). https://doi.org/10.5281/zenodo.10256836 —— 说明：EleutherAI 的开源语言模型少样本评测框架，为大量评测任务提供统一的实现。
11. Brandt, Conitzer, Endriss, Lang, Procaccia (eds.). "Handbook of Computational Social Choice." Cambridge University Press (2016). https://doi.org/10.1017/CBO9781107446984 —— 说明：计算社会选择领域的综合性手册，由多位作者分章撰写。

**公开数据与获取方式**
取证日期 2026-10-27。无需账号即可读取下列内容（HTTP 200）。

1. HELM 公开运行日志与结果（含多学科问答评测各子科目的得分）
   - 页面：https://crfm.stanford.edu/helm/mmlu/latest/ （HTTP 200）
   - 原始数据：https://storage.googleapis.com/crfm-helm-public/ （HTTP 200）；代码：https://github.com/stanford-crfm/helm （HTTP 200）
   - 版本：该存储桶的 `mmlu/benchmark_output/releases/` 下有 14 个发布版本 v1.0.0 至 v1.13.0（各版本 `summary.json` 的 date 字段：v1.0.0 为 2024-04-03，v1.13.0 为 2025-01-10）。使用 v1.13.0；如改用其他版本须在复现说明中写明理由。
   - 格式与规模：每个版本的 `releases/<版本>/` 下是汇总 JSON（例如 `groups/json/` 下每个学科一张各模型得分表）；v1.13.0 共 303 个文件、合计约 11.4 MB。逐运行的原始数据在 `mmlu/benchmark_output/runs/<版本>/`，体量更大，按需下载，勿全量镜像。
   - 许可证：未声明，使用前自行判断并在复现说明中注明（参考：代码仓库为 Apache-2.0；站点与存储桶未见针对得分数据的单独许可声明，2026-10-27 核查）。
2. Open LLM Leaderboard 公开数据集（含大量模型在各评测任务上的得分）
   - https://huggingface.co/datasets/open-llm-leaderboard/contents （HTTP 200，无需登录）：约 4576 行（每行一个模型），单个 parquet 文件（约 1.1 MB，`data/train-00000-of-00001.parquet`）；列为模型元数据与各评测任务的聚合得分（IFEval、BBH、MATH Lvl 5、GPQA、MUSR、MMLU-PRO 及各自的 Raw 列）。提交 sha `9c09a7cae43334062a82cb164f2ef255013dafa2`，最后更新 2025-03-20。
   - https://huggingface.co/datasets/open-llm-leaderboard/results （HTTP 200，无需登录）：逐模型的评测结果 JSON，共 10510 个文件，合计约 13.6 MB；每个 JSON 含该次评测各任务及其子任务的得分（如以 `leaderboard_bbh_` 开头的键）。提交 sha `aa81ecc38fdc5708254b833923368970efdf5ef5`，最后更新 2025-03-15。
   - 许可证：未声明，使用前自行判断并在复现说明中注明（参考：`results` 无数据集卡片；`contents` 卡片无 license 字段，但含各模型的 `Hub License` 列）。榜单已不再实时更新，请记录所用快照的 sha 与日期。
3. （可选）原始评测集：cais/mmlu https://huggingface.co/datasets/cais/mmlu （HTTP 200，无需登录；卡片标注 MIT）。

请记录所用数据的日期/版本与校验和。

**资源与预算**
- 计算：仅 CPU 即可，不需要 GPU。处理的数据是已公开的评测得分表（任务数约 10^1–10^2，模型数约 10^1–10^4），数据量和单次计算量都很小。
- 估算：全部计算在单台 8 核 CPU 上合计不超过 4 CPU 小时（按数据规模估计，未实测；含重复运行）。
- 内存：16 GB 以内足够。存储：10 GB 以内（主要为下载的汇总数据）。
- 时间上限：一周（含检索、实验与写作）。
- 付费 API：本任务本身不需要调用付费 API。
- 估算依据：只处理已公开的评测得分，不训练或评测任何模型。

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
    "evidence": "Supplied bootstrap correct=true and combined_score=0.53012102014295; no recent ideas or attempts. Named external incumbent source was unavailable; implementation details and failure causes remain unknown. Alternatives were perfect-score-only attacks, unsupported training-cost curves, and a wider aggregation-rule catalogue. Bounded score-response ceilings permit exact support-cost certificates using documented public score matrices. No experiments or literature searches were run. Only canonical local memory path ideas/01_certified_attainability_frontiers_for_targeted_leaderboard_investment/memory.md was created for this idea.",
    "idea_id": "c01_certified_attainability_frontiers",
    "next_action": "Preserve the documented candidate entrypoint; pin HELM v1.13.0 and the Open LLM contents snapshot; cross-check six-task budgets exhaustively before running paired mean, conventional median, and rival-aware Borda frontiers; report infeasible and unresolved cases separately and generate provenance-linked paper artifacts. Hypothesis: relative rule ordering may depend on the response ceiling; report a negative result if no reversal is found. Stop reason: idea_bundle_ready, experimental improvement untested.",
    "rubrics": [
      {
        "id": "improve_combined_score",
        "type": "metric"
      },
      {
        "id": "bounded_support_intervention",
        "type": "implementation"
      },
      {
        "id": "rival_aware_borda_certificate",
        "type": "implementation"
      },
      {
        "id": "exhaustive_budget_crosscheck",
        "type": "implementation"
      },
      {
        "id": "pinned_score_provenance",
        "type": "implementation"
      },
      {
        "id": "paired_frontier_evidence",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Certified Attainability Frontiers for Targeted Leaderboard Investment; wrote matching idea and rubric bundles. gate=kept; trigger=none; reason=Only an untested proposal and the supplied incumbent aggregate are available, so no evidence-backed distilled recommendation is added.",
    "tags": [
      "cycle_1",
      "worker_0",
      "untested_hypothesis",
      "gate=kept",
      "trigger=none",
      "single_canonical_memory_target"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "c01_certified_attainability_frontiers_attempt_01",
    "date": "2026-11-17",
    "event": "candidate_cloned",
    "executed_evaluation": false,
    "idea_id": "c01_certified_attainability_frontiers",
    "interface_limitation": "Only mean, median, trimmed and strict first; no Borda, provenance export or paper operations",
    "program_id": "program_1"
  },
  {
    "attempt_id": "c01_certified_attainability_frontiers_attempt_01",
    "contract_changed": false,
    "date": "2026-11-17",
    "event": "implementation_complete",
    "executed_evaluation": false,
    "executed_tests": false,
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "c01_certified_attainability_frontiers",
    "method": "common-headroom order-statistic dominance frontier, exhaustive <=6-task audit, direct witness recheck",
    "program_id": "program_1",
    "unsupported_omitted": [
      "Borda",
      "external data acquisition",
      "empirical research artifacts"
    ]
  },
  {
    "attempt_id": "c01_certified_attainability_frontiers_attempt_01",
    "candidate_files": [
      "program_1/program_spec.toml",
      "program_1/src/program.py"
    ],
    "date": "2026-11-17",
    "evaluation_artifacts_present": false,
    "event": "candidate_ready",
    "executed_evaluation": false,
    "executed_project_code": false,
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "c01_certified_attainability_frontiers",
    "later_candidates_created": false,
    "memory_appended": true,
    "program_id": "program_1",
    "spec_identical_to_starter": true,
    "validation": "static source reasoning and filesystem comparison only"
  },
  {
    "attempt_id": "c01_certified_attainability_frontiers_attempt_01",
    "evidence": "combined_score=0.42832805393112416, correct=False; scientific acceptance failed; cause unavailable; correct=false alone does not establish a protocol or implementation defect; search metrics (data): {\"combined_score\": 0.42832805393112416, \"control_pass_rate\": 0.9525462962962963, \"correct\": false, \"feasible_rate\": 0.4027777777777778, \"mean_effort_fraction\": 0.7963369070825209, \"mean_verified_gap_fraction\": 0.18981481481481483}",
    "idea_id": "c01_certified_attainability_frontiers",
    "metrics": {
      "combined_score": 0.42832805393112416,
      "control_pass_rate": 0.9525462962962963,
      "correct": false,
      "feasible_rate": 0.4027777777777778,
      "mean_effort_fraction": 0.7963369070825209,
      "mean_verified_gap_fraction": 0.18981481481481483
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T12:50:05.435064+00:00"
  },
  {
    "evidence": "Read named task/results/memory/skills and prior candidate source/spec. Interface supports uploaded matrices, mean/median/trimmed, common alpha, strict-first margin 1e-10, original-column outputs, work_seconds and node_budget. Prior source repeats whole-matrix aggregation per decision; amortization is a hypothesis, not a failure explanation. Prior combined_score=0.42832805393112416, correct=false, control_pass_rate=0.9525462962962963, feasible_rate=0.4027777777777778, mean_effort_fraction=0.7963369070825209, mean_verified_gap_fraction=0.18981481481481483; incumbent combined_score=0.53012102014295, correct=true. External incumbent source unavailable. Alternatives: repeated prefix-only certification, unsupported Borda/paper operations, and unobserved training costs. Selected conservative rank-window envelopes plus verified supports and shared preprocessing. No project code, tests, evaluator, literature search, or computational probes run. Canonical local target computed once after ID/title finalization: ideas/02_amortized_rank_window_certificates_for_targeted_investment/memory.md; no alternate same-cycle target created or used.",
    "idea_id": "c02_amortized_rank_window_certificates",
    "next_action": "Preserve documented RPC; amortize repeated panel statistics, guard rank-window lower bounds, verify supports, exhaust panels up to six tasks, and refine within remaining time. Test conditional rank-window/support differences through permitted later evaluation; accept negative outcomes. Stop reason: idea_bundle_ready; improvement untested.",
    "rubrics": [
      {
        "id": "improve_combined_score",
        "type": "metric"
      },
      {
        "id": "amortized_panel_statistics",
        "type": "implementation"
      },
      {
        "id": "conservative_rank_window_bounds",
        "type": "implementation"
      },
      {
        "id": "verified_support_and_status",
        "type": "implementation"
      },
      {
        "id": "deadline_aware_anytime_refinement",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Amortized Rank Window Certificates for Targeted Investment and wrote matching bundles. gate=kept; trigger=none; reason=The proposal is untested, the recorded failure cause remains unavailable, and interface restrictions were already recorded rather than newly established scientific findings.",
    "tags": [
      "cycle_2",
      "worker_0",
      "untested_hypothesis",
      "gate=kept",
      "trigger=none",
      "single_canonical_memory_target"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "actions": [
      "inspect permitted starter and task",
      "clone program_0 to program_1"
    ],
    "attempt_id": "c02_amortized_rank_window_certificates_attempt_01",
    "event": "candidate_start",
    "execution_performed": false,
    "idea_id": "c02_amortized_rank_window_certificates",
    "program_id": "program_1"
  },
  {
    "attempt_id": "c02_amortized_rank_window_certificates_attempt_01",
    "event": "candidate_core_edited",
    "execution_performed": false,
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "c02_amortized_rank_window_certificates",
    "program_id": "program_1",
    "validation": "source review only"
  },
  {
    "attempt_id": "c02_amortized_rank_window_certificates_attempt_01",
    "contract_changed": false,
    "evaluation_performed": false,
    "event": "candidate_ready",
    "execution_performed": false,
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "c02_amortized_rank_window_certificates",
    "implementation": [
      "run-local canonical panel and rival caches",
      "guarded retained-rank and exact mean bounds",
      "exhaustive small-panel audits",
      "direct witness checks",
      "deadline-aware deterministic refinement"
    ],
    "limitations": [
      "no optional large-panel branch-and-bound",
      "no empirical paper workflow in this stage"
    ],
    "performance_improvement_claimed": false,
    "program_id": "program_1",
    "validation": "filesystem and source review only; entrypoint and unchanged spec confirmed"
  },
  {
    "attempt_id": "c02_amortized_rank_window_certificates_attempt_01",
    "evidence": "combined_score=0.42913823911630933, correct=False; scientific acceptance failed; cause unavailable; correct=false alone does not establish a protocol or implementation defect; search metrics (data): {\"combined_score\": 0.42913823911630933, \"control_pass_rate\": 0.9552469135802469, \"correct\": false, \"feasible_rate\": 0.4027777777777778, \"mean_effort_fraction\": 0.7963369070825209, \"mean_verified_gap_fraction\": 0.18981481481481483}",
    "idea_id": "c02_amortized_rank_window_certificates",
    "metrics": {
      "combined_score": 0.42913823911630933,
      "control_pass_rate": 0.9552469135802469,
      "correct": false,
      "feasible_rate": 0.4027777777777778,
      "mean_effort_fraction": 0.7963369070825209,
      "mean_verified_gap_fraction": 0.18981481481481483
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T13:06:05.197872+00:00"
  },
  {
    "evidence": "Read named workflows/task/histories/manifest/memory/conclusions and prior candidate source/spec. Prior combined scores 0.42832805393112416 and 0.42913823911630933 both had correct=false; effort, feasibility, and verified-gap aggregates were unchanged, with slightly different control_pass_rate. Incumbent combined_score=0.53012102014295, correct=true. Failure cause unknown. Alternatives were additional caching, repeated prefix certification, costly exhaustive large-panel search, and unsupported Borda/training/paper operations. Selected a minimax hinge envelope coupling retained ranks through one support budget; its practical benefit is untested. No program/evaluator execution, computational probes, package installation, or literature search occurred. Canonical local directory finalized once after ID/title: ideas/03_coupled_clipped_score_certificates_for_targeted_investment/memory.md; no alternate same-cycle target or staging memory was created or used.",
    "idea_id": "c03_coupled_clipped_score_certificates",
    "next_action": "Implement the complete-cutoff coupled bound through unchanged RPC, retain contract-supported certification and verified witnesses, exhaust supplied panels up to six tasks, and later compare enabled/disabled envelopes under matched budgets. Stop reason: idea_bundle_ready; improvement untested and original paper/reproducibility requirements remain outstanding.",
    "rubrics": [
      {
        "id": "improve_combined_score",
        "type": "metric"
      },
      {
        "id": "coupled_clipped_budget_envelope",
        "type": "implementation"
      },
      {
        "id": "conservative_budget_prefix_certificates",
        "type": "implementation"
      },
      {
        "id": "exhaustive_frontier_and_witness_audit",
        "type": "implementation"
      },
      {
        "id": "anytime_complete_cutoff_reuse",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Coupled Clipped Score Certificates for Targeted Investment and wrote matching bundles. gate=kept; trigger=none; reason=The proposed envelope has not been implemented or evaluated, and available acceptance feedback does not establish a failure cause or a validated change in practical recommendations.",
    "tags": [
      "cycle_3",
      "worker_0",
      "untested_hypothesis",
      "gate=kept",
      "trigger=none",
      "single_canonical_memory_target"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "c03_coupled_clipped_score_certificates_attempt_01",
    "changed_files": [
      "program_1/src/program.py"
    ],
    "event": "implementation_started",
    "idea_id": "c03_coupled_clipped_score_certificates",
    "notes": "Starter cloned; RPC contract inspected; coupled envelope and conservative certificate implementation planned.",
    "program_id": "program_1",
    "validation": "not executed; prohibited by stage boundaries"
  },
  {
    "attempt_id": "c03_coupled_clipped_score_certificates_attempt_01",
    "changed_files": [
      "program_1/src/program.py"
    ],
    "contract_changed": false,
    "event": "implementation_completed",
    "features": [
      "complete coupled hinge frontiers",
      "guarded excluded-prefix lower bounds",
      "reference/exhaustive-only optimal status",
      "run-local cache and deadlines",
      "exhaustive small-panel runtime audits"
    ],
    "idea_id": "c03_coupled_clipped_score_certificates",
    "limitations": "No empirical improvement, runtime audit outcome, ablation, paper, or provenance package claimed.",
    "program_id": "program_1",
    "validation": "static review only; execution prohibited"
  },
  {
    "attempt_id": "c03_coupled_clipped_score_certificates_attempt_01",
    "candidate_artifacts": [
      "program_spec.toml",
      "src/program.py"
    ],
    "changed_files": [
      "program_1/src/program.py"
    ],
    "entrypoint_exists": true,
    "event": "candidate_ready",
    "idea_id": "c03_coupled_clipped_score_certificates",
    "later_candidates_created": false,
    "limitations": [
      "runtime audits unexecuted",
      "matched empirical ablation unexecuted",
      "no paper or provenance package",
      "no observed training responses or training-cost estimates"
    ],
    "performance_claim": null,
    "program_id": "program_1",
    "program_spec_unchanged": true,
    "tooling_incident": "Grouped apply_patch invocation not found; dedicated patch invocation succeeded.",
    "validation": "plain filesystem comparison and static source search only; no code execution or evaluation"
  },
  {
    "attempt_id": "c03_coupled_clipped_score_certificates_attempt_01",
    "evidence": "combined_score=0.42832805393112416, correct=False; scientific acceptance failed; cause unavailable; correct=false alone does not establish a protocol or implementation defect; search metrics (data): {\"combined_score\": 0.42832805393112416, \"control_pass_rate\": 0.9525462962962963, \"correct\": false, \"feasible_rate\": 0.4027777777777778, \"mean_effort_fraction\": 0.7963369070825209, \"mean_verified_gap_fraction\": 0.18981481481481483}",
    "idea_id": "c03_coupled_clipped_score_certificates",
    "metrics": {
      "combined_score": 0.42832805393112416,
      "control_pass_rate": 0.9525462962962963,
      "correct": false,
      "feasible_rate": 0.4027777777777778,
      "mean_effort_fraction": 0.7963369070825209,
      "mean_verified_gap_fraction": 0.18981481481481483
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T13:18:02.192017+00:00"
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
