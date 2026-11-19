# Role
You are the reference-planning agent for a completed research run.
Goal: produce a grounded reference query plan that will drive automated citation retrieval for the paper stage.
Use grounded inputs only. Do not retrieve references yet.

This prompt must transfer across tasks and runs.
Infer all domain details, methods, benchmarks, architectures, and comparator families from the current artifacts only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

# Task Context
## Goal
**研究任务：自动调优之后，报告的基准分数意味着什么**
**背景与动机**
在大语言模型（LLM）的实际使用中，研究者常常在一个基准的题目上自动搜索提示词（prompt）
或由多个 LLM 调用组成的程序（pipeline），再把搜索得到的"最佳配置"在同一批题目上的得分
作为该系统的性能汇报。所用的自动搜索工具多种多样。

这种做法引出一个统计问题：基准题目既被用来**挑选**配置，又被用来给该配置**打分**，因此
汇报的数字不一定反映系统在全新题目上的真实表现；基于这类汇报数字做出的比较和决定是否
可靠，也就不清楚。

**研究问题**
请围绕下面的问题开展一项完整的研究：

1. 对一个先在有限题集上搜索配置、再把选出的配置拿去使用的系统，汇报的分数与它在全新
   题目上的真实表现相差多少？差距受哪些因素影响？它是否会影响基于汇报分数做出的结论？
2. 能否设计更可靠的汇报方式？应如何通过实验检验它是否可靠？

**成功如何衡量**
结论需要有你自己运行的实验支持，并至少在一个真实 LLM 与真实基准的设置上检验；实验设计、
统计工具和理论分析的深度由你决定。结论可以是支持、反驳或视条件而定。

**关键约束**
资源约束：一周墙钟时间；以 CPU 为主，涉及 LLM 推理的实验可使用至多一张 24 GB GPU 或等价
API 预算（详见 `resources.md`）；可用数据见 `data.md`；最终产出是一篇研究论文及复现代码
（详见 `deliverable.md`）。

**起步文献**
以下条目均为 2025 年及以前公开的工作，仅作背景知识参考，不要求全部使用，也欢迎自行检索其他早期文献。

1. Wang et al. *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding
   Benchmark*. NeurIPS 2024 Datasets & Benchmarks（arXiv 2024-06-03）。
   https://arxiv.org/abs/2406.01574
   说明：提出一个多学科、每题 10 个选项的多项选择语言理解基准，在 MMLU 的基础上增加了推理型题目，并评测了多种 LLM。
2. Khattab et al. *DSPy: Compiling Declarative Language Model Calls into Self-Improving
   Pipelines*. arXiv 2023-10-05。https://arxiv.org/abs/2310.03714
   说明：提出以声明式模块编写 LLM 调用程序的编程模型，并提供按指定评价指标自动优化其提示词和示范样例的编译器。
3. Opsahl-Ong et al. *Optimizing Instructions and Demonstrations for Multi-Stage Language
   Model Programs*（MIPRO）. EMNLP 2024（arXiv 2024-06-17）。https://arxiv.org/abs/2406.11695
   说明：提出一种针对多阶段 LLM 程序同时优化指令和示范样例的方法，并在多个任务上与已有方法比较。
4. Polo et al. *Efficient multi-prompt evaluation of LLMs*. NeurIPS 2024（arXiv 2024-05-27）。
   https://arxiv.org/abs/2405.17202
   说明：提出用较少的评测样本估计 LLM 在大量提示词模板下的性能分布的方法，并在多个基准上实验。
5. Shi et al. *Efficient Prompt Optimization Through the Lens of Best Arm Identification*.
   NeurIPS 2024（arXiv 2024-02-15）。https://arxiv.org/abs/2402.09723
   说明：把提示词选择形式化为最佳臂识别问题，提出一种在有限评测次数下选择提示词的算法，并在多个任务上实验。
6. Sclar et al. *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design
   or: How I learned to start worrying about prompt formatting*. ICLR 2024（arXiv 2023-10-17）。
   https://arxiv.org/abs/2310.11324
   说明：测量 LLM 对提示词格式的细微改动的敏感性，报告同一任务下不同格式之间的性能差异，并提出估计性能范围的方法。
7. Dwork et al. *Preserving Statistical Validity in Adaptive Data Analysis*. STOC 2015
   （arXiv 2014-11-10）。https://arxiv.org/abs/1411.2664
   说明：研究同一份数据被多次自适应地用于分析时统计推断的有效性，并提出基于差分隐私的保护方法。
