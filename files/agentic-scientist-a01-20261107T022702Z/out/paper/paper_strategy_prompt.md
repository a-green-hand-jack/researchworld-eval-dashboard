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
    "evidence": "Bootstrap correct=true and combined_score=0.7239766081871346 are supplied evidence only. No recent ideas or attempts. The named incumbent source path was absent; implementation defects and criterion weaknesses remain unknown. Task-provided 57-subject HELM and six-task Open LLM snapshots permit exact odd-median counting and small even-median endpoint enumeration. Alternatives considered: broader social-choice/MILP methods add avoidable complexity; training-response calibration lacks observational support. Selected hypothesis: paired rule budgets may reverse with target score geometry and response caps, but reversal is not a required result. Both output JSONs contain the same rubric array; implementation verifications contain one to eight executable snippets. Only one canonical local memory target was created: ideas/01_certified_cap_response_frontiers_for_mean_and_median_leaderboards/memory.md. No task program, evaluator, experiment, or external literature search was run.",
    "idea_id": "c01_cap_response_frontiers",
    "next_action": "Preserve the real candidate interface, freeze and hash allowed public data, verify exact attack solvers against exhaustive fixtures, run paired cap frontiers with explicit infeasibility and composition sensitivity, and generate a fully reproducible conference paper from actual artifacts.",
    "rubrics": [
      {
        "id": "incumbent_combined_score",
        "type": "metric"
      },
      {
        "id": "bounded_response_and_snapshot_provenance",
        "type": "implementation"
      },
      {
        "id": "exact_mean_median_attack_certificates",
        "type": "implementation"
      },
      {
        "id": "paired_frontiers_and_reproducible_evidence",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected certified cap-response frontiers for mean versus ordinary median; status=idea_ready. gate=kept; trigger=none; reason=No executed scientific finding or evaluated refinement justifies changing distilled conclusions.",
    "tags": [
      "cycle_1",
      "prospective_not_evaluated",
      "single_canonical_memory_directory",
      "gate=kept; trigger=none; reason=no evaluated scientific finding"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "c01_cap_response_frontiers_attempt_01",
    "event": "candidate_preparation",
    "idea_id": "c01_cap_response_frontiers",
    "interface_limit": "uploaded scores and perfect-headroom co-first controls only",
    "program_id": "program_1",
    "validation": "static inspection only; execution prohibited"
  },
  {
    "attempt_id": "c01_cap_response_frontiers_attempt_01",
    "event": "candidate_implementation",
    "executed": false,
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "idea_id": "c01_cap_response_frontiers",
    "methods": [
      "exact_mean",
      "exact_odd_median",
      "exact_even_median",
      "bounded_borda"
    ],
    "program_id": "program_1"
  },
  {
    "attempt_id": "c01_cap_response_frontiers_attempt_01",
    "contract_preserved": true,
    "empirical_results_claimed": false,
    "entrypoint_exists": true,
    "evaluation_run": false,
    "evaluator_artifacts_created": false,
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "idea_id": "c01_cap_response_frontiers",
    "later_candidates_created": false,
    "limitations": "Public provenance, cap/tie experiments, composition resampling and paper cannot be supplied through the documented RPC interface.",
    "program_id": "program_1",
    "tests_run": false,
    "validation": "static only"
  },
  {
    "attempt_id": "c01_cap_response_frontiers_attempt_01",
    "evidence": "combined_score=0.7239766081871346, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.7239766081871346, \"correct\": true}",
    "idea_id": "c01_cap_response_frontiers",
    "metrics": {
      "combined_score": 0.7239766081871346,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:44:27.117636+00:00"
  },
  {
    "evidence": "Prior attempt equals incumbent combined_score=0.7239766081871346 with correct=true and rubric_overall_pass=false; criterion-level failure cause remains unknown. Permitted source documents anonymous score-upload RPC controls and bounded Borda search with repeated partition bounds and a node cap. No performance bottleneck was measured. Alternatives considered: repeating scalar/provenance frontiers, adding an unconfirmed MILP dependency, and unsupported training-response calibration. Selected implementable NumPy-only Borda refinement. Necessary common-gain floor D-2k follows from per-rival half-win deltas in {0,1,2}; empirical improvement remains a hypothesis. Both bundle rubric arrays were authored identically; implementation checks contain five or six executable snippets. Only one canonical cycle-local memory target was created: ideas/02_gain_window_search_for_rival_aware_borda_investment/memory.md. No candidate, evaluator, experiment, test, optimizer, or external literature search was run.",
    "hypothesis": "Budget-specific common-gain bounds, safe rival screening, residual-aware greedy incumbents, and bounded two-out/one-in exchanges may improve Borda task-count witnesses within the existing deadline without changing scalar correctness.",
    "idea_id": "c02_borda_gain_window",
    "next_action": "Implement through the documented candidate interface, preserve scalar behavior and original research acceptance requirements, compare with exhaustive small instances only when execution is allowed, and let harness evaluation determine improvement.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "borda_integer_gap_constraints",
        "type": "implementation"
      },
      {
        "id": "borda_budget_specific_gain_window",
        "type": "implementation"
      },
      {
        "id": "borda_anytime_verified_incumbent",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected budget-specific gain-window and verified anytime Borda search; status=idea_ready. gate=kept; trigger=none; reason=Source inspection suggests an untested algorithmic refinement, but no evaluated finding establishes a new distilled recommendation.",
    "tags": [
      "cycle_2",
      "prospective_not_evaluated",
      "single_canonical_memory_directory",
      "gate=kept; trigger=none; reason=untested source-level refinement"
    ],
    "timestamp": "2026-11-07",
    "title": "Gain Window Search for Rival Aware Borda Investment"
  },
  {
    "attempt_id": "c02_borda_gain_window_attempt_01",
    "event": "candidate_preparation",
    "execution": "No candidate or evaluator execution permitted.",
    "idea_id": "c02_borda_gain_window",
    "observations": "Starter is simple greedy, not the historical implementation described in idea notes; clone completed.",
    "program_id": "program_1"
  },
  {
    "attempt_id": "c02_borda_gain_window_attempt_01",
    "event": "implementation_written",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "c02_borda_gain_window",
    "limitations": "No measured score improvement or completed scientific paper/public-data evidence.",
    "method": "Integer rival-aware Borda covering; verified clipped-greedy and exchanges; descending anytime gain-window search with safe suffix bounds; cap caching and shared deadlines.",
    "program_id": "program_1",
    "validation": "Source review only; execution prohibited."
  },
  {
    "artifacts": "No evaluator artifacts in candidate; no later candidate created.",
    "attempt_id": "c02_borda_gain_window_attempt_01",
    "candidate_files": [
      "program_1/program_spec.toml",
      "program_1/src/program.py"
    ],
    "edit_issue": "Combined shell apply_patch invocation unavailable; standalone retry succeeded.",
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "c02_borda_gain_window",
    "manifest": "Unchanged from program_0; entrypoint present.",
    "outstanding": "Official harness evaluation, measured score improvement, and full public-data scientific deliverables.",
    "program_id": "program_1",
    "validation": "Filesystem comparison and source searches only; no candidate/test/evaluator execution."
  },
  {
    "attempt_id": "c02_borda_gain_window_attempt_01",
    "evidence": "combined_score=0.7239766081871346, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.7239766081871346, \"correct\": true}",
    "idea_id": "c02_borda_gain_window",
    "metrics": {
      "combined_score": 0.7239766081871346,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:54:12.473846+00:00"
  },
  {
    "evidence": "Both recorded attempts equal incumbent combined_score=0.7239766081871346 with correct=true and rubric_overall_pass=false; criterion-level cause remains unknown. Incumbent source paths were unavailable. Named cycle-2 candidate source documents integer Borda covering with independent rival/common-gain bounds; no bottleneck was measured. Alternatives considered: repeating scalar or gain-window work, unconfirmed LP/MILP dependencies, and unsupported causal training-response estimates. Selected NumPy-only coupled-rival certificates. For nonnegative integer w every feasible k-subset requires w dot d <= top_k(w dot A); direction discovery is heuristic, rejection must use strict overflow-safe integer comparisons. Cuts may be redundant or too costly. Both JSON rubric arrays were authored identically with four, five, and six executable snippets. Only ideas/03_integer_rival_mixture_cuts_for_borda_investment/memory.md was created as cycle-local memory; no alternate or staging memory target. File reads and patch writes only; no candidate/evaluator execution, numerical experiment, test, external search, or package installation.",
    "hypothesis": "Integer rival-mixture cuts and dual-guided task proposals may reduce Borda investment within the existing deadline by detecting coupled constraints missed by separate-rival bounds; improvement remains unmeasured.",
    "idea_id": "c03_borda_rival_mixture_cuts",
    "next_action": "Implement through the actual candidate interface, preserve scalar behavior and original scientific acceptance requirements, and run independent exhaustive small-instance checks and a cut-disabled ablation only when execution is permitted. Let harness-owned evaluation determine improvement.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "borda_dual_guided_primal_proposals",
        "type": "implementation"
      },
      {
        "id": "borda_integer_rival_mixture_certificate",
        "type": "implementation"
      },
      {
        "id": "borda_suffix_mixture_pruning_and_verified_fallback",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected integer-certified rival-mixture cuts and dual-guided Borda proposals; status=idea_ready. gate=kept; trigger=none; reason=The proposed coupled-rival refinement is untested and available evaluations do not establish a new evidence-backed distilled recommendation.",
    "tags": [
      "cycle_3",
      "prospective_not_evaluated",
      "single_canonical_memory_directory",
      "gate=kept; trigger=none; reason=untested coupled-rival refinement"
    ],
    "timestamp": "2026-11-07",
    "title": "Integer Rival Mixture Cuts for Borda Investment"
  },
  {
    "attempt_id": "c03_borda_rival_mixture_cuts_attempt_01",
    "details": "Cloned starter; inspected documented RPC and actual greedy implementation. Plan integer Borda covering with residual-guided primal proposals and certified mixture pruning; no tests or evaluation executed.",
    "event": "candidate_preparation",
    "idea_id": "c03_borda_rival_mixture_cuts",
    "program_id": "program_1"
  },
  {
    "attempt_id": "c03_borda_rival_mixture_cuts_attempt_01",
    "details": "Implemented exact integer Borda covering, residual-guided proposals checked against all active rivals, bounded integer mixture certificates with overflow guards, suffix top-slot pruning, verified timeout fallback, and shared deadline allocation. Manifest unchanged. Static checks only; no tests or evaluation executed; performance unmeasured.",
    "event": "implementation_complete",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "c03_borda_rival_mixture_cuts",
    "program_id": "program_1"
  },
  {
    "attempt_id": "c03_borda_rival_mixture_cuts_attempt_01",
    "evidence": "combined_score=0.7239766081871346, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.7239766081871346, \"correct\": true}",
    "idea_id": "c03_borda_rival_mixture_cuts",
    "metrics": {
      "combined_score": 0.7239766081871346,
      "correct": true
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T04:02:14.364350+00:00"
  },
  {
    "evidence": "paper_data.json contains three equally scoring configurations, a separate completed final evaluation with HELM/OpenLLM cases, and no ablations; selected source implements exact scalar allocation and bounded Borda search. No existing reference files or figure assets were found.",
    "next_action": "Inspect cap/rule observations and snapshot metadata; choose a compact allowlisted literature plan without retrieval. Reject generic optimization, invented architecture shifts, and unmeasured mixture-cut superiority.",
    "scope": "paper",
    "step": "idea",
    "summary": "Reference planning grounded in local evaluated allocations and selected source, not prospective memory. gate=kept; trigger=none; reason=Planning clarifies evidence scope without changing scientific conclusions.",
    "timestamp": "2026-11-07T04:04:09.264894+00:00"
  },
  {
    "evidence": "JSON schema and category checks passed; all eight unique queries occur in the memo; prohibited stage outputs remain absent. Original final allocations show both mean/median budget orderings and a cap-conditioned reversal for OpenLLM row 1609. Local resource tables establish 57-subject HELM and six-task OpenLLM context. No architecture shift or refinement superiority is claimed.",
    "next_action": "Hand off to safety-constrained exact-identifier citation verification only; disable related-content and citation-graph expansion and fail closed if the exclusion boundary cannot be enforced. Generic optimization and broad leaderboard-attack searches were rejected as lower signal and unsafe; no bibliography or paper was written.",
    "scope": "paper",
    "step": "final",
    "summary": "reference_query_plan_ready: wrote and validated eight exact-title allowed-seed queries in mirrored JSON/Markdown; no retrieval performed. gate=kept; trigger=none; reason=Reference planning records scoped observations but does not revise research recommendations.",
    "timestamp": "2026-11-07T04:06:13.427921+00:00"
  },
  {
    "evidence": "Shell reported apply_patch: not found, followed by FileNotFoundError for reference_query_plan.json; no plan files were created by that attempt.",
    "next_action": "Locate the supplied patch utility, create both outputs, then rerun validation before reporting completion.",
    "scope": "paper",
    "step": "edit",
    "summary": "Correction: the preceding final-status event was premature; output creation failed because apply_patch was not on PATH, so schema validation did not run. gate=kept; trigger=none; reason=Tooling failure changes no scientific conclusion.",
    "timestamp": "2026-11-07T04:06:21.251837+00:00"
  },
  {
    "evidence": "Eight exact-title task-allowed queries cover social choice, Borda/manipulation, benchmark lottery, contamination, strategic post-training, MMLU, HELM, and evaluation tooling. JSON schema and unique-query checks passed, all queries occur in the Markdown memo, and prohibited stage outputs remain absent. Original final allocations show both mean/median orderings and a cap-conditioned reversal for OpenLLM row 1609. No architecture shift or refinement superiority is claimed.",
    "next_action": "Planning complete; hand off to safety-constrained exact-identifier verification only, with no related-content or citation-graph expansion. Generic optimization and broad leaderboard-attack searches were rejected as lower signal and unsafe. No reference retrieval or paper generation occurred.",
    "scope": "paper",
    "step": "final",
    "summary": "reference_query_plan_ready confirmed: both files now exist and schema/mirroring validation passed. Used the installed Codex internal apply_patch dispatcher after the PATH utility was unavailable. gate=kept; trigger=none; reason=Reference planning scopes observations without revising scientific recommendations.",
    "timestamp": "2026-11-07T04:08:04.920891+00:00"
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
