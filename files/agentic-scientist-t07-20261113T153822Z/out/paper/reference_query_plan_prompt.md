# Role
You are the reference-planning agent for a completed research run.
Goal: produce a grounded reference query plan that will drive automated citation retrieval for the paper stage.
Use grounded inputs only. Do not retrieve references yet.

This prompt must transfer across tasks and runs.
Infer all domain details, methods, benchmarks, architectures, and comparator families from the current artifacts only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

# Task Context
## Goal
**研究任务：用少量题目预测 LLM 在完整基准上的得分**
**背景与动机**
评测一个大语言模型（LLM）在某个基准（benchmark）上的表现，需要让模型回答基准中的全部题目。
基准通常包含数百到数万道题；若在模型训练过程中对多个检查点、多个基准反复评测，或者要做大量
推理超参 / 提示格式的消融实验，评测成本会变得很高。

一个自然的想法是：只在基准的一个小子集上运行待测模型，再据此推断它在完整基准上的得分。我们手头
通常已有一批“源模型”（source models）在该基准每道题上的逐题结果（对/错）。这些历史评测记录能否
帮助我们选出值得保留的题目，并据待测模型在这些题目上的结果较准确地预测其完整基准得分、保持模型
之间的排序？

**研究问题**
在“已有若干源模型的逐题结果、待测模型只能运行少量题目”的设定下，研究如何

- 选择题目子集（题目数远小于基准总题数）；
- 由待测模型在子集上的结果预测其完整基准得分；

使得预测误差（如 MAE、RMSE）尽可能小、预测得分对模型的排序（如 Spearman、Kendall 相关）尽可能准确。
预测的好坏以待测模型的真实完整得分为参照来衡量。

请自行：梳理现有做法，提出并实现你认为合理的方案，设计公平的对照实验（与现有方法及简单做法比较），
并给出结论。结论可以是方案有效、无效或仅在一定条件下有效，须有实验证据支撑并报告不确定性。

**范围提示**
- 本任务提供的数据是对/错二值的逐题得分。
- 你需要自己决定方法、实验设置与评价协议；任务不预设任何特定方法。

**资源、数据与产出**
- 数据：公开的、对/错二值的逐题得分矩阵（模型 × 题目），无需账号，详见 `data.md`。
- 资源：仅 CPU，时间上限一周，详见 `resources.md`。
- 产出：一篇完整的研究论文及可复现的代码，具体要求见 `deliverable.md`。

**起步文献（均早于 2026-05-25；仅供起步，可自行扩展检索）**
1. Vivek, Ethayarajh, Yang, Kiela. *Anchor Points: Benchmarking Models with Much Fewer Examples.* EACL 2024. arXiv:2309.08638。https://arxiv.org/abs/2309.08638
   说明：用模型对各题的响应向量聚类，选出代表性题目（锚点），并用加权平均估计得分。
2. Maia Polo, Weber, Choshen, Sun, Xu, Yurochkin. *tinyBenchmarks: evaluating LLMs with fewer examples.* ICML 2024. arXiv:2402.14992。https://arxiv.org/abs/2402.14992
   说明：结合聚类锚点与项目反应理论（IRT）预测完整得分；发布了精简版基准与评估工具。
3. Kipnis, Voudouris, Schulze Buschoff, Schulz. *metabench -- A Sparse Benchmark of Reasoning and Knowledge in LLMs.* ICLR 2025. arXiv:2407.12844。https://arxiv.org/abs/2407.12844
   说明：基于 IRT 的信息量选题，并用广义可加模型预测。
4. Pacchiardi, Cheke, Hernández-Orallo. *100 instances is all you need: predicting the success of a new LLM on unseen data by testing on a few instances.* arXiv:2409.03563 (2024)。https://arxiv.org/abs/2409.03563
   说明：用新模型在少量参考实例上的结果训练评估器，预测它在其余实例上的表现；实验使用 HELM-Lite 等数据。
