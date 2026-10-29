# 小图随机游走覆盖时间：复现实验

论文：`paper.pdf`；LaTeX 源码：`paper.tex`。使用随附、未经修改的 ICML 2025 官方样式（`template/`）。这是一项独立实验报告，并非 ICML 已录用论文。

## 环境与命令

原始运行环境为 Debian Linux、Python 3.11.2、g++ 12.2、CPU。Python 依赖固定在 `requirements.txt`；编译论文还需要 TeX Live（pdflatex、bibtex、latexmk）。不需要 GPU、账号、外部数据或研究 API。

```bash
cd /work
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
TEXINPUTS=./template: BSTINPUTS=./template: latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
```

第一条实验命令编译 `simulate.cpp`、生成图、模拟并分析，生成所有 CSV、JSON、图和 LaTeX 表格。已有原始样本时，可用 `.venv/bin/python run.py --reuse` 仅重做分析。默认进行 500 次 bootstrap，`--bootstrap` 可以修改该次数；论文使用默认值。复现全部依赖的确切版本另存于 `environment.txt`。

## 实验定义与设计

目标为均匀随机起点下的期望覆盖步数；初始顶点在第 0 步计为已访问。不估计最坏起点的覆盖时间。所有图都是简单无向连通图，n 为 8、12、16、20、24、28、30；训练尺寸为 8、12、20、28，测试尺寸为 16、24、30。没有测试集调参。

共 10 类图：路径、环、星、完全图、截断矩形网格、稀疏 ER、稠密 ER、均匀标号树、棒棒糖、杠铃。三个随机族每个尺寸 4 张，其他族每个尺寸 1 张，共 133 张（76 训练，57 测试）。生成器的具体参数见 `run.py:graphs` 和论文。ER 图使用拒绝采样，条件是连通，不通过强行补边修复。

每图 4,000 条独立、无截断轨迹。全局图种子为 **20261027**；每图图种子、游走种子和完整边表在 `results/graphs.json` 中。游走种子为 `20261027 + 100000 + graph_id`。模拟器采用 C++ `mt19937_64` 和均匀整数抽样。在相同 C++ 标准库和编译环境下可逐样本复现；不同标准库的 `uniform_int_distribution` 不保证逐位相同，但实验定义相同。bootstrap 种子为 **20261029**。

模型使用四个对数统计量：n、m、最大度、直径；平均度 2m/n 与前两个冗余。训练集内加权中心化、标准化，在对数目标上拟合岭回归；截距不惩罚，lambda=0.01，训练损失对每类图等权。比较模型为仅使用 log(n) 的同样回归，以及通用上界 2m(n-1)。预测未经截断或校正。尺寸分割外，另做整类留出（LOFO）：每次用另外 9 类所有尺寸训练，预测被留出的整类所有尺寸。LOFO 不与尺寸分割混为同一评估。

指标为按图类型等权的 MAPE，以及 exp(平均绝对 log 误差)。每图覆盖时间区间为 iid 样本均值的 Student-t 近似 95% 区间。指标区间将每图的 4,000 样本分为 40 个独立、等大的块，对块均值独立重采样，重新拟合模型再重新计算指标；报告 500 次重采样的 2.5%、97.5% 分位数。这些仅为**固定图集合上的蒙特卡洛不确定性**，不是图总体泛化区间、单条轨迹区间或预测区间。没有将 4,000 条轨迹当作 4,000 张独立图。

## 文件

- `simulate.cpp`：CPU 随机游走模拟器，不设步数上限。
- `run.py`：图生成、统计量、拟合、验证、bootstrap、绘图和表格。
- `predict.py`：用保存的四统计量模型预测一个指定描述符组合。
- `results/graphs.json`：全部图、参数和种子；`simulation_input.txt`：模拟器输入。
- `results/cover_times.txt`：第 i 行为 graph_id=i 的 4,000 个原始覆盖步数。
- `results/estimates.csv`：逐图均值、标准误、区间、预测和 LOFO 预测。
- `results/summary.json`：汇总指标、区间、验证结果、模型参数和用时。
- `results/fitted_model.json`：尺寸分割训练集上拟合的可部署参数。
- `figures/results.pdf`：论文中的矢量图。
- `ACCESS_LOG.md`：外部访问范围与官方模板来源。

例如，对 n=20 的路径输入四个统计量：

```bash
.venv/bin/python predict.py --n 20 --m 19 --dmax 2 --diameter 19
```

输出约 365.45 步，表示模型预测的均匀起点期望值；它没有上界或精确值保证。

可选的产物检查和 PDF 渲染：

```bash
.venv/bin/pip install -r requirements-validation.txt
.venv/bin/python validate.py
```

这会检查 CSV 与原始轨迹是否一致、官方样式是否保持原样、PDF 是否不超过 4 页，以及原始轨迹是否匹配本次首次运行的 SHA-256；输出 `results/validation.json` 和逐页预览 PNG。当前 PDF 为 3 页，最终完整实验运行约 8 秒，已从头重跑并确认原始样本逐位一致。

## 数值核对与局限

对每个尺寸的路径、完全图和星形图，使用独立的解析公式核对蒙特卡洛均值；核对值和标准化偏差保存在 `summary.json` 的 `exact_checks` 中。这是对模拟实现的核对，不是对任意图的精确求解。所有论文结果来自本次实验；没有借用既有研究的实验结论。样本量很小，只有 n>=8 的已列尺寸，不能推广为所有 n<=30 图的保证。训练后的简单模型没有理论上界性质。
