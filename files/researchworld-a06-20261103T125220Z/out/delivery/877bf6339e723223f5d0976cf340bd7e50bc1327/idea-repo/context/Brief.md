# Brief

## Governing question and status

The study asks what a score means after a configuration has been selected using the same finite question set, how the gap from fresh-question performance depends on the setting, whether decisions change, and which reporting alternatives withstand empirical evaluation. The organization must deliver a complete research paper and reproduction code, including an actual newly run LLM experiment on the supplied real benchmark. Synthetic experiments alone do not satisfy the objective. Negative and conditional findings are acceptable.

This page is the context owner's requirements record. Story owns the plan, experiment owns analysis, figtab owns presentation, venue owns conference rules, paper owns manuscript integration, and review owners judge the delivery. Proposed checks here are context advice, not settled experimental results. All eleven permitted starter works have now been consulted directly at recorded versions, plus the pinned data card and Cawley–Talbot 2010. Exact reading scope, primary-source evidence and limits are in [Primary Sources](Primary-Sources), with the terminology/evaluation handoff in [Estimands and Evaluation](Estimands-and-Evaluation). Downloadable context materials and BibTeX are in the context release; no source PDFs are redistributed.

## Frozen requirements (verbatim)

The following text is copied from the five supplied files. Their paths, byte lengths, and SHA-256 digests are recorded in `provenance/frozen-inputs.json` in idea-repo. The Research objective issue repeats TASK.md and maps these inputs. These quotations, not a later plan, determine compliance.

### TASK.md

> # 研究任务：自动调优之后，报告的基准分数意味着什么
> 
> ## 背景与动机
> 
> 在大语言模型（LLM）的实际使用中，研究者常常在一个基准的题目上自动搜索提示词（prompt）
> 或由多个 LLM 调用组成的程序（pipeline），再把搜索得到的"最佳配置"在同一批题目上的得分
> 作为该系统的性能汇报。所用的自动搜索工具多种多样。
> 
> 这种做法引出一个统计问题：基准题目既被用来**挑选**配置，又被用来给该配置**打分**，因此
> 汇报的数字不一定反映系统在全新题目上的真实表现；基于这类汇报数字做出的比较和决定是否
> 可靠，也就不清楚。
> 
> ## 研究问题
> 
> 请围绕下面的问题开展一项完整的研究：
> 
> 1. 对一个先在有限题集上搜索配置、再把选出的配置拿去使用的系统，汇报的分数与它在全新
>    题目上的真实表现相差多少？差距受哪些因素影响？它是否会影响基于汇报分数做出的结论？
> 2. 能否设计更可靠的汇报方式？应如何通过实验检验它是否可靠？
> 
> ## 成功如何衡量
> 
> 结论需要有你自己运行的实验支持，并至少在一个真实 LLM 与真实基准的设置上检验；实验设计、
> 统计工具和理论分析的深度由你决定。结论可以是支持、反驳或视条件而定。
> 
> ## 关键约束
> 
> 资源约束：一周墙钟时间；以 CPU 为主，涉及 LLM 推理的实验可使用至多一张 24 GB GPU 或等价
> API 预算（详见 `resources.md`）；可用数据见 `data.md`；最终产出是一篇研究论文及复现代码
> （详见 `deliverable.md`）。

### data.md

> # 公开数据与获取方式
> 
> 核实日期：2026-10-27。
> 
> | 数据 | 获取 | 许可证 | 大小 | 账号 |
> | --- | --- | --- | --- | --- |
> | MMLU-Pro（多学科、每题 10 个选项的多项选择题；14 个学科类别，含分学科字段） | 数据集 https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro （固定到修订版 `b189ec765aa7ed75c8acfea42df31fdae71f97be`，2026-05-02）；可选：数据集附带的评测代码 https://github.com/TIGER-AI-Lab/MMLU-Pro | 数据集卡片标注 MIT；GitHub 仓库标注 Apache-2.0 | test 12,032 题 + validation 70 题；parquet 文件合计约 4.2 MB | 不需要（未设 gating，无需登录） |
> | 合成数据 | 自行用程序生成，规模与形式自定 | 无 | 极小 | 不需要 |
> 
> 说明：
> 
> - 真实实验需要自行用 LLM 对题目生成回答（包内不提供现成的模型输出）。可选择开放权重的
>   指令微调模型（用 vLLM、llama.cpp 或 transformers 在本地推理），或按预算调用外部 API；
>   模型输出可自行缓存复用。
> - 可选工具：DSPy（https://github.com/stanfordnlp/dspy ，MIT 许可证；2026-05-05 发布的
>   3.2.1 版），也可自行实现提示词/程序的搜索流程。许可证以仓库页面为准。
> - 合成实验完全不依赖外部数据，可在纯 CPU 上完成。

