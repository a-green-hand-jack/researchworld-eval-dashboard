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
**研究任务：组成型（和为 1 的向量）预测输出的保形不确定性评价**
**问题与动机**
许多预测器的输出是一个“组成”：非负且和为 1 的向量，例如分类器的 softmax 概率、主题比例等。使用者不只关心点预测是否准确，也需要判断预测附带的不确定性估计是否可靠。

保形预测（conformal prediction）在可交换性假设下为预测集提供有限样本的覆盖率保证，并有多种实现和校准方式。这些方法在组成型输出上如何比较和评价，尚缺乏统一、可复现的做法。

**核心问题：如何评价保形预测方法在组成型输出上的可靠性？不同方法在哪些条件下更适用？**

请你作为独立研究者：

1. 梳理现有保形方法与评价方式的做法与局限，明确你要回答的具体研究问题与假设；
2. 设计并实现能回答你的研究问题的实验方案，说明选择依据，并量化结果的不确定性；
3. 可以使用自行生成的合成数据，也可以使用公开真实数据集（可用数据的类别见 `data.md`）；
4. 如能给出理论分析，给出推导并用实验核对；
5. 说明你的结论在什么条件下成立、哪些条件下不应外推。

以研究问题和实验证据为主线，自行决定具体路线。

**证据标准与关键约束**
结论必须有可复现的实验证据支持，并报告不确定性；可以得出支持、反驳或视条件而定的结论，负面或与预期不符的结果同样可以接受。

时间上限一周（含阅读、实现、实验、写作），以 CPU 为主、至多数个 GPU 小时，存储 < 10 GB，不需要付费 API（见 `resources.md`）；可用数据类别见 `data.md`；产出是一篇完整的研究论文及全部代码（见 `deliverable.md`）。

**起步文献清单**
以下文献是该领域较早的背景文献，仅作背景知识参考。取证日期：2026-10-27。

1. Vovk, Gammerman, Shafer. *Algorithmic Learning in a Random World.* Springer, 2005。说明：保形预测的专著，介绍该框架的理论基础与算法。
2. Papadopoulos, Proedrou, Vovk, Gammerman. *Inductive confidence machines for regression.* ECML 2002（无 arXiv 版）。说明：提出面向回归的归纳（inductive）置信机，将模型训练与置信度校准使用不同的数据。
3. Lei, G'Sell, Rinaldo, Tibshirani, Wasserman. *Distribution-Free Predictive Inference For Regression.* arXiv:1604.04173（2016-04-14）。https://arxiv.org/abs/1604.04173 。说明：为回归提出基于保形推断的无分布假设预测区间框架，对 full 与 split 两类保形变体做了理论和实证比较。
4. Barber, Candès, Ramdas, Tibshirani. *Predictive inference with the jackknife+.* arXiv:1905.02928（2019-05-08）。https://arxiv.org/abs/1905.02928 。说明：提出 jackknife+ 预测区间，利用留一预测构造区间，并给出覆盖率保证。
5. Tibshirani, Barber, Candès, Ramdas. *Conformal Prediction Under Covariate Shift.* arXiv:1904.06019（2019-04-12）。https://arxiv.org/abs/1904.06019 。说明：把保形预测推广到训练与测试协变量分布不同的情形，提出加权保形预测并给出覆盖率保证。
6. Angelopoulos, Bates. *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification.* arXiv:2107.07511（2021-07-15）。https://arxiv.org/abs/2107.07511 。说明：保形预测与无分布不确定性量化的入门综述，含示例。
7. Angelopoulos, Bates, Malik, Jordan. *Uncertainty Sets for Image Classifiers using Conformal Prediction.* arXiv:2009.14193（2020-09-29）。https://arxiv.org/abs/2009.14193 。说明：为图像分类器构造预测集的保形算法，在大规模图像分类数据集上评估。
8. Ding, Angelopoulos, Bates, Jordan, Tibshirani. *Class-Conditional Conformal Prediction with Many Classes.* arXiv:2306.09335（2023-06-15）。https://arxiv.org/abs/2306.09335 。说明：针对类别数很多、每类标注样本有限的分类问题，提出聚类保形预测（clustered conformal prediction）并在多个数据集上评估。
9. Jung, Noarov, Ramalingam, Roth. *Batch Multivalid Conformal Prediction.* arXiv:2209.15145（2022-09-30）。https://arxiv.org/abs/2209.15145 。说明：提出批量设定下的多重有效（multivalid）保形预测算法，并给出理论保证与实验评估。
10. Javanmardi, Stutz, Hüllermeier. *Conformalized Credal Set Predictors.* arXiv:2402.10723（2024-02-16）。https://arxiv.org/abs/2402.10723 。说明：提出用保形预测为分类任务预测 credal set（概率分布的集合）的方法。
11. Cresswell, Kumar, Sui, Belbahri. *Conformal Prediction Sets Can Cause Disparate Impact.* arXiv:2410.01888（2024-10-02）。https://arxiv.org/abs/2410.01888 。说明：通过人类被试实验研究保形预测集在人机协作决策中对不同受保护群体的影响。
12. Aitchison. *The statistical analysis of compositional data.* JRSS-B 44(2), 1982（无 arXiv 版）。说明：组成数据（和为常数的向量）统计分析的经典文献。

