# Role
You are the reference-planning agent for a completed research run.
Goal: produce a grounded reference query plan that will drive automated citation retrieval for the paper stage.
Use grounded inputs only. Do not retrieve references yet.

This prompt must transfer across tasks and runs.
Infer all domain details, methods, benchmarks, architectures, and comparator families from the current artifacts only.
Do not assume any specific topic, benchmark, or prior example unless it appears in the current artifacts.

# Task Context
## Goal
**研究任务：网络干扰下 A/B 测试的全局平均处理效应估计**
**问题与动机**
在社交网络、交易市场等在线平台上做 A/B 测试时，用户之间存在相互影响（网络干扰）：
一个用户的结果不仅取决于自己是否被处理，还取决于网络中其他用户的处理状态。
此时平台真正关心的估计对象通常是**全局平均处理效应**（global average treatment
effect，GATE）：所有单元都被处理与所有单元都不被处理两种情形下平均结果之差。

标准的无干扰估计量（如简单的处理组/对照组均值差）在存在干扰时会产生系统性偏差。
一类常见思路是“基于回归的估计量”：用实验数据拟合一个把处理分配映射到结果的回归函数，
再用它预测“全体处理”和“全体对照”下的结果并取差。该思路在存在网络干扰时的估计误差
有多大、由什么决定，尚未被清楚地刻画。

**研究问题**
请你自行提出并完成一项研究，回答下面的问题：存在网络干扰时，基于回归的 GATE 估计量
实际能做到多准？它的估计误差由什么决定，哪些因素会影响它的表现，
结论在怎样的干扰机制和网络结构下成立、在怎样的条件下失效？你需要自己确定要考察的
因素、提出假设并检验。

你需要自己设计模拟环境（网络、结果生成机制、干扰形式）、对比的基线，以及评价估计质量
的指标（并说明选择理由），并如实报告正面与负面结果。
研究应主要基于合成结果与公开图数据，不需要真实平台的实验数据。

**成功的标准与约束**
成功的标准：结论要有证据支撑——可核查的分析或模拟证据，报告不确定性，并写明结论的
适用范围。支持、反驳或“视条件而定”的结论都可以接受；没有得到明确规律、或结果与预期
不符时，请如实报告。

约束：时间上限一周；仅用 CPU 即可完成主体研究（有 GPU 可用但不是必需）；数据为合成结果
与公开图，不需要账号或真实平台数据；产出是一篇研究论文及可复现的代码，具体要求见
`deliverable.md`，资源见 `resources.md`、`data.md`。

**起步文献清单**
以下文献均发表于 2024-10-16 之前，供你起步；你可以（也应当）自行检索更多相关工作。
取证日期：2026-10-27。

1. Aronow, P. M., & Samii, C. (2017). Estimating average causal effects under general
   interference, with application to a social network experiment. *Annals of Applied
   Statistics*. https://arxiv.org/abs/1305.6156
   说明：提出基于随机化的网络干扰下因果效应估计框架，给出逆概率加权估计量与方差估计，并用美国学校社交网络数据做模拟和田野实验。

2. Ugander, J., Karrer, B., Backstrom, L., & Kleinberg, J. (2013). Graph cluster
   randomization: network exposure to multiple universes. *KDD 2013*.
   https://arxiv.org/abs/1305.6979
   说明：提出利用图聚类做随机分配的实验设计，刻画“网络暴露”，给出 Horvitz–Thompson 估计量并分析其方差。

3. Eckles, D., Karrer, B., & Ugander, J. (2017). Design and analysis of experiments in
   networks: Reducing bias from interference. *Journal of Causal Inference*.
   https://arxiv.org/abs/1404.7530
   说明：评估网络实验中的设计方法（含图聚类随机化）和纳入邻居处理信息的分析方法，给出理论条件并用模拟考察其表现。

4. Chin, A. (2019). Regression adjustments for estimating the global treatment effect in
   experiments with interference. https://arxiv.org/abs/1808.08683
   说明：提出用拟合模型预测“全体处理”和“全体对照”下的结果来估计全局平均处理效应的回归调整估计量，给出线性模型下的性质和基于重抽样的推断，并再分析了一项天气保险采纳实验。

5. Karrer, B., et al. (2021). Network experimentation at scale.
   *KDD 2021*. https://arxiv.org/abs/2012.08591
   说明：介绍在 Facebook 部署的聚类随机化网络实验系统，包括设计与估计流程，并给出两个案例研究。

