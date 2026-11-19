# Brief: sensitivity of pairwise-comparison leaderboards

This page is the context owner's requirement brief. Authority: Research objective world/idea-repo#1 and the five frozen files below. The original Chinese requirements take precedence over interpretation or plan. All five supplied files were read in full. No literature search for the withheld study is permitted.

## Research question and non-negotiable evidence

The objective asks how sensitive rankings estimated from pairwise comparisons are to small changes in the underlying comparisons, and whether measured sensitivity differs across datasets/evaluation designs. Researchers choose the operational question, datasets, metrics, method and baselines. The study must use **real data from at least two evaluation designs**, explicitly define edit magnitude and cross-dataset comparability, report supported conclusions with conditions and limitations, and accept negative/conditional findings. A single striking number does not satisfy the task.

The working operational question supported by the supplied analysis release is: under a fixed comparison schedule and a specified regularized BT fit, how many observed decisive outcomes can a heuristic reverse to reverse a selected initial leading-pair margin, how do random edits behave at the same budget, and how does this relate to baseline uncertainty and whole-ranking disagreement? This is a conditional data-sensitivity audit. The plan owner decides emphasis; context does not replace its division of work.

## Verbatim objective

# 研究任务：成对比较排行榜的稳定性

## 问题与动机

许多公开的模型评测排行榜（例如基于用户投票的大模型竞技场）通过聚合大量
「A 与 B 比较，谁更好」的成对偏好数据，用 Bradley-Terry 等成对比较模型拟合
每个参赛者的分数，再据此给出排名与置信区间。这些排名常被用于选型、发布宣传和
研究比较，但它们对底层比较数据的依赖程度并不清楚。

本任务研究：这类排行榜的排名对底层比较数据的小幅改动有多敏感（改动可能来自数据噪声，也可能来自
有人有意为之），以及这种敏感性在不同数据集、不同评测设计（例如众包投票、专家标注、模型裁判、
体育比赛）之间是否不同。

## 要求与证据标准

请自行界定可操作的研究问题，选择数据集和评价指标，设计并实现分析方法，用实验给出有证据支持的
结论。方法路线与对比基线由你自选。结论应基于至少两类不同评测设计的真实数据；改动的规模如何
度量、不同数据集之间如何比较，由你定义并说明理由。结论须说明适用条件与局限，而不只是给出单一
数字；"敏感性很小""视条件而定""与预期不同"同样是可以接受的结论。

## 约束

仅用 CPU、时间约一周、使用公开数据（见 `data.md`、`resources.md`）；产出为一篇研究论文及复现
代码（见 `deliverable.md`）。


## Verbatim deliverable, review and independence requirements

# 产出要求

## 提交物

1. 一篇完整的研究论文（PDF 与 LaTeX 源文件）。从 ICML、ICLR、NeurIPS 中自选一个会议，使用该会议
   最新一届的官方 LaTeX 模板，遵守其正文页数上限（参考文献、附录是否计入页数按该会议的规定）；
   该会议要求随文提交的 checklist（例如 NeurIPS 的 paper checklist）一并填写。论文至少包含摘要、
   引言、相关工作、方法、实验、讨论与局限、参考文献。
2. 全部代码与复现说明：环境与依赖版本、数据获取步骤和所用数据的版本、随机种子、运行命令和预计
   耗时，以及论文中每张表、每张图由哪个脚本生成。

## 评审标准

论文按所选会议主会的审稿标准评审，重点看：

- 新颖性与定位：贡献是什么，与已有工作的关系和区别是否讲清楚；
- 严谨性：方法和实验设计是否合理，基线、对照和消融是否恰当，是否报告不确定性（多次运行、
  置信区间或显著性检验）；
- 证据是否充分：实验能否支撑论文的每个结论，结论的适用范围是否写清楚；
- 表达：论文是否清楚、完整，他人能否据此复现；
- 局限：是否如实讨论方法和结论的局限与失效情形。

负面结果、与预期不符的结果同样有价值；结论有充分证据、不确定性报告完整，比结论本身是正面还是
负面更重要。

## 如实报告（禁止编造）

- 论文中的每个数字、每张表和每张图都必须来自你在本任务中实际运行、随附代码可以重新产生的结果；
  不得编造数据或结果，不得用占位数字、估计值或"示意"性的合成结果冒充实测结果。
- 失败的运行、与预期不符的结果和放弃的方案如实报告；因预算没有完成的实验写明未完成，不写成
  已完成。
- 只引用真实存在、你确实查阅过的文献，不得编造引用。

## 不得访问的内容

本任务的研究问题已有一篇已发表的论文研究过。为保证研究独立，不得检索、访问、阅读或使用：

- 那篇论文本身，及其任何镜像、预印本、摘要页、会议或评审页面、幻灯片、海报、视频、博客和代码
  仓库；
