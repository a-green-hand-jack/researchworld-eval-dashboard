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
**研究任务：在标注集、未标注集与预测器均固定时的置信区间宽度**
**问题与动机**
在许多科学领域（生态遥感、天文形态分类、人口普查分析等），分析者常处于如下设定：

- 只有一小份带有金标准标签的样本（获取成本高，是精度的主要瓶颈）；
- 有一大份只有特征、没有标签的样本；
- 有一个已经预训练好的、不可修改的预测模型，可以给任意样本打出预测值。

目标是对某个感兴趣的总体参数（具体估计目标由你选定并说明理由）构造**统计上有效的置信区间**：名义覆盖率必须成立，同时区间应尽可能窄。

近年已有方法把预测器输出与标注数据结合起来做有效推断。本任务把约束进一步固定：不增加标签、不更换预测器、不增加未标注样本。

**核心问题：在标注集、未标注集和预测器都固定、名义覆盖率必须成立的条件下，现有方法给出的置信区间是否还能进一步缩短？能缩短多少？在什么条件下可以，在什么条件下不能？**

**要求**
请你作为独立研究者：

1. 梳理现有方法在该设定下的做法与假设，明确你要回答的具体研究问题；
2. 提出并检验你的路线，与现有可得的有效区间方法比较；可使用公开的真实数据集，也可用已知真值的合成数据补充；
3. 报告证据与局限，说明结论在哪些条件下有收益、哪些条件下没有收益；如能给出理论分析，请写明假设与适用范围，并用实验核对。

**成功如何衡量**
- 有效性：在重复抽样下，区间的经验覆盖率达到名义水平（例如 95%）；
- 宽度：同样输入下，平均区间宽度的比较；
- 结论须有多次重复实验和不确定性报告支撑。

结论可以是支持、反驳或视条件而定；没有收益或区间失效的结果同样接受。

**约束概述**
仅用 CPU，时间上限一周，不需要付费 API（详见 `resources.md`）；数据可用公开真实数据或自行生成的合成数据（详见 `data.md`）；产出是一篇论文加代码（详见 `deliverable.md`）。

以研究问题和实验证据为主线，自行决定具体路线。

**起步文献清单**
取证日期：2026-10-26。

1. Angelopoulos, Bates, Fannjiang, Jordan, Zrnic. *Prediction-Powered Inference.* Science 2023；arXiv:2301.09633（2023-01-23 首次提交）。https://arxiv.org/abs/2301.09633 。说明：提出一类在少量金标准标注与大量未标注数据上、利用机器学习预测构造有效置信区间的方法，并在多个科学数据集上演示。
2. Angelopoulos, Duchi, Zrnic. *PPI++: Efficient Prediction-Powered Inference.* arXiv:2311.01453（2023-11-02）。https://arxiv.org/abs/2311.01453 。说明：提出带数据驱动调节参数的预测驱动推断估计量及其置信区间与计算实现，涵盖均值、分位数和回归等估计问题。
3. Zrnic, Candès. *Cross-Prediction-Powered Inference.* arXiv:2309.16598（2023-09-28）。https://arxiv.org/abs/2309.16598 。说明：提出在预测模型由同一份标注数据训练时（交叉拟合）构造有效置信区间的方法。
4. Zrnic, Candès. *Active Statistical Inference.* arXiv:2403.03208（2024-03-05 首次提交；链接为 v2，2024-05-29）。https://arxiv.org/abs/2403.03208v2 。说明：提出利用模型不确定性决定对哪些样本获取标签、再构造有效置信区间的主动标注方法。
5. Fisch, Maynez, Hofer, Dhingra, Globerson, Cohen. *Stratified Prediction-Powered Inference for Hybrid Language Model Evaluation.* arXiv:2406.04291（2024-06-06）。https://arxiv.org/abs/2406.04291 。说明：面向语言模型评测的预测驱动推断变体，给出相应的估计量、置信区间与实验。
6. Chernozhukov et al. *Double/Debiased Machine Learning for Treatment and Causal Parameters.* arXiv:1608.00060（2016-07-30）。https://arxiv.org/abs/1608.00060 。说明：提出用机器学习估计干扰函数、对低维目标参数做去偏推断的方法，并给出渐近性质。
7. Ding, Hardt, Miller, Schmidt. *Retiring Adult: New Datasets for Fair Machine Learning.* NeurIPS 2021；arXiv:2108.04884（2021-08-10）。https://arxiv.org/abs/2108.04884 。说明：基于美国人口普查（ACS PUMS）构建的一组表格数据集及其 Python 包 `folktables`，用于机器学习与公平性研究。
8. Willett et al. *Galaxy Zoo 2: detailed morphological classifications for 304,122 galaxies from the Sloan Digital Sky Survey.* arXiv:1308.3496（2013-08-15）。https://arxiv.org/abs/1308.3496 。说明：Sloan Digital Sky Survey 星系图像的众包形态学分类数据集（304,122 个星系）及其构建方法。
9. Cortez, Cerdeira, Almeida, Matos, Reis. *Modeling wine preferences by data mining from physicochemical properties.* Decision Support Systems 47(4), 2009。UCI 数据集页：https://archive.ics.uci.edu/dataset/186/wine+quality 。说明：葡萄牙 Vinho Verde 红、白葡萄酒的理化指标与感官评分数据集，以及据此用数据挖掘方法建模品质的研究。

