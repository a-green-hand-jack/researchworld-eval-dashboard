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
    "evidence": "Supplied bootstrap manifest: correct=true, combined_score=0.8769659694273084. Histories have no events and conclusions contain no findings. The exact incumbent source path was unavailable. No experiments or evaluator executions were performed. Considered geometry-only comparisons and real-only latent audits; selected a synthetic target-separated design because both targets and exact binomial calibration-event checks are available. Outputs are idea_bundle.json and target_rubrics.json; local memory uses only ideas/01_noise_aware_latent_composition_coverage/memory.md.",
    "idea_id": "c01_noise_aware_latent_composition_bridge",
    "next_action": "Implement exact boundary/interior-center controls, corrected quantiles, and a multinomial L1 union-bound bridge; run paired independent-seed experiments with uncertainty and efficiency reporting; deliver a complete reproducible paper while preserving the documented candidate interface. Status: idea_ready_not_executed.",
    "rubrics": [
      {
        "id": "combined_score_improves",
        "type": "metric"
      },
      {
        "id": "finite_sample_compositional_quantile",
        "type": "implementation"
      },
      {
        "id": "multinomial_latent_coverage_bridge",
        "type": "implementation"
      },
      {
        "id": "separate_targets_and_exact_atom_check",
        "type": "implementation"
      },
      {
        "id": "paired_uncertainty_and_honest_efficiency",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Noise-Aware Latent Composition Coverage: test whether observed multinomial-composition coverage masks latent-probability undercoverage and whether a count-depth-aware L1 enlargement restores marginal validity. gate=kept; trigger=none; reason=No evaluated scientific finding or execution evidence yet warrants changing the empty distilled guidance; the new direction remains an explicitly untested hypothesis.",
    "tags": [
      "cycle_1",
      "worker_0",
      "untested_hypothesis",
      "canonical_memory_directory"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "c01_noise_aware_latent_composition_bridge_attempt_01",
    "details": "Cloned program_0. RPC supplies training covariates and residual norms only; no count depths, counts, probability targets, calibration scores, or region construction control. Preserve starter numerical estimator and document limitations. No code execution or evaluation.",
    "event": "interface_inspection",
    "idea_id": "c01_noise_aware_latent_composition_bridge",
    "program_id": "program_1",
    "status": "proposal_not_expressible"
  },
  {
    "attempt_id": "c01_noise_aware_latent_composition_bridge_attempt_01",
    "bridge_implemented": false,
    "contract_preserved": true,
    "details": "Required inputs and calibration/geometry control are absent. Source changes are documentation only. Specification comparison passed, entrypoint exists, no evaluator artifacts under candidate, and no later candidate created. Memory appended. apply_patch unavailable; used plain filesystem editing. No scientific or performance results claimed.",
    "event": "candidate_ready",
    "execution_performed": false,
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/IDEA_LIMITATIONS.md"
    ],
    "idea_id": "c01_noise_aware_latent_composition_bridge",
    "program_id": "program_1",
    "status": "unchanged_estimator_with_documented_limitation"
  },
  {
    "attempt_id": "c01_noise_aware_latent_composition_bridge_attempt_01",
    "evidence": "combined_score=0.8769659694273084, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.8769659694273084, \"constant_control_score\": 0.8323741513810385, \"control_pass_fraction\": 1.0, \"correct\": true, \"global_ilr_score_gap\": 0.044591818046269834, \"group_coverage_error\": 0.01461890461564688, \"marginal_coverage_error\": 0.011455620659722228, \"permuted_control_score\": 0.831412096052641, \"reference_mass\": 0.45302433437771267}",
    "idea_id": "c01_noise_aware_latent_composition_bridge",
    "metrics": {
      "combined_score": 0.8769659694273084,
      "constant_control_score": 0.8323741513810385,
      "control_pass_fraction": 1.0,
      "correct": true,
      "global_ilr_score_gap": 0.044591818046269834,
      "group_coverage_error": 0.01461890461564688,
      "marginal_coverage_error": 0.011455620659722228,
      "permuted_control_score": 0.831412096052641,
      "reference_mass": 0.45302433437771267
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-12T22:47:11.554776+00:00"
  },
  {
    "evidence": "Campaign memory documents training covariates and residual norms only, with query scale prediction and no count-depth, latent-target, calibration, or region-construction control. The previous documentation-only estimator retained correct=true and combined_score=0.8769659694273084; scientific acceptance passed, overall rubric acceptance and strict improvement did not. Rejected the unsupported bridge extension; selected bounded-memory NumPy quantile stumps over local-neighbor scales as an untested design preference. No new program or evaluator execution occurred. Canonical local memory is ideas/02_cross_fitted_tail_adaptive_residual_scaling/memory.md; no alternate cycle-2 local memory target was created or used. Required output rubric arrays match by construction.",
    "idea_id": "c02_cross_fitted_tail_adaptive_residual_scaling",
    "next_action": "Implement training-only quantile-stump scaling, disjoint-fold pinball selection with incumbent and constant candidates, and finite positive RPC predictions; preserve evaluator-owned calibration and all scientific deliverable requirements, then obtain actual permitted evaluation evidence. Status: idea_ready_not_executed.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "train_only_tail_quantile_learner",
        "type": "implementation"
      },
      {
        "id": "training_only_cross_fitted_selection",
        "type": "implementation"
      },
      {
        "id": "positive_shrunk_scale_rpc_integration",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Cross-Fitted Tail-Adaptive Residual Scaling: test training-only conditional log-norm quantile learning with cross-fitted incumbent shrinkage. gate=updated; trigger=b; reason=Recorded interface inspection establishes a new actionable interface-feasibility category, independent of untested scientific merits.",
    "tags": [
      "cycle_2",
      "worker_0",
      "untested_hypothesis",
      "canonical_memory_directory",
      "interface_feasible_proposal"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "c02_cross_fitted_tail_adaptive_residual_scaling_attempt_01",
    "date": "2026-11-12",
    "event": "implementation_started",
    "executed_tests": false,
    "idea_id": "c02_cross_fitted_tail_adaptive_residual_scaling",
    "interface": "training covariates and residual norms only",
    "program_id": "program_1"
  },
  {
    "attempt_id": "c02_cross_fitted_tail_adaptive_residual_scaling_attempt_01",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "contract_preserved": true,
    "date": "2026-11-12",
    "empirical_results": null,
    "evaluation_executed": false,
    "evaluator_artifacts_found": false,
    "event": "candidate_ready",
    "idea_id": "c02_cross_fitted_tail_adaptive_residual_scaling",
    "implementation": "NumPy quantile stumps, training-only three-fold selection over incumbent/constant/log blends, fitting-only quantile alignment, one-standard-error rule, positive scale prediction",
    "later_candidates_created": false,
    "paper_and_repeated_experiments": "incomplete",
    "program_id": "program_1",
    "static_entrypoint_check": true,
    "tests_executed": false
  },
  {
    "attempt_id": "c02_cross_fitted_tail_adaptive_residual_scaling_attempt_01",
    "evidence": "combined_score=0.8784929468848246, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.8784929468848246, \"constant_control_score\": 0.8323741513810385, \"control_pass_fraction\": 1.0, \"correct\": true, \"global_ilr_score_gap\": 0.04611879550378608, \"group_coverage_error\": 0.014335326454920713, \"marginal_coverage_error\": 0.009941948784722222, \"permuted_control_score\": 0.8303997490442233, \"reference_mass\": 0.449612299601237}",
    "idea_id": "c02_cross_fitted_tail_adaptive_residual_scaling",
    "metrics": {
      "combined_score": 0.8784929468848246,
      "constant_control_score": 0.8323741513810385,
      "control_pass_fraction": 1.0,
      "correct": true,
      "global_ilr_score_gap": 0.04611879550378608,
      "group_coverage_error": 0.014335326454920713,
      "marginal_coverage_error": 0.009941948784722222,
      "permuted_control_score": 0.8303997490442233,
      "reference_mass": 0.449612299601237
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-12T22:56:21.009791+00:00"
  },
  {
    "evidence": "Cycle 2 passed with correct=true, combined_score=0.8784929468848246 versus prior 0.8769659694273084, and control_pass_fraction=1.0; no repeated-run uncertainty or component attribution is available. The interface supplies only training covariates and residual norms. Rejected unsupported count/latent methods and simultaneous objective changes; chose bounded NumPy depth-two ensembles plus a depth-one ablation and incumbent fallback. Both JSON bundles were written with identical rubric arrays by construction. Sole cycle-local memory target: ideas/03_honest_interaction_quantile_ensemble/memory.md; no alternate cycle-3 or staging memory was created or used. No candidate, evaluator, benchmark, optimizer, installation, or experimental computation was run; no prohibited literature was accessed.",
    "idea_id": "c03_honest_interaction_quantile_ensemble",
    "next_action": "Implement honest quantile trees and fold-local incumbent blends, preserve scale RPC and evaluator-owned calibration, then obtain authorized validation and harness evidence; retain all uncertainty, full-paper, reproducibility, and honest-reporting obligations. Status: idea_ready_not_executed.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "honest_leaf_quantile_estimation",
        "type": "implementation"
      },
      {
        "id": "recursive_tail_interaction_ensemble",
        "type": "implementation"
      },
      {
        "id": "fold_local_shrinkage_and_positive_scale",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Honest Interaction Quantile Ensemble: test shallow non-additive residual-tail models with disjoint structure/leaf estimation and training-only incumbent shrinkage. gate=kept; trigger=none; reason=One non-ablated aggregate improvement does not establish a general tail-learning effect or justify a confident Do/Don't change; the new interaction hypothesis has no evaluation evidence, so existing interface and training-only guidance remains appropriate.",
    "tags": [
      "cycle_3",
      "worker_0",
      "untested_hypothesis",
      "canonical_memory_directory",
      "training_only_interaction_extension"
    ],
    "timestamp": "2026-11-12"
  },
  {
    "attempt_id": "c03_honest_interaction_quantile_ensemble_attempt_01",
    "event": "candidate_preparation",
    "execution": "not_permitted",
    "idea_id": "c03_honest_interaction_quantile_ensemble",
    "planned_files": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "program_id": "program_1",
    "status": "cloned"
  },
  {
    "attempt_id": "c03_honest_interaction_quantile_ensemble_attempt_01",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "empirical_improvement": "unknown",
    "evaluation": "not_run_harness_owned",
    "event": "candidate_ready",
    "executed": false,
    "idea_id": "c03_honest_interaction_quantile_ensemble",
    "implementation": {
      "blend_weights": [
        0.25,
        0.5,
        1.0
      ],
      "depths": [
        1,
        2
      ],
      "honest_ensembles": true,
      "nested_complete_incumbent": true,
      "rpc_unchanged": true,
      "training_only_selection": true,
      "trees_per_ensemble": 16
    },
    "program_id": "program_1",
    "research_deliverables": "incomplete_stage_restricted",
    "static_checks": {
      "entrypoint_exists": true,
      "prohibited_candidate_artifacts_found": false,
      "spec_unchanged": true
    },
    "status": "ready"
  },
  {
    "attempt_id": "c03_honest_interaction_quantile_ensemble_attempt_01",
    "evidence": "combined_score=None, correct=False; evaluation failed: exit=1; cause unavailable; search metrics (data): {\"combined_score\": null, \"correct\": false}",
    "idea_id": "c03_honest_interaction_quantile_ensemble",
    "metrics": {
      "combined_score": null,
      "correct": false
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-12T23:06:20.053737+00:00"
  },
  {
    "evidence": "paper_data.json is present (3,259,291 bytes); figures is empty; no existing references.bib or references_provenance.json. Global memory is contextual, not quantitative grounding.",
    "next_action": "Inspect structured evaluation evidence and successful implementation before choosing focused queries.",
    "scope": "paper",
    "step": "paper",
    "summary": "Started reference-query planning only; no retrieval or scientific execution. gate=kept; trigger=none; reason=Artifact inspection has not yet established a new scientific recommendation.",
    "timestamp": "2026-11-12T23:09:15.531258+00:00"
  },
  {
    "evidence": "paper_data.json contains two successful search evaluations and a completed six-seed final evaluation, unlike the incomplete qualitative memory summary. Final mean utility is 0.8772268474776957, global-ILR utility gap 0.04762325792650014, reference mass 0.4508402082655165. Evaluator confirms H/B/S logistic-normal cases in dimensions 3/10, raw-Linf and Bonferroni baselines, seed bootstrap intervals, and non-volume reference mass. Successful source implements training-only quantile stumps and ridge blends, but selected-component diagnostics are unavailable. Honest interaction ensemble failed and count-noise bridge was not implemented. No existing reference provenance to reuse. apply_patch executable/tool is unavailable after PATH and filesystem checks; use direct file creation for required new outputs.",
    "next_action": "Write eight targeted queries covering split/local scaling, quantile boosting, CQR distinction, ILR, logistic-normal context, multivariate baselines, covariate shift, and conditional-coverage limits; reject CIFAR, latent-count bridges, neural architecture, broad optimization, and direct composition-plus-conformal searches as unsupported or unnecessarily risky.",
    "scope": "paper",
    "step": "paper",
    "summary": "Grounded eight literature queries in successful residual-scale learning and actual six-case synthetic evaluation. gate=kept; trigger=none; reason=Reference planning adds no experimentally established scientific recommendation.",
    "timestamp": "2026-11-12T23:10:54.241521+00:00"
  },
  {
    "evidence": "reference_query_plan.json passes exact top-level and per-query schema checks, category checks, uniqueness/count checks, and query-to-memo consistency. references.bib, references_provenance.json, paper.tex, and claims_grounding.json remain absent. No network or reference-retrieval commands were executed. Local and global memory updates are append-only. Queries target actual split/local scaling, additive tail quantiles, ILR representation, synthetic logistic-normal context, implemented multivariate comparators, and coverage/shift limitations; unsupported dataset, latent-count, interaction-forest, and generic process alternatives were rejected explicitly.",
    "next_action": "Stop this planning stage. Future retrieval should use the eight queries only with forbidden-literature screening, immediate stop-and-record on accidental encounter, and source verification before citation. Next hypothesis remains setting-dependent local-scale usefulness, not component-level or universal superiority.",
    "scope": "paper",
    "step": "final",
    "summary": "reference_query_plan_ready: wrote matching Markdown and JSON plans with eight unique queries and validated the required contract. gate=kept; trigger=none; reason=Literature planning does not change existing scientific recommendations.",
    "timestamp": "2026-11-12T23:12:35.731554+00:00"
  },
  {
    "evidence": "final.qualification.status=completed, outcome=qualified, correct=true; six final seeds with matched H/B/S dimension-3/10 comparisons. No downstream_study or resolved edit inputs. Source-inspected full scale-selection procedure lacks selected-component diagnostics or matched final ridge-scale baseline. ICLR geometry is single-column 5.5in by 9in. The memory helper appended local memory then rejected the global_memory directory symlink; this append uses its resolved target and preserves prior content. apply_patch is unavailable, so new strategy outputs were created directly.",
    "next_action": "Check strategy JSON, registered supplementary source IDs, figure readability budgets and absence of forbidden stage outputs; then append final framing status.",
    "scope": "paper",
    "step": "paper",
    "summary": "Selected condition-dependent local residual scaling over latent-count, broad family, universal-superiority and search-chronology framings.",
    "timestamp": "2026-11-12T23:20:10.950250+00:00"
  },
  {
    "evidence": "Final qualification explicitly completed/qualified/true, independently read despite absent downstream_study. Strategy preserves negative homoscedastic findings, empirical-only shift findings, S3 reference-mass increase, absent component attribution, absent matched final ridge-scale comparator and unknown diagnostics. Planned three full-text-width figures with explicit readability budgets, 8.5 substantive ICLR body pages and seven supplementary sections. Registered numerical source IDs resolve; LLM process provenance has no fabricated result anchor. Exact JSON contract, memo question/thesis/title parity, figure budgets, qualification values and absence of paper.tex, claims_grounding.json and generated figures passed. No final-paper validation, scientific execution, network access or manuscript drafting performed. The earlier memory-helper symlink error is resolved by passing canonical global paths; prior entries remain append-only.",
    "next_action": "Stop framing. Downstream writer should implement the condition-first plan, verify permitted references and source linkage, generate the planned figures, and retain qualification facts and scientific limitations through review and audit. Component-specific benefit remains an untested hypothesis.",
    "scope": "paper",
    "step": "final",
    "summary": "paper_strategy_ready: wrote matching JSON and Markdown strategy; strategy-only checks passed. Condition-dependent local scaling beat unsupported latent-count, broad-family, universal-superiority and chronology framings.",
    "timestamp": "2026-11-12T23:21:09.183087+00:00"
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
Validation feedback from a previous draft is present.
Read these files before editing:
- `./strategy_validation_feedback.json`
- `./strategy_validation_feedback.md`
Fix every listed hard error first, keep grounded content stable when possible, and rerun validation after each repair pass until the hard errors are gone.
Treat figure readability findings as soft feedback unless a validator explicitly reports them as hard errors.
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
