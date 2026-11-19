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
    "evidence": "Supplied manifest: incumbent correct=true, combined_score=0.9080607409041159. Named incumbent source file unavailable. Mounted README documents repeated identities and shared details_repo values, but no group assignments. No candidate, benchmark, optimizer, evaluator, or computational probe executed. Alternatives: source-only IRT/anchors, supervised selection, pure random averaging; selected frozen-surrogate residual correction has a conditional finite-population argument but unknown empirical benefit and possible audit-variance/pilot-capacity costs.",
    "idea_id": "cycle_01_frozen_surrogate_random_audit",
    "next_action": "Preserve the documented candidate contract and harness split; implement pilot-only frozen predictions, disjoint uniform audit, complement-weighted residual correction, and source-only tuning. Test invariants and run paired ordinary/identity-family-held-out research comparisons before expanding results and paper.",
    "rubrics": [
      {
        "id": "combined_score_improves",
        "type": "metric"
      },
      {
        "id": "pilot_only_frozen_surrogate",
        "type": "implementation"
      },
      {
        "id": "disjoint_uniform_audit_budget",
        "type": "implementation"
      },
      {
        "id": "finite_population_residual_correction",
        "type": "implementation"
      },
      {
        "id": "source_only_grouped_model_selection",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Proposed Frozen Surrogate Random Audit; required JSON bundles written; status=idea_bundle_ready. gate=kept; trigger=none; reason=Only an untested proposal and interface evidence are available; no evaluated scientific finding warrants distilled guidance changes.",
    "tags": [
      "untested_hypothesis",
      "no_scientific_execution",
      "canonical_local_memory=ideas/01_frozen_surrogate_random_audit/memory.md",
      "single_cycle_local_memory_target"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "cycle_01_frozen_surrogate_random_audit_attempt_01",
    "event": "implementation_start",
    "idea_id": "cycle_01_frozen_surrogate_random_audit",
    "limitations": [
      "no ancestry metadata in RPC",
      "no execution or tests permitted",
      "nested selections and duplicate-content groups require compatible audit design"
    ],
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_01_frozen_surrogate_random_audit_attempt_01",
    "contract_unchanged": true,
    "evaluation_executed": false,
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/surrogate.py",
      "program_1/src/invariant_checks.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle_01_frozen_surrogate_random_audit",
    "limitations": [
      "pilot and audit observations co-delivered; freeze before accessing audit labels",
      "anonymous supplied source lineage groups only, no ancestry metadata",
      "unequal content groups require group-weighted correction",
      "empirical score and research deliverables unmeasured"
    ],
    "program_id": "program_1",
    "tests_executed": false
  },
  {
    "attempt_id": "cycle_01_frozen_surrogate_random_audit_attempt_01",
    "evaluation_executed": false,
    "event": "final_edit_complete",
    "idea_id": "cycle_01_frozen_surrogate_random_audit",
    "program_id": "program_1",
    "status": "ready_for_harness",
    "tests_executed": false,
    "zero_budget_fallback": "source_weighted_prior"
  },
  {
    "attempt_id": "cycle_01_frozen_surrogate_random_audit_attempt_01",
    "evidence": "combined_score=0.9189386797038666, correct=True; scientific acceptance passed; search metrics (data): {\"anchor_mae\": 0.13300734976798292, \"combined_score\": 0.9189386797038666, \"constant_mae\": 0.4580913999000772, \"control_correct\": 1.0, \"correct\": true, \"irt_mae\": 0.07504423299125063, \"kendall\": 0.6250942381270175, \"mae\": 0.0810613202961334, \"permuted_mae\": 0.08687585668671148, \"prior_mae\": 0.14429218883447575, \"rmse\": 0.10282682720675318, \"spearman\": 0.7816459431057419, \"uniform_mae\": 0.11168295368474038}",
    "idea_id": "cycle_01_frozen_surrogate_random_audit",
    "metrics": {
      "anchor_mae": 0.13300734976798292,
      "combined_score": 0.9189386797038666,
      "constant_mae": 0.4580913999000772,
      "control_correct": 1.0,
      "correct": true,
      "irt_mae": 0.07504423299125063,
      "kendall": 0.6250942381270175,
      "mae": 0.0810613202961334,
      "permuted_mae": 0.08687585668671148,
      "prior_mae": 0.14429218883447575,
      "rmse": 0.10282682720675318,
      "spearman": 0.7816459431057419,
      "uniform_mae": 0.11168295368474038
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T12:54:24.868797+00:00"
  },
  {
    "evidence": "Recorded incumbent correct=true, combined_score=0.9189386797038666, MAE=0.0810613202961334; uniform MAE=0.11168295368474038; IRT MAE=0.07504423299125063. Candidate-owned notes document a fixed initial pilot count. Criterion-level rubric failure cause is unknown. Alternatives considered: unsupported per-target adaptive IRT, nonlinear source-response mixtures and audit-allocation repair. Selected score-directed conditional covariance acquisition and all-answer ridge decoding are supported by the common-subset RPC, supplied source weights and anonymous source/content groups. No new scientific computation or evaluator access occurred.",
    "idea_id": "cycle_02_score_targeted_all_query_ridge",
    "next_action": "Implement unchanged RPC; refit selector and decoder in disjoint source-lineage folds; verify nested content-group-unique selections and prediction invariances; run paired selector/decoder ablations against incumbent, uniform, anchors and IRT with uncertainty when execution is permitted.",
    "rubrics": [
      {
        "id": "combined_score_improves",
        "type": "metric"
      },
      {
        "id": "weighted_full_score_covariance",
        "type": "implementation"
      },
      {
        "id": "score_conditioned_nested_design",
        "type": "implementation"
      },
      {
        "id": "all_observations_score_decoder",
        "type": "implementation"
      },
      {
        "id": "lineage_refit_source_validation",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Proposed Score Targeted All Query Ridge; required JSON bundles written; status=idea_bundle_ready. gate=kept; trigger=none; reason=One aggregate evaluation motivates a new experiment but supplies neither uncertainty nor evidence of its mechanism or transfer; no stable distilled recommendation is established.",
    "tags": [
      "untested_hypothesis",
      "no_scientific_execution",
      "canonical_local_memory=ideas/02_score_targeted_all_query_ridge/memory.md",
      "single_cycle_local_memory_target"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "cycle_02_score_targeted_all_query_ridge_attempt_01",
    "details": "Cloned program_0; inspected candidate RPC only. Implement source-weighted score covariance, nested acquisition and lineage-held-out all-query ridge/offset tuning. No execution permitted.",
    "event": "implementation_started",
    "idea_id": "cycle_02_score_targeted_all_query_ridge",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_score_targeted_all_query_ridge_attempt_01",
    "details": "Weighted full-score covariance, nested regularized score acquisition, all-query ridge/offset source-lineage validation, runtime invariants and canonical history decoding. RPC/spec preserved; no code execution or evaluation.",
    "event": "implementation_completed",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/surrogate.py",
      "program_1/src/invariant_checks.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle_02_score_targeted_all_query_ridge",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_score_targeted_all_query_ridge_attempt_01",
    "checks": {
      "candidate_artifacts_absent": true,
      "entrypoint_exists": true,
      "only_program_1_created": true,
      "spec_unchanged": true
    },
    "event": "candidate_ready",
    "execution": "Not run: stage prohibits tests, candidate execution and evaluation.",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/surrogate.py",
      "program_1/src/invariant_checks.py",
      "program_1/src/IMPLEMENTATION.md"
    ],
    "idea_id": "cycle_02_score_targeted_all_query_ridge",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_02_score_targeted_all_query_ridge_attempt_01",
    "evidence": "combined_score=0.9445969116773968, correct=True; scientific acceptance passed; search metrics (data): {\"anchor_mae\": 0.13300734976798292, \"combined_score\": 0.9445969116773968, \"constant_mae\": 0.38880569980715496, \"control_correct\": 1.0, \"correct\": true, \"irt_mae\": 0.07504423299125063, \"kendall\": 0.7729564482943201, \"mae\": 0.055403088322603176, \"permuted_mae\": 0.0771531446521588, \"prior_mae\": 0.14429218883447575, \"rmse\": 0.07348930100704983, \"spearman\": 0.8852024098775814, \"uniform_mae\": 0.11168295368474038}",
    "idea_id": "cycle_02_score_targeted_all_query_ridge",
    "metrics": {
      "anchor_mae": 0.13300734976798292,
      "combined_score": 0.9445969116773968,
      "constant_mae": 0.38880569980715496,
      "control_correct": 1.0,
      "correct": true,
      "irt_mae": 0.07504423299125063,
      "kendall": 0.7729564482943201,
      "mae": 0.055403088322603176,
      "permuted_mae": 0.0771531446521588,
      "prior_mae": 0.14429218883447575,
      "rmse": 0.07348930100704983,
      "spearman": 0.8852024098775814,
      "uniform_mae": 0.11168295368474038
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T13:06:42.013542+00:00"
  },
  {
    "evidence": "Recorded cycle-02 correct=true, combined_score=0.9445969116773968, MAE=0.055403088322603176, RMSE=0.07348930100704983, Spearman=0.8852024098775814 and Kendall=0.7729564482943201; cycle-01 MAE=0.0810613202961334. Candidate-owned RPC and surrogate source reads support source-weighted nonlinear decoding using anonymous source/content groups and common queried histories. Manifest absolute candidate path unavailable; named results-root counterpart readable. Alternatives considered: unsupported per-target adaptive IRT, limited-extrapolation kernel neighbors and scalar isotonic calibration. Selected log-odds curve plus prefix-matched residual ridge keeps acquisition fixed and admits direct ablations; saturation is a hypothesis, not a diagnosed failure. No candidate execution, exploratory computation, benchmark, external research or evaluator inspection occurred.",
    "idea_id": "cycle_03_log_odds_shift_residual_decoder",
    "next_action": "Implement unchanged RPC; refit incumbent selection/tuning and decoder inside disjoint source-lineage folds; infer all source shifts from query prefixes only; compare paired incumbent, curve-only, residual-only and full-blend decoders plus existing baselines with uncertainty when execution is permitted.",
    "rubrics": [
      {
        "id": "combined_score_improves",
        "type": "metric"
      },
      {
        "id": "all_query_log_odds_shift",
        "type": "implementation"
      },
      {
        "id": "prefix_matched_residual_regression",
        "type": "implementation"
      },
      {
        "id": "lineage_nested_decoder_validation",
        "type": "implementation"
      },
      {
        "id": "frozen_selection_history_invariants",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Proposed Log Odds Shift Residual Decoder; matching required JSON bundles written; status=idea_bundle_ready. gate=kept; trigger=none; reason=The new decoder has no measured outcome and the existing aggregate improvement does not isolate a transferable mechanism, so no established distilled recommendation changes.",
    "tags": [
      "untested_hypothesis",
      "no_scientific_execution",
      "canonical_local_memory=ideas/03_log_odds_shift_residual_decoder/memory.md",
      "single_cycle_local_memory_target"
    ],
    "timestamp": "2026-11-17"
  },
  {
    "attempt_id": "cycle_03_log_odds_shift_residual_decoder_attempt_01",
    "changes": [
      "cloned program_0 to program_1"
    ],
    "event": "candidate_started",
    "execution": "not permitted; not performed",
    "idea_id": "cycle_03_log_odds_shift_residual_decoder",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_03_log_odds_shift_residual_decoder_attempt_01",
    "event": "decoder_implemented",
    "execution": "not performed",
    "files": [
      "program_1/src/nonlinear_decoder.py",
      "program_1/src/program.py",
      "program_1/src/IMPLEMENTATION.md",
      "program_1/src/DECODER.md"
    ],
    "idea_id": "cycle_03_log_odds_shift_residual_decoder",
    "measured_improvement": null,
    "method": "prefix-only regularized log-odds shift; original-population curve; weighted residual ridge; source-lineage nested tuning; unchanged acquisition and incumbent fallback",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_03_log_odds_shift_residual_decoder_attempt_01",
    "editing_issue": "combined shell patch unavailable; standalone apply_patch retry succeeded",
    "event": "candidate_ready",
    "execution": "not performed per stage restrictions",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/nonlinear_decoder.py",
      "program_1/src/IMPLEMENTATION.md",
      "program_1/src/DECODER.md"
    ],
    "filesystem_checks": {
      "entrypoint_exists": true,
      "forbidden_artifacts_under_candidate": false,
      "incumbent_unchanged": true,
      "later_candidate_created": false,
      "runtime_invariants_unchanged": true,
      "spec_unchanged": true
    },
    "idea_id": "cycle_03_log_odds_shift_residual_decoder",
    "measured_improvement": null,
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle_03_log_odds_shift_residual_decoder_attempt_01",
    "evidence": "combined_score=0.9453539826294075, correct=True; scientific acceptance passed; search metrics (data): {\"anchor_mae\": 0.13300734976798292, \"combined_score\": 0.9453539826294075, \"constant_mae\": 0.40526908638842024, \"control_correct\": 1.0, \"correct\": true, \"irt_mae\": 0.07504423299125063, \"kendall\": 0.7734254586835944, \"mae\": 0.05464601737059244, \"permuted_mae\": 0.07599748646182174, \"prior_mae\": 0.14429218883447575, \"rmse\": 0.07231380243004325, \"spearman\": 0.8854483329598837, \"uniform_mae\": 0.11168295368474038}",
    "idea_id": "cycle_03_log_odds_shift_residual_decoder",
    "metrics": {
      "anchor_mae": 0.13300734976798292,
      "combined_score": 0.9453539826294075,
      "constant_mae": 0.40526908638842024,
      "control_correct": 1.0,
      "correct": true,
      "irt_mae": 0.07504423299125063,
      "kendall": 0.7734254586835944,
      "mae": 0.05464601737059244,
      "permuted_mae": 0.07599748646182174,
      "prior_mae": 0.14429218883447575,
      "rmse": 0.07231380243004325,
      "spearman": 0.8854483329598837,
      "uniform_mae": 0.11168295368474038
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-17T13:21:48.537456+00:00"
  },
  {
    "evidence": "reference_query_plan.json and reference_query_plan.md cover conditional score covariance/ridge, optional log-odds residual decoding, earlier randomized audit correction, anchor/IRT/supervised/adaptive comparators, MMLU-Pro, HELM and Open LLM Leaderboard. Final nine-case evidence supersedes narrower private memory; no ablations isolate nonlinear gains. No retrieval occurred. Initial helper appended local memory but rejected symlinked global_memory; resolved absolute global paths are used for this append.",
    "next_action": "Validate output schema, query uniqueness, memo consistency and untouched forbidden output files; later retrieval must obey the prohibited-literature constraints.",
    "scope": "paper",
    "step": "paper",
    "summary": "Wrote ten grounded reference queries and mirrored memo; direct title resolution and foundational design/estimation searches replace generic research-question searches. gate=kept; trigger=none; reason=Citation planning adds no new empirical mechanism or transferable recommendation.",
    "timestamp": "2026-11-17T13:28:46.153996+00:00"
  },
  {
    "evidence": "Schema/category checks, query uniqueness, exact query mirroring, nine final cases, final MAE, required memory files and absence of references.bib/references_provenance.json/paper.tex/claims_grounding.json all passed. Initial shell apply_patch was unavailable; the bundled Codex apply-patch entrypoint successfully created both outputs. Initial global-memory helper rejected the symlink; subsequent appends use resolved absolute paths. Chosen queries map to measured packages, actual comparator families and dataset ecosystems rather than generic optimization, chronology or unsupported architectural transfer.",
    "next_action": "Later citation retrieval should use the ten planned queries under strict prohibited-literature screening; no new experiments or nonlinear-mechanism claims are authorized by this plan.",
    "scope": "paper",
    "step": "final",
    "summary": "reference_query_plan_ready: both outputs written and validated; ten focused queries, no retrieval. gate=kept; trigger=none; reason=This planning stage does not establish a new scientific recommendation.",
    "timestamp": "2026-11-17T13:30:54.869270+00:00"
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
