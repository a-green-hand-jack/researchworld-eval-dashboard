# 少量二值响应预测 LLM 基准得分：实验报告

## 1. 摘要与目标（Summary & goals）

利用历史源模型的逐题正确性矩阵，以少量目标模型响应预测完整题库的**平坦二值均分**及模型排序。研究重点是区分选题、分数重建与残差审计，而非宣称发明差分估计或取得全面最优结果。原始要求见 `research_request.md`，论文见 `paper/main.tex`、`paper/appendix.tex`。

提出源难度分层交叉拟合差分估计（SCFD）：每层随机查询，分成互斥 pilot/audit，两方向分别拟合、审计后平均。在规定随机设计、pilot 信息隔离和可积预测条件下，估计对固定题库均分设计无偏；这**不保证更低 MAE、更好排序或部署置信区间**。

主要结论：50 题时，SCFD 的 IID/frontier 宏 MAE 为 **3.77/3.80 个百分点（pp）**，均匀抽样为 4.48/4.40 pp。但简单诚实的固定分层差分已达 **3.91/3.83 pp**，SCFD 在 frontier 仅多改善 **0.0274 pp（约 0.03 pp）**；实际使用宜优先考虑简单方法。IID 最优的原始配置是分层 score ridge（3.02 pp），frontier Rasch（3.76 pp）也优于 SCFD。贡献主要是协议、信息边界与偏差—方差权衡的受控研究；主会新颖性仍有限，**不保证录用**。

## 2. 实验计划（Plan）

冻结协议为 `todos.md`；成功信号是正确性、预算合规、有限输出及隐藏标签隔离，而不是必须取得正向提升。

| 阶段 | 内容与验收信号 | 最终状态 |
|---|---|---|
| 数据/实现审计 | 固定数据版本；二值与重复审计；官方固定实现等价测试；小总体枚举验证 | 完成，最终 12 项测试通过 |
| 固定参数与 smoke | 目标 item ridge α=10、五层；source score ridge 仅源内 RidgeCV；检查收敛及信息隔离，不按目标误差调参 | 完成；初始优化失败已记录并修复 |
| 冻结主实验 | 13 题库 × 2 划分 × 5 seeds = 130 cells；17 配置 × 4 预算 = **8,840** 个方法—预算输出 | 完成，含消融与明确标注的双预算参考 |
| 机制/压力诊断 | 去分层、去对称化、去审计、污染残差；65 个 gap cells；200 次重复 mask、8 个诊断 panel | 完成；保留负结果 |
| 主分析后补充 | MIRT：130 cells，每预算 2 种估计；自审后 nearest-source：130 cells，每预算 1 种估计 | 均覆盖原主实验全部 4 预算；未扩展 gap |
| 数值与稿件修订 | 从保存预测修复排序并更新表图；澄清总查询成本和计算成本 | 完成；不改变原始误差、拟合、mask 或主对比 |

**冻结/后补边界：**主终点为预算 50、IID/frontier 分别报告的分组等权宏 MAE；四个预设对比是两种划分下 SCFD 对 uniform/stratified mean。MIRT 为主分析后补充（`logs/irt_comparator_amendment.md`），nearest-source 为自审后补充，均未修改 SCFD 参数、终点或原四对比。记录是本地冻结协议与修订溯源，非独立时间戳预注册认证。

## 3. 实验设置（Setup）

### 数据、划分与 QC

- 唯一数据来源为固定仓库 commit `55faff496947789f94e6b5908c77cbc3e84f81ad` 的 `data/scores/*.jbl`：`arc_challenge, bbh, gpqa, ifeval, mmlu_pro, musr, openllm_math, commonsense, gsm, legalbench, math, med_qa, mmlu`。共 13 个公开矩阵，每库 79–448 模型、437–12,032 题；所有项有限且为 0/1。
- 保留重复列、常数列和全部模型行，尤其保留 OpenLLM-MATH 的 **53 个全零行**；不把这些上游异常解释成已完成质量认证。SHA-256、维度、重复数量与得分范围见 `artifacts/data_audit.csv`，数据清单见 `artifacts/download_manifest.json`、`paper/tables/data.tex`。
- 完全相同的响应行先归组，整组划分，避免完全相同签名跨源/目标。源训练保留原行重数；主评估目标组等权，原行加权另作敏感性。分组不等于模型家族隔离或污染检测。
- IID：随机取 70% 唯一组作源（向下取整）。Frontier：按完整组均分排序，在最接近 70% 的完整得分并列块边界划分，高分组作目标。Gap：低约 50% 作源、高约 30% 作目标，弃中间部分。完整目标响应仅供 oracle 分组/压力划分及最终评价，不能进入选题与预测；frontier/gap **不是时间或真实部署外推协议**。
- Seeds 为 0–4；frontier 成员不随 seed 改变，五次主要表示查询设计变化，不是五个独立模型总体。保存源/目标行、查询与两半集合；测试覆盖分组隔离、隐藏标签不变性、预算与互斥性、固定类等价及排序不变量。`logs/tests.log`：**12 passed in 4.54s**。