6. Cortez, M., Eichhorn, M., & Yu, C. L. (2022). Staggered rollout designs enable causal
   inference under interference without network knowledge. *NeurIPS 2022*.
   https://arxiv.org/abs/2205.14552
   说明：提出让处理逐步分配给随机子集的分阶段上线设计，在干扰限于低阶邻居交互的假设下给出不依赖网络结构信息的总处理效应无偏估计量及方差界。

7. Han, K., & Ugander, J. (2023). Model-based regression adjustment with model-free
   covariates for network interference. https://arxiv.org/abs/2302.04997
   说明：提出依次生成并选择基于图和基于处理的协变量的回归调整方法，给出基于分块自助法的置信区间，并在半合成实验和一项真实实验数据上检验。

8. Optimized covariance design for AB test on social network under interference.
   (2023；作者见页面) *NeurIPS 2023*. https://arxiv.org/abs/2311.14042
   说明：在一跳干扰模型下推导 Horvitz–Thompson 估计量的偏差与方差，并提出通过优化处理分配向量的协方差矩阵来设计随机化方案，附模拟研究。

9. Traud, A. L., Mucha, P. J., & Porter, M. A. (2012). Social structure of Facebook
   networks. *Physica A*. https://arxiv.org/abs/1102.2166
   说明：分析 100 所美国高校的 Facebook 好友网络（Facebook100）的社会结构，包括用户属性的同配性和社区划分；文中所用数据已公开。

10. Defferrard, M., Bresson, X., & Vandergheynst, P. (2016). Convolutional neural networks
    on graphs with fast localized spectral filtering. *NeurIPS 2016*.
    https://arxiv.org/abs/1606.09375
    说明：把卷积神经网络推广到图结构数据，基于谱图理论设计快速的局部卷积滤波器，在 MNIST 和 20NEWS 上做实验。

11. Kipf, T. N., & Welling, M. (2017). Semi-supervised classification with graph
    convolutional networks. *ICLR 2017*. https://arxiv.org/abs/1609.02907
    说明：提出一种直接作用于图结构数据的卷积神经网络变体，用于半监督节点分类，在引文网络和知识图谱数据集上做实验。

**数据与获取方式**
本任务**不依赖真实平台实验数据**：处理分配由你按设计随机生成，结果由你设定的
干扰机制合成。需要的只是图（网络拓扑）。取证日期：2026-10-27。

**可选公开图**
两个图均为可选，页面与下载均无需账号。

| 图 | 来源 | 规模 | 许可/条款 | 版本/快照 | 需要账号 |
| --- | --- | --- | --- | --- | --- |
| Facebook100 之 Stanford3（socfb-Stanford3） | Network Repository：https://networkrepository.com/socfb-Stanford3.php ；直接下载 https://nrvis.com/download/data/socfb/socfb-Stanford3.zip（HTTP 200，约 1.6 MB 压缩包）。数据出处：Traud, Mucha & Porter (2012)，https://arxiv.org/abs/1102.2166 | 11,586 个节点、568,309 条边（无向、无权；压缩包内为 Matrix Market 格式的 `socfb-Stanford3.mtx`，文件头 `11586 11586 568309`；Network Repository 页面统计为 11.6K 节点、568.3K 边） | CC BY-SA（署名—相同方式共享）：https://networkrepository.com/policy.php 写明 “All data are licensed under a Creative Commons Attribution-ShareAlike License”（2026-10-27 核实）；数据页面要求引用 Rossi & Ahmed, *The Network Data Repository with Interactive Graph Analytics and Visualization*, AAAI 2015，数据出处另引 Traud, Mucha & Porter (2012) | 压缩包 `socfb-Stanford3.zip` 1,649,740 字节，服务器 Last-Modified 为 2024-01-08；包内 .mtx 文件时间戳 2012-12-30；sha256 `b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d` | 否 |
| SNAP ego-Facebook | https://snap.stanford.edu/data/ego-Facebook.html | 4,039 节点，88,234 边（`facebook_combined.txt.gz` 共 88,234 行边表，已核对；无向）。该文件由多个自我网络合并而成，含自我节点本身（页面说明） | 页面未列许可证，只给出引用来源：J. McAuley and J. Leskovec, *Learning to Discover Social Circles in Ego Networks*, NIPS 2012（2026-10-27 核实）；使用时请引用该文 | `facebook_combined.txt.gz` 218,576 字节，Last-Modified 2013-07-16；sha256 `125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7` | 否 |

**合成图**
也可自行生成：随机块模型（SBM）、Barabasi-Albert 无标度图、Watts-Strogatz 小世界图等
（networkx 等库即可）。

