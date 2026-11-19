# Role
You are the reference-planning agent for a completed research run.
Goal: produce a grounded reference query plan that will drive automated citation retrieval for the paper stage.
Use grounded inputs only. Do not retrieve references yet.

This prompt must transfer across tasks and runs.
Infer all domain details, methods, benchmarks, architectures, and comparator families from the current artifacts only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

# Task Context
## Goal
**研究任务：模型规模如何影响小型算法任务上的"延迟泛化"**
**背景**
在模运算等小型算法任务上，神经网络常出现"延迟泛化"（grokking）：训练集准确率
很早就接近 100%，而验证集准确率要在训练很久之后才突然上升。已有工作从电路效率、
从懒惰状态到丰富状态的训练动力学转变、权重范数等角度解释这一现象。

在模运算类算法任务上，模型规模在延迟泛化中起什么作用，目前缺少系统的实证刻画。

**研究问题**
请你自主提出并检验一个关于下述问题的可证伪的解释，并用实验支持或反驳它：

> 在模运算类算法任务上，延迟泛化的出现与模型规模之间有什么关系？

**动机**
厘清模型规模对延迟泛化的作用，可以为选择实验设置提供依据，也能约束对这一现象的各种解释。

**成功如何衡量**
一个好的回答应当：明确给出你的解释和它的可证伪预测；用本任务内自己运行的实验检验这些预测；
说明结论的适用范围与不成立的情形。结论可以是支持、反驳或视条件而定。

**关键约束**
资源与时间预算见 `resources.md`（一周、以 CPU 为主）；数据为程序合成，见 `data.md`；
最终产出为一篇论文及全部代码，见 `deliverable.md`。

**要求**
- 研究设计、实验、分析和结论由你自行决定；任务不规定方法或预期结果。
- 结论必须有实验证据，并说明统计不确定性。
- 其余约束见同目录的 `starter_literature.md`、`data.md`、`resources.md`、`deliverable.md`。

**起步文献（均发表于 2025-12-16 之前）**
1. Power, Burda, Edwards, Babuschkin, Misra. *Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets*. 2022.
   https://arxiv.org/abs/2201.02177
   说明：在小型算法生成的数据集（含模运算）上研究神经网络的泛化，报告训练集拟合之后很久才出现泛化的现象。
2. Nanda, Chan, Lieberum, Smith, Steinhardt. *Progress Measures for Grokking via Mechanistic Interpretability*. ICLR 2023.
   https://arxiv.org/abs/2301.05217
   说明：对在模加法任务上训练的小型 Transformer 做机理可解释性分析，并据此定义训练过程中的进展度量。
3. Liu, Michaud, Tegmark. *Omnigrok: Grokking Beyond Algorithmic Data*. ICLR 2023.
   https://arxiv.org/abs/2210.01117
   说明：通过分析损失地形与权重范数来研究延迟泛化，并在图像、语言、分子等任务上进行实验。
4. Varma, Shah, Kenton, Kramár, Kumar. *Explaining Grokking Through Circuit Efficiency*. 2023.
   https://arxiv.org/abs/2309.02390
   说明：从电路效率的角度提出对延迟泛化的一种解释，并用训练实验检验由此得出的若干预测。
5. Kumar, Bordelon, Gershman, Pehlevan. *Grokking as the Transition from Lazy to Rich Training Dynamics*. ICLR 2024.
   https://arxiv.org/abs/2310.06110
   说明：把延迟泛化与训练动力学从懒惰状态到丰富状态的转变联系起来，并在两层网络的回归设置中分析。
6. Davies, Langosco, Krueger. *Unifying Grokking and Double Descent*. 2023.
   https://arxiv.org/abs/2303.06173
   说明：把延迟泛化与双下降两类训练现象放在同一个框架下讨论。
7. Morris, Sitawarin, Guo, Kokhlikyan, Suh, Rush, Chaudhuri, Mahloujifar. *How much do language models memorize?* 2025.
   https://arxiv.org/abs/2505.24832
   说明：提出一种估计模型对数据点所含信息量的方法，并在语言模型上进行测量。