5. Li, Ma, Ballesteros, Benajiba, Horwood. *Active Evaluation Acquisition for Efficient LLM Benchmarking.* ICML 2025. arXiv:2410.05952。https://arxiv.org/abs/2410.05952
   说明：用学习得到的策略自适应地选题，并预测其余题目的结果。
6. Zhang, Dorner, Hardt. *How Benchmark Prediction from Fewer Data Misses the Mark.* NeurIPS 2025. arXiv:2506.07673。https://arxiv.org/abs/2506.07673
   说明：在 19 个基准上比较 11 种基准预测方法；其代码仓库发布了逐题得分数据和各方法的实现（见 data.md）。
7. Balkır, Pernthaller, Basaldella, Hernández-Orallo, Collier. *Confident Rankings with Fewer Items: Adaptive LLM Evaluation with Continuous Scores.* arXiv:2601.13885 (2026-01-20)。https://arxiv.org/abs/2601.13885
   说明：把基于 IRT 的自适应评测扩展到连续有界得分（如 ROUGE、BLEU、LLM 评审分），并给出带自适应停止准则的排序方法。
8. Wang 等. *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark.* arXiv:2406.01574 (2024-06-03)。https://arxiv.org/abs/2406.01574
   说明：MMLU 的增强版多任务语言理解基准，题目更偏推理、选项增至十个；是 Open LLM Leaderboard v2 的组成部分。
9. Ghosh 等. *ONEBench to Test Them All: Sample-Level Benchmarking Over Open-Ended Capabilities.* arXiv:2412.06745 (2024-12-09)。https://arxiv.org/abs/2412.06745
   说明：把多个评测数据集汇总成统一的、持续扩充的样本池，并研究在各模型只评测了部分样本时如何聚合稀疏测量、得到模型得分与排序。
10. Liang 等. *Holistic Evaluation of Language Models (HELM).* TMLR 2023, arXiv:2211.09110。https://arxiv.org/abs/2211.09110
    说明：对语言模型做多场景、多指标整体评测的框架，并对 30 个模型做了大规模评测。
11. Fourrier, Habib, Lozovskaya, Szafer, Wolf. *Open LLM Leaderboard v2.* Hugging Face, 2024。https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
    说明：Hugging Face 的公开排行榜，在 IFEval、BBH、MATH Lvl 5、GPQA、MuSR、MMLU-Pro 等基准上评测并公布大量开源模型的结果。

**数据与获取方式（取证日期 2026-10-27）**
**主要数据：逐题（模型 × 题目）二值得分矩阵**
- 来源：Zhang, Dorner, Hardt 的 benchmark-prediction 代码仓库，目录 `data/scores/`，由 Open LLM Leaderboard 与 HELM 整理而成的 `.jbl` 文件（joblib 序列化文件，Python 读取）。
  - 仓库：https://github.com/socialfoundations/benchmark-prediction ，使用固定 commit `55faff496947789f94e6b5908c77cbc3e84f81ad`（2025-08-30），不要使用分支最新版（例：`git clone` 后 `git checkout 55faff496947789f94e6b5908c77cbc3e84f81ad`，或直接下载 `https://raw.githubusercontent.com/socialfoundations/benchmark-prediction/55faff496947789f94e6b5908c77cbc3e84f81ad/data/scores/<文件名>`）。
  - 许可证：MIT，覆盖仓库代码和其中打包的 `.jbl` 文件（版权 Guanhua Zhang 与 Moritz Hardt）；`.jbl` 的上游数据来自 Open LLM Leaderboard 与 HELM（见下）。
  - 文件清单（文件大小为 GitHub API 所报告）：`arc_challenge.jbl`（约 2.0 MB）、`bbh.jbl`（约 20.6 MB）、`gpqa.jbl`（约 4.3 MB）、`ifeval.jbl`（约 0.24 MB）、`mmlu_pro.jbl`（约 43 MB）、`musr.jbl`（约 2.7 MB）、`openllm_math.jbl`（约 3.2 MB）；HELM 侧：`commonsense.jbl`、`gsm.jbl`、`legalbench.jbl`、`math.jbl`、`med_qa.jbl`、`mmlu.jbl`（均小于 1.3 MB）。Open LLM Leaderboard 侧各基准有对应的 `*_models.jbl` 模型列表。另有 `data/openllm_model_list.txt`、`data/helm_model_list.txt`。
  - 规模：Open LLM Leaderboard 侧四百余个模型（`data/openllm_model_list.txt` 445 行）、HELM 侧约 80 个模型（`data/helm_model_list.txt` 82 行）；各基准实际有结果的模型数不同，请自行核对。
  - 无需账号；`git clone` 或网页下载即可。上述 13 个文件合计约 80 MB。
  - 该仓库另附 `benchpred` Python 包（该仓库对应论文所比较方法的实现）和 `main.py`，用法见仓库 README；使用前请自行检查其实现。
