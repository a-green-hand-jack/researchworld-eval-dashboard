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
**研究任务：表格模型上 SHAP 特征归因的重复运行可靠性**
**问题与动机**
SHAP 被广泛用于为高风险场景（信贷、医疗等）中的模型决策提供理由。在实际部署中，
SHAP 通常依赖随机近似算法估计，并受计算预算限制，因此同一个训练好的模型、同一个
输入实例，多次运行解释器可能得到不同的归因向量。

实践中常见的做法是对一个实例只运行一次解释器，并把所得特征归因作为该预测的依据。
这种做法在什么条件下足够可靠、在什么条件下不够可靠，目前缺少系统的实证证据。
我们希望你研究这一问题，并保留部署中真实的计算预算这一约束。

请自行确定并论证具体的研究问题与方法。研究需要回答：对一个训练好的表格模型，
单次运行所得的 SHAP 特征归因在多大程度上可以被当作该预测的可靠依据；这一判断需要依据
哪些度量和比较标准；结论在哪些条件下成立、在哪些条件下不成立。

**期望**
- 设计可复现的实验方法，在多个公开表格数据集和多种模型上系统验证，
  并把结论表述为可被他人检验的论断。
- 合格的研究给出明确论断及足以支持或反驳它的证据，并报告不确定性；结论可以是
  "足够可靠""视条件而定"或"不可靠"，只要证据充分，都是可接受的结果。
- 明确你的实验设置（数据、模型、计算预算）和统计处理方式，并说明选择理由。
- 如实报告负面或不确定的结果，并指出局限。

**约束**
计算以 CPU 为主，整个任务须在一周内完成，使用公开表格数据（详见 `data.md`、
`resources.md`），产出是一篇论文及全部代码（详见 `deliverable.md`）。

**起步文献（均为公开文献；你可以也应当自行检索更多）**
1. Lundberg, S. M., Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions.* NeurIPS 30.
   https://arxiv.org/abs/1705.07874 —— 说明：提出 SHAP 的加性特征归因框架，并给出包括 Kernel SHAP 在内的估计方法。
2. Krishna, S. et al. (2022). *The Disagreement Problem in Explainable Machine Learning: A Practitioner's Perspective.*
   https://arxiv.org/abs/2202.01602 —— 说明：关于多种事后解释方法在同一模型上给出不一致解释的研究，含对从业者的调研与实证比较。
3. Yuan, H. et al. (2022). *An empirical study of the effect of background data size on the stability of SHapley Additive exPlanations (SHAP) for deep learning models.*
   https://arxiv.org/abs/2204.11351 —— 说明：针对深度学习模型，实证考察估计 SHAP 时所用背景数据的规模与解释稳定性的关系。
4. Musco, C., Witter, R. T. (2024). *Provably Accurate Shapley Value Estimation via Leverage Score Sampling.*
   https://arxiv.org/abs/2410.01917 —— 说明：提出一种 Shapley 值估计算法，并给出估计误差的理论保证。
5. Chen, H., Janizek, J. D., Lundberg, S., Lee, S.-I. (2020). *True to the Model or True to the Data?*
   https://arxiv.org/abs/2006.16234 —— 说明：讨论 Shapley 值类解释在计算时采用不同期望方式所对应的不同含义。
6. Marx, C., Calmon, F., Ustun, B. (2020). *Predictive Multiplicity in Classification.*
   https://arxiv.org/abs/1909.06677 —— 说明：提出并度量“精度相近的多个分类模型对同一样本给出不同预测”的现象，并在多个真实数据集上评估。
7. Nogueira, S., Sechidis, K., Brown, G. (2018). *On the Stability of Feature Selection Algorithms.* JMLR 18(174).
   https://jmlr.org/papers/v18/17-514.html —— 说明：讨论特征选择算法的稳定性度量，给出一种稳定性度量并分析其性质。
8. Webber, W., Moffat, A., Zobel, J. (2010). *A Similarity Measure for Indefinite Rankings.* ACM TOIS 28(4).
   https://doi.org/10.1145/1852102.1852106 —— 说明：提出一种用于比较两个排序（允许长度不等、不完整）的相似度度量，并分析其性质。
