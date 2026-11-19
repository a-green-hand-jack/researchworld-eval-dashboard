# 组成型响应的保形可靠性评价：交付与复现

## 先读什么

- **完整论文：[`paper.pdf`](paper.pdf)**；LaTeX 源码：[`paper.tex`](paper.tex)，文献库 `references.bib`。
- **中文研究摘要：[`final_report.md`](final_report.md)**。
- **全部实验：** `artifacts/main/metrics.csv`、`controls.csv`、`runs.csv`、300 份 JSON 与拟合/阈值 NPZ。
- **统计结果：** `artifacts/analysis/`（完整精度均值、CI、10 个预先冻结的配对效应、所有维数/分布结果、LaTeX 表格）。
- **审计与限制：** `self_review.md`（修复前审查）、`review_resolution.md`（修复与最终验证）、`deviations.md`、`literature_access_log.md`。

论文使用 **ICML 2026 官方模板的 preprint 选项**，不声称已投稿、在审或录用。正文及正文浮动图表共 **7 页**，不超过初次投稿 8 页上限；参考文献/影响声明/附录另计，总计 23 页。官方模板未改动。公开要求中未发现必须随文附上的独立 checklist；论文包含明确标为自愿的复现清单与必须的 Impact Statement。规则/模板来源详见 `template_provenance.md`；未执行官方在线格式检查。

## 研究对象与主要限制

对象是下一次**实际观测到的组成向量**，而不是分类标签或潜在真实概率。全部为合成数据：3/5/10 个分量、内部 Dirichlet 与单一结构零面混合分布；同一小型训练预测器；源分布与困难组比例变化。没有真实应用、估计密度比、任意概念漂移或多重边界面验证。不能从边际覆盖率、很大体积、或分组修复推导每个输入/结构零响应的名义覆盖。

统一评价包含边际、预设可观测组、已实现零状态覆盖，以及内部/各面/固定混合参考质量。参考质量不是响应概率或应用效用，面探针仍看不到更低维交集。负面结果、维数差异及 MC 精度不足均保留。

## 环境与资源

实际环境（`environment.json`；精确依赖见 `requirements.txt`）：

- Python 3.11.15；NumPy 2.4.6；SciPy 1.17.1；pandas 3.0.6；Matplotlib 3.11.2。
- CPU，4 个进程，每进程 BLAS/OpenMP 单线程；未使用 GPU 或付费 API。
- Python 标准库 unittest，不需要 pytest。初始 6 项测试，交付版 7 项测试通过（`final_tests.log`）。
- LaTeX：`pdflatex`、`bibtex`，以及常规 TeX Live 数学/Times/microtype 包。官方样式及其 helper 位于 `template/`。
- 原始主实验耗时约 22.08 秒（该主机实测，不是跨机器承诺），300 个单元累计 elapsed 83.90 秒；最大单 worker RSS 77,968 KB。含试验、分析和 PDF 的干净复现通常建议预留 **2–10 分钟**，慢 CPU 可更久。资源时长不是 primary result。
- 保存原始结果、300 单元独立 replay 和干净复现仍远低于 10 GB。文件/总大小见最终 `delivery_manifest.json`。

## 数据、许可、随机性

无需下载数据或模型，无账号/协议/第三方数据许可依赖。`experiment.py:generate` 定义全部数据；`plan.md` 与论文附录给出完整公式。每个单元 1,500 train、499 calibration、source/shift 各 2,000 test；alpha=.1。均值、浓度、零概率、组比例、预测器及超参数均固定。`config.json` 是运行配置。

- 主种子：1000–1049（50 个）；pilot：900001、900002；数值校验使用分离的 999990/999991 命名空间。
- RNG：`SeedSequence([seed,K,law,stream])`；stream0/1/2/3/5/20 分别为 train/cal/source-test/shift-test/OOF/probes，独立 pilot 第二池为21。
- Bootstrap 种子 77331、20,000 次；重采样完整 master-seed 向量，维数/分布/方法/源偏移保持配对。95% CI 为逐项描述性；10 个冻结效应另报近似 Bonferroni 调整 99.5% CI，不声称精确 FWER 控制。
- 相同库/CPU 数学环境确定性结果可以逐行重现；不同数值库可能有浮点末位差异。时长、RSS、PDF 日期/哈希可随环境变化。

## 一条命令从零复现（推荐）

在已安装上述依赖的 workspace 根目录运行：

```bash
python reproduce.py --destination reproduction_run --workers 4
```