**数据与获取方式**
取证日期：2026-10-27。可以使用下列公开数据、其他公开数据，或完全使用自行生成的合成数据。

| 数据 | 获取 | 许可/账号 | 规模与格式 |
| --- | --- | --- | --- |
| CIFAR-10 | https://www.cs.toronto.edu/~kriz/cifar.html （重定向到 https://cave.cs.toronto.edu/kriz/cifar.html ，HTTP 200）；或 `torchvision.datasets.CIFAR10` | 页面未给出许可证，只要求使用时引用技术报告 Krizhevsky 2009（Learning Multiple Layers of Features from Tiny Images）；无需账号 | 60000 张 32x32 彩色图像、10 类，50000 训练 + 10000 测试；python 版压缩包 `cifar-10-python.tar.gz` 163 MB（170498071 字节，md5 `c58f30108f718f92721af3b95e74349a`）；文件自 2009-06-04 起未变 |
| 合成数据 | 自行生成 | 无 | 生成方式和规模由你设计。无外部依赖，无许可问题。 |
| 其他公开数据 | 可在 torchvision、scikit-learn、Hugging Face Datasets、OpenML 等常用数据集库检索 | 选用时请自行核实 | 输出为概率向量、比例或分布（和为 1 的非负向量）的公开数据集均可，包括分类数据集上分类器的输出概率。请在复现说明中记录所用数据的许可证和版本（需要账号或同意协议的数据，须说明获取方式）。 |