### resources.md

> # 资源与预算
> 
> - 时间上限：一周（墙钟）。
> - 模拟或合成实验（如采用）：仅需 CPU。估算依据：单次模拟的数据规模至多数十万个数值，
>   单次统计计算为毫秒到秒级；数千次重复模拟在多核 CPU 上约数小时（出题方粗略估计，未实测）。
> - 真实 LLM 实验：需要自行推理。可使用一张 GPU（24 GB 显存足够运行 7B-8B 量级的开放权重
>   指令模型，约 15-17 GB 权重）或等价的 API 预算；GPU 与外部 API 是否可用以实际运行环境为准。推理量粗算：总输出量在千万 token
>   量级时，用 7-8B 模型在一张 24 GB 卡上约需数小时；提示词/程序搜索工具自身的调用另计，量级相当。生成
>   回答与得分缓存后，后续 CPU 统计分析估计在 16 CPU 小时以内。
> - 存储与内存：每个 7-8B 开放权重模型约 15-17 GB，输出与得分缓存 < 1 GB；建议预留 100 GB
>   磁盘、32 GB 系统内存、8 核以上 CPU。
> - 不要求大规模训练；不需要多卡。
> - 估算说明：这些数字是出题方的粗略估计，未经实测；请在报告中给出你实际使用的计算量。

### deliverable.md

> # 产出要求
> 
> ## 提交物
> 
> 1. 一篇完整的研究论文（PDF 与 LaTeX 源文件）。从 ICML、ICLR、NeurIPS 中自选一个会议，使用该会议
>    最新一届的官方 LaTeX 模板，遵守其正文页数上限（参考文献、附录是否计入页数按该会议的规定）；
>    该会议要求随文提交的 checklist（例如 NeurIPS 的 paper checklist）一并填写。论文至少包含摘要、
>    引言、相关工作、方法、实验、讨论与局限、参考文献。
> 2. 全部代码与复现说明：环境与依赖版本、数据获取步骤和所用数据的版本、随机种子、运行命令和预计
>    耗时，以及论文中每张表、每张图由哪个脚本生成。
> 
> ## 评审标准
> 
> 论文按所选会议主会的审稿标准评审，重点看：
> 
> - 新颖性与定位：贡献是什么，与已有工作的关系和区别是否讲清楚；
> - 严谨性：方法和实验设计是否合理，基线、对照和消融是否恰当，是否报告不确定性（多次运行、
>   置信区间或显著性检验）；
> - 证据是否充分：实验能否支撑论文的每个结论，结论的适用范围是否写清楚；
> - 表达：论文是否清楚、完整，他人能否据此复现；
> - 局限：是否如实讨论方法和结论的局限与失效情形。
> 
> 负面结果、与预期不符的结果同样有价值；结论有充分证据、不确定性报告完整，比结论本身是正面还是
> 负面更重要。
> 
> ## 如实报告（禁止编造）
> 
> - 论文中的每个数字、每张表和每张图都必须来自你在本任务中实际运行、随附代码可以重新产生的结果；
>   不得编造数据或结果，不得用占位数字、估计值或"示意"性的合成结果冒充实测结果。
> - 失败的运行、与预期不符的结果和放弃的方案如实报告；因预算没有完成的实验写明未完成，不写成
>   已完成。
> - 只引用真实存在、你确实查阅过的文献，不得编造引用。
> 
> ## 不得访问的内容
> 
> 本任务的研究问题已有一篇已发表的论文研究过。为保证研究独立，不得检索、访问、阅读或使用：
> 
> - 那篇论文本身，及其任何镜像、预印本、摘要页、会议或评审页面、幻灯片、海报、视频、博客和代码
>   仓库；
> - 引用、讨论或复现那篇论文的任何页面，包括后续论文、综述、论文笔记、论文聚合站点和社交媒体
>   讨论。
> 
> 也不要尝试推测或检索那篇论文的标题、作者或结果。`starter_literature.md` 中的文献，以及与那篇
> 论文无关的其他公开文献、数据和代码，可以正常使用。若在检索中偶然遇到上述内容，立即停止阅读，
> 并在复现说明中如实记录遇到了什么、在哪里遇到、读到了多少。