**数据与获取方式**
取证日期：2026-10-26。你也可以使用其他公开数据，或完全使用合成数据；下表分为主数据与可选数据。

**主数据**
PPI 参考实现包 `ppi-python` 附带的示例数据（9 个 `.npz` 集合）。

- 获取：`pip install ppi-python==0.2.3`（PyPI 发布于 2024-12-22；GitHub 标签 `v0.2.3`，提交 `6b8475b`）。首次调用 `ppi_py.datasets.load_dataset('./data/', '<集合名>')` 时由包内代码通过 `gdown` 从 Google Drive 下载到本地 `./data/<集合名>.npz`（`gdown` 已列入该包的依赖）。无需账号或协议。已在宿主机上实测：9 个文件均可匿名下载，合计约 48 MB；容器内未测。
- 仓库：https://github.com/aangelopoulos/ppi_py ；PyPI：https://pypi.org/project/ppi-python/ 。
- 许可：代码仓库为 MIT（`v0.2.3` 的 LICENSE 已核实）。仓库 README、LICENSE 与 PyPI 页面均未给出 `.npz` 数据文件的独立许可声明（PyPI 页面 license 字段为空）；各集合的原始来源见仓库 `examples/*.ipynb` 开头的引文。
- 版本：固定为 `v0.2.3`。

| 集合名 | 大小 | 数组（形状） | 示例 notebook 中的描述 |
| --- | --- | --- | --- |
| `galaxies` | 约 0.3 MB | `Y`、`Yhat`（各 16743） | 星系是否有旋臂：人工标注与计算机视觉预测 |
| `forest` | 约 0.03 MB | `Y`、`Yhat`（各 1596） | 亚马逊地块是否毁林：实地标注与卫星影像预测 |
| `alphafold` | 约 0.4 MB | `Y`、`Yhat`、`phosphorylated`、`ubiquitinated`、`acetylated`（各 10802） | 蛋白无序区域标注与基于 AlphaFold 结构的预测，及三种翻译后修饰的指示变量 |
| `gene_expression` | 约 1 MB | `Y`、`Yhat`（各 61150） | 启动子序列诱导的基因表达水平：实验测量与 Transformer 预测 |
| `census_income` | 约 11 MB | `Y`、`Yhat`（各 380091），`X`（380091×2） | 美国加州 2019 年普查收入：报告值与模型预测，特征为年龄和性别 |
| `census_healthcare` | 约 9 MB | `Y`、`Yhat`（各 318215），`X`（318215×2） | 美国加州 2019 年普查：是否有私人医保（报告值与预测），特征含收入 |
| `census_education` | 约 14 MB | `Y`、`Yhat`（各 318215），`X`（318215×4） | 美国加州 2019 年普查：收入与教育程度相关量及其预测 |
| `plankton` | 约 12 MB | `Y`、`Yhat`（各 421238），`Y_unlabeled`、`Yhat_unlabeled`（各 329832） | 浮游生物成像（2013 年标注、2014 年未标注），含两年不同分布 |
| `ballots` | 约 0.6 MB | `Y`、`Yhat`（各 1027），`Yhat_unlabeled`（78150） | 2022 年旧金山一次特别选举的选票：人工判读与扫描读取 |