- 引用、讨论或复现那篇论文的任何页面，包括后续论文、综述、论文笔记、论文聚合站点和社交媒体
  讨论。

也不要尝试推测或检索那篇论文的标题、作者或结果。`starter_literature.md` 中的文献，以及与那篇
论文无关的其他公开文献、数据和代码，可以正常使用。若在检索中偶然遇到上述内容，立即停止阅读，
并在复现说明中如实记录遇到了什么、在哪里遇到、读到了多少。


## Supplied data: design, unit and provenance requirements

The dataset table supplies pinned commits and some file SHA-256 hashes, not a mandate to use every dataset. Arena-55k (57,477 battles) is crowdsourced anonymous preference; MT-Bench human and GPT-4 provide human annotation and model judging on a designed benchmark; NBA gives observed sports outcomes and requires removing the duplicate representation of each game. Arena-140k, model judges on Arena and WebDev are optional. The latter two have license qualifications in the frozen table; these are not interchangeable with unrestricted data. Raw data belong in work-directory `data/`, not the code repository or paper submission. Record exact sources, revisions, checksums, parsing, tie rules and exclusions.

# 公开数据与获取方式（取证日期 2026-10-27）

你可自行选择使用哪些数据。所有条目于 2026-10-27 核实页面可访问；版本列为 Hugging Face 数据集 commit 或 GitHub commit，均为固定快照。

| 数据 | 获取 | 版本 | 许可 | 规模与格式 | 需账号 |
| --- | --- | --- | --- | --- | --- |
| Chatbot Arena 人类偏好（约 5.7 万场，57,477 场） | https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k | commit `18c298340948c0e7f7727399fd459cca6ce0ca6f`（2024-05-17） | apache-2.0 | `train.csv`，184,175,071 字节，sha256 `0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2` | 否 |
| Chatbot Arena 人类偏好（更大版本，约 14 万场，可选） | https://huggingface.co/datasets/lmarena-ai/arena-human-preference-140k | commit `6322995ab34d7c2693e3f47dd13fa5caa0789a74`（2025-08-01） | cc-by-4.0 | 7 个 parquet 文件，合计约 1.6 GB（含对话文本） | 否 |
| MT-Bench 人类判断与 GPT-4 判断 | https://huggingface.co/datasets/lmsys/mt_bench_human_judgments | commit `f7d2896d2cc5d80f8b55c2bbc722613555233c25`（2023-07-20） | cc-by-4.0 | 两个 parquet：`human-…parquet` 738,612 字节（sha256 `4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769`），`gpt4_pair-…parquet` 649,996 字节 | 否 |
| 模型裁判在 Arena 对战上的判断（可选） | https://huggingface.co/datasets/potsawee/chatbot-arena-llm-judges | commit `638a7e3be3078e55d2eb0b789d34749747822c49`（2024-09-29） | 页面与元数据均未声明许可；README 说明数据抽取自 Kaggle 上的 LMSYS Chatbot Arena 竞赛训练集（该竞赛数据的 HF 版本 arena-human-preference-55k 声明 apache-2.0），使用前请自行确认条款 | `train.single-turn.json` 约 142 MB（49,938 条单轮对战）；含各裁判模型输出的全部文件约 0.58 GB | 否 |
| WebDev Arena 偏好（约 1 万场，可选） | https://huggingface.co/datasets/lmarena-ai/webdev-arena-preference-10k | commit `7c397e652ffb8c2384e6d71d21d8388c19365fdc`（2025-03-10） | other（见该数据集 LICENSE 与 README 协议） | `data/webdev-arena-preference-10k.json`，149,295,752 字节 | 匿名下载可成功；页面 README 含须同意的数据集许可协议，协议约束适用 |
| NBA 历史 Elo 比赛记录（可选） | https://github.com/fivethirtyeight/data/tree/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo | 仓库 commit `4c1ff5e3aef1816ae04af63218015066e186c147`（2025-02-25）；`nba-elo/` 目录最近一次修改为 `6d880e939a`（2022-12-16），文件内容相同 | CC-BY-4.0（仓库 LICENSE） | `nbaallelo.csv`，18,173,265 字节，126,313 行数据（63,157 场，每场两行，另含 `_iscopy` 列），sha256 `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc` | 否 |

说明：
- 若数据需要登录而你无法获得，请改用其余数据，并在论文中说明。
- 你也可以使用自行生成的合成数据，但须在论文中明示为合成。
- 请把原始数据放在工作目录下的 data/ 中，不要放进代码仓库或随论文提交；复现说明里记录来源、版本和校验和。


## Verbatim resource constraints

# 资源与预算