8. Tirumala, Markosyan, Zettlemoyer, Aghajanyan. *Memorization Without Overfitting: Analyzing the Training Dynamics of Large Language Models*. NeurIPS 2022.
   https://arxiv.org/abs/2205.10770
   说明：在语言模型上实证研究训练过程中对训练数据的记忆。
9. Zhang, Bengio, Hardt, Recht, Vinyals. *Understanding Deep Learning Requires Rethinking Generalization*. ICLR 2017.
   https://arxiv.org/abs/1611.03530
   说明：在图像分类网络上研究训练数据的拟合与泛化之间的关系，并检验显式正则化的作用。
10. Nakkiran, Kaplun, Bansal, Yang, Barak, Sutskever. *Deep Double Descent: Where Bigger Models and More Data Hurt*. ICLR 2020.
    https://arxiv.org/abs/1912.02292
    说明：报告多种深度学习任务中，测试表现随模型规模和训练轮数出现的双下降现象。
11. Loshchilov, Hutter. *Decoupled Weight Decay Regularization*. 2017.
    https://arxiv.org/abs/1711.05101
    说明：提出把权重衰减与梯度更新解耦的优化方法 AdamW。

**数据**
- 主数据：程序合成的算法任务数据，由素数 p 上的模二元运算（例如模加法）生成；对给定 p，
  输入 (a, b) 共 p² 个，可全部穷举，标签由运算直接计算。格式为整数对到整数的映射，
  内存中生成即可，体积可忽略。
- 获取方式：无需下载与账号；不涉及第三方数据，没有许可证问题；没有版本或快照需要固定。
- 可选：研究需要的其他合成数据可自行生成，并在论文中说明构造方式。
- 该类数据集的原始定义见 `starter_literature.md` 第 1 条。

**资源与预算**
- 计算：优先仅使用 CPU；如有需要可使用一张 GPU（单卡即可，不要求特定型号）。
  具体核数、内存、磁盘以运行环境为准。
- 时间上限：一周（含实验、写作与整理代码）。
- 估算依据：任务为小型模型（参数量不超过 10^6 量级）、小数据（输入对数量在 10^4 量级）的训练，
  单次运行在 CPU 上为分钟至小时级；全部实验合计约数十 CPU 小时。以上为粗略估算，未实测。