### 方法与参数

预算为 **10、25、50、100**，主预算 50；同一 uniform/stratified 轨道共享查询，uniform 预算前缀嵌套，stratified 不要求嵌套。源题目均值排序后按题号破并列，划成 H=5 个近等大层；预算近均分至各层，每层无放回随机抽样。

目标 item ridge 以题为样本、源模型响应为特征，只用当前 pilot 的目标标签，损失为平方和加 `10‖w‖²`，截距不惩罚，中心化仅使用 pilot。单方向估计为

\[
T(P\!\to\!A)=\frac{1}{N}\left[\sum_{i\in P}y_i+\sum_{i\notin P}q_i^P+\sum_h(N_h-p_h)\overline{(y-q^P)}_{A_h}\right].
\]

审计权重是 **pilot 补集大小** `N_h−p_h`，并非仅未查询部分。SCFD 为交换 P/A 后两估计的固定半平均；两方向相关，方差不能忽略协方差。预测不裁剪到 [0,1]。设计无偏依赖理想随机抽样与 audit **成员身份及标签**不进入其对应 pilot 拟合；有限 PRNG seeds 不是精确抽样分布。证明、有限总体修正、奇数折和 census 边界见 `paper/appendix.tex`。

**no-audit 成本：**两个半集各拟合一次，每次只用自己半集；平均两次总体插补，合计仍消耗同一个查询并集的 **b 个标签**，不是 b/2，也不是 2b。

### 环境与实测时间

CPU-only，无 LLM 重跑、无付费 API、无 GPU。宿主暴露 40 核、约 251 GiB RAM；使用 8 个单线程 worker，BLAS/OMP/MKL 各限 1。Python 3.11.15、NumPy 2.4.6、pandas 3.0.6、SciPy 1.17.1、scikit-learn 1.9.1、joblib 1.6.0；详见 `artifacts/environment.json`、`requirements.txt`。

| 阶段 | 实测脚本墙钟时间 | 证据 |
|---|---:|---|
| 原始主网格 | 80.2655 s | `artifacts/run_summary_main.json` |
| 200-mask 诊断 | 78.8002 s | `artifacts/diagnostic_summary.json` |
| Gap | 19.9556 s | `artifacts/run_summary_gap.json` |
| MIRT（含源内校准及评分） | 569.516 s | `artifacts/irt_summary.json` |
| Nearest-source | 4.9461 s | `artifacts/nearest_summary.json` |

主网格合计 **544.3781 worker-cell 秒**，MIRT 为 **3,840.5507 worker-cell 秒**（约 9.07/64.01 cell 分钟），它们是并行单元耗时之和，**不是实测进程 CPU 秒**，也不包含全部失败预跑、准备和写作。未测峰值内存，不外推为其他机器的保证耗时。

## 4. 基线与公平比较（Baselines）