- 原始数据出处（可选）：
  - Open LLM Leaderboard v2：https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard （HTTP 200；持续更新的在线页面，无固定快照）；其汇总结果数据集 https://huggingface.co/datasets/open-llm-leaderboard/contents （HTTP 200，非 gated，数据卡未声明许可，仅含汇总分数，不是逐题矩阵）；各模型逐题明细为 `open-llm-leaderboard/<org>__<model>-details`，抽查的 `open-llm-leaderboard/Qwen__Qwen2.5-7B-details` 为 gated（需登录并同意条款）。
  - HELM：https://github.com/stanford-crfm/helm （Apache-2.0，HTTP 200）。

**说明**
- `.jbl` 文件是模型 × 题目的得分矩阵；如需题目文本，可从上面列出的原始数据出处获取（部分逐题明细需登录）。

**资源与预算**
- 硬件：仅 CPU 即可（建议 16+ 核、32 GB 内存；无需 GPU）。
- 时间上限：一周（含阅读、实现、实验与写作）。
- 存储：约 1 GB 磁盘足够（数据约 80 MB，另含运行环境与结果）。
- 估算依据：数据为几百个模型 × 数千至上万道题的二值矩阵（合计约 80 MB）；在 CPU 上处理一个基准的单次运行通常在秒到分钟量级；整个任务的总计算量估计为数十 CPU 小时量级，可并行。以上均为估计，未实测。
- 不需要调用任何付费 API，也不需要重新评测 LLM；若自行加入需要运行模型的实验，请在预算内说明。

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

**Extra data in this environment (added by the harness, not part of the task)**