除 `plankton`、`ballots` 外，每个集合的 `Y`、`Yhat` 对应同一批记录（标签与预测）；`X` 仅在 `census_*` 集合中出现。

**可选数据**
| 数据 | 获取 | 许可/账号 | 规模与格式 |
| --- | --- | --- | --- |
| Wine Quality（UCI） | https://archive.ics.uci.edu/dataset/186/wine+quality ；压缩包 https://archive.ics.uci.edu/static/public/186/wine+quality.zip | CC BY 4.0（Creative Commons Attribution 4.0 International，UCI 数据集页面注明）；无需账号 | 含 `winequality-red.csv`（1599 条）与 `winequality-white.csv`（4898 条），共 6497 条；分号分隔；11 项理化指标 + `quality` 评分，共 12 列。UCI 页面标注 2009-10-07 捐赠。不含预测值，只含特征与评分 |
| California Housing | `sklearn.datasets.fetch_california_housing`（https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html ）；数据由 figshare 下载（https://ndownloader.figshare.com/files/5976036） | 无明确许可声明（sklearn 文档仅注明数据取自 StatLib 仓库）；无需账号 | 20640 条、8 个特征，目标为区块房价中位数。不含预测值 |
| 美国人口普查类数据（ACS PUMS，通过 `folktables`） | `pip install folktables==0.0.12`（PyPI 2023-02-08）；https://github.com/socialfoundations/folktables 。数据由包从 census.gov 下载，例如 2019 年 1-Year 加州文件 https://www2.census.gov/programs-surveys/acs/data/pums/2019/1-Year/csv_pca.zip（约 68 MB） | `folktables` 仓库为 MIT；ACS PUMS 为美国人口普查局公开数据；无需账号 | 单州数据量为 10^5 量级。不含预测值 |
| 合成数据 | 自行生成 | 无 | 生成机制与真值由你确定 |

`ppi-python` 示例数据已附带预测值 `Yhat`；Wine Quality、California Housing、folktables 不附带预测值。

