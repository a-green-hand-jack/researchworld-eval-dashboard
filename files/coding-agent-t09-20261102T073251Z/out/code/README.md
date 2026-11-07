# 网络干扰下回归 GATE 估计：论文与复现包

论文：[`paper/main.pdf`](paper/main.pdf)；LaTeX 主文件：[`paper/main.tex`](paper/main.tex)。
采用 **ICML 2026 官方模板**，正文 7 页，含参考文献、证明、完整结果和复现 checklist 共 16 页。
会议官方要求的 Impact Statement 已填写；下载的 ICML 2026 模板/说明没有独立的
NeurIPS 式 checklist，因此附录另外提供了明确标为作者自拟的已填写复现 checklist。
这是一份研究交付稿，没有投稿或录用声明。

本研究将 GATE 误差分为模型错设与端点外推放大的噪声，证明了公共暴露响应曲率有界时的
尖锐条件偏差界、二次响应的补分配对称性结论，以及高暴露阈值几乎不出现时的不可辨识界。
实际模拟显示：正确指定三次模型也可能大幅增加方差，预测验证不一定选出好的 GATE
估计量，聚类设计依赖图结构；Facebook 低度观测提供的暴露支持有明显作用。
这些结论只覆盖论文所述模型与固定图，不是对真实平台处理效应的估计。

## 环境

实际运行环境：Linux x86_64，Python **3.11.2**，Intel Xeon Gold 6230 @ 2.10GHz；
容器 CPU 配额为 4 核，各模拟进程使用单线程 BLAS，RF 单 worker。无需 GPU。
全部 Python 直接和间接依赖固定于 [`requirements-lock.txt`](requirements-lock.txt)。
主要版本：NumPy 2.2.6、SciPy 1.15.3、pandas 2.3.3、NetworkX 3.5、
Matplotlib 3.10.7、scikit-learn 1.7.2、PyMuPDF 1.26.6。
另在独立目录完整重跑了全部模拟；原始数值、汇总和生成的 LaTeX 表格逐字节一致，
见 `logs/reproduction_comparison.json`。PDF 使用 TeX Live 2022 / pdfTeX 和 latexmk 4.79 编译；官方 2026 样式未经修改。
具体系统与 TeX 版本见 [`logs/system.txt`](logs/system.txt)。

```bash
cd /work
uv venv --python python3.11 .venv
uv pip install --python .venv/bin/python -r requirements-lock.txt
bash reproduce.sh
```

在其他目录解压 `deliverables.tar.gz` 后，先进入 `gate-research/`，再执行上述环境与运行命令
（将第一行 `cd /work` 换成该解压目录）。

没有 uv 时可用 `python3 -m venv .venv`，再通过该环境的 pip 安装同一依赖文件。
系统需安装 `latexmk`、`pdflatex`、`bibtex`，及常规 LaTeX 宏包
（例如 Debian 的 `texlive-latex-extra`、`texlive-fonts-recommended`、`texlive-science`）。
如使用已有 Python 环境：`TASK_PYTHON=/absolute/path/to/python bash reproduce.sh`。

`reproduce.sh` 会覆盖结果、图和 PDF，按正式重复次数重新运行全部实验。
仅需重建论文时：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python code/analyze.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
.venv/bin/python code/audit.py
```

## 数据、版本与访问范围

`code/fetch_data.py` 只下载提供的公开 SNAP 图：
`https://snap.stanford.edu/data/facebook_combined.txt.gz`。
精确文件为 218,576 字节，SHA-256：

```text
125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7
```

4039 节点、88234 条无向边，按原始节点编号排序重标号，没有采样或删边。
文件版本、来源与条款说明见 [`data/manifest.json`](data/manifest.json)；
页面来源和引用见 [`SOURCE_ACCESS.md`](SOURCE_ACCESS.md)。页面没有明确的许可证说明。
打包的复现档不含该图文件，提供校验过的下载脚本；工作目录中保留本次实际使用的下载文件。
所有处理分配、协变量及结果均由代码合成，不使用真实平台实验数据。

没有进行宽泛文献检索、引用追踪或相关文章搜索。仅直接访问了给定起步文献中的五篇、
官方 ICML 格式页面和 SNAP 图页面。访问记录包含一次未成功的来源论文下载；该论文
未作为已查阅文献引用。未观察到受禁止内容的意外接触。完整记录见 `SOURCE_ACCESS.md`。

## 随机性与实验命令