8. Blum & Hardt. *The Ladder: A Reliable Leaderboard for Machine Learning Competitions*.
   ICML 2015（arXiv 2015-02-16）。https://arxiv.org/abs/1502.04585
   说明：提出名为 Ladder 的机制，用于机器学习竞赛榜单上对多次提交报告分数，并给出理论分析和实验。
9. Andrews, Kitagawa & McCloskey. *Inference on Winners*. NBER Working Paper 25456（2018）；
   Quarterly Journal of Economics 139(1), 2024。https://www.nber.org/papers/w25456
   说明：计量经济学论文，研究选出对象之后的统计推断问题，并给出应用示例。
10. Chernozhukov, Chetverikov & Kato. *Gaussian approximations and multiplier bootstrap for
    maxima of sums of high-dimensional random vectors*. Annals of Statistics 2013
    （arXiv 2012-12-31）。https://arxiv.org/abs/1212.6906
    说明：统计学论文，给出高维随机向量之和的分布逼近的理论结果。
11. Berk, Brown, Buja, Zhang & Zhao. *Valid post-selection inference*. Annals of Statistics
    41(2), 2013。https://doi.org/10.1214/12-AOS1077
    说明：统计学论文，研究回归分析中先选模型、再做推断的问题，并给出相应的置信区间构造。

**公开数据与获取方式**
核实日期：2026-10-27。

| 数据 | 获取 | 许可证 | 大小 | 账号 |
| --- | --- | --- | --- | --- |
| MMLU-Pro（多学科、每题 10 个选项的多项选择题；14 个学科类别，含分学科字段） | 数据集 https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro （固定到修订版 `b189ec765aa7ed75c8acfea42df31fdae71f97be`，2026-05-02）；可选：数据集附带的评测代码 https://github.com/TIGER-AI-Lab/MMLU-Pro | 数据集卡片标注 MIT；GitHub 仓库标注 Apache-2.0 | test 12,032 题 + validation 70 题；parquet 文件合计约 4.2 MB | 不需要（未设 gating，无需登录） |
| 合成数据 | 自行用程序生成，规模与形式自定 | 无 | 极小 | 不需要 |

说明：

- 真实实验需要自行用 LLM 对题目生成回答（包内不提供现成的模型输出）。可选择开放权重的
  指令微调模型（用 vLLM、llama.cpp 或 transformers 在本地推理），或按预算调用外部 API；
  模型输出可自行缓存复用。
- 可选工具：DSPy（https://github.com/stanfordnlp/dspy ，MIT 许可证；2026-05-05 发布的
  3.2.1 版），也可自行实现提示词/程序的搜索流程。许可证以仓库页面为准。
- 合成实验完全不依赖外部数据，可在纯 CPU 上完成。

**资源与预算**
- 时间上限：一周（墙钟）。
- 模拟或合成实验（如采用）：仅需 CPU。估算依据：单次模拟的数据规模至多数十万个数值，
  单次统计计算为毫秒到秒级；数千次重复模拟在多核 CPU 上约数小时（出题方粗略估计，未实测）。
- 真实 LLM 实验：需要自行推理。可使用一张 GPU（24 GB 显存足够运行 7B-8B 量级的开放权重
  指令模型，约 15-17 GB 权重）或等价的 API 预算；GPU 与外部 API 是否可用以实际运行环境为准。推理量粗算：总输出量在千万 token
  量级时，用 7-8B 模型在一张 24 GB 卡上约需数小时；提示词/程序搜索工具自身的调用另计，量级相当。生成
  回答与得分缓存后，后续 CPU 统计分析估计在 16 CPU 小时以内。
- 存储与内存：每个 7-8B 开放权重模型约 15-17 GB，输出与得分缓存 < 1 GB；建议预留 100 GB
  磁盘、32 GB 系统内存、8 核以上 CPU。