- **简单诚实对照：**uniform mean、stratified mean、固定源题难度差分及其分层版；uniform CFD 隔离分层贡献。
- **分数回归：**以源模型行为样本，查询响应作特征、源全分作标签，RidgeCV α∈{0.1,1,10}；分别用 uniform/stratified 查询。它与逐目拟合目标响应的 item ridge 方向不同。
- **AIPW 两版本：**保留固定仓库原公式（pinned），同时报告总体权重修正版（population）。带非惩罚截距的同样本残差均值约为零，不能把训练残差修正称为独立审计；公式差异见 `paper/main.tex`，数值影响并非本实验主效应。
- **Rasch/anchors：**正则 1PL，源 θ/题难度先验方差 4/9；源迭代 cap=200、容差 10⁻⁶，目标单能力 cap=80。Binary anchors 使用源正确性向量、MiniBatchKMeans（3 初始化、batch 1024、cap 100），选真实代表题并按簇大小加权；另用同批 anchors 加 Rasch 解码。二者均为明确标注的改编，不是 confidence Anchor Points 或完整 tinyBenchmarks。
- **后补 MIRT：**固定秩 5 的点估计 logistic 模型，L-BFGS-B cap=1000，目标 Newton cap=60；混合估计的权重只通过源组内 80/20 划分校准，再全源重拟合。非完整 Bayesian/GPIRT 系统；**260 个源/内源拟合均数值成功，最多 474 次迭代**，不代表全局最优，亦非目标优化收敛证书（后者未单独保存）。
- **后补 nearest-source：**在保存的 uniform 查询响应上按 Hamming 距离取最近源行，所有最小距离并列行平均；保留实际查询目标结果，只对未查部分借用源响应。原 130 cells × 4 预算全部完成，无目标得分调参。
- **消融：**one-direction、no-audit、contaminated residual，使用匹配 pilot 拟合；污染版本混合训练与审计残差，不能宣称诚实。`uniform_2b` 明确多花一倍查询，不是等预算优胜证据。所有对照数字均由本协议重跑，不照搬论文数值。

## 5. 结果（Results）

### 5.1 评价与不确定性

主评估先在每库对目标响应组等权，再对 13 库等权；宏 RMSE 是各库 MSE 平均后的平方根，不是库 RMSE 的平均。排序在每库内计算 Spearman ρ、Kendall τ_b 和 pair agreement；后者去除真实并列，预测并列记半分，不跨无关题库拼榜。

区间为先将五 seeds 在库内平均，再进行 **10,000 次题库 bootstrap** 的百分位 95% 区间。共享模型池、相关任务与共用 mask 意味着它们仅是**已观测题库重加权的描述性区间**，不是独立总体推断或单模型分数 CI；Holm 校正也不能消除题库依赖。seed SD 是五次宏 MAE 的样本标准差，不是标准误。

### 5.2 主预算 50

误差单位均为 pp，方括号为上述描述性 95% 区间。数据：`artifacts/analysis/macro_summary.csv`；完整论文表：`paper/tables/main.tex`、`all_iid.tex`、`all_frontier.tex`。

| 方法 | IID MAE [区间] | Frontier MAE [区间] | IID / Frontier RMSE | IID / Frontier ρ |
|---|---:|---:|---:|---:|
| Uniform | 4.48 [3.99,4.86] | 4.40 [3.92,4.86] | 5.75 / 5.60 | .848 / .664 |
| Stratified mean | 3.98 [3.51,4.39] | 3.93 [3.50,4.40] | 5.12 / 5.00 | .865 / .694 |
| Item difference | 3.89 [3.44,4.28] | 3.91 [3.52,4.29] | 5.01 / 4.99 | .848 / .664 |
| Stratified difference | 3.91 [3.45,4.32] | 3.83 [3.37,4.32] | 5.05 / 4.89 | .865 / .694 |
| Score ridge | 3.09 [2.63,3.54] | 7.51 [6.16,8.95] | 4.06 / 9.08 | .902 / .499 |
| Stratified score ridge | 3.02 [2.57,3.45] | 7.37 [6.05,8.77] | 4.04 / 8.89 | .914 / .532 |
| AIPW-pinned | 3.61 [3.21,3.97] | 3.86 [3.51,4.22] | 4.64 / 4.89 | .865 / .655 |
| AIPW-population | 3.60 [3.21,3.95] | 3.82 [3.46,4.18] | 4.63 / 4.84 | .866 / .656 |
| Rasch 1PL | 3.74 [3.30,4.15] | 3.76 [3.41,4.10] | 4.85 / 4.80 | .848 / .664 |
| Binary anchors | 4.47 [3.77,5.41] | 9.15 [5.43,13.35] | 6.06 / 14.93 | .872 / .608 |
| Uniform CFD | 3.81 [3.41,4.16] | 3.90 [3.52,4.29] | 4.88 / 4.96 | .855 / .648 |
| **SCFD** | **3.77 [3.35,4.10]** | **3.80 [3.36,4.26]** | **4.84 / 4.86** | **.874 / .676** |
| MIRT-5（后补） | 3.85 [3.18,4.50] | 9.43 [7.91,11.24] | 5.00 / 10.69 | .899 / .546 |
| MIRT mixture（后补） | 3.27 [2.83,3.68] | 6.93 [5.67,8.44] | 4.26 / 8.23 | .897 / .624 |
| Nearest-source（后补） | 4.16 [3.23,5.17] | 9.26 [7.23,11.56] | 6.04 / 11.41 | .854 / .290 |

