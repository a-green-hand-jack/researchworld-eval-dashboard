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
    "evidence": "The validated manifest reports combined_score=0.7779622741764081 and correct=true; histories and prior memory have no experimental results. The referenced baseline source was unavailable, which does not establish a protocol defect. Considered a descriptive width-only sweep and capacity-confounded frozen-feature controls; selected a directly runnable paired width-by-decay intervention with censoring-aware analysis. No training, evaluator execution, computational probes, package installation, or web access occurred. Canonical local memory target is ideas/01_separating_width_effects_from_the_post_fit_decay_clock/memory.md; no alternate cycle-local target was created.",
    "idea_id": "cycle_01_width_decay_clock",
    "next_action": "Preserve the documented candidate interface, implement the paired grid and random-label controls, calibrate throughput during execution, test positive-decay clock collapse with seed-block uncertainty and explicit right censoring, and generate all paper artifacts from actual recorded results.",
    "rubrics": [
      {
        "id": "combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "paired_width_decay_intervention",
        "type": "implementation"
      },
      {
        "id": "explicit_censoring_and_decay_clock",
        "type": "implementation"
      },
      {
        "id": "paired_uncertainty_and_auditable_reporting",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Separating Width Effects from the Post-Fit Decay Clock; idea_bundle_written and execution_pending. gate=kept; trigger=none; reason=No experimental evidence or validated refinement is available; an untested design is not a scientific conclusion.",
    "tags": [
      "cycle_1",
      "untested_hypothesis",
      "no_execution",
      "gate=kept",
      "trigger=none"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "evidence": "Both bundles share four rubric objects; the three implementation verifications contain five, six, and five executable literal snippets. Only ideas/01_separating_width_effects_from_the_post_fit_decay_clock/memory.md was used for local memory. No computational validation or experimental execution occurred.",
    "idea_id": "cycle_01_width_decay_clock",
    "next_action": "Implement the study, preserve all run outcomes, and treat the conditional clock as unidentified if supported common post-fit follow-up is unavailable.",
    "scope": "idea",
    "step": "verify",
    "summary": "Manually checked matching rubric content and one canonical local memory target; clarified immediate events, exact event-rate intervals, and informative-censoring limitations. gate=kept; trigger=none; reason=Prospective safeguards do not constitute experimental findings.",
    "tags": [
      "cycle_1",
      "manual_design_check",
      "gate=kept",
      "trigger=none"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "cycle_01_width_decay_clock_attempt_01",
    "configuration": {
      "init_multiplier": 1.0,
      "learning_rate": 0.003,
      "weight_decay": 1.0
    },
    "event": "interface_inspection_and_clone",
    "execution_performed": false,
    "idea_id": "cycle_01_width_decay_clock",
    "limitation": "fixed optimizer settings only; no observations or experimental controls for the proposed grid",
    "program_id": "program_1",
    "source": "program_0"
  },
  {
    "attempt_id": "cycle_01_width_decay_clock_attempt_01",
    "configuration": {
      "init_multiplier": 1.0,
      "learning_rate": 0.003,
      "weight_decay": 1.0
    },
    "entrypoint_present": true,
    "evaluation_performed": false,
    "event": "candidate_ready",
    "execution_performed": false,
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/EXPERIMENT_SCOPE.md"
    ],
    "idea_id": "cycle_01_width_decay_clock",
    "interface_preserved": true,
    "later_candidates_created": false,
    "manifest_unchanged": true,
    "program_id": "program_1",
    "scientific_status": "untested; proposed grid and trajectory analysis unavailable through the controller",
    "validation": "static diff and filesystem listing only"
  },
  {
    "attempt_id": "cycle_01_width_decay_clock_attempt_01",
    "evidence": "combined_score=0.8582846262840949, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.8582846262840949, \"complete_episode_fraction\": 1.0, \"control_validity_rate\": 1.0, \"correct\": true, \"grokking_incidence\": 0.0, \"mean_final_accuracy\": 0.43313850513637975, \"restricted_mean_delay\": 1.0}",
    "idea_id": "cycle_01_width_decay_clock",
    "metrics": {
      "combined_score": 0.8582846262840949,
      "complete_episode_fraction": 1.0,
      "control_validity_rate": 1.0,
      "correct": true,
      "grokking_incidence": 0.0,
      "mean_final_accuracy": 0.43313850513637975,
      "restricted_mean_delay": 1.0
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-12T23:56:50.217942+00:00"
  },
  {
    "evidence": "Recorded incumbent: combined_score=0.8582846262840949, correct=true, complete_episode_fraction=1.0, control_validity_rate=1.0, grokking_incidence=0.0, mean_final_accuracy=0.43313850513637975, restricted_mean_delay=1.0. Overall rubric pass is false; its precise failing criterion is unknown. Local incumbent source documents only common learning_rate, weight_decay, init_multiplier and no observations. Select init_multiplier=0.5 while preserving learning_rate=0.003 and weight_decay=1.0. Considered a further learning-rate increase, which changes update and decay rates together, and width-specific normalization/factorial grids, which the interface forbids. Aggregate improvement would not establish width effects, uncertainty, delayed events, or norm mediation. Both bundles share three rubric objects by manual authored-content comparison, with four and six executable implementation snippets. Sole canonical local memory target: ideas/02_testing_initialization_scale_at_a_fixed_decay_clock/memory.md. No alternate cycle-local directory was created or used; no candidate, evaluator, training, or computational probe was run.",
    "idea_id": "cycle_02_initialization_barrier",
    "next_action": "Implement the common (0.003,1.0,0.5) configuration with the existing reset/plan contract, evaluate in the execution loop, and report only publicly supplied observations. Preserve all uncertainty, paper, and reproducibility obligations; leave width/arm and seed-level conclusions unresolved unless actual evidence is provided.",
    "rubrics": [
      {
        "id": "combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "isolated_initialization_intervention",
        "type": "implementation"
      },
      {
        "id": "fixed_public_controller_contract",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Testing Initialization Scale at a Fixed Decay Clock; idea_bundle_written and execution_pending. gate=kept; trigger=none; reason=The initialization explanation is prospective and aggregate incumbent results do not establish a new scientific conclusion.",
    "tags": [
      "cycle_2",
      "initialization_intervention",
      "untested_hypothesis",
      "interface_bounded",
      "gate=kept",
      "trigger=none"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "cycle_02_initialization_barrier_attempt_01",
    "evidence": "Read starter source and manifest only; no execution or evaluator inspection.",
    "idea_id": "cycle_02_initialization_barrier",
    "next_action": "Clone program_0 to program_1 and edit candidate source and scope documentation.",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "idea",
    "summary": "Implement common initialization multiplier 0.5 while retaining learning rate 0.003 and weight decay 1.0; gate=kept; trigger=none; reason=no new experimental evidence and conclusions edits are not permitted.",
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "cycle_02_initialization_barrier_attempt_01",
    "evidence": "Changed program_1/src/program.py and program_1/src/EXPERIMENT_SCOPE.md only relative to clone. Manifest cmp identical. Source diff preserves validation semantics and lifecycle. apply_patch unavailable; plain text editing used instead.",
    "idea_id": "cycle_02_initialization_barrier",
    "next_action": "Stop and hand off candidate for official harness evaluation.",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "edit",
    "summary": "Cloned program_0 to program_1 and implemented fixed init_multiplier=0.5, learning_rate=0.003, weight_decay=1.0; updated scope documentation.",
    "timestamp": "2026-11-13"
  },
  {
    "attempt_id": "cycle_02_initialization_barrier_attempt_01",
    "evidence": "Manifest and entrypoint exist; candidate listing contains only manifest and two source files, with no evaluator artifacts. No later candidate created. No tests, training, imports, evaluation, or network access performed. Required memory files appended.",
    "idea_id": "cycle_02_initialization_barrier",
    "next_action": "Harness-owned evaluation only; test the initialization hypothesis against public returned metrics without claiming size mediation, significance, or grokking from aggregate accuracy alone.",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "final",
    "summary": "candidate_ready; gate=kept; trigger=none; reason=no experimental evidence and conclusions edits are outside stage boundaries.",
    "timestamp": "2026-11-13"
  },
  {
    "attempt_id": "cycle_02_initialization_barrier_attempt_01",
    "evidence": "combined_score=0.869465108041091, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.869465108041091, \"complete_episode_fraction\": 1.0, \"control_validity_rate\": 1.0, \"correct\": true, \"grokking_incidence\": 0.0, \"mean_final_accuracy\": 0.47786043216436414, \"restricted_mean_delay\": 1.0}",
    "idea_id": "cycle_02_initialization_barrier",
    "metrics": {
      "combined_score": 0.869465108041091,
      "complete_episode_fraction": 1.0,
      "control_validity_rate": 1.0,
      "correct": true,
      "grokking_incidence": 0.0,
      "mean_final_accuracy": 0.47786043216436414,
      "restricted_mean_delay": 1.0
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-13T00:30:26.978842+00:00"
  },
  {
    "evidence": "Cycle 1 combined_score=0.8582846262840949 and mean_final_accuracy=0.43313850513637975; cycle 2 combined_score=0.869465108041091 and mean_final_accuracy=0.47786043216436414. Both correct=true, complete_episode_fraction=1.0, control_validity_rate=1.0, grokking_incidence=0.0, restricted_mean_delay=1.0. Public uncertainty and width/arm breakdown unavailable. Local incumbent source confirms a common reset/plan controller without training observations. Select learning_rate=0.006, weight_decay=0.5, init_multiplier=0.5, preserving nominal shrinkage but not effective regularization or post-fit exposure. Considered stronger decay alone, out-of-range lower initialization, and unsupported width-specific scaling/private grids. Both bundles contain the same three rubric objects by manual comparison; implementation rubrics contain four and six executable patterns. Sole canonical local memory target: ideas/03_separating_optimizer_speed_from_nominal_decay_exposure/memory.md; no alternate cycle-local target or staging memory created. No candidate, training, evaluator, computational probe, package installation, or network access occurred. Conclusions updated directly without helper execution.",
    "idea_id": "cycle_03_matched_shrinkage_speed",
    "next_action": "Implement the common configuration in program_1 with unchanged validation and response fields; hand off for official evaluation. Report only public observations; leave uncertainty, width mediation, delayed events and full paper/reproducibility requirements unresolved until supported.",
    "rubrics": [
      {
        "id": "combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "matched_shrinkage_speed_intervention",
        "type": "implementation"
      },
      {
        "id": "fixed_public_controller_contract",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Separating Optimizer Speed from Nominal Decay Exposure; idea_bundle_written; execution_pending. gate=updated; trigger=b; reason=Recorded initialization results open an evidence-bounded finite-horizon search lead, distinct from unobserved grokking or size mediation.",
    "tags": [
      "cycle_3",
      "matched_nominal_shrinkage",
      "optimization_speed",
      "interface_bounded",
      "gate=updated",
      "trigger=b"
    ],
    "timestamp": "2026-11-13"
  },
  {
    "attempt_id": "cycle_03_matched_shrinkage_speed_attempt_01",
    "details": "Inspected allowed starter and task text; cloned program_0 to program_1. Planned common learning_rate=0.006, weight_decay=0.5, init_multiplier=0.5 with unchanged manifest and lifecycle; no execution or evaluation.",
    "event": "candidate_preparation",
    "idea_id": "cycle_03_matched_shrinkage_speed",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_03_matched_shrinkage_speed_attempt_01",
    "configuration": {
      "init_multiplier": 0.5,
      "learning_rate": 0.006,
      "weight_decay": 0.5
    },
    "controller_lifecycle_unchanged": true,
    "entrypoint_exists": true,
    "evaluator_artifacts_created": false,
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/EXPERIMENT_SCOPE.md"
    ],
    "idea_id": "cycle_03_matched_shrinkage_speed",
    "later_candidates_created": false,
    "limitations": "Matched nominal shrinkage is not matched effective regularization or post-fit exposure. Current performance, width effects, uncertainty, and full research deliverables remain pending harness-owned observations.",
    "manifest_unchanged": true,
    "program_id": "program_1",
    "validation": "Static source comparison and file listing only; no execution or evaluation."
  },
  {
    "attempt_id": "cycle_03_matched_shrinkage_speed_attempt_01",
    "evidence": "combined_score=0.7361627701027276, correct=False; scientific acceptance failed; cause unavailable; correct=false alone does not establish a protocol or implementation defect; search metrics (data): {\"combined_score\": 0.7361627701027276, \"complete_episode_fraction\": 0.8333333333333333, \"control_validity_rate\": 0.8333333333333333, \"correct\": false, \"grokking_incidence\": 0.0, \"mean_final_accuracy\": 0.44465108041091034, \"restricted_mean_delay\": 1.0}",
    "idea_id": "cycle_03_matched_shrinkage_speed",
    "metrics": {
      "combined_score": 0.7361627701027276,
      "complete_episode_fraction": 0.8333333333333333,
      "control_validity_rate": 0.8333333333333333,
      "correct": false,
      "grokking_incidence": 0.0,
      "mean_final_accuracy": 0.44465108041091034,
      "restricted_mean_delay": 1.0
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-13T01:16:56.314460+00:00"
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