Read-only data prepared for this task is mounted at /extra/t07-open-llm-leaderboard-columns; each directory has a README.md that says what is in it.

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
    "evidence": "Mounted README documents repeated identities/details repositories, explicit Base Model metadata, verified columns, and no provided groups or scores. Bootstrap manifest reports correct=true and combined_score=0.9414127869558047; named candidate source path was unavailable. No new experiment or score. Considered richer IRT-only prediction, pure random sampling, and protocol-only work; selected a bounded source-prediction plus uniform-residual-audit intervention with conditional unbiasedness only at the raw full-correction endpoint.",
    "idea_id": "cycle_01_anchor_audit_residual",
    "next_action": "Inspect permitted candidate/interface files; implement an equal-budget pilot and then nested lineage-held-out comparisons with group-level uncertainty, complete reproducible code, and an artifact-generated paper. Stop reason: idea_ready_untested. Sole local target: ideas/01_lineage_held_out_anchor_audit_residual_estimation/memory.md.",
    "rubrics": [
      {
        "id": "combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "source_only_anchor_predictor",
        "type": "implementation"
      },
      {
        "id": "uniform_complement_residual_audit",
        "type": "implementation"
      },
      {
        "id": "lineage_disjoint_nested_validation",
        "type": "implementation"
      },
      {
        "id": "paired_group_level_evidence",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Lineage-Held-Out Anchor-Audit Residual Estimation. gate=updated; trigger=b; reason=Supplied identity and explicit ancestry metadata enable an auditable grouped stress-test category absent from the empty conclusions.",
    "tags": [
      "cycle_1",
      "untested_hypothesis",
      "no_experiments",
      "canonical_local_memory",
      "worker_0"
    ],
    "timestamp": "2026-11-13"
  },
  {
    "attempt_id": "cycle_01_anchor_audit_residual_attempt_01",
    "event": "interface_and_clone",
    "idea_id": "cycle_01_anchor_audit_residual",
    "limitations": [
      "opaque_source_groups_only",
      "no_target_full_scores_or_groups",
      "no_execution_or_evaluation"
    ],
    "plan": "fixed anchors followed by uniform complement audit; source-group validation",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_01_anchor_audit_residual_attempt_01",
    "event": "implementation",
    "evidence_scope": "no measured results; internal source-validation bootstrap is post-selection, not target evidence",
    "execution": "prohibited_not_run",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle_01_anchor_audit_residual",
    "mechanism": "source-group-selected low-rank D-optimal anchors and uniform-complement audit with weights 0/0.5/1",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_01_anchor_audit_residual_attempt_01",
    "candidate_evaluation_artifacts": false,
    "entrypoint_exists": true,
    "event": "final_handoff",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle_01_anchor_audit_residual",
    "later_candidate_created": false,
    "limitations_documented": true,
    "program_id": "program_1",
    "spec_unchanged": true,
    "status": "ready_for_harness_evaluation",
    "validation": "filesystem_only_no_execution"
  },
  {
    "attempt_id": "cycle_01_anchor_audit_residual_attempt_01",
    "evidence": "combined_score=0.9444775970444405, correct=False; scientific acceptance failed; cause unavailable; correct=false alone does not establish a protocol or implementation defect; search metrics (data): {\"anchor_mae\": 0.24719956291422063, \"combined_score\": 0.9444775970444405, \"constant_mae\": 0.2100909190340938, \"control_failure_rate\": 0.0, \"copy_mae\": 0.1778997763664952, \"correct\": false, \"delta_anchor_ci_high\": 1.0, \"delta_anchor_ci_low\": -1.0, \"delta_anchor_mae\": -0.19167715995866108, \"irt_mae\": 0.04121063683083198, \"kendall_tau_b\": 0.6472179218700796, \"mae\": 0.05552240295555956, \"missing_episode_rate\": 0.0, \"no_calibration_mae\": 0.11230918829448545, \"no_diversity_mae\": 0.060846081878834724, \"permuted_mae\": 0.1294150243149829, \"reset_mae\": 0.04647316766485056, \"reset_max_abs_error\": 0.0, \"rmse\": 0.06878752313066207, \"source_mean_mae\": 0.12786232844772225, \"spearman\": 0.8092089396608806, \"uniform_mae\": 0.09894661693226534}",
    "idea_id": "cycle_01_anchor_audit_residual",
    "metrics": {
      "anchor_mae": 0.24719956291422063,
      "combined_score": 0.9444775970444405,
      "constant_mae": 0.2100909190340938,
      "control_failure_rate": 0.0,
      "copy_mae": 0.1778997763664952,
      "correct": false,
      "delta_anchor_ci_high": 1.0,
      "delta_anchor_ci_low": -1.0,
      "delta_anchor_mae": -0.19167715995866108,
      "irt_mae": 0.04121063683083198,
      "kendall_tau_b": 0.6472179218700796,
      "mae": 0.05552240295555956,
      "missing_episode_rate": 0.0,
      "no_calibration_mae": 0.11230918829448545,
      "no_diversity_mae": 0.060846081878834724,
      "permuted_mae": 0.1294150243149829,
      "reset_mae": 0.04647316766485056,
      "reset_max_abs_error": 0.0,
      "rmse": 0.06878752313066207,
      "source_mean_mae": 0.12786232844772225,
      "spearman": 0.8092089396608806,
      "uniform_mae": 0.09894661693226534
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-13T17:17:14.928338+00:00"
  },
  {
    "evidence": "Historical interface memory documents opaque source_groups, nested 8/16/32 prefixes, and no target full scores or target groups. Historical candidate MAE=0.05552240295555956 versus reported IRT MAE=0.04121063683083198; calibration/diversity ablations were numerically worse. Historical combined_score=0.9444775970444405 with correct=false did not establish acceptance or its failure cause; accepted bootstrap remains combined_score=0.9414127869558047 with correct=true. Considered another residual audit, richer latent reconstruction, protocol-only changes, and direct score-risk acquisition; selected the last as a bounded observable-only mechanism admitting a same-predictor D-optimal ablation. No new computation, measurement, or forbidden literature access.",
    "idea_id": "cycle_02_score_targeted_covariance",
    "next_action": "Inspect candidate-owned documented files, implement selected-column score-covariance acquisition and the group-balanced conditional score predictor, and use group-disjoint source pseudo-targets for calibration and matched-budget controls only if execution is permitted. Keep diagnostics internal and original paper/target-evidence requirements intact; report inaccessible work as incomplete. Stop reason: idea_ready_untested. Sole cycle-local target: ideas/02_score_targeted_covariance_design_with_group_held_out_calibration/memory.md.",
    "rubrics": [
      {
        "id": "combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "score_targeted_prefix_design",
        "type": "implementation"
      },
      {
        "id": "grouped_conditional_score_predictor",
        "type": "implementation"
      },
      {
        "id": "source_only_nested_calibration",
        "type": "implementation"
      },
      {
        "id": "paired_source_group_controls",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Score-Targeted Covariance Design with Group-Held-Out Calibration: direct full-score conditional-variance acquisition, equal source-group training weights, and source-only nested calibration. gate=updated; trigger=d; reason=Qualify the ancestry-stress-test recommendation to distinguish offline metadata from the documented opaque-source-group-only candidate interface, and distinguish recorded aggregate underperformance against IRT from an unknown acceptance-failure cause.",
    "tags": [
      "cycle_2",
      "worker_0",
      "untested_hypothesis",
      "no_experiments",
      "source_groups_not_lineage",
      "canonical_local_memory"
    ],
    "timestamp": "2026-11-13"
  },
  {
    "attempt_id": "cycle_02_score_targeted_covariance_attempt_01",
    "event": "implementation_started",
    "execution": "Not permitted; no tests or experiments run.",
    "idea_id": "cycle_02_score_targeted_covariance",
    "observations": "Starter supports grouped source-only fitting and nested 8/16/32 prefixes; no target labels or identities.",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_score_targeted_covariance_attempt_01",
    "event": "implementation_written",
    "files": [
      "program_1/src/program.py",
      "program_1/src/score_design.py",
      "program_1/src/METHOD.md"
    ],
    "idea_id": "cycle_02_score_targeted_covariance",
    "limitations": [
      "No code execution permitted",
      "No target labels or target identities",
      "Local Rasch/anchor controls are not official baseline reproductions",
      "Paper and empirical claims not completed"
    ],
    "method": "Group-balanced score covariance design; source-only grouped calibration; internal untouched-source controls.",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_score_targeted_covariance_attempt_01",
    "candidate_file_listing": "program_spec.toml; src/program.py; src/score_design.py; src/METHOD.md",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/score_design.py",
      "program_1/src/METHOD.md"
    ],
    "entrypoint_exists": true,
    "evaluator_artifacts_created": false,
    "event": "candidate_ready",
    "idea_id": "cycle_02_score_targeted_covariance",
    "later_candidates_created": false,
    "limitations": "No measured accuracy or runtime; local controls are not official baseline reproductions; no target evidence or research paper completed.",
    "program_id": "program_1",
    "spec_unchanged": true,
    "validation": "Filesystem listing, byte comparison of specs, and static reasoning only; no execution/tests/evaluation."
  },
  {
    "attempt_id": "cycle_02_score_targeted_covariance_attempt_01",
    "evidence": "combined_score=0.9649669664663327, correct=False; scientific acceptance failed; cause unavailable; correct=false alone does not establish a protocol or implementation defect; search metrics (data): {\"anchor_mae\": 0.24719956291422063, \"combined_score\": 0.9649669664663327, \"constant_mae\": 0.19445070209615578, \"control_failure_rate\": 0.0, \"copy_mae\": 0.19343264686385855, \"correct\": false, \"delta_anchor_ci_high\": 1.0, \"delta_anchor_ci_low\": -1.0, \"delta_anchor_mae\": -0.2121665293805533, \"irt_mae\": 0.04121063683083198, \"kendall_tau_b\": 0.720911927988862, \"mae\": 0.0350330335336673, \"missing_episode_rate\": 0.0, \"no_calibration_mae\": 0.03464729153264736, \"no_diversity_mae\": 0.05351526989144261, \"permuted_mae\": 0.12148785819970097, \"reset_mae\": 0.03602846597539919, \"reset_max_abs_error\": 0.0, \"rmse\": 0.04484693916622435, \"source_mean_mae\": 0.12786232844772225, \"spearman\": 0.8644226555576705, \"uniform_mae\": 0.09894661693226534}",
    "idea_id": "cycle_02_score_targeted_covariance",
    "metrics": {
      "anchor_mae": 0.24719956291422063,
      "combined_score": 0.9649669664663327,
      "constant_mae": 0.19445070209615578,
      "control_failure_rate": 0.0,
      "copy_mae": 0.19343264686385855,
      "correct": false,
      "delta_anchor_ci_high": 1.0,
      "delta_anchor_ci_low": -1.0,
      "delta_anchor_mae": -0.2121665293805533,
      "irt_mae": 0.04121063683083198,
      "kendall_tau_b": 0.720911927988862,
      "mae": 0.0350330335336673,
      "missing_episode_rate": 0.0,
      "no_calibration_mae": 0.03464729153264736,
      "no_diversity_mae": 0.05351526989144261,
      "permuted_mae": 0.12148785819970097,
      "reset_mae": 0.03602846597539919,
      "reset_max_abs_error": 0.0,
      "rmse": 0.04484693916622435,
      "source_mean_mae": 0.12786232844772225,
      "spearman": 0.8644226555576705,
      "uniform_mae": 0.09894661693226534
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-13T17:35:03.901393+00:00"
  },
  {
    "evidence": "Historical cycle-2 MAE 0.0350330335336673 versus IRT 0.04121063683083198; no-calibration 0.03464729153264736 and no-diversity 0.05351526989144261. Acceptance was not established and its cause remains unknown. No new experiment. Considered repeated auditing, adaptive posterior acquisition, and calibration-only changes; selected a matched-prefix estimator intervention requiring no new observations. Hypothesis: group-balanced Rasch-shrunk source profiles and ability offsets can complement the linear predictor; model-based posterior spread is not target-calibrated uncertainty.",
    "idea_id": "cycle_03_rasch_residual_profile_mixture",
    "next_action": "Inspect candidate-owned documentation, keep source-only score-targeted prefixes fixed across predictors, implement replayable binary posterior inference and exact observed/unobserved score decomposition, then use nested grouped source controls if authorized. Preserve target-evidence and paper requirements. Stop reason: idea_ready_untested. Sole local target: ideas/03_rasch_residual_profile_mixtures_on_fixed_score_targeted_prefixes/memory.md.",
    "rubrics": [
      {
        "id": "combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "fixed_prefix_group_isolation",
        "type": "implementation"
      },
      {
        "id": "group_balanced_rasch_residual_particles",
        "type": "implementation"
      },
      {
        "id": "replayable_binary_posterior_full_score",
        "type": "implementation"
      },
      {
        "id": "grouped_blend_and_matched_controls",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Rasch-Residual Profile Mixtures on Fixed Score-Targeted Prefixes. gate=updated; trigger=b; reason=Add the untested nonlinear residual-profile posterior category while retaining the existing source-only acquisition and evidence restrictions.",
    "tags": [
      "cycle_3",
      "untested_hypothesis",
      "no_experiments",
      "canonical_local_memory",
      "worker_0"
    ],
    "timestamp": "2026-11-13"
  },
  {
    "attempt_id": "cycle_03_rasch_residual_profile_mixture_attempt_01",
    "event": "preparation",
    "idea_id": "cycle_03_rasch_residual_profile_mixture",
    "notes": "Starter inspected; prior score-targeted source absent; documented covariance fallback planned. No code execution or evaluation.",
    "program_id": "program_1",
    "status": "cloned"
  },
  {
    "attempt_id": "cycle_03_rasch_residual_profile_mixture_attempt_01",
    "event": "implementation",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "idea_id": "cycle_03_rasch_residual_profile_mixture",
    "notes": "Grouped source-only covariance fallback; Rasch-residual particles and convex blend; replay-safe posterior; unchanged manifest/RPC. No execution or empirical results.",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_03_rasch_residual_profile_mixture_attempt_01",
    "entrypoint_present": true,
    "event": "final_readiness",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "forbidden_artifacts_found": false,
    "idea_id": "cycle_03_rasch_residual_profile_mixture",
    "limitations": "Prior selector unavailable; documented covariance fallback used. Runtime, target performance, independent outer-source comparisons, uncertainty, baseline experiments, and paper remain unverified or incomplete.",
    "manifest_unchanged": true,
    "program_id": "program_1",
    "status": "ready_for_harness",
    "validation": "passive filesystem comparison and source search only; no code execution or evaluation"
  },
  {
    "attempt_id": "cycle_03_rasch_residual_profile_mixture_attempt_01",
    "evidence": "combined_score=0.9684365684559878, correct=True; scientific acceptance passed; search metrics (data): {\"anchor_mae\": 0.24719956291422063, \"combined_score\": 0.9684365684559878, \"constant_mae\": 0.2040049293753487, \"control_failure_rate\": 0.0, \"copy_mae\": 0.19502341674926077, \"correct\": true, \"delta_anchor_ci_high\": 1.0, \"delta_anchor_ci_low\": -1.0, \"delta_anchor_mae\": -0.21563613137020848, \"irt_mae\": 0.04121063683083198, \"kendall_tau_b\": 0.75310530481357, \"mae\": 0.031563431544012165, \"missing_episode_rate\": 0.0, \"no_calibration_mae\": 0.12348718192012596, \"no_diversity_mae\": 0.05351873980080848, \"permuted_mae\": 0.12275843002570605, \"reset_mae\": 0.026756557227656522, \"reset_max_abs_error\": 0.0, \"rmse\": 0.041163281675283644, \"source_mean_mae\": 0.12786232844772225, \"spearman\": 0.8878296042522897, \"uniform_mae\": 0.09894661693226534}",
    "idea_id": "cycle_03_rasch_residual_profile_mixture",
    "metrics": {
      "anchor_mae": 0.24719956291422063,
      "combined_score": 0.9684365684559878,
      "constant_mae": 0.2040049293753487,
      "control_failure_rate": 0.0,
      "copy_mae": 0.19502341674926077,
      "correct": true,
      "delta_anchor_ci_high": 1.0,
      "delta_anchor_ci_low": -1.0,
      "delta_anchor_mae": -0.21563613137020848,
      "irt_mae": 0.04121063683083198,
      "kendall_tau_b": 0.75310530481357,
      "mae": 0.031563431544012165,
      "missing_episode_rate": 0.0,
      "no_calibration_mae": 0.12348718192012596,
      "no_diversity_mae": 0.05351873980080848,
      "permuted_mae": 0.12275843002570605,
      "reset_mae": 0.026756557227656522,
      "reset_max_abs_error": 0.0,
      "rmse": 0.041163281675283644,
      "source_mean_mae": 0.12786232844772225,
      "spearman": 0.8878296042522897,
      "uniform_mae": 0.09894661693226534
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-13T17:51:56.142148+00:00"
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