**资源与预算**
- 计算：以 CPU 为主即可（8 核以上、16 GB 内存为宜）。若需要自己训练预测器，可使用一张 GPU（至多数小时），也可使用现成的预训练模型或小型模型。
- 估算依据（粗估，未实测）：数据量级 10^3–10^4 个样本；实验阶段单次运行通常为秒级以内；整个研究的实验阶段总算力预计在数十个 CPU 小时量级，另需至多数个 GPU 小时准备预测器。实际用量取决于你设计的实验规模。
- 付费 API：不需要。
- 时间上限：一周（含阅读、实现、实验、写作）。
- 存储：< 10 GB。
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
    "evidence": "Task permits generated compositional responses and covariates; histories are empty; incumbent manifest reports correct=true and combined_score=0.6417212587320733. Manifest-named source entrypoint was unavailable, so no implementation defect is inferred. Alternatives were broad label-only classification, log-ratio-only evaluation, and a larger latent-deconvolution project. No experiment or literature search was run.",
    "idea_id": "cycle_01_boundary_stratified_geometry",
    "next_action": "Implement observed-response pooled and fixed-feature Mondrian regions with paired Euclidean, Hellinger, and additive-log-ratio scores; audit group reliability and separate full-simplex/face reference masses with uncertainty; keep latent probability membership diagnostic only.",
    "scope": "idea",
    "step": "idea",
    "summary": "Selected paired boundary-stratified conformal reliability and efficiency audit. gate=kept; trigger=none; reason=No evaluated discovery is available to distill.",
    "tags": [
      "unexecuted_hypothesis",
      "canonical_local_memory=ideas/01_boundary_stratified_conformal_evaluation_without_target_leakage/memory.md",
      "baseline_mechanism_unknown"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "evidence": "Hypothesis: marginal coverage and full-dimensional volume can conceal feature-group and boundary-reference weaknesses. Four implementation rubrics use concrete executable source snippets and one metric rubric defers to the canonical harness gate. One canonical idea-local memory target was used, with no alternate directory created.",
    "idea_id": "cycle_01_boundary_stratified_geometry",
    "next_action": "Execute the preregistered paired synthetic core through the documented candidate interface, validate rank and boundary cases, quantify seed-level and Monte Carlo uncertainty, and generate the complete paper and reproducibility package without selecting favorable results.",
    "rubrics": [
      {
        "id": "canonical_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "finite_sample_calibration_and_split_integrity",
        "type": "implementation"
      },
      {
        "id": "closed_simplex_geometry_comparison",
        "type": "implementation"
      },
      {
        "id": "observable_mondrian_and_estimand_separation",
        "type": "implementation"
      },
      {
        "id": "paired_uncertainty_and_boundary_reference_audit",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "final",
    "summary": "Wrote matching idea and rubric bundles; final status=idea_bundle_written, improvement unassessed. gate=kept; trigger=none; reason=Structural artifact completion supplies no evaluated scientific conclusion.",
    "tags": [
      "idea_bundle_written",
      "not_evaluated"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "cycle_01_boundary_stratified_geometry_attempt_01",
    "contract": "training-only ILR center/scale; calibration and membership owned by harness",
    "event": "candidate_preparation",
    "idea_id": "cycle_01_boundary_stratified_geometry",
    "plan": "cross-fitted training residuals and covariate/predicted-boundary-aware scale; no extra response fields",
    "program_id": "program_1",
    "validation": "static only; execution prohibited"
  },
  {
    "attempt_id": "cycle_01_boundary_stratified_geometry_attempt_01",
    "candidate_artifacts": "no evaluator artifacts; only program_1 created",
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle_01_boundary_stratified_geometry",
    "implemented": [
      "fixed covariate-only regime interactions",
      "training cross-validation of ridge penalties",
      "out-of-fold center residuals for scale fitting",
      "predicted-boundary scale features"
    ],
    "limitations": [
      "no calibration control or Mondrian thresholds",
      "fixed ILR region geometry",
      "no executed experiments or paper",
      "no measured score claim"
    ],
    "program_id": "program_1",
    "specification": "unchanged",
    "validation": "static comparison and candidate file listing only; no execution"
  },
  {
    "attempt_id": "cycle_01_boundary_stratified_geometry_attempt_01",
    "evidence": "combined_score=0.6283805225369655, correct=True; scientific acceptance passed; search metrics (data): {\"baseline_utility_gap\": 0.009982014298422937, \"combined_score\": 0.6283805225369655, \"control_check_pass_rate\": 1.0, \"correct\": true, \"iid_coverage_error\": 0.017371961805555548, \"mean_volume\": 0.34381343700267647, \"shift_coverage_error\": 0.09747178819444445}",
    "idea_id": "cycle_01_boundary_stratified_geometry",
    "metrics": {
      "baseline_utility_gap": 0.009982014298422937,
      "combined_score": 0.6283805225369655,
      "control_check_pass_rate": 1.0,
      "correct": true,
      "iid_coverage_error": 0.017371961805555548,
      "mean_volume": 0.34381343700267647,
      "shift_coverage_error": 0.09747178819444445
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T12:40:33.169960+00:00"
  },
  {
    "evidence": "Prior joint center/scale candidate combined_score=0.6283805225369655 versus incumbent 0.6417212587320733, correct=true and control_check_pass_rate=1.0. Prior preparation documents training-only ILR center/scale controls and evaluator-owned calibration. Manifest-named incumbent source unavailable here. Rejected unsupported Mondrian/geometry changes, another joint rewrite, and constant-only scaling; no task program or literature search run.",
    "idea_id": "cycle_02_shrunk_local_moment_scaling",
    "next_action": "Verify public contract; implement cached nested training-only residual moments, bounded Gaussian smoothing and neutral-inclusive held-out selection; preserve centers and response schemas; submit through canonical harness.",
    "scope": "idea",
    "step": "idea",
    "summary": "Selected scale-only smooth local-moment correction with shrinkage to incumbent and neutral control. gate=kept; trigger=none; reason=A single confounded lower aggregate score does not establish a mechanism-level scientific recommendation; this alternative remains untested.",
    "tags": [
      "unexecuted_hypothesis",
      "canonical_local_memory=ideas/02_training_only_shrunk_local_moment_scale_correction/memory.md",
      "mechanism_of_prior_regression_unknown"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "evidence": "Both required JSON files contain matching rubric arrays. Three implementation verifications specify 4, 5, and 7 executable snippets. Write-set review confirms the sole local memory target ideas/02_training_only_shrunk_local_moment_scale_correction/memory.md. No computational validation or task-program execution performed.",
    "idea_id": "cycle_02_shrunk_local_moment_scaling",
    "next_action": "Implement schema-preserving scale correction and cached nested training selection in the execution workspace; retain neutral and unchanged-center controls; use canonical harness assessment. Run independent uncertainty experiments and produce paper artifacts only when permitted.",
    "rubrics": [
      {
        "id": "canonical_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "training_only_standardized_moments",
        "type": "implementation"
      },
      {
        "id": "shrunk_local_variance_correction",
        "type": "implementation"
      },
      {
        "id": "held_out_selection_with_neutral_control",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "final",
    "summary": "Wrote idea and matching rubric bundles; status=idea_bundle_written, improvement unassessed. Hypothesis isolates shrink-to-incumbent local scale correction with centers and calibration fixed. gate=kept; trigger=none; reason=Static bundle completion supplies no new scientific performance or mechanism evidence.",
    "tags": [
      "idea_bundle_written",
      "not_evaluated",
      "single_canonical_memory_target"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "cycle_02_shrunk_local_moment_scaling_attempt_01",
    "details": "Cloned program_0; confirmed self-contained training-only ILR RPC contract. Implement scale-only correction; no execution or evaluation permitted.",
    "event": "implementation_started",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "cycle_02_shrunk_local_moment_scaling",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_shrunk_local_moment_scaling_attempt_01",
    "details": "Nested deterministic training-only cross-fitted standardized ILR moment tables; batched Gaussian smoothing with shrinkage; neutral-inclusive outer Gaussian-loss selection; same centers, base fits, response schema, and state transitions; common row-scalar respects scale bounds. Tiny-sample neutral fallback. Filesystem-only checks completed; runtime checks and official evaluation not run; no empirical scores claimed.",
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "cycle_02_shrunk_local_moment_scaling",
    "program_id": "program_1",
    "spec_unchanged": true
  },
  {
    "attempt_id": "cycle_02_shrunk_local_moment_scaling_attempt_01",
    "details": "Final bounds/documentation patch succeeded on standalone retry after a combined-shell apply_patch command-not-found failure. Candidate ready. No execution, tests, or evaluation performed.",
    "event": "final_ready",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "cycle_02_shrunk_local_moment_scaling",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_shrunk_local_moment_scaling_attempt_01",
    "evidence": "combined_score=0.6421289430111841, correct=True; scientific acceptance passed; search metrics (data): {\"baseline_utility_gap\": 0.013867224241875808, \"combined_score\": 0.6421289430111841, \"control_check_pass_rate\": 1.0, \"correct\": true, \"iid_coverage_error\": 0.018196614583333326, \"mean_volume\": 0.3331370883517795, \"shift_coverage_error\": 0.07864583333333335}",
    "idea_id": "cycle_02_shrunk_local_moment_scaling",
    "metrics": {
      "baseline_utility_gap": 0.013867224241875808,
      "combined_score": 0.6421289430111841,
      "control_check_pass_rate": 1.0,
      "correct": true,
      "iid_coverage_error": 0.018196614583333326,
      "mean_volume": 0.3331370883517795,
      "shift_coverage_error": 0.07864583333333335
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T12:48:00.979568+00:00"
  },
  {
    "evidence": "Historical cycle 02 passed: combined_score=0.6421289430111841, correct=true, control_check_pass_rate=1.0, iid_coverage_error=0.018196614583333326, shift_coverage_error=0.07864583333333335, mean_volume=0.3331370883517795; prior incumbent recorded as 0.6417212587320733. Named results-relative incumbent source exposes training-only X/Y and Gaussian-loss scale selection; no evaluator inspection. Rejected tail-model/coordinate-shape changes for attribution and Mondrian controls as unsupported. Required bundles statically reviewed with matching rubric content; 4/5/7/5 literal implementation snippets. Sole cycle-local memory target is ideas/03_training_only_conformal_rank_scale_selection/memory.md. No new scientific computation or computational validation.",
    "idea_id": "cycle_03_rank_calibrated_scale_selection",
    "next_action": "Implement cached swapped training-only pseudo-calibration/evaluation halves, exact finite ranks, stable ILR-box-volume selection, original-selector fallback, and unchanged RPC controls. Use the canonical harness, then independent paired uncertainty experiments and complete paper/reproduction artifacts where permitted. Keep simplex efficiency distinct and do not treat correlated pseudo-folds as independent replicates.",
    "rubrics": [
      {
        "id": "canonical_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "nested_training_pseudocalibration",
        "type": "implementation"
      },
      {
        "id": "finite_conformal_rank_selection",
        "type": "implementation"
      },
      {
        "id": "rank_calibrated_ilr_efficiency_objective",
        "type": "implementation"
      },
      {
        "id": "fixed_scale_family_and_incumbent_fallback",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "final",
    "summary": "Wrote Training-Only Conformal-Rank Scale Selection and matching rubric bundles; status=idea_bundle_written, new method unexecuted. Isolate the selector while preserving accepted centers and scale family. gate=updated; trigger=b; reason=The recorded accepted scale-only successor supplies the first evidence-backed promising method category, while its tiny unreplicated aggregate gain supports neither causal attribution nor a shift-coverage claim.",
    "tags": [
      "unexecuted_hypothesis",
      "single_canonical_memory_target",
      "selector_only_intervention",
      "historical_gain_unreplicated"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "evidence": "idea_bundle.json + target_rubrics.json",
    "idea_id": "cycle_03_rank_calibrated_scale_selection",
    "next_action": "run attempt",
    "scope": "idea",
    "step": "idea",
    "summary": "generated idea bundle (auto-healed by idea.sh)",
    "timestamp": "2026-11-17T12:53:43.300362+00:00"
  },
  {
    "attempt_id": "cycle_03_rank_calibrated_scale_selection_attempt_01",
    "event": "candidate_preparation",
    "files": [
      "program_1/src/program.py",
      "program_1/program_spec.toml"
    ],
    "idea_id": "cycle_03_rank_calibrated_scale_selection",
    "program_id": "program_1",
    "status": "cloned; implementation pending; execution prohibited"
  },
  {
    "attempt_id": "cycle_03_rank_calibrated_scale_selection_attempt_01",
    "changed_files": [
      "program_1/src/program.py"
    ],
    "contract": "program_1/program_spec.toml unchanged; entrypoint present; response schema preserved",
    "event": "candidate_ready",
    "idea_id": "cycle_03_rank_calibrated_scale_selection",
    "implementation": "cached nested training-only swapped-half rank selection; exact ranks; stable ILR log-mean-volume objective; original Gaussian fallback; connected runtime controls",
    "program_id": "program_1",
    "unfinished": [
      "official evaluation",
      "independent experiments and uncertainty estimates",
      "research manuscript and reproduction package"
    ],
    "validation": "static filesystem checks only; no code or tests executed; no evaluator artifacts or later candidates created"
  },
  {
    "attempt_id": "cycle_03_rank_calibrated_scale_selection_attempt_01",
    "evidence": "combined_score=0.6450635814905741, correct=True; scientific acceptance passed; search metrics (data): {\"baseline_utility_gap\": 0.016801862721265826, \"combined_score\": 0.6450635814905741, \"control_check_pass_rate\": 1.0, \"correct\": true, \"iid_coverage_error\": 0.018120659722222213, \"mean_volume\": 0.3222492359302662, \"shift_coverage_error\": 0.11304253472222224}",
    "idea_id": "cycle_03_rank_calibrated_scale_selection",
    "metrics": {
      "baseline_utility_gap": 0.016801862721265826,
      "combined_score": 0.6450635814905741,
      "control_check_pass_rate": 1.0,
      "correct": true,
      "iid_coverage_error": 0.018120659722222213,
      "mean_volume": 0.3222492359302662,
      "shift_coverage_error": 0.11304253472222224
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T12:57:27.030079+00:00"
  },
  {
    "evidence": "paper_data.json contains three evaluated variants and a completed eight-episode final evaluation; six logistic-normal/Dirichlet IID and shifted synthetic cases at K=3,8; scaled_ilr, unscaled_ilr, simplex_linf, bonferroni and feature controls. Final IID coverage error=0.013562011718750005, shift coverage error=0.13034261067708333. No reference/provenance files or figures exist. Earlier geometry/Mondrian ideas are not evidence of implementation.",
    "next_action": "Inspect selected-source selector and exposed benchmark contract; choose 6-10 narrow background queries with forbidden-content safeguards, not broad joint-topic or generic benchmarking searches.",
    "scope": "paper",
    "step": "idea",
    "summary": "Reference planning grounded in final evaluation rather than qualitative memory. gate=kept; trigger=none; reason=Planning citations adds no new evaluated methodological conclusion.",
    "timestamp": "2026-11-17T13:01:09.401112+00:00"
  },
  {
    "evidence": "JSON contract and query uniqueness validated; every query is mirrored in Markdown. Actual source confirms fixed Helmert ILR ridge centers, bounded local-moment scaling, and nested training-only rank-volume selection. Final mean simplex volume is larger than simplex_linf despite higher aggregate utility. Queries target split calibration, normalized scores, training-only selection, ILR geometry, actual synthetic distributions, simultaneous multivariate baselines, shift weighting background, conditional-validity limits, and inverse-transform measure. Rejected broad optimization/benchmarking and internal case-name queries as low precision; rejected joint conformal-composition discovery searches as prohibited-content risks and unused classification, geometry, and architecture comparisons as ungrounded. No bibliography/provenance/manuscript/claims artifacts were created.",
    "next_action": "Pass the two plan files to the later retrieval stage, enforcing forbidden-content safeguards and source verification; keep weighted conformal as literature-only and separate ILR selection volume from simplex evaluation volume.",
    "scope": "paper",
    "step": "final",
    "summary": "reference_query_plan_ready: wrote and validated nine grounded queries with matching Markdown memo; no retrieval performed. gate=updated; trigger=a; reason=Corrected the stale global conclusion that rank-based selection remains untested using completed final-run evidence, without claiming causal superiority.",
    "timestamp": "2026-11-17T13:04:11.184467+00:00"
  },
  {
    "evidence": "The helper appended proposed transitions to conclusions_history.jsonl before each atomic overwrite failed; these are unsuccessful proposals, not changes to conclusions.md. The preceding reference_query_plan_ready entry incorrectly reported gate=updated because the shell continued after the failed helper. The two required plan files and JSON validation succeeded; local and global memory appends succeeded.",
    "next_action": "Use the plan files as the current grounded handoff. Treat global conclusions calling rank-based selection untested as stale; do not retry conclusions updates in this stage.",
    "scope": "paper",
    "step": "conclusions_skip",
    "summary": "Correction to prior final log: gate=skipped; trigger=a; reason=All three permitted conclusions-update attempts failed with OSError Errno 30, Read-only file system, at conclusions.md.tmp. The existing conclusions paragraph was not updated; reference query outputs remain complete.",
    "timestamp": "2026-11-17T13:07:25.952758+00:00"
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