- 存储：需求小（远小于 1 GB）。
- 不需要大规模集群或付费 API。

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
    "evidence": "Supplied histories are empty; campaign memory had no discoveries. Bootstrap metadata reports correct=true and combined_score=0.0011792691662170303 without a scientific or failure breakdown. The supplied absolute baseline source path was unavailable. No experiments, task program, evaluator, external retrieval, or computational probes were run. Width-only and mechanistic-circuit alternatives were considered but offer weaker identification or require broader diagnostics. Required JSON bundles have been written; local memory uses only ideas/01_capacity_versus_decay_clock_in_width_dependent_grokking/memory.md.",
    "idea_id": "cycle_01_capacity_decay_clock",
    "next_action": "Resolve the documented candidate contract in the execution workspace, run separately seeded timing pilots, lock the primary paired-width protocol, retain censored and failed runs, and test capacity and decay-clock predictions with paired uncertainty before optional scope extensions. Status=idea_bundle_ready; scientific and harness verification pending.",
    "rubrics": [
      {
        "id": "canonical_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "paired_width_protocol",
        "type": "implementation"
      },
      {
        "id": "functional_scale_and_decay_clock",
        "type": "implementation"
      },
      {
        "id": "random_function_capacity_control",
        "type": "implementation"
      },
      {
        "id": "sustained_events_and_censoring",
        "type": "implementation"
      },
      {
        "id": "paired_uncertainty_and_reproducibility",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Capacity Versus Decay Clock in Width Dependent Grokking: distinguish earlier memorization from changed generalization time with paired widths, random-function controls, matched initial logit scale, and decay interventions. gate=kept; trigger=none; reason=No tested discovery or changed recommendation is established by an untested first-cycle proposal.",
    "tags": [
      "cycle_1",
      "worker_0",
      "no_scientific_execution",
      "gate=kept",
      "trigger=none"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "cycle_01_capacity_decay_clock_attempt_01",
    "event": "candidate_cloned_and_interface_reviewed",
    "executed": false,
    "idea_id": "cycle_01_capacity_decay_clock",
    "limitation": "Only a shared learning-rate recipe is exposed; proposed training and analysis interventions are unavailable.",
    "planned_recipe": {
      "decay_rate": 1.0,
      "initial_lr": 0.01
    },
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_01_capacity_decay_clock_attempt_01",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/EXPERIMENT_SCOPE.md"
    ],
    "contract_unchanged": true,
    "entrypoint_present": true,
    "event": "candidate_ready",
    "executed": false,
    "forbidden_artifacts_under_candidate": false,
    "idea_id": "cycle_01_capacity_decay_clock",
    "limitation": "RPC exposes only shared learning-rate scheduling; proposed width/calibration/label/decay experiments and uncertainty analysis cannot be implemented.",
    "program_id": "program_1",
    "recipe": {
      "decay_rate": 1.0,
      "initial_lr": 0.01
    },
    "scientific_hypothesis_tested": false,
    "status": "ready_for_harness"
  },
  {
    "attempt_id": "cycle_01_capacity_decay_clock_attempt_01",
    "evidence": "combined_score=0.0013285757680326544, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.0013285757680326544, \"correct\": true}",
    "idea_id": "cycle_01_capacity_decay_clock",
    "metrics": {
      "combined_score": 0.0013285757680326544,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T23:06:35.359747+00:00"
  },
  {
    "evidence": "Prior candidate program.py and EXPERIMENT_SCOPE.md expose only a shared bounded reset/recipe/schedule controller with no feedback. Prior attempt: correct=true, combined_score=0.0013285757680326544, rubric_overall_pass=false, run_exit_code=0; the aggregate failure cause remains unknown. Unsupported capacity grids and adaptive feedback were rejected; a lower constant rate changes the incumbent initial rate, making the selected one-parameter annealing contrast more directly controlled. Required JSON outputs were written. No scientific computation, program execution, evaluation, or external retrieval occurred. Only ideas/02_shared_exponential_annealing_for_width_robust_generalization/memory.md was written as cycle-local memory.",
    "idea_id": "cycle_02_shared_exponential_annealing",
    "next_action": "Clone the incumbent to program_1, change only decay_rate to 0.1, preserve protocol guards and seed independence, then obtain the official canonical evaluation. Do not interpret aggregate gains as a width interaction or grokking mechanism, invent uncertainty, or ignore simultaneous changes to cumulative AdamW decay. Status=idea_bundle_ready; hypothesis untested.",
    "rubrics": [
      {
        "id": "canonical_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "shared_annealed_recipe",
        "type": "implementation"
      },
      {
        "id": "contract_exact_exponential_schedule",
        "type": "implementation"
      },
      {
        "id": "reset_and_workload_isolation",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Shared Exponential Annealing for Width Robust Generalization: retain initial_lr=0.01 and change only decay_rate from 1.0 to 0.1. gate=updated; trigger=b; reason=Verified candidate source establishes a previously undistilled interface-limited open-loop scheduling category; future ideas must use only exposed controls.",
    "tags": [
      "cycle_2",
      "worker_0",
      "no_scientific_execution",
      "gate=updated",
      "trigger=b"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "action": "Cloned program_0 to program_1; preparing shared decay_rate=0.1 with initial_lr=0.01 and unchanged RPC contract",
    "attempt_id": "cycle_02_shared_exponential_annealing_attempt_01",
    "event": "candidate_preparation",
    "execution": "none",
    "idea_id": "cycle_02_shared_exponential_annealing",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_shared_exponential_annealing_attempt_01",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/EXPERIMENT_SCOPE.md"
    ],
    "empirical_status": "unestablished; awaiting harness evaluation",
    "event": "candidate_ready",
    "execution": "none",
    "idea_id": "cycle_02_shared_exponential_annealing",
    "later_candidates_created": false,
    "policy": {
      "decay_rate": 0.1,
      "initial_lr": 0.01
    },
    "program_id": "program_1",
    "static_checks": {
      "candidate_artifacts_absent": true,
      "entrypoint_exists": true,
      "specification_unchanged": true
    }
  },
  {
    "attempt_id": "cycle_02_shared_exponential_annealing_attempt_01",
    "evidence": "combined_score=0.0012374734382319728, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.0012374734382319728, \"correct\": true}",
    "idea_id": "cycle_02_shared_exponential_annealing",
    "metrics": {
      "combined_score": 0.0012374734382319728,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T23:39:19.290977+00:00"
  },
  {
    "evidence": "Incumbent aggregate=0.0013285757680326544 versus strong-annealing aggregate=0.0012374734382319728; both correct=true and run_exit_code=0. No uncertainty or causal diagnosis is supplied. Verified candidate source exposes only a shared normalized open-loop exponential controller. Repeating strong annealing lacks a positive signal; lower constant initial_lr changes early updates; unsupported width sweeps and feedback were rejected. Required JSON files authored. Only ideas/03_mild_exponential_annealing_with_sustained_learning_rates/memory.md was created or written as cycle-local memory. File reads and patch application only; no scientific execution or external retrieval.",
    "idea_id": "cycle_03_mild_exponential_annealing",
    "next_action": "Clone the incumbent to program_1, change only decay_rate to 0.5, preserve all protocol guards and seed independence, and obtain the official canonical evaluation during execution. Do not infer a width-dependent grokking mechanism, significance, monotonicity or an AdamW-independent effect. Status=idea_bundle_ready; hypothesis untested.",
    "rubrics": [
      {
        "id": "canonical_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "shared_mild_annealing_recipe",
        "type": "implementation"
      },
      {
        "id": "contract_exact_exponential_schedule",
        "type": "implementation"
      },
      {
        "id": "reset_and_workload_isolation",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Mild Exponential Annealing with Sustained Learning Rates: initial_lr=0.01, decay_rate=0.5. gate=updated; trigger=d; reason=Qualify the formerly untested annealing recommendation with observed strong-annealing underperformance while leaving weaker annealing untested and causes unknown.",
    "tags": [
      "cycle_3",
      "worker_0",
      "no_scientific_execution",
      "gate=updated",
      "trigger=d"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "cycle_03_mild_exponential_annealing_attempt_01",
    "event": "preparation_started",
    "execution": "No candidate code, tests, training or evaluation executed",
    "idea_id": "cycle_03_mild_exponential_annealing",
    "plan": "Clone program_0; retain initial_lr=0.01 and set shared decay_rate=0.5; preserve RPC contract and update scope documentation",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_03_mild_exponential_annealing_attempt_01",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/EXPERIMENT_SCOPE.md"
    ],
    "contract": "Unchanged program_spec.toml, existing entrypoint, preserved validation, response keys and state transitions",
    "editing_note": "apply_patch and patch unavailable; used plain shell file writes",
    "evaluation_status": "Deferred to harness; no code, tests, training or evaluation executed",
    "event": "candidate_ready",
    "idea_id": "cycle_03_mild_exponential_annealing",
    "limitations": "No new score, trajectories, uncertainty estimates or evidence identifying a width-dependent mechanism",
    "program_id": "program_1",
    "recipe": {
      "decay_rate": 0.5,
      "initial_lr": 0.01
    },
    "verification": "Static diff, spec comparison and file inventory only; no evaluator artifacts; no later candidate created"
  },
  {
    "attempt_id": "cycle_03_mild_exponential_annealing_attempt_01",
    "evidence": "combined_score=0.0012804939911196318, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.0012804939911196318, \"correct\": true}",
    "idea_id": "cycle_03_mild_exponential_annealing",
    "metrics": {
      "combined_score": 0.0012804939911196318,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-18T00:09:17.400031+00:00"
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
