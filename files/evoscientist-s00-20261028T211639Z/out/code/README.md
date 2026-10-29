# 小图上随机游走覆盖时间的简单预测 (n ≤ 30)

论文：`paper/main.pdf`（根目录也有一份 `paper.pdf`），使用 ICLR 2026 官方 LaTeX 模板，来源 https://github.com/ICLR/Master-Template 的 `iclr2026/` 目录。

## 主要结论（全部由 `code/cover.py` 生成）
- 共 126 个图，来自 13 个图族，顶点数 n ∈ {8,12,16,20,24,30}。目标量是最坏起点覆盖时间，用两阶段蒙特卡洛估计，相对标准误中位数 1.1%，最大 2.2%。在 18 个有闭式解的图上做了验证，最大 |z| = 2.25。
- 四特征幂律 `C ≈ 0.56 n^0.83 dmax^0.70 D^1.28`（同时用了 log m，但其系数约为 0）的平均绝对对数误差（MAE_log）：留一图族交叉验证为 0.233 [0.195, 0.272]，5 折交叉验证为 0.174。对比：上界 2m(n-1) 为 2.19（中位数高估 8.5 倍）；用精确击中时间计算的 Matthews 上界为 0.567。目标量中的蒙特卡洛噪声只让 MAE 变化约 0.001（标准差）。
- 在路径、环、树、杠铃图、轮图和完全二部图上可靠，平均偏差在 6% 以内。棒棒糖图和完全图被低估约 2 倍，星图也偏低；网格和 ER 随机图被高估。这是经验预测，**不是上界**。

## 环境
Python 3.11，numpy 2.4，scipy 1.17，networkx 3.6，matplotlib 3.11。只用 CPU。
```
pip install -r requirements.txt
```

## 复现
```
python code/cover.py                                   # 约 30 秒（多进程）
latexmk -pdf -cd -interaction=nonstopmode paper/main.tex
```
- 随机种子：主种子 `MASTER_SEED = 2026`。每个图的随机数流由 `np.random.default_rng([2026, graph_id])` 生成；随机图实例的种子也由主种子确定，因此重复运行的输出逐位相同（已验证）。
- 蒙特卡洛设置：阶段 1 对每个起点跑 R1=256 条游走，选出经验最坏起点；阶段 2 在该起点重新跑 R2=2000 条独立游走，用来估计覆盖时间。置信区间由图级 bootstrap 得到（2000 次重抽样）。蒙特卡洛不确定性的传播方法：把目标量按其标准误扰动 200 次，每次重新拟合并评分。

## 文件
- `code/cover.py`：生成图、模拟、计算精确击中时间和 Matthews 界、交叉验证、消融实验，并输出图表。
- `results/graphs.json`：每个图的统计量、覆盖时间估计、标准误和各个上界。
- `results/summary.json`：所有预测器的误差、置信区间、分图族偏差、全数据拟合系数和消融结果。
- `results/exact_checks.json`：闭式解验证。`results/run_log.txt`：运行日志。
- `results/table_*.tex`、`paper/figs/*.pdf`：论文中的表和图。

## 访问限制说明
整个过程只访问了 GitHub 上的 ICLR 模板仓库，没有检索或访问任何回答本研究问题的论文，也没有访问引用或讨论此类论文的页面。参考文献仅限任务给出的起步文献，以及 Matthews (1988) 和 NetworkX 这两条标准引用。