### starter_literature.md

> # 起步文献
> 
> 以下条目均为 2025 年及以前公开的工作，仅作背景知识参考，不要求全部使用，也欢迎自行检索其他早期文献。
> 
> 1. Wang et al. *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding
>    Benchmark*. NeurIPS 2024 Datasets & Benchmarks（arXiv 2024-06-03）。
>    https://arxiv.org/abs/2406.01574
>    说明：提出一个多学科、每题 10 个选项的多项选择语言理解基准，在 MMLU 的基础上增加了推理型题目，并评测了多种 LLM。
> 2. Khattab et al. *DSPy: Compiling Declarative Language Model Calls into Self-Improving
>    Pipelines*. arXiv 2023-10-05。https://arxiv.org/abs/2310.03714
>    说明：提出以声明式模块编写 LLM 调用程序的编程模型，并提供按指定评价指标自动优化其提示词和示范样例的编译器。
> 3. Opsahl-Ong et al. *Optimizing Instructions and Demonstrations for Multi-Stage Language
>    Model Programs*（MIPRO）. EMNLP 2024（arXiv 2024-06-17）。https://arxiv.org/abs/2406.11695
>    说明：提出一种针对多阶段 LLM 程序同时优化指令和示范样例的方法，并在多个任务上与已有方法比较。
> 4. Polo et al. *Efficient multi-prompt evaluation of LLMs*. NeurIPS 2024（arXiv 2024-05-27）。
>    https://arxiv.org/abs/2405.17202
>    说明：提出用较少的评测样本估计 LLM 在大量提示词模板下的性能分布的方法，并在多个基准上实验。
> 5. Shi et al. *Efficient Prompt Optimization Through the Lens of Best Arm Identification*.
>    NeurIPS 2024（arXiv 2024-02-15）。https://arxiv.org/abs/2402.09723
>    说明：把提示词选择形式化为最佳臂识别问题，提出一种在有限评测次数下选择提示词的算法，并在多个任务上实验。
> 6. Sclar et al. *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design
>    or: How I learned to start worrying about prompt formatting*. ICLR 2024（arXiv 2023-10-17）。
>    https://arxiv.org/abs/2310.11324
>    说明：测量 LLM 对提示词格式的细微改动的敏感性，报告同一任务下不同格式之间的性能差异，并提出估计性能范围的方法。
> 7. Dwork et al. *Preserving Statistical Validity in Adaptive Data Analysis*. STOC 2015
>    （arXiv 2014-11-10）。https://arxiv.org/abs/1411.2664
>    说明：研究同一份数据被多次自适应地用于分析时统计推断的有效性，并提出基于差分隐私的保护方法。
> 8. Blum & Hardt. *The Ladder: A Reliable Leaderboard for Machine Learning Competitions*.
>    ICML 2015（arXiv 2015-02-16）。https://arxiv.org/abs/1502.04585
>    说明：提出名为 Ladder 的机制，用于机器学习竞赛榜单上对多次提交报告分数，并给出理论分析和实验。
> 9. Andrews, Kitagawa & McCloskey. *Inference on Winners*. NBER Working Paper 25456（2018）；
>    Quarterly Journal of Economics 139(1), 2024。https://www.nber.org/papers/w25456
>    说明：计量经济学论文，研究选出对象之后的统计推断问题，并给出应用示例。
> 10. Chernozhukov, Chetverikov & Kato. *Gaussian approximations and multiplier bootstrap for
>     maxima of sums of high-dimensional random vectors*. Annals of Statistics 2013
>     （arXiv 2012-12-31）。https://arxiv.org/abs/1212.6906
>     说明：统计学论文，给出高维随机向量之和的分布逼近的理论结果。
> 11. Berk, Brown, Buja, Zhang & Zhao. *Valid post-selection inference*. Annals of Statistics
>     41(2), 2013。https://doi.org/10.1214/12-AOS1077
>     说明：统计学论文，研究回归分析中先选模型、再做推断的问题，并给出相应的置信区间构造。

## Operational reading and ownership handoff

