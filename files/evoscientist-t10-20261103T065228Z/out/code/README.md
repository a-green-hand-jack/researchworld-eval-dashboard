# 固定预测器下的置信区间：论文与复现包

## 主要提交物

- `paper.pdf`：完整英文研究论文，ICML 2026 官方匿名模板；正文（含主图表）不超过 8 页，参考文献和附录另计。
- `paper.tex`, `references.bib`, `icml2026.sty`, `icml2026.bst`：LaTeX 源码及未修改的官方样式。官方来源与哈希在 `template/source.txt`、`artifacts/source_hashes.json`。
- `final_report.md`：中文研究报告。
- `code/`, `tests/`, `requirements.txt`, `requirements.lock`：完整实现、测试、实际依赖版本。
- `artifacts/{main,ablation,exact}/`：实际逐次重复结果和 manifest；`artifacts/tables/`：汇总、配对不确定性、Holm 校正、论文数值宏和表格。
- `figures/`：四组图的 PDF 和 PNG。
- `research_request.md`, `todos.md`, `protocol_amendment.md`, `supplementary_protocol.md`：任务、初始设计和按发生顺序保留的设计补充。
- `ACCESS_LOG.md`, `experiment_log.md`, `paper_review.md`, `theory_audit*.md`, `review_response.md`：访问、失败、独立审计与修订记录。
- `submission.zip` 与 `submission_manifest.json`：便携提交包及哈希，包含论文、源码、实际最终原始 CSV、表图与审计说明；不再分发原始数据和文献 PDF，也不打包冗余历史复跑。数据可用所附脚本重新获取。

**结论不是普遍缩短，也不是新算法优先权声明。** 在预设低误差非线性合成场景，具有数学上有限样本 ≥95% 覆盖保证的二项分量组合，比全预算精确标签区间平均窄 29.14%（配对 MC 95% 区间 29.03–29.25%）。N=n、较大误差及两个真实经验分布中无此收益。Series4 虽有约 48.63% 的模拟宽度下降，但主设置覆盖仅 94.43%，不算满足严格有限样本要求的收益。详见论文与报告。

## 运行环境

