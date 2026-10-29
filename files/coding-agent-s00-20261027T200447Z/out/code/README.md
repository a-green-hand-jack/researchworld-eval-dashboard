# 小图随机游走覆盖时间：可复现实验

论文为英文，使用**官方 NeurIPS 2024 LaTeX 模板**，PDF 共 4 页（含参考文献）。本研究预测从均匀随机顶点出发的平均覆盖时间，**不是最坏起点覆盖时间**。

## 文件

- `paper.pdf`：编译完成的论文。
- `paper.tex`、`references.bib`、`neurips_2024.sty`：论文源码和官方样式。
- `experiment.py`：图生成、模拟调用、回归、两种留出评估、不确定性分析和绘图。
- `simulator.c`：无截断的简单随机游走模拟器；运行时自动编译为共享库。
- `predict.py`：使用已拟合系数，对给定图统计量输出预测。
- `requirements.txt`：实际实验环境的锁定 Python 依赖。
- `results/graphs.json`：所有图的边列表、图生成种子和模拟种子，顶点从 0 开始编号。
- `results/walks.npz`：136 个数组，每图 8,192 个原始覆盖时间，共 1,114,112 次轨迹。
- `results/graph_results.csv`：每图均值、标准误、95% 区间、统计量、训练标记和预测。
- `results/summary.json`：汇总误差、区间、各图类型结果、精确公式检查和完整系数。
- `results/prediction.pdf` / `.png`：论文图。
- `experiment.log`、`latex-build.log`：运行及编译日志。
- `ACCESS_LOG.md`、`Styles.zip`：外部访问记录及官方模板原始压缩包。

## 环境与完整复现

运行平台：Linux x86-64，CPython 3.11.2，GCC，Intel Xeon Gold 6230 CPU。无 GPU、无外部数据、无 API 调用。Python 包版本见 `requirements.txt`；主要包为 NumPy、SciPy、NetworkX、scikit-learn、Matplotlib。LaTeX 编译使用 pdfLaTeX 和 BibTeX，需标准 TeX Live 包（包括 natbib、booktabs、microtype）。

在本目录运行（已有 `.venv` 时可跳过环境安装）：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiment.py > experiment.log 2>&1
pdflatex -interaction=nonstopmode -halt-on-error paper.tex > latex-build.log
bibtex paper >> latex-build.log
pdflatex -interaction=nonstopmode -halt-on-error paper.tex >> latex-build.log
pdflatex -interaction=nonstopmode -halt-on-error paper.tex >> latex-build.log
```

若系统提供 `uv` 而缺少 `venv`/pip，可改用：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

主实验在本机数秒完成，含绘图的全流程也远少于数分钟；不含依赖安装。`summary.json` 的 `runtime_seconds` 计至数值分析完成、绘图之前。`graph_simulation_seconds` 包含编译、图生成、模拟及轨迹写盘。安装后实验本身不访问网络。

仅重做分析和绘图：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python experiment.py --reuse
```

默认主种子为 **20261027**。图生成种子由 NumPy Generator 产生；第 `i` 张图（从 1 开始）的模拟种子为 `20261027 + 1000003*i`。评估重采样种子为 `20261027 + 999`。所有图与轨迹种子另存于 `graphs.json`。改变 `--walks` 可调整每图轨迹数；`--reuse` 要求轨迹数与缓存一致。改变设计或轨迹数后，需同步更新论文中的数字；默认命令复现本文结果。不同软件版本或平台可能产生最后几位浮点差异。

预测一个 10 顶点路径图：

```bash
.venv/bin/python predict.py --n 10 --m 9 --max-degree 2 --diameter 9
```

此脚本读取 `summary.json` 中规模留出模型的完整系数，不会重新拟合。它只做基本数值范围检查，不验证四个统计量是否确实对应同一张图。直径以边数计；输出单位为步。实证范围为 6–30 顶点。

## 设计与主要结果

规模为 6、8、10、12、16、20、24、30。每个规模包括路径、环、星、完全图、梯形网格、棒棒糖和杠铃图各 1 张，以及随机标号树和条件于连通的 ER 图各 5 张，共 136 张。细节见论文及 `generate_graphs()`。每张图独立均匀抽取起点，不设轨迹长度上限。

固定训练规模为 6、10、16、24，测试规模为 8、12、20、30。第二协议逐一留出整个图类型，其余类型所有规模用于训练。模型输入为顶点数、平均度、最大度、直径的对数，训练集标准化后使用 alpha=1 的岭回归；没有在测试集上调参。基线为训练集校准的 `a*n*log(n)` 和理论上界 `2*m*(n-1)`。

| 指标 | 结果 |
|---|---:|
| 规模留出模型 MAPE | 13.79% |
| 规模留出拟合 n log n 基线 MAPE | 40.52% |
| 将通用上界视为点预测的 MAPE | 863.37% |
| 模型 MAPE 的模拟噪声 95% 区间（含重新拟合） | [13.63%, 13.94%] |
| 模型 MAPE 的测试图重采样 95% 区间 | [11.61%, 16.30%] |
| 整类留出总体 MAPE | 17.81% |
| 整类留出棒棒糖 / 随机树 MAPE | 42.29% / 10.52% |
| 每图均值 95% 区间相对半宽：中位数 / 最大值 | 1.27% / 2.54% |

32 个路径、环、星和完全图实例与精确均值相比，最大偏差为 2.02 个蒙特卡洛标准误；31/32 的近似 95% 区间覆盖精确值。各图模拟区间采用样本标准差除以轨迹数平方根；500 次正态均值扰动及重新拟合估计模拟噪声对总体误差的影响。2,000 次图级 bootstrap 仅描述固定模型下对当前经验图混合的敏感性，不能当作覆盖所有小图的置信保证。

本数据中树与 ER 图数量较多，主指标按图等权；按类型等权的规模留出和整类留出 MAPE 分别为 15.14% 和 20.82%。模型没有理论误差保证；这次小规模实验不能外推到任意图、最坏起点、加权图或有向图。预测优于上界不等于改进该上界定理。

## 模板和访问限制

`neurips_2024.sty` 原样复制自官方 `Styles.zip`；论文使用 preprint 选项，仅在 `paper.tex` 中将默认 “Under review” 页脚替换为独立研究报告说明，避免暗示正在投稿。没有修改模板布局和样式文件。起步文献仅引用任务提供的信息，没有下载或浏览其原文，也没有检索回答本问题的原始论文及引用或讨论它的页面。网络文档访问仅用于官方模板，详见 `ACCESS_LOG.md`。