**说明**
- 模拟所需的处理分配机制、结果生成机制及其参数均需你自行设计并写入论文。
- 不要求、也不需要下载任何大文件。

**资源与预算**
- 计算：仅 CPU 即可完成研究的主体部分；有一张消费级 GPU 可加速，但不是必需。
  总算力预计在数十 CPU 小时量级（估算，未实测），可按预算缩小实验规模。
- 内存：8–16 GB 足够；图数据为 MB 级（估计，未实测）。
- 存储：数据与运行输出预计小于 1 GB（估计，未实测）。
- 时间上限：一周（从开始到提交完整论文与代码）。
- 估算依据：数据为 MB 级的图（1 万至数万节点量级）；单次模拟（一次随机分配、合成结果
  与估计）从毫秒到分钟量级；完整研究需在多种设置下重复多次，总量约数十 CPU 小时。
  以上为按量级的估算，未实测。
- 网络：可以联网检索文献与下载公开图，但须遵守 deliverable.md 中的访问限制。
- 费用：本任务本身不需要付费数据或付费服务。

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
    "evidence": "Bootstrap manifest combined_score=0.9909514004064053 and correct=true; histories empty; supplied incumbent source path unavailable. No research computation or external search performed. Alternatives were a broad architecture sweep, cluster-design optimization, and a neural replacement; none has a demonstrated bottleneck advantage. Authored idea_bundle.json and identical target_rubrics.json rubric array. Canonical local memory is ideas/01_endpoint_contrast_audit_with_hidden_spillover_twins/memory.md, the only cycle-local memory target used.",
    "idea_id": "cycle01_endpoint_contrast_audit",
    "next_action": "Inspect only the documented candidate interface and allowed incumbent artifacts; preserve accepted behavior; implement paired spillover worlds and contrast diagnostics, execute the preregistered CPU study, and regenerate paper artifacts with uncertainty and negative findings. Stop reason: idea_bundle_ready; evaluation pending.",
    "rubrics": [
      {
        "id": "incumbent_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "contrast_estimability_and_amplification",
        "type": "implementation"
      },
      {
        "id": "prespecified_hidden_endpoint_twins",
        "type": "implementation"
      },
      {
        "id": "replicate_level_reproducible_evidence",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Endpoint Contrast Audit with Hidden Spillover Twins; gate=kept; trigger=none; reason=An untested proposal supplies no evaluated basis for changing distilled conclusions.",
    "tags": [
      "cycle_1",
      "worker_0",
      "hypothesis_only",
      "gate=kept",
      "trigger=none"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle01_endpoint_contrast_audit_attempt_01",
    "event": "candidate_cloned",
    "idea_id": "cycle01_endpoint_contrast_audit",
    "limitation": "No simulation execution, endpoint truth, assignment probabilities or artifact exchange permitted",
    "program_id": "program_1",
    "scope": "internal endpoint contrast audit; preserve baseline predictions and RPC"
  },
  {
    "attempt_id": "cycle01_endpoint_contrast_audit_attempt_01",
    "changed_files": [
      "program_1/src/program.py",
      "program_1/src/AUDIT_SCOPE.md"
    ],
    "contract": "unchanged program_spec and response schema; baseline estimator preserved",
    "event": "candidate_ready",
    "idea_id": "cycle01_endpoint_contrast_audit",
    "implemented": "actually called internal estimability, OLS amplification, separate ridge weights and fixed-bump support diagnostics",
    "limitations": "No paired-world simulation, probability estimate, empirical calibration, paper PDF or score-improvement claim",
    "program_id": "program_1",
    "validation": "static filesystem checks only; no project execution or evaluation"
  },
  {
    "attempt_id": "cycle01_endpoint_contrast_audit_attempt_01",
    "code_executed": false,
    "entrypoint_exists": true,
    "evaluator_artifacts_created": false,
    "event": "final_static_confirmation",
    "files": [
      "program_spec.toml",
      "src/program.py",
      "src/AUDIT_SCOPE.md"
    ],
    "idea_id": "cycle01_endpoint_contrast_audit",
    "note": "Standalone patch retry succeeded after combined shell editing failure; self-contained merge now complete; stopping",
    "program_id": "program_1",
    "spec_unchanged": true
  },
  {
    "attempt_id": "cycle01_endpoint_contrast_audit_attempt_01",
    "evidence": "combined_score=0.9909514004064053, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.9909514004064053, \"control_success_fraction\": 1.0, \"correct\": true, \"failed_episode_fraction\": 0.0, \"mean_absolute_capped_normalized_bias\": 0.6191122046076132, \"mean_capped_normalized_rmse\": 0.8400433426068793}",
    "idea_id": "cycle01_endpoint_contrast_audit",
    "metrics": {
      "combined_score": 0.9909514004064053,
      "control_success_fraction": 1.0,
      "correct": true,
      "failed_episode_fraction": 0.0,
      "mean_absolute_capped_normalized_bias": 0.6191122046076132,
      "mean_capped_normalized_rmse": 0.8400433426068793
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:03:03.148305+00:00"
  },
  {
    "evidence": "Prior candidate correct=true and combined_score=0.9909514004064053, equal to incumbent; recorded implementation kept predictions unchanged. Read the public contract and baseline source at ../../.baseline-seed-ic701viu/program_0/src/program.py after the manifest absolute path proved unavailable. Only graph, covariates, observed assignment/outcomes and model controls are available; no endpoint truths or design probabilities. Alternatives were repeated diagnostics, unsupported in-RPC paired-world simulations, and an unnecessarily large model search. Authored matching idea_bundle.json and target_rubrics.json. The only cycle-local memory target used is ideas/02_nonbacktracking_two_hop_regression_with_invariant_gcv/memory.md; no alternate or staging memory was created. No task program, evaluator or exploratory computation was run.",
    "idea_id": "cycle02_nonbacktracking_two_hop_gcv",
    "next_action": "Implement called sparse two-hop features and the small GCV-selected ridge family under the unchanged RPC; then obtain authorized correctness and comparative evidence, retain negative results and leave broader unexecuted paper/simulation requirements explicitly outstanding. Stop reason: idea_bundle_ready; evaluation pending.",
    "rubrics": [
      {
        "id": "incumbent_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "nonbacktracking_two_hop_features",
        "type": "implementation"
      },
      {
        "id": "invariant_regularized_gcv_selection",
        "type": "implementation"
      },
      {
        "id": "endpoint_prediction_dispatch_and_constant_guard",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Nonbacktracking Two-Hop Regression with Invariant GCV; hypothesis: sparse nonbacktracking two-hop features with deterministic observed-outcome GCV can improve endpoint regression under low-order spillovers. gate=kept; trigger=none; reason=The diagnostic-only attempt and source contract clarify available actions but provide no comparative scientific evidence for promoting or rejecting the proposed estimator family.",
    "tags": [
      "cycle_2",
      "worker_0",
      "hypothesis_only",
      "gate=kept",
      "trigger=none"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle02_nonbacktracking_two_hop_gcv_attempt_01",
    "details": "Cloned program_0; inspected documented RPC. Plan six observed-data GCV ridge bases with sparse nonbacktracking walk exposure. No code execution or evaluation.",
    "event": "implementation_started",
    "idea_id": "cycle02_nonbacktracking_two_hop_gcv",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle02_nonbacktracking_two_hop_gcv_attempt_01",
    "changed_files": [
      "program_1/src/program.py"
    ],
    "cloned_files": [
      "program_1/program_spec.toml",
      "program_1/src/program.py"
    ],
    "event": "candidate_ready",
    "execution": "None: tests and evaluation prohibited in this stage",
    "idea_id": "cycle02_nonbacktracking_two_hop_gcv",
    "implementation": "Sparse multiplicity-weighted nonbacktracking two-hop exposure; six fixed simple-first bases; centered/scaled SVD ridge with analytic observed-outcome GCV; saved preprocessing; constant guard; actual RPC dispatch wired",
    "limitations": "No measured improvement or runtime verification; predictive GCV does not establish endpoint optimality or dependent-data inference; full research deliverables not completed in candidate-only stage",
    "memory_files": [
      "./memory.md",
      "../../memory.md",
      "../../memory.jsonl"
    ],
    "program_id": "program_1",
    "static_checks": "Spec cmp identical; only spec and source under program_1; no evaluator artifacts; later-candidate glob had no matches",
    "tool_limitation": "apply_patch unavailable; direct file editing used"
  },
  {
    "attempt_id": "cycle02_nonbacktracking_two_hop_gcv_attempt_01",
    "evidence": "combined_score=None, correct=False; evaluation failed: exit=1; cause unavailable; search metrics (data): {\"combined_score\": null, \"correct\": false}",
    "idea_id": "cycle02_nonbacktracking_two_hop_gcv",
    "metrics": {
      "combined_score": null,
      "correct": false
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:11:38.369763+00:00"
  },
  {
    "evidence": "Read supplied skills/task/history/memory and documented incumbent source at ../../.baseline-seed-ic701viu/program_0/src/program.py. Cycle 1 preserved predictions and tied incumbent; cycle 2 has correct=false, no score, exit=1 and unknown cause, so no protocol-repair or estimator-rejection conclusion follows. Available observations are graph/covariates/assignment/outcomes; controls are estimator and three prediction rows. Alternatives included diagnostic repetition, unsupported in-RPC simulations and ordinary GCV. Wrote matching idea_bundle.json and target_rubrics.json with fixed-grid endpoint-risk selection, row-space/residual-df guards, incumbent fallback and constant-output dispatch. Risk rationale is conditional on correct linear reference and iid Gaussian noise and does not justify unbiased selected-risk reporting. Only canonical local memory ideas/03_endpoint_contrast_sure_for_exposure_regression/memory.md was targeted; no alternate or staging memory was created. No evaluator internals, external literature, candidate/evaluator execution or numerical probes were used.",
    "idea_id": "cycle03_endpoint_contrast_sure",
    "next_action": "Implement the called endpoint-SURE fit/predict path under the unchanged RPC, then obtain authorized acceptance and comparative evidence; isolate tuning with same-reference GCV, retain negative results and uncertainty, and leave unexecuted research/paper deliverables explicitly outstanding. Stop reason: idea_bundle_ready; evaluation pending.",
    "rubrics": [
      {
        "id": "incumbent_combined_score_improvement",
        "type": "metric"
      },
      {
        "id": "endpoint_anchored_reference_features",
        "type": "implementation"
      },
      {
        "id": "estimable_reference_and_noise_guard",
        "type": "implementation"
      },
      {
        "id": "endpoint_contrast_risk_selection",
        "type": "implementation"
      },
      {
        "id": "endpoint_sure_dispatch_and_constant_guard",
        "type": "implementation"
      }
    ],
    "scope": "idea",
    "step": "idea",
    "summary": "Selected Endpoint-Contrast SURE for Exposure Regression: estimate fixed-penalty endpoint-contrast risk to tune a small exposure regression rather than optimize observed prediction error. gate=kept; trigger=none; reason=No new comparative result or established failure cause supports a distilled recommendation; endpoint-risk tuning remains an explicitly conditional analytical hypothesis.",
    "tags": [
      "cycle_3",
      "worker_0",
      "hypothesis_only",
      "gate=kept",
      "trigger=none"
    ],
    "timestamp": "2026-11-07"
  },
  {
    "attempt_id": "cycle03_endpoint_contrast_sure_attempt_01",
    "changes_planned": [
      "program_1/src/program.py"
    ],
    "event": "implementation_started",
    "execution": "not_run_stage_prohibited",
    "idea_id": "cycle03_endpoint_contrast_sure",
    "program_id": "program_1"
  },
  {
    "attempt_id": "cycle03_endpoint_contrast_sure_attempt_01",
    "event": "candidate_ready",
    "execution": "not_run_stage_prohibited",
    "files_changed": [
      "program_1/src/program.py"
    ],
    "idea_id": "cycle03_endpoint_contrast_sure",
    "implementation": "fixed quadratic exposure reference with estimability-guarded endpoint-contrast risk tuning, incumbent fallback, and exact constant bypass",
    "outstanding": [
      "matched-seed incumbent and same-reference GCV comparisons",
      "mechanism and noise stress studies",
      "paper and reproducibility deliverables"
    ],
    "performance": "unmeasured",
    "program_id": "program_1",
    "specification": "unchanged",
    "validation": "filesystem checks only; entrypoint exists; no evaluator artifacts"
  },
  {
    "attempt_id": "cycle03_endpoint_contrast_sure_attempt_01",
    "evidence": "combined_score=0.9933739062995568, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.9933739062995568, \"control_success_fraction\": 1.0, \"correct\": true, \"failed_episode_fraction\": 0.0, \"mean_absolute_capped_normalized_bias\": 0.4963629031455466, \"mean_capped_normalized_rmse\": 0.6969233455876764}",
    "idea_id": "cycle03_endpoint_contrast_sure",
    "metrics": {
      "combined_score": 0.9933739062995568,
      "control_success_fraction": 1.0,
      "correct": true,
      "failed_episode_fraction": 0.0,
      "mean_absolute_capped_normalized_bias": 0.4963629031455466,
      "mean_capped_normalized_rmse": 0.6969233455876764
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-07T03:19:35.773288+00:00"
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