- Python 3.11.15；CPU，未使用 GPU、付费 API 或新标签。
- 核心库精确版本：`requirements.txt`。`requirements.lock` 是本次完整 pip 环境快照；最小复现优先安装 `requirements.txt`，不必把所有宿主工具当作研究依赖。
- LaTeX：本机 TeX Live 的 `pdflatex`, `bibtex`, `latexmk`。无需 Python PPI 包进行推断；按论文公式实现。

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
python code/fetch_data.py
python -m pytest -q tests
```

`fetch_data.py` 只请求用户明确允许的两个 Google Drive 数据文件；已有文件则不重复下载，同时检查形状、二元标签、界限、缺失、重复与哈希。它不浏览仓库或发现文献。

## 从已交付结果生成论文（不重跑抽样）

在**工作区根目录**运行：

```bash
python code/analyze.py
latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
python code/verify.py
```

所有主文数值表、全量附录表、四幅图、配对统计和正文数值宏由 `code/analyze.py` 从实际 CSV 生成。PDF 内的理论表达式不是经验结果；数值理论诊断另存 `artifacts/tables/analytic_diagnostics.json`。编译不需要联网。

## 从头复现实验

脚本为防证据覆盖，发现同名原始 CSV 会报错。**不要在已有证据目录删除文件来运行。** 推荐建立一个只复制源码、样式和数据的独立目录：

```bash
mkdir -p verification/fresh_run
cp -r code tests verification/fresh_run/
cp -r data verification/fresh_run/
cp requirements.txt verification/fresh_run/
cd verification/fresh_run
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p artifacts
python code/fetch_data.py
python -m pytest -q tests
python code/run_experiments.py --mode smoke
python code/run_experiments.py --mode main
python code/run_experiments.py --mode ablation
python code/run_exact.py
python code/analyze.py
```

复制的是已有源码与未改动的原始数据，不包含原始结果。也可保留当前根目录，单独复验而不供默认分析使用：

```bash
python code/run_experiments.py --mode main --output my_replay_main
python code/run_experiments.py --mode ablation --output my_replay_ablation
python code/run_exact.py --output my_replay_exact
```

`--output` 只更改 `artifacts/` 下的输出子目录，不改变种子或配置；默认 `analyze.py` 读取 `main/ablation/exact`。这些复验不是新增独立统计证据。若只需要测试，`--mode smoke` 为 5 次重复。脚本定位根目录依据其自身路径，所以复制源码到独立目录后不会写回原项目。

本机初次主实验约 277 秒，消融约 76 秒，精确区间补充约 109 秒，均为单线程数值计算的实际墙钟时间；最终数值稳定性复验耗时另见 manifest。预计同级 CPU 全部统计实验约 8–12 分钟；下载、分析、LaTeX 和阅读不计入该估计，其他硬件可能不同。内存主要由分析单个 CSV 使用，不需 GPU。

## 数据、版本与估计目标

数据从 `ppi-python==0.2.3` 轮子的 `ppi_py/datasets/datasets.py` 得到以下固定 ID，未浏览仓库：

| 数据 | 文件 ID | 原始行数 | 用途 |
|---|---|---:|---|
| galaxies | `1pDLQesPhbH5fSZW1m4aWC-wnJWnp1rGV` | 16743 | 固定经验联合分布 |
| forest | `1Vqi1wSmVnWh_2lLQuDwrhkGcipvoWBc0` | 1596 | 固定经验联合分布 |

文件 SHA-256、大小、均值、score 范围、重复比例见 `artifacts/data_provenance.json`。未宣称 `.npz` 具有仓库代码的 MIT 许可；独立数据许可未确认。不要据此把数据作为自行授权的数据集再发布。复现代码可重新下载，源码归档可不包含原始数据。

真实数据实验是从**固定经验分布独立有放回抽样**，目标为该分布的已知均值。不是不放回有限总体推断，也不是声称原始科学总体服从 iid。未标注抽样的标签从不传给推断方法。既有 score 原样使用，无训练、无获取新标签。合成真值、条件均值和实际抽样机制在 `code/generators.py`、`run_exact.py` 中完整定义；合成未标注样本不生成标签。

## 随机性、配置与不确定性

- 主种子 `20261103`，NumPy `SeedSequence` 子命名空间：pilot=1, main=2, ablation=3, exact=4。每个配置的子流顺序与 manifest 的 `spawn_key`、`entropy` 一致。
- 同一重复给所有方法相同的 `y,z,u`；五折为 iid 顺序的固定平衡块；pilot 为前 20%，属于原标签预算。
- 固定 B=4、每箱两个全训练均值伪观测、Series ridge=`1e-3/n`、alpha=.05；不按最短区间选择方法。
- Main 103000、ablation 12000、exact 65000，共 180000 次独立设置内重复；方法行数和数值复验不增加独立数据量。
- 覆盖：Wilson 95% MC 区间；宽度：配对均值之比及 delta-method 95% MC 区间；不是宽度分布的 95% 分位范围。
- Holm：四个原始 nonlinear Series4/PPI++ 宽度对比为一组；四个 sharp CPRectHist/LabelCP 为另一组。其他比较、覆盖误差条不作同时推断。
- 数学有限样本覆盖与模拟覆盖分开；观察覆盖 100% 不证明真实覆盖为 1，包含 .95 的 MC 区间也不证明有效性。

## 脚本—数据—图表对应

| 论文对象 | 原始结果 | 生成脚本/输出 |
|---|---|---|
| 表 1（asymptotic） | `artifacts/main/*_n1000_N10000.csv` | `analyze.py` → `tables/asymptotic.tex` |
| 表 2（exact） | `artifacts/exact/*.csv` | `analyze.py` → `tables/exact.tex` |
| 图 1 `main.pdf/png` | main 中五种 law | `analyze.py:figures` |
| 图 2 `exact.pdf/png` | exact sharp/moderate/real | 同上 |
| 图 3 `ablation.pdf/png` | 独立 ablation linear/nonlinear | 同上 |
| 图 4 `sensitivity.pdf/png` | main nonlinear 三种 n + 明示解析 oracle | 同上；oracle 来自 `generators.oracle_variances` |
| 附录 safety 表 | main rare200 和 shift | `analyze.py` → `tables/safety.tex` |
| 附录全量表 | main/exact/ablation | `analyze.py` → `tables/full_*.tex` |
| 摘要及正文 headline 宏 | 配对聚合 | `analyze.py:facts` → `tables/macros.tex`, `facts.json` |
| 覆盖、偏差、RMSE、宽度标准误 | 各 raw CSV | `tables/summary.csv` |
| 配对比值/差值、MC 区间 | 同一重复内配对 | `tables/paired_ratios.csv` |
| 预设 Holm 家族 | 上表筛选 | `tables/primary_holm.csv` |
| 理论数值诊断（明确非实测） | 推导公式及冻结参数 | `analyze.py:analytic_diagnostics` → `analytic_diagnostics.json` |

## 审计、已知边界和失败

- `theory.md` 及独立 `theory_audit.md`、`theory_audit_addendum.md` 区分假设、证明和实现；历史发现不删除。
- 原始绝对方差阈值导致微小 score 缩放失效，已去除。后续发现原始二阶矩相减会在 offset+small-scale 下消去方差；最终使用共同锚点、组内中心化与组间方差组合，并增加回归测试。另有一次新增极小尺度直接方差测试失败，进一步在方差 helper 内部锚定后通过；不是被隐藏的失败。
- 早期 main/ablation 在去阈值后 21 CSV SHA 完全一致；最终中心化版本另作全量重放，按浮点容差核对。哈希、差异上界和历史位置见 `artifacts/*check*.json`、manifest 和 `review_response.md`。
- 精确方法是 binomial CP 数学覆盖保证的浮点实现，不是 interval-arithmetic 数值认证。二项网格测试不能代替普遍证明。
- 固定四箱与 U 型边界对齐，是有意阳性对照；没有证明学习优于合适的预设非线性 map，也没有证明所有情况下变窄。
- 真实 n=200 中 Series4 覆盖显著不足；N=n、适度噪声、真实经验分布中 exact 方法更宽；EB 明显保守；分布偏移破坏匹配假设。全部保留。
- 无全领域新颖性证明、无最短区间/全局最优性声明、无真实科学应用效益保证。初始独立自审认为其 ICML 方法新颖性仍有明显不足，不能把“提交物完整”误作“必能达到会议录用标准”。

## 文献访问

仅直接读取允许的 starter PDFs 和与禁读内容无关的 2009 EB 文献；没有开放检索、引文追踪、论文推荐或仓库浏览，也未试图辨认禁止论文。实际阅读范围、下载版本与 URL 见 `ACCESS_LOG.md`、`literature/access.tsv` 和两个阅读笔记。论文只引用实际查阅的六篇方法文献；尚未查阅的 starter 项目不冒充已读引用。
