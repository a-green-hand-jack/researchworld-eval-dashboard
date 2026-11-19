# Brief: aggregation rules and targeted investment

This page is the context owner's live objective brief. The authoritative task is `world/idea-repo#1` and the frozen five files below. No result is established by this page: experiment-repo owns measurements, story-repo owns the study design, and paper-repo owns the report.

## Research question and non-negotiable task requirements

The objective asks what investment a developer needs to make a selected model rank first on public multi-task leaderboards, and how this varies by aggregation rule. The choice of investment metric and rules is open; clear definitions, testable claims, reproducible public-data evidence, and conditions of validity/failure are required. Training large models is neither required nor encouraged.

The supplied task text is quoted in full:

> # 研究任务：多任务排行榜的聚合规则与针对性投入
> 
> ## 背景与动机
> 
> 多任务基准（multi-task benchmark）已成为评估机器学习模型的核心基础设施：一个排行榜由多个子数据集组成，每个模型在各子数据集上得到分数，再通过某种聚合规则（例如取平均、取中位数等）得到总排名。排行榜名次影响模型的采用、论文发表与资金，因此开发者有动机采取策略性行动，使某个特定模型的名次上升。其中一类行动是：把部分子数据集的相关数据纳入自己模型的训练，从而提高目标模型在这些子数据集上的得分。
> 
> 这类针对性投入在多大程度上能改变排行榜名次，以及这与所采用的聚合规则有何关系，目前缺少系统的分析。
> 
> ## 研究问题
> 
> 在公开的多任务排行榜上，开发者要通过上述针对性投入使某个目标模型排到第一，需要怎样的投入？这种投入如何随聚合规则变化？请自行界定"投入"的含义和度量方式，并给出你的结论。
> 
> 结论可以是支持、反驳或视条件而定的。能回答这一问题的证据应当：对所用概念和假设给出清晰定义；有可检验的论断；在公开榜单数据上得到可复现的实证支持；并说明结论在什么条件下成立、在什么条件下不成立。
> 
> ## 范围说明
> 
> - 聚合规则有哪些、研究哪些，由你自行界定。
> - 你需要自行选择并明确论证所需的建模假设，说明其合理性与局限。
> - 研究方式（理论分析、实证分析或二者结合）由你自行选择；无论采用哪种方式，所用的榜单数据必须公开，结论所依据的结果须可复现。
> - 不要求也不鼓励实际训练大模型；所需数据均为已公开的评测结果。
> 
> ## 约束与产出
> 
> - 数据：公开的多任务评测榜单得分（来源见 `data.md`），无需账号。
> - 资源与时间：仅 CPU，不需要 GPU；时间上限一周（细节见 `resources.md`）。
> - 产出：一篇完整的研究论文及可复现的代码（要求见 `deliverable.md`）。

## Deliverable and integrity requirements (quoted)

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

## Resource conditions (quoted)

> # 资源与预算
> 
> - 计算：仅 CPU 即可，不需要 GPU。处理的数据是已公开的评测得分表（任务数约 10^1–10^2，模型数约 10^1–10^4），数据量和单次计算量都很小。
> - 估算：全部计算在单台 8 核 CPU 上合计不超过 4 CPU 小时（按数据规模估计，未实测；含重复运行）。
> - 内存：16 GB 以内足够。存储：10 GB 以内（主要为下载的汇总数据）。
> - 时间上限：一周（含检索、实验与写作）。
> - 付费 API：本任务本身不需要调用付费 API。
> - 估算依据：只处理已公开的评测得分，不训练或评测任何模型。

## Supplied public data: implications

`data.md` (evidence date 2026-10-27) supplies two complementary score sources:

