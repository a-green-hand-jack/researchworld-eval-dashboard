# 网络干扰下回归 GATE 估计：论文与复现材料

## 交付入口

- **`paper.pdf`**：完整英文论文，NeurIPS **2026 官方主会模板**，正文 8 页（最终页数见 `artifacts/final_verification.json`），参考文献、证明/实验附录、官方完整 checklist 另计。
- **`paper/main.tex`**：主 LaTeX 源；`paper/neurips_2026.sty` 与官方原件字节一致；所有图、生成表格和 checklist 同目录。
- **`code_and_results.zip`**：便携代码、论文源、模拟原始结果及汇总。为避免不明确的再分发许可，不包含下载的原始论文、官方模板 ZIP 和原始/转换后的公开图；复现时由 `fetch_data.py` 从给定来源获取。
- **`final_report.md`**：中文研究摘要、主要证据及局限。
- **`artifacts/analysis/`**：全量汇总、逐图种子指标、配对比较、可用性和核验结果。

这是一份独立执行、如实报告的研究稿，不是已投稿/录用论文。LLM 参与研究设计、证明、实现、分析和写作；没有真人专家审批或完整新颖性/数据权利背书。源访问限制、数据许可疑点、未实现的比较和失败工具调用均有披露。

## 核心问题与结果

研究固定特征回归把混合分配下的拟合外推到“全处理减全对照”时的误差。条件 MSE 恰等于端点条件偏差平方加协方差加权的回归对比方差。该恒等式是模拟中的审计工具，**不能**用观测拟合误差识别未知端点偏差。

- 固定 n=1000，正确 Add 回归的 Bernoulli 线性机制 RMSE：度8为 **0.197（MCSE 0.005）**，度128为 **0.777（0.019）**。
- 多加正确但不必要的特征可能显著增大外推方差；规则图度128的 Quad RMSE 为 **6.872**，不是更好的因果估计。
- 平衡分配下二次失配的平均偏差可能由互补对称性抵消；regular32 的 Add 偏差在 p=.2/.5/.8 为 **−.558/−.005/.592**，对应 MCSE **.019/.012/.020**。
- threshold 干扰可以在观察支持上几乎无信号残差，但缺失一个完整的全局溢出效应；正确阈值基函数也可能完全秩亏。
- ego-Facebook 上，相关误差仍有单位边际方差，但 Add 的 iid 区间覆盖率仅 **.480**（Wilson 95% [.424,.536]）；已知协方差诊断为 **.950**（[.919,.969]）。这不是可用的未知协方差估计方案。
- 聚类不是一致更优；Háj​ek 空暴露、OLS 秩亏、HT 概率下溢均保留。稀有暴露 HT 的全部零估计/零经验 MCSE **不证明**真实有偏或精确。

原始主实验为 12,000 个分配/噪声实验，预设规模与分配敏感性另12,000，共 **24,000**；每个实验共享处理分配和噪声，生成7机制×10方法的记录。因此1,680,000行不是这么多个独立实验。

## 环境

Python **3.11.15**；精确版本在 `requirements.txt`、`environment.json`。仅 CPU，一条 BLAS/OpenMP 线程，无需 GPU。系统为 Linux x86-64，暴露40逻辑CPU；CPU型号不可读，没有绕过沙箱限制。需要约1GB可用存储足够本任务版本；实际体积见最终核验。主模拟峰值内存未测量，不能宣称精确内存上限；最终分析峰值RSS约 **446 MiB**，来自 `artifacts/analysis_resources.json`。

另需系统提供 **pdflatex、latexmk** 及常见 TeX 包（官方 NeurIPS 样式、amsmath、hyperref、booktabs、graphicx、microtype 等）。重绘图表不需要下载或读取任何新论文。

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## 全量复现

在解压后的工作区根目录执行。**模拟脚本覆盖各自 suite 的结果文件**，不会自动追加。先备份交付的 `artifacts/{main,size,allocation}`。脚本默认阻止覆盖，只有明确设置开关才继续：

```bash
ALLOW_OVERWRITE=1 bash reproduce.sh
```

等价的逐步命令：

