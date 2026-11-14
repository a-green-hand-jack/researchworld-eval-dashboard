# 单次 SHAP 解释的重复运行可靠性

本目录是一项独立完成的实证研究，包括论文、真实实验输出和全部代码。论文采用 **ICML 2026 最新官方模板**，正文按投稿的 8 页上限编排；未向会议投稿。研究只讨论固定模型、输入、背景和解释定义下的计算可靠性，不把 SHAP 当作因果证明。

- 论文：`paper/main.pdf`；LaTeX 主文件：`paper/main.tex`。
- 完整实验方案：`PROTOCOL.md`（内部前瞻记录，不是外部预注册）。
- 文献访问、失败与偏离记录：`RESEARCH_LOG.md`。
- 数据下载与 SHA-256：`data/manifest.json`。
- 冻结模型、划分与实例：`data/*.joblib`。
- 所有联盟精确值：`results/games/*.npz`。
- 所有独立种子的估计：`results/runs/*.npz`。
- 背景变化实验：`results/background/*.npz`。
- 事后数值求解诊断：`results/solver/*.npz`、`results/analysis/solver.json`。
- 汇总与区间：`results/analysis/summary.csv`、`report.json`。
- 逐实例结果：`results/analysis/per_case.csv`。
- 环境：`requirements.txt`、`environment.json`。

## 环境和运行

需要 Python 3.11、可联网访问公开数据、LaTeX（pdflatex、bibtex，含常见 TeX Live 宏包）。无 GPU、付费 API 或账号要求。

```bash
cd /work
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
make reproduce WORKERS=4
```

按顺序运行的等价命令：

```bash
.venv/bin/python code/download.py
.venv/bin/python code/prepare.py
.venv/bin/python code/games.py --workers 4
.venv/bin/python code/reference_summary.py
.venv/bin/python code/explain.py --workers 4
.venv/bin/python code/explain.py --datasets german --default --workers 4
.venv/bin/python code/background.py
.venv/bin/python code/validate.py
.venv/bin/python code/timing.py
.venv/bin/python code/solver_audit.py
.venv/bin/python code/analyze.py
.venv/bin/python code/write_numbers.py
make paper
```

仅用已附结果重做论文图表：`make analyze paper`。所有模型、样本、背景和解释种子由 `code/common.py` 的主种子 **20261102** 及 `numpy.random.SeedSequence` 派生，不依赖 Python 的随机哈希。`prepare.py` 使用固定分层划分，保存原始行索引；三模型使用匹配的测试实例和背景。

`games.py` 和 `explain.py` 会跳过已有缓存。改变实验配置后，应先把对应旧输出移动到另一个目录，再重新运行，避免混用配置。现有结果是论文所用冻结输出。

## 数据

1. **Statlog German Credit**：UCI DOI `10.24432/C5NC77` 的原始混合型 `german.data`，1,000 行、20 特征；下载 URL 和哈希在 manifest 中。原类别 2 作为正类。UCI 声明 CC BY 4.0，原提供者 Hans Hofmann。类别原子化为原始特征，而不是把每个 one-hot 列单独解释。
2. **Pima Diabetes**：OpenML data id 37、version 1，768 行、8 特征，licence 字段为 `Public`。血糖、血压、皮褶厚度、胰岛素和 BMI 的零值作为缺失；仅用训练集的中位数填补。原数据人群局限和历史采样偏差不支持临床外推。
3. **ACS Income**：folktables 0.0.12 的 `ACSIncome`，2018 年、California、1-Year、person，原始 `psam_p06.csv`。folktables 标准过滤（年龄 >16、收入 >100、周工时 >0、PWGTP >=1），目标个人年收入 >50,000；195,665 条过滤后记录、10 特征。以该版本函数定义为准。原始下载 378,817 行。固定 75/25 分层划分，训练部分再分层抽至 20,000。分析不使用调查权重，不能解释为加州人口加权估计。folktables 代码 MIT；ACS 是公开 PUMS 微数据，未把代码许可证误作数据许可证。阅读的 Census 官方政策、隐私与 API terms 页面保存在 `literature/`；未找到原始 PUMS 文件的单独许可证文字。Census API terms 只用于记录官网使用条款，不声称它为直接下载文件授予额外许可。

数据获取不跟随任何解释可靠性主题的搜索结果。文献只直接读取用户明确允许的来源；完整访问范围和无意接触记录见 `RESEARCH_LOG.md`。

## 结果结构

- `games/<dataset>_<model>_<case>_b16.npz`：`v[mask]` 为固定16行背景下的全联盟值，`phi` 为精确 Shapley，`case_id` 为原始数据行索引，另含墙钟和 CPU 秒数。
- `runs/*.npz`：`phi[method,budget,seed,feature]`；method 0=实际 KernelExplainer，1=反向成对的排列采样；budget 按 2d、8d、32d、128d 排列，seed 共64。`cost` 是实际内部联盟数；`active` 是真实背景下会改变的原始列。`ref` 为精确值。`warnings` 保留全部警告。
- `runs/*_default.npz`：只测 German、128d、默认 top-10 稀疏化，method 和 budget 轴各长度1。
- `background/*.npz`：`phi[B_index,draw,feature]`，背景规模4/16/64，各8次独立抽取；每个数据集8实例，所有三模型。
- `timing.json`：真实模型、无联盟查表的180次在线调用，含实际模型输入行数；不能以缓存实验耗时代替。
- 置信区间以实例为 bootstrap 单位。整体结果在每个数据集内重抽实例，保留模型间配对；不是把重复种子当作更多独立测试记录。