- HELM MMLU, required default release **v1.13.0**, date 2025-01-10, 303 summary files about 11.4 MB. Use summary score tables in `groups/json/`; run-level logs are optional and should not be mirrored wholesale. An alternative version requires a reason in reproduction instructions. The 57 MMLU subjects permit fine-grained task targeting, but extracting an equally weighted subject matrix must be distinguished from the site's own aggregate metric/weighting. Preserve counts and score uncertainties if actually used.
- Open LLM Leaderboard `contents` pinned at **9c09a7cae43334062a82cb164f2ef255013dafa2** (2025-03-20), about 4,576 model rows and six aggregate task columns (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO), plus Raw columns. Pin snapshot; distinguish raw accuracy from displayed normalized scores. Its task granularity is six benchmark families, not HELM's subject granularity. Numbers of selected tasks and fractions of task sets therefore require both counts and denominators.
- Open LLM `results` at **aa81ecc38fdc5708254b833923368970efdf5ef5** (2025-03-15), about 10,510 JSON files and 13.6 MB, is an allowed richer alternative containing subtasks. Do not imply those subtask files were analyzed when using only `contents`.
- `cais/mmlu` is optional; it is not a requirement to run models or access question text.
- Record actual dates, URLs, versions, checksums, parsing decisions, exclusions, duplicate models/runs, and complete-case cohort construction. Counts in the supplied description are provenance hints, not results to copy into the paper.
- Both leaderboard score datasets have **no separately declared data license** in the supplied audit. Apache-2.0 on HELM code, a model's `Hub License`, and MIT on optional MMLU are not permissions for all score-data redistribution. Report this distinction. Use public unauthenticated downloads and reproducible acquisition instructions; do not invent a license.

## Definitions and boundaries the study must settle

1. Define a target, fixed competitor cohort, task score direction/scale, aggregation formula, score ceiling and allowed intervention. Nonnegative gains on selected target cells with all other cells fixed are a **score-space counterfactual**, not evidence of attainable training effects.
2. Define investment precisely. Unit cost per affected task measures support size/sparsity. It does not measure examples, dollars, FLOPs, elapsed training time, or ethical severity. A gain fraction toward a ceiling is a second intervention-strength axis, not a causal dose-response estimate.
3. Define first place: co-first versus strict first, tolerances, incumbent winners (zero budget), and infeasibility under caps. Strict first may remain impossible at full ceiling when a competitor already attains the optimum; ties and numerical tolerance matter.
4. Compare rules on the same target/cohort/scenario. A rule's incumbents differ; paired comparisons should distinguish all targets from common challengers (excluding the union of rule winners). Report rather than silently discard infeasible targets.
5. Rank-based aggregation requires reranking affected tasks against competitors after a target changes. Freezing original competitor rank scores changes the rule. Average task rank/Borda also needs an explicit tie convention and sensitivity to model duplication/composition.
6. Mean, median, geometric mean, minimum and rank aggregation encode different value choices. Multiplicative aggregation needs a zero/positivity convention; bounded normalized scores can change the meaning of ceilings. No universally robust rule follows just from one empirical ordering.
7. Exact combinatorial optima and deterministic full-cohort summaries do not have optimization sampling error. Random-task baselines require Monte Carlo uncertainty. Task-resampling ranges measure dependence on the chosen task composition; without item-level scores/model repetitions they are not uncertainty about model generalization or training gains.
8. Dependence between subject gains, cross-task transfer/forgetting, different task costs, measurement noise, competitor adaptation, and realistic learning curves delimit applicability. Strong contamination/behavioral claims require evidence outside a score table.

## Starter literature and independence guardrail

`starter_literature.md` names eleven allowed sources: Hendrycks et al. MMLU; Suzgun et al. BBH; Liang et al. HELM; Dehghani et al. Benchmark Lottery; Lanctot et al. social choice evaluation; Singh et al. Leaderboard Illusion; Zhou et al. benchmark cheating; Yang et al. rephrased contamination; Chen et al. strategic post-training; Gao et al. evaluation harness; and the Brandt et al. Handbook of Computational Social Choice. These are starting points rather than proof of novelty. Bibliographic identities and substantive reading notes have been checked against direct source documents and published as wiki `Literature` and release `context-v1`. All nine arXiv identities match; the evaluation-harness DOI is a software-release record with a different title and author order from the generic framework citation. See the companion source register for the correction and actual reading depth.