| Requirement | Context implication | Function that must deliver it |
| --- | --- | --- |
| Size and drivers of selection/reporting gap | Define the selected configuration, reported score, fresh-question target, sampling mechanism, and search exposure; distinguish expected optimism from a single realized gap. | story specifies; experiment measures |
| Consequences for conclusions | At least one explicit decision comparison (ranking, improvement, threshold, or interval claim) must be evaluated, not just average score gaps. | story specifies; experiment measures; figtab displays |
| More reliable reporting | Include a concrete alternative with a stated estimand and test its error/calibration and utility against naive reuse. Independence, simultaneous correction, or nested resampling have different assumptions. | story/experiment settle method and evaluation |
| Actual real LLM experiment | Newly generate real responses; cached responses may be reused after generation. Pin model, prompt configurations, extraction/scoring, benchmark revision, and sampling. A small model is allowed; 7–8B is a resource illustration, not a required model size. | experiment |
| Real benchmark | Pinned MMLU-Pro revision `b189ec765aa7ed75c8acfea42df31fdae71f97be`, 12032 test and 70 validation items per supplied description and pinned card. Verify actual loaded counts and identifiers; the card notes some items have fewer than ten options. | experiment |
| Depth and uncertainty | Multiple runs, confidence intervals, or significance checks must support each substantive conclusion. Synthetic mechanisms should isolate drivers without impersonating LLM measurements. | experiment; internal review checks |
| Limits and compute | One week; CPU emphasis; at most one 24 GB GPU or equivalent API; actual environment determines availability. Supplied runtime/hardware figures are unmeasured estimates, not available allocations or study measurements. | experiment records; feasibility judges |
| Full paper | PDF + LaTeX, latest official ICML/ICLR/NeurIPS template, official body page limit and required checklist. Minimum sections are mandatory. | venue supplies rules; paper delivers |
| Reproduction | Dependency versions, pinned data, seeds, commands, expected times, script-to-figure/table map, failures/abandoned runs, actual compute accounting. | each code owner; paper integrates |
| Citation truth and forbidden material | Cite only actually consulted real sources. Do not identify or seek the unnamed paper or any discussion of it. Read supplied older sources directly; avoid broad topical search. Record accidental exposure immediately and stop. | every position; idea supplies safe source provenance |

## Evidence and claim guardrails

1. Specify whether fresh questions mean independent draws from a population, a held-out finite benchmark pool, or a new stratified sample. An untouched audit pool estimates performance; its score is not literal known population truth. Benchmark contamination in pretraining is a distinct limitation.
2. For a fixed bank selected by empirical accuracy, define a selected-configuration target conditional on the selection data. Splitting and cross-validation may target a selection procedure trained on fewer examples instead of the final full-data-selected configuration. Do not equate these targets without justification.
3. Preserve the difference between a fixed candidate bank, sequential evaluation of that bank, and newly generated adaptive candidates that use item labels or feedback. A finite-bank bound cannot simply count the candidates generated after seeing the same labels.
4. Preserve pairing and category structure: prompt results share items; comparisons should not assume independent prompt scores. State pooled (question-weighted) versus macro/category weighting, tie handling, parser failures, and random-generation seeds.
5. Evaluate reporting quality with signed gap/bias, absolute or squared error as appropriate, interval coverage/width or bound failures, and a prespecified decision error. Quantify Monte Carlo uncertainty and independent-audit sampling uncertainty. Not every mechanism must worsen every setting.
6. Search breadth, question count, error correlation, and true-quality differences are plausible drivers. Correlation and quality dispersion can make an apparent universal winner's-curse claim false. These are evaluation factors to establish, not empirical findings yet.
7. Sufficient validation of a reporting correction requires repeating the whole selection/reporting procedure under an explicit data-generating scheme. Resampling only the already selected candidate can miss the selection step.
8. State any evaluation that conditions on one realized response matrix or reuses a shared audit pool. Overlapping repetitions are not new independent LLM runs. Adaptive inspection of the audit pool changes its role.

## Settled plan and handoff (updated 2026-11-06: Tier C)

The current primary real scope is the prespecified Tier C fallback, replacing Tier B after its elapsed-time gate failed. This update answers idea-repo #5 against objective #1 and all five frozen inputs, story's current `study/plan.md` / `study/real-scope-decision.md` at `a8e61b3e52d70052f090d193754c907a30ab0aec`, the full story #11 decision thread, and the accessible Feasibility v3 judgement. These are owner-supplied scope/validity statements; idea has not inspected experiment implementation, raw main answers/correctness, or a completed manuscript. Earlier context-v3's Tier B interpretation remains historical.