该目录必须不存在。程序复制所需源文件及官方模板到新目录，依次执行测试、pilot、独立探针与生成器校验、全 300 单元主实验、bootstrap/表格、所有图及完整 PDF 编译。输出位于新目录；不覆盖本交付的任何证据。缺少 LaTeX 时可先执行：

```bash
python reproduce.py --destination reproduction_no_pdf --workers 4 --skip-pdf
```

这不会生成该新目录的 PDF，但交付根目录已有完整 PDF。依赖安装如有必要可用 `python -m pip install -r requirements.txt`；本研究实际没有联网安装依赖。

**重要缓存陷阱：** `experiment.py` 以 seed/K/law 文件名复用已有单元，未校验 config/source hash。不要修改设置后在原 artifacts 目录续跑；`reproduce.py` 强制新目录以规避此问题。不要覆盖原 `main.log`：分析中的资源表读取该次运行的日志末行。科学结果原始证据请保持不可变。

## 分步命令（在干净复制目录）

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest -v test_experiment
python experiment.py --mode pilot --workers 4 > pilot.log 2>&1
python qa.py > qa.log 2>&1
python experiment.py --mode main --workers 4 > main.log 2>&1
python analyze.py > analysis.log 2>&1
python plot.py > plotting.log 2>&1
TEXINPUTS=./template//: pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
TEXINPUTS=./template//: pdflatex -interaction=nonstopmode -halt-on-error paper.tex
TEXINPUTS=./template//: pdflatex -interaction=nonstopmode -halt-on-error paper.tex
```

`--mode smoke` 使用独立种子与较少探针，仅供排错，不进入推断。`verify.py` 是额外全单元 replay 校验：写入新的 `artifacts/replay`，已存在时主动拒绝运行，避免把缓存当作验证。交付中已完成 replay，见 `artifacts/verification.json`；全部 6,300 数字结果逐项相同。不要为重新校验而删除原证据，可在新目录使用该脚本。

## 每张图、表的来源

| 论文对象 | 来源/生成器 |
|---|---|
| Table 1 覆盖率 | `analyze.py` → `artifacts/analysis/source_coverage.tex` |
| Table 2 参考质量 | `analyze.py` → `source_size.tex` |
| Table 3 冻结效应 | `analyze.py` → `contrasts.tex`、`contrasts.csv`、`contrast_seed_values.csv` |
| Table 4 偏移比较 | `analyze.py` → `shift.tex` |
| Table 5 解析几何常数 | `paper.tex` 解析公式/精确分数；不是 MC 结果；证明见论文附录A |
| Table 6 实测闭集对照 | `experiment.py` → `controls.csv`；`analyze.py` → `controls.tex` |
| Table 7 冻结效应定义 | `paper.tex`、`plan.md`，设计定义而非实验结果 |
| Table 8 实测资源 | `analyze.py` → `resources.tex`、`run_summary.json`，源数据 runs.csv/main.log |
| 附录全部 12 个单元表 | `analyze.py` → `full_source.tex`、`full_shift.tex`；完整精度 summary_cells.csv |
| Figure 1 / Figure 2 | `plot.py` → `figures/audit.pdf` / `shift.pdf`（同时 PNG） |
| Figure 3 / Figure 4 | `plot.py` → `figures/sensitivity.pdf` / `strata.pdf`（同时 PNG） |

`figure-spec.md` 与 `figure_audit.md` 记录作图语义、聚合与检查。为避免把接近 1/0 的估计或很窄区间误显示为精确饱和/退化，表格生成器使用自适应精度。精确零探针命中也只是有限 MC 结果。

## 文献访问与研究独立性

没有做组成保形主题搜索、猜测禁读论文身份、引用图遍历、仓库查找或后续论文检索。仅直接访问起步清单中的五篇指定 arXiv 论文及官方 ICML 模板/规则页面。已知范围内没有偶遇禁读内容。全部 URL/阅读范围、真实引用元数据、官方网页存档见 `literature_access_log.md`、`literature_notes.md`、`references.bib`、`sources/`。只引用实际阅读的五篇来源。该受限阅读不能证明贡献优先权或完整相关工作覆盖。

## 诚实性与未完成事项

没有失败主实验、删种子、伪造表格或占位结果。完整 replay 后原数字不变。修复了主设计之外的空加权校准边界实现，保留原冻结代码；仅修改显示精度/文档没有改动原数据。未完成或不做：uniform .01 cellwise MC 目标、whole-simplex fraction 次要诊断、真实数据、多面/顶点响应、官方格式检查、逐页完整视觉检查。没有把这些写成已完成。一般化能力与主会新颖性/贡献充分性仍是实质限制；自审不等于录用保证。