```bash
python fetch_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q test_gate.py test_reporting.py
python run_experiments.py --suite main --reps 300
python run_experiments.py --suite size --reps 200
python run_experiments.py --suite allocation --reps 200
OPENBLAS_NUM_THREADS=1 python analyze.py
OPENBLAS_NUM_THREADS=1 python plot_results.py
python prepare_paper.py
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error paper/main.tex
python verify_artifacts.py
```

`verify_artifacts.py`复制最终 PDF 到根目录、检查官方样式/checklist/页数、重放5个已交付主实验分配、核验数值，并生成最终验证报告。`prepare_paper.py` 依赖 `paper/template/official_2026/` 中三个已交付官方文件，不需原始ZIP。

### 仅使用已交付结果重建论文

```bash
OPENBLAS_NUM_THREADS=1 python analyze.py
OPENBLAS_NUM_THREADS=1 python plot_results.py
python prepare_paper.py
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error paper/main.tex
python verify_artifacts.py
```

### 实测耗时（本机，非跨平台保证）

| 阶段 | 实测秒数 |
|---|---:|
| 5次重复/单合成图种子的先导（不纳入论文结果） | 60.2 |
| 主实验，300重复 | 241.1 |
| 规模敏感性，200重复 | 133.1 |
| p=.2/.8敏感性，200重复 | 55.5 |
| 最终统计汇总与严格完整性验证 | 约48 |
| 全部15项测试 | 约4 |

主试验加两套敏感性约7.2分钟；安装、下载、图表和LaTeX另计。保守允许约15–30分钟完成整个CPU复现，具体随硬件/网络/TeX环境变化。原始资源预算是数十CPU小时的估计，而本研究范围实际更小。

## 数据获取、版本与处理

`fetch_data.py`只访问用户给定URL和数据/政策页面，不进行搜索。它保留压缩包、校验哈希、清理自环/重复存储、无向化并保存稀疏矩阵。模拟如有多个分量则保留最大分量；实际公开图保留节点/边计数与给定版本一致。没有导入人口属性或真实实验结果。

| 数据 | URL/来源 | SHA256（原始下载） |
|---|---|---|
| SNAP combined ego-Facebook，4039点/88234边 | `https://snap.stanford.edu/data/facebook_combined.txt.gz` | `125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7` |
| Facebook100 Stanford3，11586点/568309边 | `https://nrvis.com/download/data/socfb/socfb-Stanford3.zip` | `b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d` |

SNAP文件时间戳2013-07-16；Stanford压缩包服务器给定版本时间2024-01-08、内部矩阵2012-12-30。实际HTTP元数据/字节数在 `data/manifest.json`（如缓存已存在可能不重复获取Last-Modified）。Stanford矩阵头实际只有单个 `%`；不要错误地把首个维数行当边。

来源与署名：SNAP页面署名 J. McAuley、J. Leskovec，*Learning to Discover Social Circles in Ego Networks* (NIPS 2012)；Stanford源为 Traud、Mucha、Porter，仓库要求署名 Ryan A. Rossi、Nesreen K. Ahmed，*The Network Data Repository with Interactive Graph Analytics and Visualization* (AAAI 2015)。已实际读取Traud原文和数据/政策页；后两篇原文在尝试的直达URL不可用，论文据已读页面如实注明来源，不冒称阅读过原文。详见 `artifacts/data_source_notes.md`。

仓库政策称 **CC BY-SA**，已读文本没有确认版本；保留来源、条款和转换说明，不臆造版本。SNAP页面未列许可，不能把“可下载”冒充“任意再分发授权”。便携包不含原始/转换后的公开图。请在进一步发布前解决许可与完整署名要求。新代码MIT许可不覆盖第三方数据、论文PDF或官方样式。

## 配置、随机性与指标

