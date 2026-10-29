# 小图随机游走覆盖时间：可复现经验研究

论文为英文，使用 ICLR 2026 官方 LaTeX 样式（未修改样式文件）。本报告未投稿，也不声称获得会议接收。

## 主要产出

- `paper.pdf`、`paper.tex`：编译论文及源文件，含方法、实验、局限与参考文献。
- `experiment.py`：图生成、固定划分、拟合、误差评估、两类不确定性和绘图。
- `simulate.cpp`：CPU 简单随机游走模拟器，每次游走重新均匀抽取起点，无步数截断。
- `write_tables.py`：从结果自动生成论文表格。
- `results/graphs.json`：78 张图的元数据、种子与完整边列表。
- `results/walks.csv`：78 行，每行 4,000 个独立游走长度，行顺序对应 graph id。
- `results/estimates.csv`：逐图均值、标准误、近似 95% MC 区间、预测值。
- `results/summary.json`：全精度模型系数、汇总结果、精确公式校验、运行时间。
- `results/prediction.pdf`、`results/prediction.png`：实验图。
- `vendor/`：官方模板压缩包、原样提取的样式文件及来源说明。

## 环境与命令

已在 Linux、Python 3.11.2、g++（C++17）、pdfLaTeX/TeX Live 环境执行。实验仅用 CPU。Python 库版本锁定在 `requirements.txt`；不需要 sklearn、外部数据、API 或账号。需具备编译器和 LaTeX 的常用包（times、natbib、fancyhdr、eso-pic、amsmath、booktabs、graphicx、hyperref）。

```bash
cd /work
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python experiment.py
.venv/bin/python write_tables.py
TEXINPUTS="$PWD/vendor:" pdflatex -interaction=nonstopmode -halt-on-error paper.tex
TEXINPUTS="$PWD/vendor:" pdflatex -interaction=nonstopmode -halt-on-error paper.tex
```

若没有 uv，可用 `python3 -m venv .venv` 和 `.venv/bin/pip install -r requirements.txt`。现有环境已配置好，可直接从运行实验的命令开始。脚本使用自身所在目录定位文件。运行会覆盖 `results/` 下对应生成文件。也可执行 `bash reproduce.sh`。

本机编译加全部模拟约 2 秒；包括导入库、拟合和绘图的实验总耗时为数秒。首次依赖安装、LaTeX 编译不计入模拟时间。无须扩大扫描。

## 随机性、定义与实验设计

- 主种子 `20261027`，NumPy 默认生成器用于图生成。第 i 张图（从 0 起）的游走种子为 `20261027 + 100003*(i+1)`，C++ `std::mt19937_64`；抽样采用 `uniform_int_distribution`，避免取模偏差。
- 不确定性重采样种子为 `20261028`；图 bootstrap 4,000 次，MC 标签扰动及重拟合 2,000 次。
- 相同软件与 C++ 标准库实现下结果确定。不同 C++ 标准库的整数分布实现可能给出不同逐次游走序列；完整边列表和原始游走已保存。
- 目标为**均匀随机起点**的期望覆盖时间，初始顶点在零步已访问；不是最坏起点覆盖时间。
- n 为 8、12、16、20、24、28。每个规模含路径、环、星、完全图、4×(n/4) 网格各一张；连通 ER 图和均匀标号树各三张。ER 的 p=3/(n−1)，拒绝非连通样本；树用独立均匀 Prüfer 序列。
- 训练：上述七类图的 n=8、12、20、24，共44张。熟悉图族测试：n=16、28，共22张。
- 新图族测试：各规模一张杠铃图和棒棒糖图，共12张。杠铃图两端团大小 k=max(3,floor(n/4))，内部路径顶点数 n−2k；棒棒糖图的团和尾部路径各占 n/2 个顶点。脚本检查测试图与训练图无同构重复。
- 对四个对数特征（n、平均度、直径、最大度）按训练数据标准化；岭惩罚固定为1，截距不惩罚。未根据测试结果选择超参数。

## 结果解读

四统计量模型的平均绝对百分比误差：熟悉图族 **15.6%**，新图族 **32.3%**；拟合的 `a*n*log(n)` 基线为41.9%、55.5%。理论上界 `2m(n−1)` 用作数值预测时误差为1576.3%、174.1%；上界本来用于保证，不是经拟合的点预测。

网格平均高估55.6%，棒棒糖平均低估47.8%。因此不能从整体平均误差推出每个图族都可靠。18项路径、环、完全图精确公式校验均在1.42个估计标准误以内。

逐图 MC 区间用样本均值 ±1.96×标准误计算。MC 标签扰动重拟合得到的 MAPE 近似95%区间为15.23%–15.97%、31.60%–33.01%。它们条件于固定图集合，只传播模拟误差。另行给出的图 bootstrap 区间反映测试图组成敏感性，固定训练拟合，不是对所有连通图的总体保证，也不是家族层级 bootstrap。样本小、图族/规模人为选取、家族权重不等；结论不覆盖所有 n≤30 的图或最坏起点。

## 访问限制

未搜索或访问回答本研究问题的原始论文、镜像或引用/讨论页面。论文仅引用任务提供的三条起步文献作为背景，未下载或打开这些文献。唯一与论文写作有关的外部访问是会议模板地址及官方 ICLR 模板仓库；具体 URL 和失败请求见 `ACCESS_LOG.md`。软件依赖由包管理器安装，无外部研究数据。