- 计算：仅 CPU（参考配置 4 核）。数据量级为几千到十几万条成对比较，参与者个数从个位数（MT-Bench
  为 6 个模型）到一百余个（NBA 球队）不等；单次 Bradley-Terry 型模型拟合预计在秒级（按数据量级估算，
  未实测）。总算力受下述一周时间上限约束，不另设 CPU 小时上限。
- 不需要 GPU，不需要付费 API。若你选择使用 LLM 辅助（如文献阅读、代码生成），不计入上述计算预算，
  但须在论文中披露。
- 内存：8 GB 足够（读取 140k 版本时只读取所需列）；磁盘：数据合计不超过 3 GB。
- 时间上限：一周（含文献调研、实验、写作与复现整理）。
- 网络：仅用于获取 data.md 中列出的数据、读取文献与安装依赖。


The world sandbox is 2 CPUs/4 GB, stricter than the illustrative input resource sizes; remain CPU-only and use measured runtimes rather than the input's unmeasured seconds-per-fit estimate. Network use is restricted by the objective to supplied datasets, literature and dependencies. AI assistance, if used, must be disclosed.

## Permitted related material and independence

# 起步文献

以下文献供背景知识参考；链接于 2026-10-26 核对可访问。

1. Bradley, R. A., Terry, M. E. (1952). Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons. Biometrika 39(3/4). DOI: https://doi.org/10.2307/2334029 。说明：提出成对比较的概率模型（Bradley-Terry 模型）的原始论文。
2. Chiang, W.-L. et al. (2024). Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference. ICML 2024. https://arxiv.org/abs/2403.04132 （v1: 2024-03-07）。说明：介绍 Chatbot Arena 平台：用户对两个匿名模型的回答投票，据此估计模型排名；文中描述了平台设计与所收集的投票数据。
3. Zheng, L. et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023 Datasets & Benchmarks. https://arxiv.org/abs/2306.05685 （v1: 2023-06-09）。说明：研究用大语言模型作评审（LLM-as-a-judge）评价对话模型，提出 MT-Bench 问题集，并发布了人类专家与 GPT-4 对模型回答的成对判断数据。
4. Koh, P. W., Liang, P. (2017). Understanding Black-box Predictions via Influence Functions. ICML 2017. https://arxiv.org/abs/1703.04730 （2017-03-14）。说明：介绍如何用影响函数分析单个训练样本对模型参数和预测的影响，并在若干模型上给出实验。
5. Broderick, T., Giordano, R., Meager, R. (2020). An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference? https://arxiv.org/abs/2011.14999 （2020-11-30）。说明：提出一个衡量统计分析结论稳健性的度量，并在多个已发表的应用研究数据上做了检验。
6. Min, R. et al. (2025). Improving Your Model Ranking on Chatbot Arena by Vote Rigging. ICML 2025. https://arxiv.org/abs/2501.17858 （v1: 2025-01-29）。说明：研究针对 Chatbot Arena 这类众包投票排行榜的投票操纵策略及其对模型排名的影响。
7. Singh, S. et al. (2025). The Leaderboard Illusion. https://arxiv.org/abs/2504.20879 （2025-04-29）。说明：分析 Chatbot Arena 的评测实践（如私有测试、不同提供方的数据访问与采样差异）及其对排行榜的影响。
8. Huang et al. (2025). Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings. https://arxiv.org/abs/2508.11847v1 （v1: 2025-08-16）。说明：一篇讨论基于人类偏好的大模型排行榜（如 Chatbot Arena）排名的论文。


Only the explicitly permitted starter links are being opened for literature context. Do not infer, identify, search for, or follow references to the withheld study. Supplied starter entries are expressly allowed by deliverable.md even where their topics overlap this study. Retrieved sources, actually inspected sections and access failures are recorded in `context/sources.json` and `context/reading_log.md`, and in the wiki Reading-Log page. Source claims remain separate from new measurements; reading scope is explicit, not assumed to include unused source appendices.

## Context established so far from read sources

Huang et al. (2025), the expressly permitted starter entry 8, already studies influence-guided worst-case **deletion** in BT rankings on Arena and MT-Bench human/model judgments, validates candidate deletions by refitting, and relates sensitivity to score gaps. Its Table 1 uses tie-free denominators (39,716 Arena-human; 2,575 MT-human; 2,180 MT-LLM). It is not legitimate to claim this study first discovers leaderboard sensitivity, introduces influence-based ranking audits, or directly replicates those numerical thresholds under a different intervention, fit, tie rule and denominator. Our current supplied experiment release uses decisive **outcome reversals**, keeps ties as half-wins, ridge lambda=1 on a summed loss, adds NBA panels, compares targeted and random edits, and supplies baseline and matched-schedule uncertainty. Those differences define a possible empirical contribution, not a claim of new influence-function theory.