- 合成图种子11、23、37；先导只用11，generic config种子列表不替代实际 `graphs.json`。
- 分配/噪声：`SeedSequence([20261102,suite_code,graph_index,design_index,rep])`；顺序在 `run_experiments.py::configurations`；跨设计不共享RNG，不能伪配对。
- 自变量：own treatment、neighbor fraction、平方、排除返回原点的归一化两步暴露、度缩放计数及交互；`gate.py`内统一计算全处理/全对照端点。
- 每个固定图/分配重复独立重抽高斯误差；同一次实验的各潜在结果共享同一误差向量，因此GATE误差项在端点相消。区间覆盖率是模型式重复抽样，不是固定误差日程的设计式保证。
- `status`：`ok`、`rank_failure`、`empty_arm`、`empty_exposure`、`zero_numeric_propensity`。失败估计为空，不替换成0。阈值Oracle没有有效结果时RMSE不可用。
- 汇总风险以成功输出为条件；失败率和有效/尝试数必须一起读。三图种子汇总是固定图混合，不是图总体置信区间；成功率不同会改变混合权重。
- **审查后统计修正**：`audit_stats.py`使用全部尝试记录的分层比率影响函数方差，包括有效计数的随机变化；不再只计算成功子集内部方差。`artifacts/analysis_protocol.md`保留原计划，`analysis_amendment.md`说明修正。极少成功数、HT未观察到尾部仍不能由delta MCSE保证精度；CSV有`precision_warning`。
- `validate_results.py`严格检查配置所规定的全部分配键和重复号、每次10×7组合、允许状态、有限成功值和缺失失败值。运行日志/总行数除70不能替代此检查。

## 每张图表的生成映射

| 论文内容 | 生成脚本 | 输入/输出 |
|---|---|---|
| 正文表1 RMSE | `analyze.py` | raw `runs.csv.gz` → `paper/generated/rmse_table.tex` |
| 正文表2 偏差/暴露可用性 | `analyze.py` | raw → `support_table.tex`；明确有效/尝试计数 |
| 附录表3 图统计 | `run_experiments.py` + `analyze.py` | `artifacts/main/graphs.json` → `graph_table.tex` |
| 图1 度/规模 | `plot_results.py::degree` | `summary.csv` → `paper/figures/degree.{pdf,png}` |
| 图2 端点偏差/覆盖率 | `plot_results.py::failure` | `summary.csv` → `failure.{pdf,png}` |
| 图3 分配敏感性 | `plot_results.py::allocation` | `summary.csv` → `allocation.{pdf,png}` |
| 附录图4 RMSE热图 | `plot_results.py::heatmap` | `summary.csv` → `heatmap.{pdf,png}`；星号单元格标有效/尝试数 |
| 数值宏 | `analyze.py` | raw → `paper/generated/numbers.tex`，`claims.json` |

每张图另有同名 `_data.csv`，图表中的经验数字都来自已运行记录。理论常数、参数及精确二项式界不是伪实测。`test_reporting.py`的人工小矩阵是单元测试夹具，绝不当作研究结果。

## 文件组织与审查记录

- `gate.py`：数据生成、特征、权重、协方差和暴露计算。
- `run_experiments.py`：固定配置与完整循环；`fetch_data.py`：受限来源数据。
- `analyze.py`、`audit_stats.py`、`validate_results.py`：汇总和严格验证。
- `test_gate.py`、`test_reporting.py`：15项测试。
- `artifacts/{main,size,allocation}`：原始压缩逐次结果、分配支持诊断、配置、图清单、实际运行时间。
- `artifacts/analysis/{summary,per_seed,paired,support_summary,decomposition}.csv`：所有方法/场景，含负面和不可用结果。
- `artifacts/{paper_review,review_resolution,theory_audit,final_theory_audit,results_audit}.md`：独立自审、原始问题与修订。首次审查发现并已修正成功条件混合MCSE问题；旧审查不是最终状态证明。
- `artifacts/access_log.md`、`access_addendum.md`、`sources/*access*.json*`：仅白名单访问、错误及原文阅读范围。
- `research_request.md`、`todos.md`：任务与研究计划。

## 没有完成/不应声称完成的工作

没有实现ReFeX-LASSO或其selection-aware bootstrap、GNN、未知网络下推断、最优聚类设计、真实平台效果验证、图总体推广、完整不受限文献新颖性检索或数据权利清查。失败的工具/下载尝试不当成成功。额外正确特征、聚类和岭回归都没有被包装成普遍胜者。详见论文局限、checklist及 `experiment_log.md`。