粗体仅标识研究方法，不表示最优。SCFD 的 IID/frontier seed SD 为 **0.0633/0.2433 pp**；τ_b 为 **0.7324/0.5097**，pair agreement 为 **0.8652/0.7556**。Frontier stratified mean 的 τ_b=0.5338、pair agreement=0.7615，均高于 SCFD；**降低分数 MAE 不等于改善排序**。

四项预设配对效应（SCFD−对照，负值有利；`artifacts/analysis/primary_effects.json`）：

| 划分/对照 | MAE 差 pp [95% 描述性区间] | 获益题库 | Holm 后 sign-flip p |
|---|---:|---:|---:|
| IID / uniform | −0.7155 [−0.9044,−0.5358] | 13/13 | 0.0009766 |
| IID / stratified mean | −0.2180 [−0.3371,−0.1167] | 12/13 | 0.0021973 |
| Frontier / uniform | −0.5992 [−1.0000,−0.1867] | 11/13 | 0.0371094 |
| Frontier / stratified mean | −0.1252 [−0.2316,−0.0184] | 10/13 | 0.0515137 |

Sign-flip 枚举 2¹³ 种符号，依赖独立性/符号对称假设，仅作敏感性摘要，不宣称确证显著性。SCFD 相对 uniform 的 MAE 降幅为 IID 15.97%、frontier 13.61%；但简单分层已解释大部分数值改善。Frontier 五个 seed 中有一个 SCFD−stratified mean 差为 **+0.00652 pp**；bootstrap 区间不跨零不能抹去该波动。SCFD 对 uniform 的两库失败为 **BBH、GSM**，见 `paper/tables/per_benchmark_frontier.tex`、`paper/figures/paired_effects.pdf`。

### 5.3 消融、预算与重复 mask

匹配拟合消融（50 题；`paper/tables/ablation.tex`）：

| 方法 | IID MAE | Frontier MAE | Frontier 平均有符号误差 |
|---|---:|---:|---:|
| SCFD one-direction | 5.19 | 5.50 | −0.52 |
| Uniform CFD | 3.81 | 3.90 | −0.18 |
| SCFD no-audit（总 b 标签） | 3.58 | 3.87 | −1.41 |
| SCFD contaminated | 3.57 | 3.71 | −0.82 |
| SCFD | 3.77 | 3.80 | −0.26 |

对称化明显改善单方向误差；但 IID no-audit、两种划分的 contaminated 都可比 SCFD 更准确。诚实保证不是 MAE 最优性；五 seed 的有符号误差也不是完整设计偏差估计。

| 查询预算 | IID uniform / SCFD MAE | Frontier uniform / SCFD MAE |
|---|---:|---:|
| 10 | 10.59 / 8.89 | 11.05 / 8.95 |
| 25 | 6.59 / 5.64 | 6.53 / 5.45 |
| 50 | 4.48 / 3.77 | 4.40 / 3.80 |
| 100 | 3.17 / 2.54 | 3.13 / 2.59 |

Frontier 在 10/25/100 题时固定分层差分为 8.79/5.26/2.58 pp，亦可优于 SCFD。`uniform_2b` 在主预算名义 50 时实际用 100 题，IID/frontier MAE=3.17/3.13 pp，不作等成本胜出。预算图为 `paper/figures/budget_curves.pdf`，全表为 `paper/tables/budgets.tex`。四个有限预算点不证明渐近“误差地板”。

Gap 的 SCFD/uniform/score ridge MAE 为 **4.03/4.40/12.30 pp**，SCFD 描述性区间 [3.64,4.42]；原行加权时 SCFD 的 IID/frontier MAE=3.74/3.80 pp（`paper/tables/gap.tex`、`row_weighted.tex`）。

重复-mask 诊断固定 seed-0 源，在题数最大 MMLU-Pro 与中位 GSM、两种划分、预算 10/100 上，各取最多六个固定目标组、运行 **200 新 mask**，合计八 panel，不是新增独立模型样本。Frontier 代表值（pp；有符号误差 ± **1 MCSE**）：