The task forbids access to the existing paper on this exact research question, all its forms, and any pages citing/discussing/reproducing it; it also forbids trying to infer its identity/results. Accordingly this context work uses direct supplied source URLs, no topical search for the withheld paper, no citing-paper graph or review/aggregation pages. Accidental exposure must be logged with location and reading extent; no encounter has occurred as of this initial brief. A supplied identifier can be incorrect: do not cite an unrelated retrieved paper under supplied metadata.

## Required evidence and handoff boundaries

The final study needs at least a coherent, reproducible answer across explicitly defined rules, target cohorts, intervention costs/caps, and win criteria; data/normalization audit; optimizer correctness evidence; appropriate uncertainty; and failure cases. The objective does not prescribe five rules, two datasets, a particular solver, universal robustness, or training experiments: the plan owner chooses defensible coverage without weakening the required answer.

- story-repo: settles analysis questions/comparisons and every delivered-path owner; receive this brief and source notes.
- idea-review-repo: judges feasibility and claim/evidence match using this brief; receives source limits and any unresolved requirement.
- experiment-repo: owns score matrices, optimizer/analysis, validation and uncertainty, supplied through the plan owner; no numerical result is certified here.
- venue-repo: latest official ICML/ICLR/NeurIPS template, page limit, checklist and venue-specific compliance.
- figtab-repo: figures/tables supporting final claims with checkable axes, denominators, ties and infeasibility.
- paper-repo: complete manuscript/PDF/source plus reproduction root, translating the evidence with accurate causal limits.
- internal/external review: independently assess supported claims and task completion.

## Frozen input provenance

All five task files were read in full on 2026-11-03. SHA-256 values come from the initial-state manifest and were independently checked locally; see the repository `notes/frozen-inputs.json`. The files are TASK.md (question/scope), data.md (data pointers/provenance constraints), deliverable.md (format/evaluation/integrity/access rules), resources.md (CPU/time ceilings), starter_literature.md (allowed starting sources). Nothing is held out for model evaluation in these files; the explicit withheld material is prior research, not an evaluation split.

## Unresolved context items

The achievable relation between score increments and training inputs is unmeasured, and cannot be established from these public score tables alone. The study must label that boundary rather than inventing it. Direct-source identity checks and targeted substantive reading are complete for this context handoff; see wiki `Literature` for exact reading scope and the checked bibliography. This is not an exhaustive review or a novelty-priority certification. I read story-repo `study/plan.md` at `90c02774a3a7b0f812957a5d39f131f80fa8cea2` and found its stated score-space estimand faithful to the objective. No additional analysis requirement arises from context for that estimand. Final venue edition and final delivery compliance remain with their owners.

## Settled coordination after reply checks

The context owner checked the complete replies to story-repo#9 and idea-review-repo#4, the full `feasibility-v2` release memo, and the updated study plan at story-repo `bcdf9eb10b3e0606bc463c7b489b2872bad4d569` against the objective. Both requests are answered: every final requirement has an owner, and the bounded score-space study needs no additional analysis requirement from context or feasibility. Context supplies checked materials through wiki/releases; paper-repo owns their final manuscript/bibliography integration, with no context-owned manuscript directory. The plan now incorporates venue-repo's declared NeurIPS 2026 choice; venue/report/review owners verify final template, pages and checklist.

The plan's pending-literature wording refers to the supply already completed in wiki Literature and release context-v1, with source hashes, reading scope and the software DOI identity correction. The context handoff is complete. Feasibility and this reconciliation certify neither measured training effects nor numerical correctness nor final report acceptance. No request needs reopening for the checked scope; material changes still require reconsidering its assumptions and claims.