- **Primary target:** accuracy of the actual configuration chosen using the search questions. Expected procedure quality, oracle quality and smaller-search split targets remain distinct.
- **Current exact real target:** let `B` be the 12,032 pinned benchmark questions and `S_C` the entire retained 256-question search reservoir. For selected configuration `j_hat`, `theta_remaining(j_hat; S_C) = sum_{x in B minus S_C} Y_j_hat(x) / 11776`. The retained 512-question audit estimates this question-weighted remaining-benchmark accuracy under the fixed-C marginal partition design. The primary realized gap is observed search accuracy minus this target, estimated by search-minus-audit with audit sampling uncertainty. Selected-minus-default uses the same denominator and paired audit questions. All smaller n/K slices keep the complement of all 256 retained search items, including n < 256. Full-benchmark and unknown-question superpopulation accuracy are different targets.
- **Fixed-design conditioning:** marginalizing omitted original search/audit positions makes the retained audit uniform without replacement from `B minus S_C`. For a fixed C design, audit validity can condition on retained `S_C` and its search-selected winner; it must not additionally condition on the omitted original full-512-search identities. Omitted search labels and omitted candidates do not inform selection or calibration. The transformed simultaneous search interval instead has a fixed-design guarantee unconditional over retained-reservoir sampling. Analysis owns verifying both arguments and implementation.
- **Runtime-selected design guarantee:** outcome-blind timing need not be independent of question difficulty/correctness. Fixed-design guarantees alone do not establish coverage conditional on the observed fallback event. In story #11 comment 238, the analysis owner supplies a two-design union correction: construct the finite-population interval for each prespecified B/C design at per-design error `0.05/2 = 0.025` (including candidate multiplicity where needed). This gives a 97.5% interval within each fixed design and at least 95% unconditional coverage for the interval chosen by any B/C runtime rule, over the original random partition. It does not give coverage or audit unbiasedness conditional on the trigger. The protection applies separately to each scientific endpoint, not jointly across every reported endpoint. Idea records this owner-supplied correction, not an independent proof/implementation certification; story now confirms the correction and exposure manifest were committed before performance inspection at experiment `6fc477e68038324194b89302d3c43836be1d37bb`. No recording/approval hold remains; idea has not inspected those experiment files.
- **Evidence separation:** known-generating-truth simulation measures calibration and decision error. Whole-row iid with-replacement resampling from the 768 retained search+audit rows and four candidates measures calibration against that empirical distribution's known means; its original 95% CP methods/seeds remain separate from the two-design finite-population correction. A noisy real audit does not establish population truth, population coverage or a population false-superiority rate. Repeated cache draws reduce conditional Monte Carlo error, not audit question uncertainty. Ordinary iid/binomial search intervals retain their comparator labels.
- **Current real protocol:** Qwen2.5-1.5B-Instruct Q4_K_M and the frozen model/parser/decoding/prompt bank remain unchanged. Tier C retains original ordered partition `questions[::2]` with IDs/order/pools intact, search256/audit512 and first four prefix candidates `[0,10,14,13]`, default0. Primary n256/K4; slices n={16,32,64,128,256}, K={1,2,4}; 20,000 conditional-selection and cache repeats with original seeds. The paired-row bootstrap sensitivity uses n64/256,K4 with the original timed sizing rule; it is distinct from finite-population guarantees. Direct-answer generation and invalid-as-wrong scoring define this tested system, rather than feedback-adaptive prompt creation or the original benchmark's random-fallback scorer.
- **Generation and costs:** story/feasibility report a completed first shard of 6,144 answers, with 3,072 retained for the primary analysis. All 6,144 raw answers remain preserved and counted in actual compute; omitted outputs are excluded from primary selection/calibration. The request/decision report no raw-answer or correctness inspection before scope revision. No second shard or additional inference is required. Reported process elapsed about 75.66h failed the original deadline-minus-reserve rule; active-resource and CPU clocks have different boundaries and must not replace elapsed cost. No cause for their discrepancy is inferred here. The original deadline remains 2026-11-10 12:54:42 UTC. Feasibility v3 supports proceeding with the existing data; it is not validation of main results.
- **Comparisons and retained requirements:** naive reuse, simultaneous fixed-bank intervals, independent audit and matched-question/call splits still require calibration, point error, interval width, selected quality, cost and explicit superiority-decision comparisons. Conservative interval nonoverlap is not a generic paired test or claim-conditional false discovery rate. Reduced scope narrows search breadth and weakens precision; it does not waive any real analysis, diagnostics, uncertainty, reproduction, presentation, manuscript or independent final review. A null or imprecise result remains acceptable with full evidence.
- **Responsibilities and route:** experiment owns analysis, method validity, derivations and provenance; paper owns final methods/theory/background/related-work prose and bibliography. Idea supplies the current context release, retaining the original source notes, BibTeX and primary-source access records, with updated Brief/estimand advice as working material. Story relays this content to producing positions. No final manuscript path or separate theory deliverable is assigned to idea.
- **Delivery allocation:** story supplies `study/` and `.forgejo/CODEOWNERS`; experiment supplies `analysis/`; figtab supplies `figures/`, `tables/`, `presentation/`; venue supplies `venue/`; paper supplies manuscript/root build files and integration prose. Story reports the ownership allocation merged; paper's integrated CODEOWNERS is authoritative. Idea has not read paper code/PRs. Context and feasibility need no standalone final directory.