主种子 **20261102**；`study.py` 明确给出所有图种子、各 suite 的 SeedSequence、
固定协变量种子和 RF 种子。敏感性计算及支持消融精确复用主实验相应数据流。
所有正规图都固定图实现，重复只重抽处理与噪声；图实现间不确定性不在本研究范围内。

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
.venv/bin/python code/fetch_data.py
.venv/bin/python code/verify.py
.venv/bin/python code/study.py --mode main --reps 400
.venv/bin/python code/study.py --mode noise --reps 400
.venv/bin/python code/study.py --mode scaling --reps 400
.venv/bin/python code/study.py --mode validation --reps 150
.venv/bin/python code/study.py --mode saturation --reps 400
.venv/bin/python code/study.py --mode sensitivity --reps 400
.venv/bin/python code/support_ablation.py
.venv/bin/python code/analyze.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
.venv/bin/python code/audit.py
```

初次实际运行墙钟时间（本机同时执行了部分独立模拟进程，依赖安装和 PDF 构建不计）：

| 实验 | 重复次数与单位 | 实测秒数（四舍五入） |
|---|---|---:|
| main | 每图/设计 400 | 103 |
| noise | 每图/设计 400 | 107 |
| scaling | 每规模/度数 400 | 30 |
| validation | 每度数 150 | 129 |
| sensitivity + threshold oracle | 每图/设计 400，与 main 同数据流 | 19 |

消融、saturation、分析和构建另需时间，最新逐次运行时间见各 `results/*_run.json`。
建议为完整顺序复现预留 **5–15 分钟**（这是机器相关的预计时间，并非新增实测值）；
首次依赖安装和网络下载另计。更慢 CPU 可增加时间，但不需要数十 CPU 小时。
测试只需运行 `code/verify.py`；不要把 `--reps` 改小后生成的结果与正式论文混用。
论文中的固定次数标签对应上述正式命令。

## 每张图、表与代码的对应

所有最终图表统一由 **`code/analyze.py`** 从实际 raw CSV 生成；没有手工填入的实验数字。

| 论文项目 | 输出 | 上游实验 |
|---|---|---|
| Figure 1：度数/样本量与噪声 | `figures/degree_scaling.pdf` | `study.py --mode main/scaling` |
| Figure 2：设计与支持消融 | `figures/design_support.pdf` | main；`support_ablation.py`（含等样本量随机删点对照） |
| Figure 3：预测验证与 GATE | `figures/prediction.pdf` | `study.py --mode validation` |
| Figure 4：Peano 核与曲率界 | `figures/sensitivity.pdf` | `study.py --mode sensitivity` |
| Figure 5（附录）：对称性与覆盖率 | `figures/symmetry_coverage.pdf` | `study.py --mode saturation/noise` |
| Table 1：三次响应主结果 | `paper/generated/main_table.tex` | main |
| Table 2：固定图统计 | `paper/generated/graph_table.tex` | main 图构建 |
| Tables 3–7：全部五类响应 | `paper/generated/full_tables.tex` | main |
| Table 8：阈值 oracle 可估性 | `paper/generated/oracle_table.tex` | sensitivity 中 oracle 检查 |
| Table 9：HT 稀有事件 | `paper/generated/ht_table.tex` | main |
| Table 10：敏感性区间覆盖与宽度 | `paper/generated/sensitivity_table.tex` | sensitivity，含 Wilson 覆盖率区间 |
| 正文数值宏 | `paper/generated/numbers.tex` | 各实验；来源映射 `results/number_provenance.json` |

`*.png` 是同一图的预览，不是另一个实验。论文所有结果以 raw 数据为准。

## 结果文件与检查

- `results/*_raw.csv.gz`：每次分配、每个模型和响应的实际估计误差；oracle 失败保留 `valid=False`。
- `results/*_summary.csv`：bias、RMSE、Monte Carlo SE、覆盖率/条件分解等；详细字段见 `analyze.py`。
- `results/paired_comparisons.csv`：同一分配下 OLS-C 与 OLS-L 的平方损失差及 MCSE。
- `results/number_provenance.json`：正文生成数字的实际数值和来源说明。
- `logs/verify.json`：数值/穷举检验，包括小图 HT 无偏性、条件方差、Peano 恒等式与曲率界。
- `logs/audit.json`：样本行数、共享数据流、曲率界、不修改官方样式、PDF 页数与图数的检查。
- `EXPERIMENT_PLAN.md`、`RUN_LOG.md`：初始方案、探索性添加、运行和失败记录。

完整结果中有不利和无法精确评价的情况：HT 的稀有尾部未由 400 次模拟解决，
二跳 DGM 下所用一跳 HT 暴露映射无效，高度图阈值 oracle 可能根本不可估。
区间覆盖分析使用已知噪声协方差；曲率区间还使用外部给定的曲率上限，
它们不是从单次实验学习这两个量的实用推断算法。

该研究由自主语言模型代理执行，所有代码和实验均在本工作目录实际运行；没有虚构的人类作者。