- 不要求大规模训练；不需要多卡。
- 估算说明：这些数字是出题方的粗略估计，未经实测；请在报告中给出你实际使用的计算量。

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
    "evidence": "Task provides MMLU-Pro and a single-GPU/API budget; no previous attempts. Supplied incumbent combined_score=0.9974625501619445 and correct=true. Its exact source path was unavailable; no scientific defect is inferred. No inference, simulations, evaluator runs, or prohibited literature access occurred. Alternatives were naive bootstrap bias subtraction, split-only reporting, and a larger adaptive optimizer. Canonical local memory is ideas/01_paired_selection_certificates_with_an_untouched_audit/memory.md; no alternate cycle-local memory path was created.",
    "idea_id": "cycle01_paired_selection_certificates",
    "next_action": "Preserve valid incumbent work, preregister a frozen prompt bank and untouched audit, collect actual LLM answers, and compare post-selection paired certificates with naive, unpaired, protected-split, and approximate-bootstrap reports. Test population coverage in simulations and report real audit uncertainty separately.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "frozen_bank_and_untouched_audit",
        "type": "implementation"
      },
      {
        "id": "simultaneous_paired_certificate",
        "type": "implementation"
      },
      {
        "id": "known_truth_and_audit_uncertainty",
        "type": "implementation"
      },
      {
        "id": "real_inference_and_artifact_provenance",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Paired Selection Certificates with an Untouched Audit idea and matching rubric bundle. gate=kept; trigger=none; reason=There are no new measured findings or evidence-backed changes to distill from this untested first-cycle proposal.",
    "tags": [
      "cycle_1",
      "idea_bundle_ready",
      "untested_hypothesis",
      "single_canonical_memory_directory"
    ],
    "timestamp": "2026-11-05"
  },
  {
    "attempt_id": "cycle01_paired_selection_certificates_attempt_01",
    "event": "candidate_cloned_interface_checked",
    "execution": "none",
    "idea_id": "cycle01_paired_selection_certificates",
    "limitations": [
      "no correctness matrices or audit observations",
      "fixed 16-prompt output contract",
      "no paired certificate or empirical research claims"
    ],
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle01_paired_selection_certificates_attempt_01",
    "contract_preserved": true,
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py",
      "program_1/src/METHOD.md"
    ],
    "idea_id": "cycle01_paired_selection_certificates",
    "implemented": [
      "frozen incumbent prompt bank with ordered hashes",
      "disjoint exhaustive protected partition checks",
      "unchanged multi-arm half split",
      "single-arm three-quarter report allocation"
    ],
    "not_implemented": [
      "paired certificates without outcome observations",
      "audit analysis without audit observations",
      "real inference and paper"
    ],
    "program_id": "program_1",
    "status": "ready",
    "validation": "static filesystem checks only; no tests or evaluation"
  },
  {
    "attempt_id": "cycle01_paired_selection_certificates_attempt_01",
    "evidence": "combined_score=None, correct=False; evaluation failed: timeout; search metrics (data): {\"combined_score\": null, \"correct\": false}",
    "idea_id": "cycle01_paired_selection_certificates",
    "metrics": {
      "combined_score": null,
      "correct": false
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-05T21:28:48.891639+00:00"
  },
  {
    "evidence": "Read task, skills, histories, manifest, campaign memory, and named prior candidate interface/source. That source documents unlabelled slots, fixed 16-prompt controls, uniform report weights, and n/4 through 3n/4 selection bounds; labels, outcome matrices, audit examples, and estimator controls are unavailable. Prior exit 124 with null score leaves timeout cause and scientific performance unknown. Alternatives considered: unsupported paired certificates/adaptive search, complex stratified rounding, and confounded prompt redesign. No scientific computation, evaluator execution, or forbidden literature access occurred. Canonical local memory is ideas/02_maximal_protected_reporting_under_a_frozen_prompt_bank/memory.md; this run created no alternate cycle-local memory target. Final status: idea_bundle_ready.",
    "idea_id": "cycle02_maximal_protected_reporting",
    "next_action": "Preserve validated incumbent prompt texts and RPC; implement all-arm quarter selection with seeded canonical-key shuffling and uniform protected reporting in program_1/src. During execution use permitted aggregate results to test reporting MSE and selection-quality tradeoffs. Keep original research and publication requirements intact and mark unsupported claims incomplete.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "maximal_protected_report_allocation",
        "type": "implementation"
      },
      {
        "id": "seeded_label_free_partition",
        "type": "implementation"
      },
      {
        "id": "frozen_bank_uniform_contract",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Maximal Protected Reporting Under a Frozen Prompt Bank and matching rubrics. Hypothesis: allocate n/4 to selection and 3n/4 to protected reporting for every arm count to improve reporting MSE without claiming improved selected-system accuracy. gate=kept; trigger=none; reason=The allocation is an untested hypothesis and the timed-out attempt supplies no usable performance estimate from which to distill a scientific recommendation.",
    "tags": [
      "cycle_2",
      "idea_bundle_ready",
      "untested_hypothesis",
      "single_canonical_memory_directory",
      "timeout_cause_unknown"
    ],
    "timestamp": "2026-11-05"
  },
  {
    "attempt_id": "cycle02_maximal_protected_reporting_attempt_01",
    "event": "implementation_started",
    "idea_id": "cycle02_maximal_protected_reporting",
    "plan": "Clone program_0; preserve frozen prompt bank, tie order, and RPC contract; sort keys before seeded shuffle and allocate n/4 to selection for every arm count.",
    "program_id": "program_1",
    "validation_scope": "Static filesystem inspection only; execution and evaluation forbidden."
  },
  {
    "attempt_id": "cycle02_maximal_protected_reporting_attempt_01",
    "changed_files": [
      "program_1/src/program.py"
    ],
    "contract": "program_spec.toml unchanged; self-contained entrypoint present; exact five response fields preserved",
    "event": "candidate_ready",
    "idea_id": "cycle02_maximal_protected_reporting",
    "implementation": "Sorted supplied keys, reset-seeded shuffle, n/4 selection and 3n/4 reporting for all legal arms; frozen prompts, tie priority, uniform weights, partition and bank assertions preserved.",
    "program_id": "program_1",
    "scientific_status": "No measured improvement or experiment claimed; harness evaluation pending; paper and real-LLM experiments not completed in this stage.",
    "tooling_limitation": "apply_patch unavailable; used plain-file Perl editing and reviewed diff.",
    "validation": "Static diff, file inventory, and contract comparison only; no tests or execution; no evaluator artifacts or later candidates created."
  },
  {
    "attempt_id": "cycle02_maximal_protected_reporting_attempt_01",
    "evidence": "combined_score=None, correct=False; evaluation failed: timeout; search metrics (data): {\"combined_score\": null, \"correct\": false}",
    "idea_id": "cycle02_maximal_protected_reporting",
    "metrics": {
      "combined_score": null,
      "correct": false
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-05T23:33:43.856419+00:00"
  },
  {
    "evidence": "Read workflow skills, campaign memory, histories, manifest, and named prior candidate-owned source/specification. Interface supplies only unlabelled key/stratum slots and frozen-bank partition controls, not outcomes, audit data, or estimator controls. Alternatives were an unchanged quarter split, half split, confounded prompt redesign, and unsupported outcome corrections. Both prior attempts have timeout exit 124 and null scores; acceptance and scientific performance are unestablished. No scientific computation, tests, evaluator execution, or forbidden-literature access occurred. Sole local memory target is ideas/03_randomized_stratum_balanced_protected_reporting/memory.md; no alternate cycle-local target was created. Final status: idea_bundle_ready.",
    "idea_id": "cycle03_stratum_balanced_reporting",
    "next_action": "Clone validated incumbent, preserve exact prompt texts and RPC, implement canonical seeded stratum grouping and randomized cumulative quarter quotas, and retain uniform weights. Use only authorized aggregate evaluation; compare unstratified quarter allocation only if permitted. Do not claim selected-winner unbiasedness, better coverage, real-inference completion, or paper completion without evidence.",
    "rubrics": [
      {
        "id": "incumbent_score_improvement",
        "type": "metric"
      },
      {
        "id": "randomized_proportional_stratum_quotas",
        "type": "implementation"
      },
      {
        "id": "protected_three_quarter_report_partition",
        "type": "implementation"
      },
      {
        "id": "frozen_bank_uniform_rpc_contract",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Wrote Randomized Stratum Balanced Protected Reporting and matching rubrics. Hypothesis: randomized proportional stratum quotas with quarter selection and three-quarter reporting may reduce composition-driven reporting MSE. gate=kept; trigger=none; reason=This is an untested design hypothesis and the two null-score timeouts provide no evidence-backed methodological recommendation to distill.",
    "tags": [
      "cycle_3",
      "idea_bundle_ready",
      "untested_hypothesis",
      "single_canonical_memory_directory",
      "timeout_cause_unknown"
    ],
    "timestamp": "2026-11-05"
  },
  {
    "attempt_id": "cycle03_stratum_balanced_reporting_attempt_01",
    "event": "implementation_started",
    "idea_id": "cycle03_stratum_balanced_reporting",
    "program_id": "program_1",
    "scope": "clone starter; replace only partition policy; static review only"
  },
  {
    "attempt_id": "cycle03_stratum_balanced_reporting_attempt_01",
    "evaluation_run": false,
    "event": "candidate_ready",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "cycle03_stratum_balanced_reporting",
    "policy": "canonical randomized systematic quarter quotas; three-quarter reporting",
    "program_id": "program_1",
    "research_deliverables": "incomplete",
    "scientific_improvement": "unestablished",
    "spec_unchanged": true,
    "validation": "static diff and filesystem inspection only; no execution"
  },
  {
    "attempt_id": "cycle03_stratum_balanced_reporting_attempt_01",
    "evidence": "combined_score=None, correct=False; evaluation failed: timeout; search metrics (data): {\"combined_score\": null, \"correct\": false}",
    "idea_id": "cycle03_stratum_balanced_reporting",
    "metrics": {
      "combined_score": null,
      "correct": false
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-06T01:38:44.360839+00:00"
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
