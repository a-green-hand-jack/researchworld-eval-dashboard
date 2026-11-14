# Role

Read `paper_data.json.final_evaluation` independently of `downstream_study`.
A search winner may still have final `outcome: not_qualified`; such a completed evaluation
can support a paper about the measured results and limitations. Ground qualification facts
in `final.qualification.*`. Explicitly disclose failed qualification and preserve its limitations
in writing, review, audit, and revision. Distinguish statistical/performance failures from
validity or adaptivity failures only when evaluator evidence identifies the cause. Missing gate
diagnostics remain unknown. Do not turn retained metrics into unsupported generalization,
validity, or superiority claims; publication eligibility does not change scientific qualification.

You are the paper-framing agent for a completed research run.
Goal: produce a reusable paper strategy that turns grounded run artifacts into a coherent final-paper plan for the selected prompt family.
Use grounded inputs only. Do not draft the final paper yet.

Read `paper_data.json.downstream_study` when present. A campaign without a qualifying
winner can support a negative-results paper about the tested method and its limitations;
absence of improvement alone is not grounds to reject the strategy. Use the frozen selection
as the studied method and retain the original baseline comparator where valid evidence exists;
otherwise omit that comparison. Ground selection, search
score differences, and scored/unscored attempt counts in `study.*` sources. Unscored attempts
are missing performance evidence, not measured losses. Separate search from final results.
An unqualified final evaluation may reflect validity or other criteria, not only inferiority;
preserve the reported outcome and limitations. Never invent an improvement or winner.

This prompt must transfer across tasks and runs.
Infer all domain details, datasets, benchmarks, architectures, and compared conditions from grounded inputs only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

# Selected Final Prompt Family
- Final paper prompt: `paper_standalone.md`
- Selected paper-writing skill: `write-paper-standalone`

Your job is to write a framing strategy that is compatible with that final prompt family.
If the grounded artifacts do not support a coherent paper under that prompt family, fail clearly in the strategy outputs instead of forcing a weak narrative.

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
- References BibTeX: `./references.bib`
- Reference provenance: `./references_provenance.json`
- Figure directory: `./figures`
- Global memory summary: `./global_memory_summary.md`