Min et al. (2025), starter entry 6, studies **new-vote injection** and realistic information/access constraints, including de-anonymization, concurrent voting and non-target comparisons. Reversing historical labels is a different threat model. Do not describe the current audit as an executable live-platform attack.

## Evidence and reporting conventions the delivery must preserve

- Define the edited unit as a distinct decisive comparison; preserve participants and schedule; disclose ties and uneditable rows. Report both integer edits and edited fraction of **all original N rows**, plus decisive counts. Different denominators must not be compared as if equivalent.
- State fitted loss normalization, ridge coefficient, score scale and identification rule. Fractional ties are a scoring convention, not a fitted model for tie probabilities; monotone score rescaling preserves ranks but not reported margins.
- A successful candidate after exact refit is a witness/upper bound on an adversarial minimum. A failed heuristic at a budget supplies no robustness certificate. An initial leader/runner-up reversal is not equivalent to the runner-up becoming global winner; separately report winner changes and whole-ranking displacement.
- Separate randomness of edits, sampling uncertainty, human-label selection and sensitivity to modeling choices. Cluster MT questions across turns/pairs/judges; do not treat replicated judgments as independent items. State unavailable clusters (Arena user IDs) and incomplete dependence models.
- Same edit fraction does not match score gaps, tie rates, comparison graph, entrants, temporal drift or labeling mechanism. Arena-versus-MT-versus-NBA results are descriptive. Matched MT cells address schedule and sample count but cannot isolate a general causal effect of human versus model judging.
- Near-equal baseline scores can make few-edit reversals unsurprising. Show baseline margins and uncertainty with attack results; avoid interpreting ranking reversal as reversal of a statistically resolved quality difference.
- Final tables/figures must identify snapshot, actual N/k, uncertainty type, endpoint and source script. Prior-paper numbers may be cited as published facts but must not appear as newly run baselines. Every new numerical result must be generated by delivered code.

## Ownership and unresolved items

Context owns this Brief and source-grounded notes. Plan/split belongs to story-repo; analysis to experiment-repo; figures/tables to figtab-repo; venue rules to venue-repo; manuscript/PDF/source to paper-repo; independent review to its owners. Story-repo has settled the onward-delivery route: the context dossier is published through this wiki and release, and paper-repo integrates it into its owned manuscript/reference paths. Context does not need paper-repo code or PR access for that agreed supply. Venue-repo has now supplied release `venue-requirements-v1`, whose attached requirements and checklist guidance I read. Its verified choice is **NeurIPS 2026 main track**, unmodified official `neurips_2026.sty`, default anonymous review mode, at most **nine content pages** including figures/tables, with references/optional appendices/completed checklist excluded. The same PDF must end with the completed official **16-question** checklist after any appendices. Venue supplies exact template/provenance and required artifact paths; paper owns the completed checklist and rendered page/layout check. Final numerical claims are supplied by experiment-repo's published release and remain subject to independent checks.

Independent feasibility, in the completed answer to idea-review-repo#4 and release `feasibility-v2`, agrees that existing evidence suffices for the bounded descriptive questions; it identifies no mandatory new experiment. It explicitly does not certify main-track novelty/significance or approve an unassembled paper. Story's `planning/study_plan.md` and `planning/requirements.md` agree on the same bounded estimand and division. Its agreed routing decision (story#7) is to keep context as wiki/release supply; no final context path or paper PR access is needed. Paper integrates the actually-read source notes/BibTeX into its own manuscript/bibliography.

Unestablished source item: I could verify original Bradley–Terry metadata, but the article was not accessible through DOI/JSTOR/publisher PDF. That original is not included in the citation-ready bibliography. The model can be documented from the actually read permitted Chiang/Huang sources and the explicit study specification. If another owner uses the original as a consulted reference, it must first read it. Unestablished provenance item: Zheng Appendix C reports showing GPT-4 explanations after human disagreement, but I could not establish from that paper alone whether the supplied human `winner` field represents any amended versus initial vote; do not infer it. Neither point blocks the conditional empirical question. Final manuscript/build/reproduction/review remains other owners' work, not completed by this context handoff.


## Settled handoff check

The closed answers in story-repo#7 and idea-review-repo#4 have been checked against objective #1 and this Brief. Story main `d3c3684c1250bc928ecf18324b25e7be9018200d`, specifically `planning/study_plan.md` and `planning/requirements.md`, preserves the conditional empirical-schedule estimand, historical reversal/deletion/injection distinction, upper-bound interpretation, descriptive cross-design scope, separate uncertainty objects, and post-hoc fixed-reference MT follow-up. Feasibility release `feasibility-v2` supports the existing evidence for those bounded questions and requires no additional experiment for that scope. Neither answer certifies conference-level significance or final delivery. The source dossier in context-v2 remains the current literature handoff; no source finding or empirical result changes in this check. Final integration, reproducibility and independent version review remain assigned to their owners.