**Tier B history:** context-v3 recorded the cleared launch design K8/search512/audit1024, 12,288 planned responses, remaining-benchmark denominator 11,520 and empirical cache 1,536 rows. Its validation-based forecast and feasibility-v2 clearance were launch decisions, not achieved main costs. Those counts are no longer the primary analyzed scope; the original freeze/failed forecast and fallback reason must remain in final provenance.

Venue's accessible **Venue Requirements** page selects ICLR 2027 anonymous initial-submission format, with 9 main-text pages, the official template, and a required truthful AI use statement. It reports no separately required attached checklist found in the consulted official guidelines, AI policy or template, and explicitly did not inspect a live submission form. These are venue-owner findings, not independent verification by idea. They preserve the frozen obligation to include any checklist actually required; paper must implement the statements and check the built layout. Exact current and historical inspected materials are recorded in `provenance/handoff-reconciliation.json`.

## What remains to establish

- Primary-source evidence and comparison conventions are supplied. The general phenomenon, independent evaluation, nested resampling and simultaneous inference are established antecedents; the study must state its actual incremental contribution. Not all appendix proofs were audited and no exhaustive novelty search is claimed.
- The requested current-scope counts and fixed-design/post-selection conditioning distinctions are supplied above. Story retains responsibility for subsequent scope/target/ownership revisions. No extra context approval holds unblinding or analysis.
- Story confirms the derived Tier C manifest, interval correction and pre-unblinding exposure hashes are committed; no recording prerequisite remains pending. Analysis retains verification of the omitted-position sampling/interval implementation and delivery of actual completed analyses, audit/paired decisions, cache calibration, uncertainty and full cumulative costs/failures. Idea has not independently inspected that implementation or any main performance. The original task's full real-study requirement remains mandatory.
- Final presentation, manuscript implementation, actual page boundary, required statements, synchronized PDF/source, reproduction and independent version review remain their owners' checks. No delivered paper version was inspected in this reconciliation.

No main LLM or synthetic performance result is asserted on this page. Scope counts are design quantities; generation/timing and clearance are explicitly attributed to their owners. Any performance result requires analysis-owned run provenance.

## Primary-source implications now established

- MMLU-Pro's original scorer uses generated-answer extraction and a random fallback; report a changed parser/failure rule explicitly. Gold answer/rationale columns must not enter the generation inputs for held-out items.
- DSPy/MIPRO support data-driven prompt/program optimization, but their papers distinguish training/development/final evaluation roles. Do not attribute a misuse protocol to all optimizers.
- PromptEval performance quantiles and FormatSpread's range across prompts are different from confidence intervals for a selected configuration's fresh-question quality. Best-arm selection quality is separate from reporting calibration.
- Andrews–Kitagawa–McCloskey supplies a direct classical selected-winner estimand; PoSI supplies simultaneous protection over an a priori family; CCK supplies assumption-dependent covariance-aware maximum approximations. These are antecedents, not new methods established by this study.
- Dwork et al. and Ladder study controlled adaptive interactions. Their guarantees cannot be claimed after unrestricted access to the same labels/feedback. Ladder's practical parameter-free testing guide is explicitly heuristic in its paper.
- Cawley–Talbot shows why selection must be rerun inside outer evaluation and why selection bias can affect comparisons unequally. Nested evaluation usually targets the selection procedure at an inner sample size, not the exact final full-data-selected configuration.

Exact versions and source hashes are in `provenance/primary-sources.json`, source summaries in `literature/primary-source-notes.md`, and bibliographic entries in `literature/context-references.bib` in the released context package. Some consulted v1 titles differ from the later titles in the supplied starter list; the source notes state each difference. No claim relies on unseen final-version text.