**资源与预算**
- 计算：仅 CPU 即可完成（4 核以上、16 GB 内存为宜）；不需要 GPU。若使用现成预测值（如示例数据自带的预测），无需训练深度模型。
- 估算依据：数据为 10^3–10^6 条的表格或标量记录（见 `data.md`），单次估计与区间计算预计为毫秒到秒级，总计预计 < 8 CPU 小时。此为估算，未实测。
- 时间上限：一周（含阅读、实现、实验、写作）。
- 存储：< 5 GB。
- 付费 API：不需要。
- 联网：可访问公开文献与数据下载；数据下载需访问 Google Drive（示例数据）、archive.ics.uci.edu、census.gov、figshare；不得访问 deliverable.md 中列出的禁止内容。

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
    "evidence": "Alternatives considered: active allocation (violates fixed labels), DML with X (changes information set), bootstrap-only small-n fixes (modest gain).",
    "idea_id": "cycle01_crppi_mean_ci",
    "next_action": "Implement estimators + harness, validate vs ppi_py, run synthetic known-truth grid then real-data grid.",
    "rubrics": {
      "coverage_at_nominal": "metric",
      "experiment_harness_with_uncertainty": "implementation",
      "recalibrated_ppi_implemented": "implementation",
      "theory_predicts_width_ratio": "metric",
      "width_ratio_vs_ppi_plus_plus": "metric"
    },
    "scope": "idea",
    "step": "idea",
    "summary": "Selected cross-fitted recalibrated PPI mean intervals (isotonic/binned g(Yhat), shrinkage, efficiency-bound theory) vs classical/PPI/PPI++/stratified PPI. gate=kept; trigger=none; reason=first cycle with no executed evidence.",
    "timestamp": "2026-11-11T00:00:00Z"
  },
  {
    "attempt_id": "cycle01_crppi_mean_ci_attempt_01",
    "idea_id": "cycle01_crppi_mean_ci",
    "program_id": "program_1",
    "step": "implement",
    "summary": "program_1 cloned from program_0; src/program.py adds cross-fitted isotonic/binned recalibrated PPI mean CI with PPI++ fallback selection (1% margin), baselines, and src/harness.py with wilson/bootstrap/synthetic harness; untested"
  },
  {
    "attempt_id": "cycle01_crppi_mean_ci_attempt_01",
    "evidence": "combined_score=0.027080121099549548, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.027080121099549548, \"controls_passed\": 1.0, \"correct\": true, \"coverage_min_family\": 0.9333333333333333, \"coverage_pooled\": 0.9433333333333334, \"log_ratio_vs_classical_mean\": 0.49413320035056846, \"log_ratio_vs_ppi_family_alphafold\": 0.010428103934328083, \"log_ratio_vs_ppi_family_forest\": 0.016791531451063855, \"log_ratio_vs_ppi_family_galaxies\": 0.0035018565908873267, \"log_ratio_vs_ppi_family_gene_expression\": 0.028990259989334164, \"log_ratio_vs_ppi_family_synthetic\": 0.07568885353213431, \"log_ratio_vs_ppi_lambda1_mean\": 0.05393618082192103, \"n_failed_episodes\": 0}",
    "idea_id": "cycle01_crppi_mean_ci",
    "metrics": {
      "combined_score": 0.027080121099549548,
      "controls_passed": 1.0,
      "correct": true,
      "coverage_min_family": 0.9333333333333333,
      "coverage_pooled": 0.9433333333333334,
      "log_ratio_vs_classical_mean": 0.49413320035056846,
      "log_ratio_vs_ppi_family_alphafold": 0.010428103934328083,
      "log_ratio_vs_ppi_family_forest": 0.016791531451063855,
      "log_ratio_vs_ppi_family_galaxies": 0.0035018565908873267,
      "log_ratio_vs_ppi_family_gene_expression": 0.028990259989334164,
      "log_ratio_vs_ppi_family_synthetic": 0.07568885353213431,
      "log_ratio_vs_ppi_lambda1_mean": 0.05393618082192103,
      "n_failed_episodes": 0
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-11T10:41:08.974705+00:00"
  },
  {
    "evidence": "idea_bundle.json + target_rubrics.json; cycle1 metrics score 0.027, coverage pooled 0.943",
    "idea_id": "cycle02_label_free_basis_ppi_press",
    "next_action": "implement and evaluate vs incumbent",
    "scope": "idea",
    "step": "idea",
    "summary": "Selected label-free spline-basis control-variate PPI with PRESS selection and LOO-residual SE. gate=updated; trigger=b; reason=new category after cycle1 evaluation.",
    "timestamp": "2026-11-11T10:42:25Z"
  },
  {
    "attempt_id": "cycle02_label_free_basis_ppi_press_attempt_01",
    "idea_id": "cycle02_label_free_basis_ppi_press",
    "program_id": "program_1",
    "step": "implement",
    "summary": "program_1 implemented: label-free hinge basis + vector-lambda PPI + PRESS selection + LOO-residual SE with t(n-1-p); PPI++ fallback; harness with ablations. Files: src/program.py, src/harness.py. Untested."
  },
  {
    "attempt_id": "cycle02_label_free_basis_ppi_press_attempt_01",
    "evidence": "combined_score=0.004641570343273279, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.004641570343273279, \"controls_passed\": 1.0, \"correct\": true, \"coverage_min_family\": 0.9333333333333333, \"coverage_pooled\": 0.95, \"log_ratio_vs_classical_mean\": 0.47169464959429214, \"log_ratio_vs_ppi_family_alphafold\": 0.004872193619134172, \"log_ratio_vs_ppi_family_forest\": 0.0024126203314315487, \"log_ratio_vs_ppi_family_galaxies\": 0.0014330156547436338, \"log_ratio_vs_ppi_family_gene_expression\": 0.011109273479074356, \"log_ratio_vs_ppi_family_synthetic\": 0.0033807486319826856, \"log_ratio_vs_ppi_lambda1_mean\": 0.031497630065644766, \"n_failed_episodes\": 0}",
    "idea_id": "cycle02_label_free_basis_ppi_press",
    "metrics": {
      "combined_score": 0.004641570343273279,
      "controls_passed": 1.0,
      "correct": true,
      "coverage_min_family": 0.9333333333333333,
      "coverage_pooled": 0.95,
      "log_ratio_vs_classical_mean": 0.47169464959429214,
      "log_ratio_vs_ppi_family_alphafold": 0.004872193619134172,
      "log_ratio_vs_ppi_family_forest": 0.0024126203314315487,
      "log_ratio_vs_ppi_family_galaxies": 0.0014330156547436338,
      "log_ratio_vs_ppi_family_gene_expression": 0.011109273479074356,
      "log_ratio_vs_ppi_family_synthetic": 0.0033807486319826856,
      "log_ratio_vs_ppi_lambda1_mean": 0.031497630065644766,
      "n_failed_episodes": 0
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-11T10:57:48.846372+00:00"
  },
  {
    "evidence": "idea_bundle.json + target_rubrics.json; cycle2 score 0.0046 < incumbent 0.0271; synthetic gain 0.003 (basis) vs 0.076 (isotonic)",
    "idea_id": "cycle03_stacked_calibration_ppi",
    "next_action": "implement on incumbent program, run harness once, report per-family coverage and width ratios",
    "rubrics": {
      "ablation_harness_with_uncertainty": "implementation",
      "incumbent_score_improvement": "metric",
      "stacked_repeated_crossfit_implemented": "implementation"
    },
    "scope": "idea",
    "step": "idea",
    "summary": "Selected repeated cross-fitted NNLS-stacked calibration PPI with split-dispersion variance and PPI++ fallback. gate=updated; trigger=a; reason=cycle2 evaluation contradicts the label-free-basis lead.",
    "timestamp": "2026-11-11T11:10:00Z"
  },
  {
    "attempt_id": "cycle03_stacked_calibration_ppi_attempt_01",
    "idea_id": "cycle03_stacked_calibration_ppi",
    "next_action": "harness evaluates program_1 once",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "implement",
    "summary": "program_1 implemented from incumbent: NNLS-stacked calibrator library (isotonic, bins 3/5/8, local-linear kernels, linear), repeated cross-fit R=5 with [Yhat,g] control variates, averaged-residual variance + split dispersion, t df n-3, PPI++ 1% fallback; harness run_ablation added. Files: src/program.py, src/harness.py. Untested.",
    "timestamp": "2026-11-11T11:30:00Z"
  },
  {
    "attempt_id": "cycle03_stacked_calibration_ppi_attempt_01",
    "evidence": "combined_score=0.022255735814912924, correct=True; scientific acceptance passed; search metrics (data): {\"combined_score\": 0.022255735814912924, \"controls_passed\": 1.0, \"correct\": true, \"coverage_min_family\": 0.9166666666666666, \"coverage_pooled\": 0.9433333333333334, \"log_ratio_vs_classical_mean\": 0.4893088150659318, \"log_ratio_vs_ppi_family_alphafold\": 0.0037823141071903696, \"log_ratio_vs_ppi_family_forest\": 0.005425940895992022, \"log_ratio_vs_ppi_family_galaxies\": 0.0035630075950539167, \"log_ratio_vs_ppi_family_gene_expression\": 0.02776956644462489, \"log_ratio_vs_ppi_family_synthetic\": 0.07073785003170342, \"log_ratio_vs_ppi_lambda1_mean\": 0.049111795537284446, \"n_failed_episodes\": 0}",
    "idea_id": "cycle03_stacked_calibration_ppi",
    "metrics": {
      "combined_score": 0.022255735814912924,
      "controls_passed": 1.0,
      "correct": true,
      "coverage_min_family": 0.9166666666666666,
      "coverage_pooled": 0.9433333333333334,
      "log_ratio_vs_classical_mean": 0.4893088150659318,
      "log_ratio_vs_ppi_family_alphafold": 0.0037823141071903696,
      "log_ratio_vs_ppi_family_forest": 0.005425940895992022,
      "log_ratio_vs_ppi_family_galaxies": 0.0035630075950539167,
      "log_ratio_vs_ppi_family_gene_expression": 0.02776956644462489,
      "log_ratio_vs_ppi_family_synthetic": 0.07073785003170342,
      "log_ratio_vs_ppi_lambda1_mean": 0.049111795537284446,
      "n_failed_episodes": 0
    },
    "next_action": "generate next idea",
    "program_id": "program_1",
    "scope": "attempt",
    "step": "evaluate",
    "summary": "harness evaluated program_1 exactly once",
    "timestamp": "2026-11-11T11:16:41.889562+00:00"
  },
  {
    "scope": "paper",
    "step": "reference_plan",
    "summary": "Wrote 10-query grounded reference plan (PPI, PPI++, cross-PPI, stratified PPI, DML, isotonic calibration, NNLS stacking, control variates, dataset context); rejected generic/chronology queries.",
    "timestamp": "2026-11-11T11:40:36Z"
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