| 题库/预算 | SCFD MAE；误差±MCSE | AIPW-population MAE；误差±MCSE |
|---|---:|---:|
| GSM / 10 | 7.35；+0.30±0.35 | 7.70；+0.47±0.40 |
| GSM / 100 | 2.00；+0.05±0.08 | 2.04；−0.18±0.10 |
| MMLU-Pro / 10 | 9.80；+0.06±0.50 | 10.25；−3.84±0.49 |
| MMLU-Pro / 100 | 3.24；+0.05±0.15 | 3.24；−1.10±0.15 |

MCSE 先在每个 mask 内平均目标误差，再跨 mask 计算，保留共享 mask 的目标协方差。图 `paper/figures/bias_diagnostics.pdf` 用 ±2 MCSE；目标级结果及 MSE=组内方差+经验偏差平方分解见 `artifacts/diagnostics/`、`artifacts/analysis/repeated_mask_summary.csv`、`paper/tables/diagnostics.tex`。经验偏差平方含有限 200 次模拟噪声；聚合正负偏差可抵消，不能据小误差条证明目标级零偏差，也不能外推成预算 50 的偏差验证或区间覆盖率。

### 5.4 修复、完整性与稿件产物

- `artifacts/analysis/integrity.json`：130 主 cells、65 gap cells、8,840 原主输出；Rasch 最多 62 次迭代，最大末次更新 9.9987×10⁻⁷；原网格未定义相关系数为 0。MIRT 完整性见 `artifacts/analysis/irt_integrity.json`。
- **排序缺陷已修复，不是待解决限制。**旧精确浮点排序把公共平移后的数学并列打散。现在仅对所有排序指标的 truth/prediction 保留小数点后 **10 位**再排序，误差使用未量化原值；无 jitter，不将此政策解释为统计等价。`logs/rank_correction.log` 记录修订 **18,326 个排序字段**、**1,170 项公共偏移不变量检查全部通过**；明细为 `logs/rank_correction_ledger.csv`，实现为 `src/recompute_metrics.py`。MAE、主效应、拟合与查询均未改变，最终表图已更新；SCFD frontier 排序不及简单分层的结论未反转。
- `artifacts/paper_review.md` 是**修复前历史自审**：其中排序缺陷、nearest 缺失、no-audit 成本和计算披露问题不能当作当前未修复项。当前仍成立的是贡献强度/主会新颖性风险。
- 最终 `paper.pdf`：**25 页总计、8 页正文**，使用原版官方 NeurIPS 2026 模板，符合初投稿 9 页正文限制，16 项 checklist 均作答。证据：`logs/latex_build.log`、`paper/checklist_filled.tex`；旧自审的 24 页不是最终版本。格式合规不等于录用，亦不表示该届截止日期仍开放。

## 6. 分析、局限与下一步（Analysis, limitations & next steps）

**解释与推荐。**来源相近时，源分数映射可获更好点预测；frontier 下其强负误差暴露外推风险，增加 MIRT 表达能力或 nearest-source 也未消除此压力失败。随机分层与固定源难度控制已很强，SCFD 的目标专属拟合在 frontier 仅增加约 0.03 pp 收益，未证明具有实际必要性。若首要目标是简洁、可解释且诚实的均分估计，建议先报告 stratified mean/difference；仅在明确需要残差审计保证时讨论 SCFD 的代价。排序用途须单独验证，不能以 MAE 代替。

**失败与修订透明性。**初次主运行完成 42 cells 后，因源 Rasch 公共平移方向未收敛而中止；沿似然不变方向精确最小化二次先验后，作废并重跑全部主 cells（`logs/main_pre_optimizer_fix.log`、`logs/optimizer_repair.json`）。MIRT 最初四个 smoke cells 使用 cap=250，部分到顶；只按源优化状态将 cap 改为 1000，并全网格重跑，保留 `logs/irt_initial_fit.log` 和初始输出。最终源拟合成功不等于全局最优或未保存的目标收敛保证。绘图曾因 pandas 属性名冲突失败并修复（`logs/analysis_pandas_failure.log`）；排序修复按上一节公开记录，不能把错误结果保留作未修复“局限”。这些修订不是按目标误差挑选有利运行。

**尚未回答的问题。**未完成完整 Bayesian/GPIRT、原版 confidence anchors、神经过程/RL 自适应选题及完整 metabench 复现；没有家族或时间 holdout、单模型 score-CI 覆盖率、排序置信保证或自适应停止实验。二值矩阵不支持新题文本泛化主张，平坦均分也可能不同于官方场景/学科加权分。13 库共享模型池、仅五 seeds、重复 mask 只覆盖小型固定目标面板；重复行分组不能证明模型独立。保留上游常数/重复列及端点行，是透明取舍，不是数据语义真实性认证。有限 PRNG、未测峰值内存及跨 BLAS 非逐位一致性也限制复现解释。