9. Ding, F., Hardt, M., Miller, J., Schmidt, L. (2021). *Retiring Adult: New Datasets for Fair Machine Learning.* NeurIPS 34.
   https://arxiv.org/abs/2108.04884 —— 说明：提出基于美国人口普查局 ACS 数据构建的一组表格数据集及其工具包 folktables，用于机器学习研究。
10. Gorishniy, Y., Rubachev, I., Khrulkov, V., Babenko, A. (2021). *Revisiting Deep Learning Models for Tabular Data.* NeurIPS 34.
    https://arxiv.org/abs/2106.11959 —— 说明：系统比较表格数据上的深度学习模型，并提出 ResNet 类和 Transformer 类（FT-Transformer）两种神经网络架构。

**数据**
任务只需公开的表格分类数据集。以下为可用的公开表格分类数据集，标明主数据与可选数据；
你也可以自选其他公开数据集，并说明选择理由。

| 数据集 | 角色 | 获取方式 | 许可证 | 版本 / 规模 |
| --- | --- | --- | --- | --- |
| Statlog (German Credit Data) | 主 | https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data （UCI；DOI 10.24432/C5NC77）；无需账号 | CC BY 4.0（UCI 页面声明） | UCI 页面最后更新 2023-08-10；1,000 条 × 20 个属性；二分类 |
| ACS 收入预测（folktables） | 主 | `pip install folktables`（PyPI 0.0.12，2023-02-08 发布）；https://github.com/socialfoundations/folktables ；数据由 US Census ACS PUMS 下载（https://www.census.gov/programs-surveys/acs/microdata.html ）；无需账号 | folktables 代码为 MIT；ACS PUMS 为美国人口普查局公开数据，census.gov 页面未给出单独的许可证文字（2026-10-27 查阅），使用前请自行阅读该站条款 | 仓库默认分支最新提交 ebace19d（2024-05-15）；ACS PUMS 2024 年度文件的发布时间为 2025-12-04 前（已核实 2024 年 1 年期某州个人记录文件的 Last-Modified）；单个州单个年度的个人记录为数万到数十万条量级 |
| Pima Indians Diabetes | 可选 | OpenML `diabetes`（data id 37，version 1）：https://www.openml.org/d/37 ；亦可用 `sklearn.datasets.fetch_openml(data_id=37)`；无需账号 | OpenML 记录 licence = "Public" | 2014-04-06 上传；768 条 × 8 个数值特征 + 类别 |
| Give Me Some Credit | 可选 | OpenML id 46929（version 1）：https://www.openml.org/d/46929 ；无需账号。原始来源为 Kaggle 竞赛 "Give Me Some Credit"（2011，需 Kaggle 账号并接受规则；核实时 Kaggle 页面对自动请求返回 404，未能确认可用，因此只把 OpenML 作为获取方式） | OpenML 记录 licence = "Public" | 2025-04-30 上传（TabArena 整理版）；150,000 条 × 10 个特征 + 目标，含缺失值；二分类 |
| Arrhythmia | 可选 | https://archive.ics.uci.edu/dataset/5/arrhythmia （UCI；DOI 10.24432/C5BS32）；无需账号 | CC BY 4.0（UCI 页面声明） | UCI 页面最后更新 2024-02-05；452 条 × 279 个特征 |

数据体量为 MB 到数百 MB。表中记录数为原始记录数，各表是否去重或去缺失由使用者决定。
核实日期：2026-10-27。

**资源与预算**
- 计算：以 CPU 为主，预计总算力在约 24 CPU 小时量级（为估算，未实测）；
  可选使用至多一张 GPU，不是必需。
- 估算依据：数据量级为数百到数十万条记录、数个到数百个特征；模型为常见的表格模型，
  单次训练在 CPU 上为秒到分钟量级；解释器调用占主要开销，随被解释的实例数和所需精度增长。
  以上均为估算，未实测。请在论文中说明你的预算选择。