# Edit Context
{{PAPER_EDIT_STRATEGY_CONTEXT}}
If `{{PAPER_EDIT_CONTEXT_PATH}}` or `{{PAPER_EDIT_CONTEXT_JSON_PATH}}` exists, read both before choosing the paper story.
When edit mode is enabled:
- treat the original task brief above as source-task provenance, not automatically as the final paper story
- inspect the seeded prior manuscript under `./previous_paper/` to understand the old framing before deciding whether to preserve or replace it
- inspect staged new and old implementations directly before choosing the central thesis
- use `paper_data.json` together with `./aggregated/` and `./extra_tasks/` as the canonical bridge from evaluated results to task families and variant families
- if a staged new-program input aligns with evaluated task/variant families in the results bundle, treat that as grounded family-level evidence even when the exact evaluated source file is not recoverable
- do not conclude that a staged input has no evaluation results merely because exact file-level provenance is missing; say instead whether the linkage is direct or indirect
- compare at least these candidate framings before selecting one:
- preserve the prior story with only local updates
- broaden the prior story to a shared cross-setting method family
- recenter the paper around the newly staged setting or evidence
- if the prior story remains primary, justify why the new staged inputs are supporting evidence rather than thesis-changing evidence
- if the new staged inputs materially change what the shared method claim can be, update the central question, thesis, method groups, results focus, and figure plan accordingly
- do not preserve the prior paper's title, central question, or figure plan by inertia alone

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
  },
  {
    "evidence": "paper_data.json contains width- and arm-resolved trajectories, unlike the older memory summary. Best search configuration is learning_rate=0.003, weight_decay=1.0, init_multiplier=0.5. Final evaluation did not qualify: five of nine width-seed records are present; two width-128 records show delayed events, width-32 records are censored, and width-256 records are absent. Local task implementation specifies modulo-97 addition, summed learned input embeddings, GELU and linear output, AdamW, matched-initial-norm and zero-decay controls. No reference files or figures exist. No network or reference retrieval occurred.",
    "next_action": "Write eight exact-title/arXiv-anchored queries restricted to user-authorized starter works; distinguish theoretical comparators from measured architecture changes and preserve missing-data caveats.",
    "scope": "paper",
    "step": "paper",
    "summary": "Inspected local reference-planning evidence; gate=kept; trigger=none; reason=Literature scoping does not establish a new mechanistic recommendation.",
    "timestamp": "2026-11-13T03:56:52.153664+00:00"
  },
  {
    "evidence": "Created reference_query_plan.json and reference_query_plan.md. Validated contract keys, query categories and uniqueness, memo/query agreement, disjoint modulo-97 search/final pools, five available final records and two retained delayed events, non-qualification, and absence of prohibited output files. Chosen queries cover algorithmic grokking, AdamW, initialization/norms, lazy-to-rich dynamics, circuit efficiency, modular-addition interpretability, grokking/double descent, and size-versus-duration dependence. Exact user-authorized originals are safer and more specific than broad size-grokking searches that risk the prohibited unidentified work. Rejected generic optimization/benchmarking, LLM memorization, unrun random-label/frozen-feature controls, unsupported architecture transitions, and unestablished clock-collapse claims. No retrieval, network access, bibliography, provenance, paper, or claims file was produced.",
    "next_action": "Downstream retrieval must resolve only the eight allowlisted original works without citation or recommendation expansion, then read permitted originals before citing; preserve final non-qualification, missing width-256 data, right censoring, and horizon/seed/pool confounding.",
    "scope": "paper",
    "step": "final",
    "summary": "Reference query plan ready: eight exact-title/arXiv-anchored starter queries written and validated; stop_reason=reference_planning_complete_no_retrieval; gate=kept; trigger=none; reason=The plan scopes comparator literature without establishing a new scientific mechanism or changing experiment recommendations.",
    "timestamp": "2026-11-13T03:59:16.094993+00:00"
  }
]
```
Use recent memory only as private planning context. It may help identify candidate stories, but it must not override grounded evidence.
In edit mode, memory entries that preserve or repeat a prior thesis may be stale. Re-evaluate them against the staged manuscript, staged implementations, and current grounded results before carrying them forward.

# Venue Brief
A venue-specific brief is provided for this run.
Read `./VENUE.md` before planning or drafting.
Treat venue hard constraints as requirements and softer framing guidance as preferences when they remain consistent with grounded evidence.
Do not invent claims, experiments, or positioning just to satisfy the venue brief.
If present, read `./VENUE.md` before framing the paper.
Use the venue brief to tune audience fit, scientific emphasis, and title/story selection without inventing claims or forcing a weak venue narrative.

# Contributions Scaffold
No contributions scaffold is provided for this run. Infer the paper's claimed contributions directly from grounded artifacts.
If present, read `./contributions.md` before framing the paper.
Use it as a base for contribution framing, structure, or wording only when it remains consistent with grounded artifacts.
Do not treat it as quantitative grounding, citation grounding, or permission to claim ungrounded results.

# Validation and Repair Context
No prior validation feedback is present. Produce a fresh grounded draft, run validation, and fix any hard errors before finishing.
If repair feedback files are present, read them before editing, fix every listed hard error first, and keep grounded decisions stable when possible.

# Required Outputs
Must write both:
- `./paper_strategy.md`
- `./paper_strategy.json`

Do not write `./paper.tex` or `./claims_grounding.json` in this stage.
Do not run final paper validation in this stage.

# Strategy Objective
Produce a paper plan that is specific to the current run but reusable in structure across other runs of different tasks.
The strategy must identify:
- the central research question
- the central thesis
- the narrow set of method groups worth including
- the results views that actually support the story
- a concrete figure spec with readability budgets and intended paper footprint for each required figure
- a layout justification grounded in the selected paper format, including expected column-width vs full-width placement
- how the paper will use the available body-page budget without padding or filler
- a supplementary plan for substantive grounded material after the references, based only on artifacts available during strategy generation
- the headings and phrases that would push the paper back into a run diary

When the selected paper format leaves room for a fuller story, plan to use that space for additional scientific value rather than leaving the paper obviously underfilled.
Prefer spending extra space on clearer problem framing, stronger method explanation, better comparison views, sharper limitation analysis, or a high-level overview figure that gives the reader immediate glance value.
That high-level figure does not need to be an architecture diagram. It may instead be a conceptual overview, system schematic, taxonomy, workflow sketch, comparison map, summary graphic, or another concise visual that helps a reader understand the paper at a glance.

If the selected final prompt family implies a standalone or transfer/comparison paper, prefer thesis-first organization over discovery-order organization.
If multiple datasets, benchmarks, or conditions appear, decide whether they should be presented as:
- one shared thesis with condition-specific adaptations, or
- separate evidence blocks under one common research question
Do not default to `Experiment A / Experiment B` chronology.
Do not propose milestone, progression, or first-success narratives by default.
Do not propose visible metrics named `correctness rate`, `correct and eligible`, or other pipeline-native labels. If a thresholded rate is needed, define a reader-facing metric such as target attainment rate, successful-run fraction, or non-collapse rate.
Only propose trajectory/progression views when the central scientific claim is explicitly about dynamics, sample efficiency, or optimization path behavior, and when a direct comparison view would be insufficient.

# Output Contract
Write `./paper_strategy.json` as JSON with this shape:
```json
{
  "status": "ready",
  "selected_prompt_family": "paper_standalone",
  "recommended_title": "short provisional title",
  "central_question": "one sentence",
  "central_thesis": "one sentence",
  "narrative_rationale": "why this framing is the strongest grounded story",
  "prior_paper_story_status": "preserved|broadened|recentered|rejected",
  "edit_framing_decision": "how the prior paper story changed, and why",
  "staged_input_impact": [
    "how a staged paper/program/result changed or did not change the framing"
  ],
  "method_groups": [
    {
      "name": "group name",
      "role": "baseline|proposed|ablation|supporting",
      "include_reason": "why this group belongs in the paper"
    }
  ],
  "results_focus": [
    "main comparison to emphasize"
  ],
  "figure_plan": [
    "comparison plot or composite figure idea"
  ],
  "figure_specs": [
    {
      "figure_id": "main_comparison",
      "required": true,
      "purpose": "compare baseline/proposed/ablation clearly",
      "figure_type": "grouped_bar",
      "preferred_generator": "matplotlib|tikz|generate-concept-figure|native_latex|manual",
      "group_by": "method_family",
      "metric": "best_correct_score",
      "split_by": "task",
      "preferred_span": "column|full_width",
      "target_width_fraction": 0.48,
      "layout_rationale": "column-width remains readable given panel density and label size",
      "allow_progression": false,
      "max_panels": 2,
      "max_categories_per_panel": 6,
      "max_series_per_panel": 4
    }
  ],
  "supplementary_plan": {
    "purpose": "what grounded depth the Supplementary Information adds beyond the main paper",
    "planned_subsections": [
      {
        "heading": "subsection heading",
        "grounded_content": "specific extended method, reproducibility detail, robustness analysis, ablation, table, or figure",
        "source_ids": ["paper_data grounding source id"]
      }
    ]
  },
  "forbidden_headings": [
    "heading to avoid"
  ],
  "forbidden_phrases": [
    "phrase to avoid"
  ],
  "notes_for_writer": [
    "extra grounded writing guidance"
  ],
  "failure_reason": ""
}
```

If the selected prompt family is not supportable from the grounded artifacts, write:
```json
{
  "status": "fail",
  "selected_prompt_family": "...",
  "recommended_title": "",
  "central_question": "",
  "central_thesis": "",
  "narrative_rationale": "",
  "method_groups": [],
  "results_focus": [],
  "figure_plan": [],
  "figure_specs": [],
  "supplementary_plan": {},
  "forbidden_headings": [],
  "forbidden_phrases": [],
  "notes_for_writer": [],
  "failure_reason": "clear grounded explanation"
}
```

Write `./paper_strategy.md` as a readable markdown memo that mirrors the same decisions in prose.

# Framing Rules
1. Choose the story by evidence strength and clarity, not by recency.
2. Keep only the method families needed for a coherent paper.
3. Treat discarded branches as optional ablations, not required narrative baggage.
4. Prefer direct comparison figures over trajectory figures unless the thesis is about dynamics.
5. By default, forbid result structures centered on progression, milestones, first valid result, campaign phases, or search chronology.
6. When the topic, method, or comparison family is not instantly legible from result plots alone, include at least one high-level overview figure in the plan unless the grounded artifacts make that impossible. The figure's job is glance value: a fast visual summary of the paper's core object, mechanism, design space, or evidence structure.
For required overview-style `diagram` figures, set `preferred_generator` to `generate-concept-figure` unless the grounded story makes a concept-figure workflow impossible; if you choose another generator, explain why in `notes_for_writer`. Plan at most one figure with `preferred_generator: generate-concept-figure`; use another supported generator for any additional diagrams.
7. For each required figure, set explicit readability budgets: default to at most 4 total panels, at most 3 panels per row, at most 6 categories per panel, and at most 4 series per panel unless there is a grounded reason to relax them.
8. For each required figure, inspect the selected paper template or style files and note the practical column width / full-width geometry the writer will target. Then decide whether the figure should be placed at column width or full width in the final paper. Base that choice on the figure's density, aspect ratio, expected label size, and expected readability at the final paper size; do not plan to rescue a dense figure by shrinking it.
9. If a high-level overview figure is included, prefer planning it for early placement in the paper—ideally on page 1 or 2—unless the grounded story strongly argues otherwise.
10. In `figure_specs` or `notes_for_writer`, record a short layout rationale for each required figure so the writer can justify placement choices instead of guessing.
11. Encourage figure implementations that combine plotting and drawing when useful, for example matplotlib/seaborn for quantitative panels. For required overview-style `diagram` figures, prefer `generate-concept-figure`; use TikZ or other vector drawing tools for non-overview schematics or documented fallback implementations. Composite figures may stack or mix plots and diagrams when that improves reader comprehension.
12. Avoid headings or wording that imply chronological search order.
13. For thresholded comparisons across tasks or panels, keep one reader-facing meaning per figure. Do not reuse one label for different thresholds.
14. Keep internal pipeline terms out of `forbidden_phrases` exceptions and `notes_for_writer` recommendations unless they are explicitly marked as private-only context.
15. Make the strategy portable: structure it so the same prompt can work on unrelated future tasks without task-specific baked-in assumptions.
16. If no clean story exists, fail in the strategy outputs rather than bluffing.
17. In edit mode, the strategy must make an explicit framing decision about the prior paper: preserved, broadened, recentered, or rejected. Do not leave this implicit.
18. In edit mode, if newly staged programs or results materially alter the scope of the claimed method family, prefer updating the paper's center of gravity over preserving an outdated but denser prior narrative.
19. In edit mode, do not privilege the prior paper merely because it has richer ablations, more figures, or a cleaner existing draft. Those are convenience factors, not scientific grounds for keeping the same thesis.
20. A ready strategy must include a non-empty `supplementary_plan`: `purpose` must be a non-empty string and `planned_subsections` must contain at least one grounded entry. Do not guess later posthoc rankings during strategy generation. The writer receives the authoritative ranking separately and routes `appendix`-ranked analyses to Supplementary Information alongside this plan; `paper_strategy.json` is not retroactively modified. Never use the supplement to hide evidence essential to the central thesis. A failed strategy may use an empty object.

# Memory Protocol
- Continuously update `./memory.md` (create if missing; append-only).
- Also append framing decisions to:
  - `./global_memory/memory.md`
  - `./global_memory/memory.jsonl`
- Log why the chosen framing beat the rejected ones.
- Log any failure decision with the grounded reason.

# Constraints
- No user interaction.
- No final-paper drafting in this stage.
- No invented numbers, citations, experiments, or methods.
- If grounding is insufficient, fail clearly in the strategy outputs.

# Vector-First Figure Output Contract
- Plan quantitative plots so the writer can export both PDF and PNG from source at 300 DPI for the PNG.
- Require the writer to reference the PDF from LaTeX whenever a PDF exists.
- For raster-only output, require at least 2400 px wide for full-width placement or 1200 px wide for column-width placement.
- Never upscale an existing raster image; require regeneration from source at the required size.