**下一步。**先围绕“诚实审计买到什么、付出多少”收紧论文贡献，再预先冻结家族/时间与覆盖率新协议；若加入更完整模型或自适应方法，必须实现并实际运行后另列结果，不能把当前缺项写成已完成。稀疏公开子集可能漏掉罕见失败并诱导过拟合；重要决策应保留全量评价与随机刷新，平均分精度不构成安全/公平保证。

**复现入口（供后续执行，本报告未重跑）：**

```bash
python -m pip install -r /work/requirements.txt
python /work/src/download_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest /work/tests -q
python /work/src/audit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python /work/src/run_experiments.py --jobs 8
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python /work/src/diagnostics.py --jobs 8 --reps 200
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python /work/src/run_experiments.py --regimes gap --budgets 50 --jobs 8
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python /work/src/irt_comparator.py --jobs 8
python /work/src/nearest_source.py
OPENBLAS_NUM_THREADS=1 python /work/src/analyze.py
python /work/src/build_paper.py
```

已有 cells 默认缓存；更改代码/配置后完整重跑主/gap/MIRT 网格须给相应 runner 加 `--force`。现行 runner 已采用十位小数排序政策；复现不需把旧修复 ledger 再覆盖。`src/analyze.py` 生成上述表图，`src/build_paper.py` 编译并复制到根 `paper.pdf`。

**交付状态：**根目录提供 `paper.pdf`、完整 LaTeX 归档 `paper_source.zip`、代码/结果归档 `code_and_results.zip` 与 `README.md`。数值核验覆盖 **23,010 条指标记录**与 **1,170 项排序不变量**；PDF 页数、官方 style 原样哈希及 ZIP 完整性/校验和见 `artifacts/final_verification.json`。LaTeX 入口为 `paper/main.tex`。ZIP 的结构测试不代替实验科学有效性审核。

```bash
python -m zipfile -t code_and_results.zip
python -m zipfile -t paper_source.zip
python src/verify_artifacts.py
```

## Sources

本报告没有新增网络访问或引文；仅沿用已读取的七篇白名单原论文、指定固定仓库及官方模板。文献版本/读取边界见 `literature/reading_notes.md`、`paper/references.bib`，模板溯源见 `literature/template_rules.md`。未进行引用追踪或禁读论文身份推断；允许正文内普通引用、模板样例书目及 handbook 延伸阅读标签的偶然显示已披露，未打开其链接，不保证绝无偶然提及。

1. Vivek et al. *Anchor Points: Benchmarking Models with Much Fewer Examples*. arXiv:2309.08638v2. https://arxiv.org/pdf/2309.08638
2. Polo et al. *tinyBenchmarks: evaluating LLMs with fewer examples*. ICML 2024；arXiv:2402.14992v2. https://arxiv.org/pdf/2402.14992
3. Kipnis et al. *metabench – A Sparse Benchmark of Reasoning and Knowledge in Large Language Models*. ICLR 2025；arXiv:2407.12844v2. https://arxiv.org/pdf/2407.12844
4. Pacchiardi et al. *100 instances is all you need: predicting the success of a new LLM on unseen data by testing on a few instances*. arXiv:2409.03563v1. https://arxiv.org/pdf/2409.03563
5. Li et al. *Active Evaluation Acquisition for Efficient LLM Benchmarking*. arXiv:2410.05952v1. https://arxiv.org/pdf/2410.05952
6. Zhang et al. *How Benchmark Prediction from Fewer Data Misses the Mark*. arXiv:2506.07673v2（实际读取 2026 修订版）. https://arxiv.org/pdf/2506.07673
7. Balkır et al. *Confident Rankings with Fewer Items: Adaptive LLM Evaluation with Continuous Scores*. arXiv:2601.13885v2. https://arxiv.org/pdf/2601.13885
8. 指定数据/代码仓库： https://github.com/socialfoundations/benchmark-prediction/tree/55faff496947789f94e6b5908c77cbc3e84f81ad （保留仓库 MIT 声明；不推定覆盖全部上游内容许可）。
9. NeurIPS 2026 官方格式与规则： https://neurips.cc/Conferences/2026/CallForPapers ；https://neurips.cc/Conferences/2026/MainTrackHandbook ；https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip 。
