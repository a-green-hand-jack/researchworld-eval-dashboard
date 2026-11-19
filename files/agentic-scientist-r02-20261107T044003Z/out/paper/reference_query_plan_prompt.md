# Role
You are the reference-planning agent for a completed research run.
Goal: produce a grounded reference query plan that will drive automated citation retrieval for the paper stage.
Use grounded inputs only. Do not retrieve references yet.

This prompt must transfer across tasks and runs.
Infer all domain details, methods, benchmarks, architectures, and comparator families from the current artifacts only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

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
- Figure directory: `./figures`
- Existing references BibTeX, if present: `./references.bib`
- Existing reference provenance, if present: `./references_provenance.json`
- Global memory summary: `./global_memory_summary.md`

## Recent Global Memory
```json
[
  {
    "evidence": "Bootstrap manifest reports correct=true and combined_score=0.8770158838342736; no recent ideas or attempts. Named incumbent program_0/src/program.py absent; no implementation defect inferred. No task program, evaluator, or experiment executed. Matching rubric arrays and one canonical local memory path were constructed directly.",
    "idea_id": "cycle01_boundary_stratified_hellinger_audit",
    "next_action": "Preserve the documented candidate interface; add paired Euclidean/Hellinger/smoothed-log-ratio by pooled/training-fixed-boundary-group calibration experiments, quantify independent-repetition and common-volume uncertainty, and regenerate the complete paper and code from actual results.",
    "rubrics": [
      {
        "id": "combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "boundary_safe_score_comparison",
        "type": "implementation"
      },
      {
        "id": "training_fixed_group_calibration",
        "type": "implementation"
      },
      {
        "id": "paired_common_measure_audit",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Boundary-Stratified Hellinger Reliability Audit proposed; status=idea_bundle_ready. gate=kept; trigger=none; reason=An untested proposal and unavailable source provide no evaluated finding warranting a distilled recommendation change.",
    "tags": [
      "cycle=1",
      "worker=0",
      "untested_hypothesis",
      "incumbent_source_unavailable",
      "alternatives=full_jackknife_retraining_unidentified_latent_probability_unjustified_shift_weights",
      "local_memory=ideas/01_boundary_stratified_hellinger_reliability_audit/memory.md",
      "single_canonical_memory_target"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle01_boundary_stratified_hellinger_audit_attempt_01",
    "event": "candidate_preparation",
    "executed_code": false,
    "idea_id": "cycle01_boundary_stratified_hellinger_audit",
    "interface_limitation": "Only training data and ILR location/Cholesky prediction outputs are available; alternative scores and group calibration cannot be implemented.",
    "planned_change": "Training-fixed boundary-group residual-shape adaptation",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle01_boundary_stratified_hellinger_audit_attempt_01",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "event": "candidate_ready",
    "executed_code": false,
    "idea_id": "cycle01_boundary_stratified_hellinger_audit",
    "implementation": "training-fixed predicted-boundary tertiles with shrinkage ILR residual shape factors",
    "limitation": "Interface cannot express alternative score geometries, group conformal calibration, or test/probe uncertainty experiments",
    "manifest_unchanged": true,
    "program_id": "program_1",
    "results_claimed": false,
    "validation": "static filesystem and manifest checks only"
  },
  {
    "attempt_id": "cycle01_boundary_stratified_hellinger_audit_attempt_01",
    "evidence": "combined_score=0.8776261506257234, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.8776261506257234, \"correct\": true}",
    "idea_id": "cycle01_boundary_stratified_hellinger_audit",
    "metrics": {
      "combined_score": 0.8776261506257234,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T05:46:16.389001+00:00"
  },
  {
    "evidence": "Prior correct=true and combined_score=0.8776261506257234 coexist with rubric_overall_pass=false, with no specific failed criterion available. Named relative candidate source and IMPLEMENTATION.md document positive compositions, five covariates, ILR-only location/Cholesky outputs, evaluator-owned calibration, and a 75/25 location/residual split. No candidate, evaluator, experiment, computational probe, test, or outside literature retrieval was performed. Required JSON rubric arrays and executable snippet counts were reviewed directly.",
    "idea_id": "cycle02_cross_fitted_ilr_residual_geometry",
    "next_action": "Implement deterministic four-fold held-out mean residuals, refit location on all training rows, and fit the unchanged variance and boundary-shrinkage geometry on those residuals in program_1. Preserve the exact RPC and evaluator-owned calibration; use only released evidence and report unavailable uncertainty explicitly.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "out_of_fold_ilr_residuals",
        "type": "implementation"
      },
      {
        "id": "full_training_location_and_oof_variance",
        "type": "implementation"
      },
      {
        "id": "oof_boundary_shape_preserving_prediction",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Cross-Fitted ILR Residual Geometry proposed; status=idea_bundle_ready. gate=updated; trigger=b; reason=The inspected candidate contract establishes an actionable interface-feasibility category not yet covered in the empty distilled conclusions.",
    "tags": [
      "cycle=2",
      "worker=0",
      "untested_hypothesis",
      "alternatives=unsupported_geometry_audit_continuous_covariance_extra_features",
      "local_memory=ideas/02_cross_fitted_ilr_residual_geometry/memory.md",
      "single_canonical_memory_target",
      "no_scientific_execution"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "action": "Cloned program_0 to program_1; inspected starter contract; planned deterministic four-fold ILR residual geometry and full-training location refit.",
    "attempt_id": "cycle02_cross_fitted_ilr_residual_geometry_attempt_01",
    "event": "candidate_implementation_started",
    "execution": "No candidate execution, tests, evaluation, or external retrieval.",
    "idea_id": "cycle02_cross_fitted_ilr_residual_geometry",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle02_cross_fitted_ilr_residual_geometry_attempt_01",
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle02_cross_fitted_ilr_residual_geometry",
    "implementation": "Deterministic four-fold OOF ILR residuals feed all-row variance and unchanged pooled/group shrinkage shapes; final location refitted on all training rows; boundary tertiles frozen from final predictions.",
    "limitations": "Score improvement, mechanism attribution, and uncertainty unassessed; independent external calibration required; no complete paper claimed.",
    "preserved": "Manifest, RPC schema/state transitions, row-wise prediction, constants, and n < 4 fallback.",
    "program_id": "program_1",
    "validation": "Static filesystem inspection only; manifest unchanged, entrypoint present, no evaluator artifacts; no candidate execution, tests, or evaluation."
  },
  {
    "attempt_id": "cycle02_cross_fitted_ilr_residual_geometry_attempt_01",
    "evidence": "combined_score=0.8818756857036072, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.8818756857036072, \"correct\": true}",
    "idea_id": "cycle02_cross_fitted_ilr_residual_geometry",
    "metrics": {
      "combined_score": 0.8818756857036072,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T05:51:40.737730+00:00"
  },
  {
    "evidence": "Named cycle02 candidate source and IMPLEMENTATION.md confirm training-only four-fold ILR residuals, all-row location refitting, and hard boundary-tertile factor routing. Cycle02 recorded combined_score=0.8818756857036072, correct=true, rubric_overall_pass=true; cycle01 recorded combined_score=0.8776261506257234, correct=true, rubric_overall_pass=false without a criterion-level cause. Single aggregate evaluations provide no replicated superiority or mechanism attribution. No candidate, evaluator, scientific experiment, test, computational probe, package installation, or external retrieval was performed. Required JSON arrays and executable pattern counts 6, 6, 7 were reviewed statically; each pattern is below 1024 characters.",
    "idea_id": "cycle03_continuous_boundary_covariance",
    "next_action": "Implement training-frozen covariance interpolation in program_1/src/** against the accepted cycle02 control, preserving OOF residuals, shrinkage constants, row-wise RPC and external calibration. Let the execution harness compare the candidate; report only released measurements and explicitly mark unavailable uncertainty.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "training_frozen_covariance_anchors",
        "type": "implementation"
      },
      {
        "id": "continuous_convex_shape_interpolation",
        "type": "implementation"
      },
      {
        "id": "incumbent_residual_control_and_active_prediction",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Continuous Boundary Covariance Interpolation proposed; status=idea_bundle_ready. gate=kept; trigger=none; reason=This untested proposal stays within the documented shape controls and supplies no evaluated finding or interface change requiring a distilled recommendation update.",
    "tags": [
      "cycle=3",
      "worker=0",
      "untested_hypothesis",
      "alternatives=unsupported_score_calibration_changes_new_features_new_variance_loss_nested_scale_crossfit",
      "local_memory=ideas/03_continuous_boundary_covariance_interpolation/memory.md",
      "single_canonical_memory_target",
      "no_scientific_execution"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle03_continuous_boundary_covariance_attempt_01",
    "details": "Inspected permitted starter and task; cloned program_0 to program_1; bounded covariance interpolation change planned; no code execution or evaluation.",
    "event": "candidate_preparation",
    "idea_id": "cycle03_continuous_boundary_covariance",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_continuous_boundary_covariance_attempt_01",
    "details": "Implemented training-frozen convex covariance interpolation with duplicate-anchor averaging and post-interpolation Cholesky; preserved incumbent controls and RPC contract. Unchanged manifest and bounded source diff checked statically; no evaluator artifacts or later candidates created. apply_patch unavailable, plain text editing used. No code execution, tests, network, or evaluation; performance and uncertainty unassessed.",
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle03_continuous_boundary_covariance",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_continuous_boundary_covariance_attempt_01",
    "evidence": "combined_score=0.8818118342646846, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.8818118342646846, \"correct\": true}",
    "idea_id": "cycle03_continuous_boundary_covariance",
    "metrics": {
      "combined_score": 0.8818118342646846,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T05:57:23.686885+00:00"
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