## 图表和数字的来源

论文主图表由 `code/analyze.py` 从附带数组生成，事后求解对照表由 `code/solver_audit.py` 生成；无手工填写实验结果。`code/write_numbers.py` 从汇总 JSON/CSV 生成正文使用的 `paper/numbers.tex` 宏。

| 论文内容 | 生成文件 | 原始来源 |
| --- | --- | --- |
| 数据与预测性能表 | `paper/tables/models.tex` | `results/models.json`，由 `prepare.py` 生成 |
| 主要联合成功率表 | `paper/tables/main.tex` | `results/runs/*.npz` |
| 数值与排序曲线 | `paper/figures/accuracy.pdf` | 同上 |
| 排列基线比较图 | `paper/figures/baseline.pdf` | 同上；按实例 bootstrap |
| 排名间隔图 | `paper/figures/margin.pdf` | 精确 `ref` 与重复估计 |
| 背景重抽样表 | `paper/tables/background.tex` | `results/background/*.npz` |
| 默认稀疏化表 | `paper/tables/regularization.tex` | `*_default.npz` 与主实验 |
| 平均四次与加大预算表 | `paper/tables/averaging.tex` | 主实验低预算估计与8d估计 |
| 完整分指标表 | `paper/tables/full_metrics.tex` | 主实验；逐实例值在 CSV |
| 事后 SVD 求解对照表 | `paper/tables/solver.tex` | `results/solver/*.npz`，由 `solver_audit.py` 重放相同低预算采样 |
| 在线计时表 | `paper/tables/timing.tex` | `results/timing.json`，由 `timing.py` 生成 |

图中的排序间隔分组是描述性分析，样本量按“模型×实例”计；模型间共享实例，不能把这些行当成完全独立样本。主要表和基线图报告匹配实例 bootstrap 区间。

## 校验和限制

`code/validate.py` 独立比较全排列与子集公式、验证加法博弈、全联盟 Kernel 求解，并在全部九个数据/模型单元上比较真实输入 Kernel SHAP 与缓存博弈（含原始类别分组）。它验证算法/封装，不以合成结果支持论文实证结论。结果写入 `results/validation.json`。

只训练每个单元的一个固定模型，是隔离解释器随机性的设计。训练集、模型种子、地区、年份、条件 SHAP、其它输出尺度、其它解释器均不在本研究结论范围内。前三集合要求严格，近乎并列的特征互换不必然构成有实际后果的变化。数字容差不是监管或临床标准。所有结论需连同这些条件阅读。

## 实测资源与耗时

本次使用 Intel Xeon Gold 6230（容器限额4个 CPU 等价，40个可见 CPU），不使用 GPU。保留的主全枚举输出约 **1.05 CPU 小时**；主/稀疏化重复解释约 **0.31 CPU 小时**；背景实验约 **0.036 CPU 小时**；事后求解诊断约 **0.019 CPU 小时**。合计约 **1.42 CPU 小时**，不包含下载、环境安装、训练、绘图、在线计时、验证、编译和被覆盖的试运行。精确秒数见 `results/analysis/report.json` 和 `solver.json`。全枚举阶段在本次并发情况下实测约19分钟墙钟；全部研究、写作和检查约1小时内完成。

从头运行预计在4个 CPU 等价、相近环境下需要约 **30–60分钟计算和下载**（网络和同机负载可改变此时间；这是基于本次实测的复现估计，不是另一次计时结果）。只重生成分析和 PDF 约1分钟。数据与结果合计低于2 GB；虚拟环境另外约0.8 GB。建议至少4 GB可用磁盘和数 GB内存。

## 事后求解诊断

预定低预算输出中观察到极端误差后，增加了明确标注为事后的 SVD 对照。重放18,432个相同2d采样设计，与原始软件输出逐元素完全一致，再仅替换线性回归求解器。原软件有277次最大误差超过1概率单位，SVD对照为0次；但最低预算的总体正确率仍低。原始输出未删除、裁剪或替换。所有论文主结果仍来自原版 SHAP。此实验解释数值极端值，并不证明 SVD 是最优近似算法。

## 提交包

`source_and_paper.zip` 包含论文 PDF、全部 LaTeX/图表源码、全部 Python 代码、固定环境、运行日志、所有重复估计和背景/求解诊断数组、分析汇总和复现说明。为便于下载，它省略了约723 MB的全联盟 payoff 缓存及约1.1 GB的原始 ACS 缓存；这些均完整保存在当前 `/work` 的 `results/games/` 和 `data/raw/` 中，也可由代码重新产生。ZIP 中保留每个精确参照的归因向量、端点、CPU时间和文件哈希（`results/reference_summary.json`），使 `make analyze paper` 可直接重做已报告结果。完整独立验证、改采样设计或从头实验须先运行数据/训练/全联盟步骤。论文中的实验数字来自实际运行，并非这些摘要的估计或占位结果。

最终检查：轻量 ZIP 已解压到独立目录，成功重建全部图表和12页PDF；检查的主要CSV、表格和数字宏与原件逐字节一致（`results/release_check.json`）。论文正文在第7页结束，符合8页上限；参考文献第8页，附录从第9页开始。