- 时间：整个任务（调研、实验、写作）上限一周。
- 存储：数据与结果合计 < 数 GB。
- 付费 API：不需要。
- 软件：公开开源的 Python 科学计算与机器学习库，具体自选；需要联网获取公开数据和文献。

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
    "evidence": "Prompt supplies an accepted incumbent combined_score=0.9064091496251445 and correct=true, with no recent attempts or failure evidence. Named incumbent source unavailable; interface and improvement headroom unknown. No computational probes, program/evaluator runs, installations or external literature access. Pairwise repeatability cannot expose shared bias; background changes confound the primary fixed-game question; learned abstention adds calibration assumptions. Selected independent within-call permutation-path confidence bounds plus exact low-dimensional real-data controls; useful coverage is not established.",
    "idea_id": "cycle01_single_call_shap_certificates",
    "next_action": "Inspect the documented candidate contract during execution, preserve incumbent evidence, implement real snippets under program_1/src/**, validate the simultaneous bound and exact controls, then run a cost-only pilot and freeze allocation. Final status: idea_bundle_written; no evaluation performed.",
    "rubrics": [
      {
        "id": "improve_validated_combined_score",
        "type": "metric"
      },
      {
        "id": "fixed_raw_feature_probability_game",
        "type": "implementation"
      },
      {
        "id": "single_call_simultaneous_certificate",
        "type": "implementation"
      },
      {
        "id": "independent_exact_game_reference",
        "type": "implementation"
      },
      {
        "id": "instance_clustered_reliability_uncertainty",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Fixed-budget single-call SHAP certificates and matching rubrics. gate=kept; trigger=none; reason=Untested design only, with no new measured evidence warranting a distilled recommendation.",
    "tags": [
      "cycle_1",
      "untested_hypothesis",
      "baseline_source_unavailable",
      "local_memory=ideas/01_fixed_budget_single_call_shap_certificates/memory.md",
      "single_canonical_local_memory",
      "gate=kept; trigger=none; reason=No new measured evidence"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle01_single_call_shap_certificates_attempt_01",
    "event": "candidate_preparation",
    "executed_project_code": false,
    "idea_id": "cycle01_single_call_shap_certificates",
    "limitations": [
      "raw preprocessing pipeline unavailable",
      "no certificate response field",
      "no empirical study outcomes"
    ],
    "program_id": "program_1",
    "status": "cloned"
  },
  {
    "attempt_id": "cycle01_single_call_shap_certificates_attempt_01",
    "certificate": "independent complete paths, simultaneous empirical Bernstein, internal only",
    "empirical_results_claimed": false,
    "evaluation_executed": false,
    "event": "candidate_implementation",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/reliability.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle01_single_call_shap_certificates",
    "program_id": "program_1",
    "spec_changed": false
  },
  {
    "attempt_id": "cycle01_single_call_shap_certificates_attempt_01",
    "entrypoint_exists": true,
    "evaluation_executed": false,
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/reliability.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle01_single_call_shap_certificates",
    "later_candidates_created": false,
    "program_id": "program_1",
    "response_schema_preserved": true,
    "spec_preserved": true,
    "status": "ready",
    "validation": "static filesystem inspection only"
  },
  {
    "attempt_id": "cycle01_single_call_shap_certificates_attempt_01",
    "evidence": "combined_score=0.9426474742464885, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.9426474742464885, \"control_pass_rate\": 1.0, \"correct\": true, \"efficiency_error\": 2.5279585452483204e-16, \"failed_fraction\": 0.0, \"reference_fidelity\": 0.9283093428081105, \"replay_error\": 0.0, \"signed_agreement\": 0.9204589843750001, \"top3_overlap\": 0.9425998263888888, \"wall_seconds\": 98.26029905304313}",
    "idea_id": "cycle01_single_call_shap_certificates",
    "metrics": {
      "combined_score": 0.9426474742464885,
      "control_pass_rate": 1.0,
      "correct": true,
      "efficiency_error": 2.5279585452483204e-16,
      "failed_fraction": 0.0,
      "reference_fidelity": 0.9283093428081105,
      "replay_error": 0.0,
      "signed_agreement": 0.9204589843750001,
      "top3_overlap": 0.9425998263888888,
      "wall_seconds": 98.26029905304313
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:05:02.464987+00:00"
  },
  {
    "evidence": "The named results-root candidate source supplies encoded original groups, a fixed B<=16 background, d<=20, shallow forest arrays and an attribution-only response; the absolute manifest source path was unavailable. Current aggregate combined_score=0.9426474742464885, correct=true, reference_fidelity=0.9283093428081105, signed_agreement=0.9204589843750001, top3_overlap=0.9425998263888888, failed_fraction=0. Overall rubric failure lacks criterion-level evidence and its cause remains unknown. Reverse-permutation pairing was considered but has no universal variance advantage. Selected exact signed-literal leaf-game contributions for forests, retaining logistic/affine paths, because the exposed tree structure admits same-game algebra with no sampled-coalition evaluations. No computational experiment, program/evaluator run, installation or external literature lookup was performed.",
    "idea_id": "cycle02_exact_leaf_game_shap",
    "next_action": "Implement the exact forest dispatch and real verification snippets under program_1/src/**; independently validate repeated splits, threshold boundaries, backgrounds and efficiency on small trees; then obtain the authorized official comparison. Report runtime or fidelity regressions and preserve research/deliverable requirements. Final status: idea_bundle_written; no evaluation performed.",
    "rubrics": [
      {
        "id": "improve_validated_combined_score",
        "type": "metric"
      },
      {
        "id": "same_game_leaf_literal_partition",
        "type": "implementation"
      },
      {
        "id": "exact_signed_leaf_beta_contributions",
        "type": "implementation"
      },
      {
        "id": "forest_exact_dispatch_preserves_contract",
        "type": "implementation"
      },
      {
        "id": "independent_small_tree_validation",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Exact leaf-game SHAP under fixed coalition budgets and matching rubrics. gate=kept; trigger=none; reason=The exact-tree direction is untested and available aggregate feedback neither localizes remaining error nor establishes a new empirical recommendation.",
    "tags": [
      "cycle_2",
      "untested_hypothesis",
      "exact_tree_control",
      "local_memory=ideas/02_exact_leaf_game_shap_under_fixed_coalition_budgets/memory.md",
      "single_canonical_local_memory",
      "gate=kept; trigger=none; reason=No localized new empirical evidence"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle02_exact_leaf_game_shap_attempt_01",
    "evidence": "Starter exposes scalar-encoded feature groups, finite empirical background and forest arrays; predictor uses float32 inputs and float64 threshold comparisons. No candidate execution.",
    "idea_id": "cycle02_exact_leaf_game_shap",
    "next_action": "Implement estimator, dispatch and unexecuted independent validation routines.",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "edit",
    "summary": "Cloned starter to program_1 and inspected forest contract; implementing exact leaf-game attribution.",
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle02_exact_leaf_game_shap_attempt_01",
    "evidence": "Changed src/forest.py, src/reliability.py, src/validate_forest.py and src/IMPLEMENTATION.md. cmp confirmed unchanged program_spec.toml and src/program.py; diff confirmed reliability.py only adds forest import/dispatch. Entrypoint/spec exist; no evaluator artifacts found. Validation routines written but not run; no candidate/project execution, network access or evaluation performed.",
    "idea_id": "cycle02_exact_leaf_game_shap",
    "next_action": "Stop for harness-owned official evaluation; improvement and runtime remain unmeasured, and the empirical paper deliverables remain incomplete.",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "final",
    "summary": "program_1 ready: exact forest leaf-game SHAP dispatched, nonforest estimation and RPC contract retained.",
    "tags": [
      "candidate_ready_for_harness",
      "static_verification_only",
      "validation_not_run"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle02_exact_leaf_game_shap_attempt_01",
    "evidence": "combined_score=0.9747236091254068, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.9747236091254068, \"control_pass_rate\": 1.0, \"correct\": true, \"efficiency_error\": 5.506740141518782e-16, \"failed_fraction\": 0.0, \"reference_fidelity\": 0.9684045114067584, \"replay_error\": 0.0, \"signed_agreement\": 0.9617513020833333, \"top3_overlap\": 0.9660373263888888, \"wall_seconds\": 156.28725960338488}",
    "idea_id": "cycle02_exact_leaf_game_shap",
    "metrics": {
      "combined_score": 0.9747236091254068,
      "control_pass_rate": 1.0,
      "correct": true,
      "efficiency_error": 5.506740141518782e-16,
      "failed_fraction": 0.0,
      "reference_fidelity": 0.9684045114067584,
      "replay_error": 0.0,
      "signed_agreement": 0.9617513020833333,
      "top3_overlap": 0.9660373263888888,
      "wall_seconds": 156.28725960338488
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:14:57.740695+00:00"
  },
  {
    "evidence": "The named cycle-02 candidate source supplies logistic coefficients/intercept, fixed B<=16 background rows and d<=20 original scalar groups, with an attribution-only RPC. Cycle 02 achieved combined_score=0.9747236091254068, correct=true, rubric_overall_pass=true, reference_fidelity=0.9684045114067584, signed_agreement=0.9617513020833333, top3_overlap=0.9660373263888888, failed_fraction=0 and wall_seconds=156.28725960338488. Aggregate metrics do not localize remaining error. Alternatives considered: regression-budget reallocation, reverse permutations, deterministic coalition designs and polynomial sigmoid surrogates. Selected probability-scale Fourier/Owen integration with exact inclusion-polynomial quadrature, division-free products, analytic frequency-tail bound, capped refinement and unchanged sampled fallback. No task/evaluator execution, computational probe, installation or literature search was performed; file reads and artifact edits only.",
    "idea_id": "cycle03_logistic_fourier_shap",
    "next_action": "Implement logistic integration and independent exhaustive small-game checks under program_1/src/**, preserve accepted forest/affine/RPC behavior, then obtain authorized validation and official incumbent/runtime comparison. Report numerical/runtime failures and unexecuted checks honestly; public-data paper/code/checklist deliverables remain required. Final status: idea_bundle_written; only one canonical cycle-03 local memory path used.",
    "rubrics": [
      {
        "id": "improve_validated_combined_score",
        "type": "metric"
      },
      {
        "id": "same_probability_game_fourier_kernel",
        "type": "implementation"
      },
      {
        "id": "exact_owen_integral_without_division",
        "type": "implementation"
      },
      {
        "id": "bounded_frequency_refinement_and_rejection",
        "type": "implementation"
      },
      {
        "id": "integrated_logistic_dispatch_preserves_contract",
        "type": "implementation"
      },
      {
        "id": "independent_probability_game_validation",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Probability-scale logistic SHAP by bounded Fourier quadrature and matching rubric arrays. gate=updated; trigger=b; reason=The newly accepted exact-forest candidate establishes a promising structure-aware baseline category absent from the empty conclusions, without identifying the family responsible for residual aggregate error.",
    "tags": [
      "cycle_3",
      "untested_logistic_quadrature",
      "probability_scale",
      "local_memory=ideas/03_probability_scale_logistic_shap_by_bounded_fourier_quadrature/memory.md",
      "single_canonical_local_memory",
      "gate=updated; trigger=b; reason=New structure-aware baseline category supported by accepted cycle-02 candidate"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle03_logistic_fourier_shap_attempt_01",
    "details": "Cloned program_0; inspected permitted candidate sources; implementing bounded probability-game logistic quadrature. No code execution or evaluation.",
    "event": "candidate_preparation",
    "idea_id": "cycle03_logistic_fourier_shap",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_logistic_fourier_shap_attempt_01",
    "details": "Bounded all-background probability-game Fourier/Owen quadrature and unchanged-budget/RNG fallback implemented. Independent validation source written, not run. No measured improvement claimed.",
    "event": "candidate_implementation",
    "files_changed": [
      "program_1/src/logistic_fourier.py",
      "program_1/src/reliability.py",
      "program_1/src/validate_logistic_fourier.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle03_logistic_fourier_shap",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_logistic_fourier_shap_attempt_01",
    "checks": "Filesystem-only: required candidate files exist; specification, RPC entrypoint and forest source byte-identical to starter; no forbidden evaluator artifacts under program_1; no later candidate created.",
    "event": "candidate_ready",
    "execution": "No candidate code, tests, evaluation, network or exploratory computation executed. Independent validation source is unrun; performance and research conclusions are unmeasured.",
    "files_changed": [
      "program_1/src/logistic_fourier.py",
      "program_1/src/reliability.py",
      "program_1/src/validate_logistic_fourier.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle03_logistic_fourier_shap",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_logistic_fourier_shap_attempt_01",
    "evidence": "combined_score=0.9977844815380661, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.9977844815380661, \"control_pass_rate\": 1.0, \"correct\": true, \"efficiency_error\": 7.166851590080133e-11, \"failed_fraction\": 0.0, \"reference_fidelity\": 0.9972306019225825, \"replay_error\": 0.0, \"signed_agreement\": 0.9988281250000001, \"top3_overlap\": 1.0, \"wall_seconds\": 159.5342314611189}",
    "idea_id": "cycle03_logistic_fourier_shap",
    "metrics": {
      "combined_score": 0.9977844815380661,
      "control_pass_rate": 1.0,
      "correct": true,
      "efficiency_error": 7.166851590080133e-11,
      "failed_fraction": 0.0,
      "reference_fidelity": 0.9972306019225825,
      "replay_error": 0.0,
      "signed_agreement": 0.9988281250000001,
      "top3_overlap": 1.0,
      "wall_seconds": 159.5342314611189
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:27:11.875612+00:00"
  },
  {
    "evidence": "paper_data.json contains three evaluated configurations and a completed final evaluation; figures directory is empty; no existing references.bib or references_provenance.json. Global memory is qualitative context, not quantitative evidence.",
    "next_action": "Inspect compact episode metadata and implemented estimators, then select 6\u201310 specific citation queries without any retrieval.",
    "scope": "paper",
    "step": "paper",
    "summary": "Reference planning started from local artifacts only. gate=kept; trigger=none; reason=Planning adds no new experimental conclusion.",
    "tags": [
      "reference_query_plan",
      "no_retrieval"
    ],
    "timestamp": "2026-11-07T03:39:47.782511+00:00"
  },
  {
    "evidence": "paper_data.json final evaluation contains three episodes and German/ACS logistic/forest cases; final provenance identifies ACSIncome-2024-RELSHIPP. Queries target Kernel SHAP, exact interventional trees, Owen integration, probability-scale logistic attribution, empirical Bernstein theory, selection stability, fixed-game semantics, leverage-score comparators, and folktables context. Exact permitted starter titles and narrow method anchors are better than generic optimization or broad SHAP rerun searches because they explain the implemented estimators and reduce prohibited-literature exposure. No references or network content retrieved; no forbidden encounter.",
    "next_action": "Validate JSON schema, query uniqueness, markdown mirroring, output restrictions, and append-only memory updates.",
    "scope": "paper",
    "step": "paper",
    "summary": "Selected nine grounded citation queries and wrote both reference plans. gate=kept; trigger=none; reason=Literature planning does not change experimental recommendations.",
    "tags": [
      "reference_query_plan",
      "nine_queries",
      "no_retrieval",
      "no_new_experiments"
    ],
    "timestamp": "2026-11-07T03:42:05.599822+00:00"
  },
  {
    "evidence": "Shell returned apply_patch: not found. The preceding memory event incorrectly described plan files as written; at that point only the planning decision and memory append succeeded. No references were retrieved.",
    "next_action": "Locate the supported patch entrypoint, create the two plan files, then validate them.",
    "scope": "paper",
    "step": "paper",
    "summary": "Correction: plan content selected, but initial file creation failed because apply_patch is absent from PATH. gate=kept; trigger=none; reason=No scientific conclusion changed.",
    "timestamp": "2026-11-07T03:42:21.896643+00:00"
  },
  {
    "evidence": "Created reference_query_plan.json and reference_query_plan.md through the Codex apply-patch entrypoint after recovering from the missing PATH helper. Validation passed: exact JSON contract, nine unique queries, all five categories, every query mirrored in Markdown, required memory files present, and no references.bib, references_provenance.json, paper.tex, or claims_grounding.json. No network/reference retrieval or candidate execution occurred. Generic searches were rejected in favor of implemented-method, exact-title, fixed-game, and benchmark-specific anchors; prohibited-literature safeguards and unsupported comparisons are explicit.",
    "next_action": "Task-specific stop: reference_query_plan_ready. Downstream retrieval should use the selected anchors only, verify primary-source relevance and permitted access, and skip any query that cannot be pursued safely.",
    "scope": "paper",
    "step": "final",
    "summary": "Reference-query planning complete: both files now created and validated. gate=kept; trigger=none; reason=No new experiment or change to scientific conclusions.",
    "tags": [
      "reference_query_plan_ready",
      "nine_queries",
      "no_retrieval",
      "validated"
    ],
    "timestamp": "2026-11-07T03:44:02.106294+00:00"
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
