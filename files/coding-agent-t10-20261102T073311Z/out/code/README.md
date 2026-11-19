# 固定预测器下置信区间还能缩短多少？

完整研究产出位于 `/work`。论文采用 **NeurIPS 2026 官方模板**；正文 7 页，参考文献、附录和填写完的官方 checklist 另计。该文件是独立研究报告，并非声称已投稿或被会议接收。

- 论文 PDF：[`paper.pdf`](paper.pdf)
- LaTeX 主文件：[`paper/main.tex`](paper/main.tex)，参考文献 [`paper/references.bib`](paper/references.bib)
- 所有方法：[`code/methods.py`](code/methods.py)
- 实验与真值：[`code/experiment.py`](code/experiment.py)
- 逐次结果：[`results/raw/`](results/raw/)，551 行汇总：[`results/summary.csv`](results/summary.csv)
- 完整记录：[`logs/RESEARCH_LOG.md`](logs/RESEARCH_LOG.md)，数字审计：[`logs/output_audit.json`](logs/output_audit.json)

## 研究结论与适用范围

目标是 IID 分布下的总体均值。固定的是每次比较中全部方法收到的标注、未标注分数和外部预测器。不同重复重新抽样用于评估覆盖；不声称给定所有已观察数据后的条件覆盖。

冻结分数中的非线性条件均值信息可以带来收益。在 `n=800, N=8000` 的连续二次合成例中，交叉拟合三次控制项比不受限线性 PPI++ 的平均 Wald 宽度缩短 **69.0%**；二元二次例中缩短 **15.4%**。这些是渐近区间；完整报告同时列出覆盖及其 Monte Carlo 不确定性，不能当成任意有限样本的覆盖保证。三个真实预测数据集的额外收益很小。

若要求严格的有限样本覆盖定理，我们使用独立 20% 标注作校正项拟合，再用有界经验 Bernstein 区间推断。在连续二次例 `n=12800, N=128000` 中，比 label-only EB 区间缩短 **28.3%**；在 `n=3200` 时缩短 **6.1%**，在 `n=800` 时反而更宽。二元无信息和稀有事件例中，精确二项区间明显更好。高维直接拟合或稀有事件下出现的欠覆盖完整保留，未当成成功缩窄。

理论给出的“不能继续改进”仅指无额外结构假设、只用分数的正则估计量的一阶方差界，不能解释成所有有限样本置信区间的最短长度定理。方法沿用控制变量、去偏与交叉拟合思想；贡献是固定输入条件下收益与有效性代价的量化审计，不宣称发明一般校准或半监督效率理论。

## 环境与依赖

实测环境：Linux x86_64，Python **3.11.2**，Intel Xeon Gold 6230，容器 CPU 配额 **4 核**，内存上限 **16 GiB**。每个进程限制为一个 BLAS 线程，最多四个工作进程。没有 GPU、付费 API 或实验中的模型 API 调用。

全部 Python 依赖精确版本在 [`requirements.lock.txt`](requirements.lock.txt)。核心包括 NumPy 2.4.6、SciPy 1.17.1、pandas 3.1.0、scikit-learn 1.9.1、Matplotlib 3.11.2、gdown 6.5.1；推断算法使用 NumPy/SciPy，没有训练 scikit-learn 模型。pypdf/PyMuPDF 用于文档核查。`ppi-python` 本身不需要安装：我们核对其固定版本的源代码，并独立实现均值公式。

```bash
cd /work
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
```

若系统有 `uv`，可用 `uv pip install --python .venv/bin/python -r requirements.lock.txt`。初始系统没有 `python` 命令别名，所以全部命令均明确使用 Python 3。

编译需要 TeX Live、`pdflatex`、`bibtex` 和 `latexmk`，本环境已有。官方 `neurips_2026.sty` 已随源文件提供且未经修改；无需在线 Overleaf 或下载旧年模板。

## 数据及来源

三个文件均来自 `ppi-python` **v0.2.3**（用户指定版本、提交 `6b8475b`）的官方 loader，保留其原始 `Y`、`Yhat`。文件和校验值已在 [`data/manifest.json`](data/manifest.json) 记录。

| 文件 | 记录数 | Google Drive ID |
|---|---:|---|
| galaxies.npz | 16,743 | `1pDLQesPhbH5fSZW1m4aWC-wnJWnp1rGV` |
| forest.npz | 1,596 | `1Vqi1wSmVnWh_2lLQuDwrhkGcipvoWBc0` |
| alphafold.npz | 10,802 | `1lOhdSJEcFbZmcIoqmlLxo3LgLG1KqPho` |

获取或验证文件：

```bash
.venv/bin/python code/acquire_data.py
```

不需要账号；已有文件会核对 SHA256，不会静默替换成不同版本。仅以带标注数组定义一个有限的**经验分布**：标注记录与未标注分数分别独立、有放回抽样，目标为整个文件的标签均值。未标注侧的标签不传给任何区间方法；完整标签只用于评价真值与 oracle 诊断。不声称经验分布覆盖等于原始科学总体覆盖，也不声称 bootstrap 中的重复行意味着获得了新标签。原模型是否与原数据独立无法从文件验证；对经验分布的重复抽样分析将文件和分数视为给定。

原始研究的出处已从固定版本 notebooks 开头查阅并在论文附录 C 归属说明；notebooks 保存于 `literature/`。PPI 代码为 MIT，许可证保留在 `literature/PPI_CODE_LICENSE.txt`。下载的 NPZ 没有单独数据许可证声明，**不能把代码 MIT 当作数据 MIT**。本地提供仅用于本任务研究复核；下游发布数据应另行解决许可。自写代码的 MIT 见 [`LICENSE`](LICENSE)，不适用于第三方资料和数据。

## 从头复现实验

```bash
cd /work
.venv/bin/python code/acquire_data.py
.venv/bin/python code/verify.py
.venv/bin/python code/experiment.py --suite main --reps 5000 --workers 4
.venv/bin/python code/experiment.py --suite ablation --reps 5000 --workers 4
.venv/bin/python code/experiment.py --suite ratio --reps 5000 --workers 4
.venv/bin/python code/experiment.py --suite finite --reps 3000 --workers 4
.venv/bin/python code/summarize.py
.venv/bin/python code/check_outputs.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
cp paper/main.pdf paper.pdf
.venv/bin/python code/audit_document.py
```

已有全部结果时，只需执行 `summarize.py`、`check_outputs.py` 和编译命令。重跑会覆盖相同条件的旧结果；需要隔离时可指定 `--outdir results/new_run`，但默认汇总读取 `results/raw`，要汇总替代运行需把该运行放在此目录。

随机数使用 NumPy `default_rng`。每个条件的 seed 为字符串

```text
fixed-score-20261102/{kind}/{case}/{n}/{N_over_n:g}
```

的 SHA256 摘要前 8 字节按 little-endian 转整数；条件 key、每个实际 seed 都保存在 `results/raw/*.json`。调度顺序不会改变结果。主实验与 degree ablation 的 `kind` 不同，因此使用独立种子；相同条件内所有方法共用一次抽样的同一组数组，方法本身不再抽随机数。不能把不同 suite 的 CV3 记录混在一起汇总。

主实验参数：Legendre 多项式三次基函数；CF1/CF3 五折，固定顺序，训练四折；EB-split1/3 前 20% 为独立 pilot；名义覆盖 95%；所有样本方差/协方差采用 `ddof=1`。官方 PPI 均值实现的部分分母采用 `ddof=0`，因此这里明确报告为无偏协方差的公式实现，而非逐位相同的包调用。`verify.py` 从已查阅的官方源文件隔离执行 `_calc_lam_glm`，核对这一分母差异后的标量调权结果。`PPI++clip` 另报原始分数系数限制 `[0,1]` 的版本；主要 PPI++ 基线允许任意实系数。

真实数据与二元合成数据额外报告 Clopper–Pearson 精确二项区间；连续数据不能套用这个区间。`binary` 标志来自已知数据类型，而不是看到本次样本都是 0/1 就临时决定。

### 实测耗时

四个科学实验 suite 合计 **233,000 次重复、49 个条件**：

| suite | 条件数 | 每条件重复 | 实测墙钟秒数 | 最大单 worker RSS |
|---|---:|---:|---:|---:|
| main | 22 | 5000 | 187.2 | 121.5 MiB |
| ablation | 9 | 5000 | 56.7 | 114.6 MiB |
| ratio | 12 | 5000 | 155.8 | 120.4 MiB |
| finite | 6 | 3000 | 184.0 | 125.0 MiB |

因此同类四核 CPU 从头运行预计约 **10–20 分钟**，依赖下载、网络、PDF 编译与额外审计另计。实测 `ratio` 运行时曾与补充基线重算部分重叠，时间不是无竞争机器的纯性能基准。每个 suite 的实际时间和系统信息见 `logs/run_*.json`。初次 main 中 `cpu_seconds` 字段是 worker 累积 CPU 时间，不能逐条件相加；论文只使用不受影响的墙钟测量，后续 driver 已修正该计数。

初次 main 后新增 Hoeffding 和精确二项基线，`augment_baselines.py` 从相同 seed 重建**相同输入**，追加基线，不改变已有结果。当前 driver 直接生成这些基线，完整重跑不需要 augmentation。早期 smoke/menu 方案与失败的处理过程记录保留；没有删除欠覆盖或无收益结果。

## 每张表、每张图的来源

**所有**论文数字、表格、图片都由 `code/summarize.py` 从 `results/raw/*.csv.gz` 和同名 JSON 生成；没有手工占位值。数据生成及理论 oracle 积分在 `code/experiment.py`。下列均为实际代码输出。

| 论文位置 | 生成文件（`paper/generated/`） | 输入 |
|---|---|---|
| 表 1：合成主比较 | `synthetic_main.tex` | main，n=800 |
| 表 2：真实数据 | `real_main.tex` | main 的三个真实 artifact，n=200/800 |
| 表 3：严格有效性 | `finite_main.tex` | main n=800、finite n=12800 |
| 图 1：字典复杂度失效 | `ablation.pdf` | ablation 的 null_binary |
| 附录 B，表 4：oracle | `oracle.tex` | main metadata 的积分矩与测得 CF3 宽度 |
| 附录 B，图 2：全部合成主结果 | `synthetic.pdf` | main，n=800 |
| 附录 B，图 3：未标注数量敏感性 | `ratio.pdf` | ratio 与 main 的比例 10 |
| 附录 C，表 5：数据与 oracle headroom | `artifacts.tex` | 完整 artifact，oracle 诊断，不拟合区间 |
| 附录 D，表 6：所有严格区间 | `finite_all.tex` | main 与 finite |
| 附录 D，图 4：严格区间随 n 变化 | `finite.pdf` | main 与 finite |
| 附录 E，表 7：全部 degree stress test | `ablation.tex` | ablation |
| 附录 F，表 8–29：所有方法主结果 | `full_{case}_{n}.tex` | main |
| 附录 G，表 30：计算资源 | `compute.tex` | `logs/run_*.json` |
| 摘要、正文中的测得数字 | `numbers.tex` | 对应上述实际条件，另存 `results/reported_numbers.json` |

误差条定义：覆盖的 Wilson 95% Monte Carlo 区间；主表为 `±1.96 sqrt(p(1-p)/M)`；宽度为平均值 `±1.96 SE`；宽度比用配对 delta method。覆盖达到 100% 的 Wilson 下界仍小于 100%，没有将零次失败当成零不确定性。所有区间均为点态 Monte Carlo 描述，不是多重比较校正的显著性发现。

`check_outputs.py` 检查所有端点有限、宽度和覆盖指示一致、重复计数和方法键完整；重建每个条件第一组输入并重新计算其全部端点；还核对官方模板文件未修改。`logs/output_audit.json` 保存每个第一组输入数组的 SHA256。

## 文献与禁止访问约束

没有用题目关键词检索、文献搜索工具、引用图谱、聚合站点或相关论文推荐。只直接访问了提供的六篇起步文献 PDF、Maurer–Pontil (2009) 的经典经验 Bernstein 论文、固定版本 PPI 仓库文件、数据下载链接以及官方会议/伦理页面。实际访问链接和失败情况保存在 `logs/source_fetch.json`、`logs/extra_fetch.json` 与研究日志。没有尝试猜测禁止论文的题目、作者或结果，也没有识别到偶然遇见禁止内容的事件。受此限制，报告不声称对全部后续文献的优先性或文献穷尽性。

NeurIPS 2026 官方模板由该年 CFP 的直接链接取得：

```text
https://neurips.cc/Conferences/2026/CallForPapers
https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
```

原始 ZIP、官方说明和未修改样式保存在 `template/`。checklist 保留原问题与 guidelines，并如实将数据许可项答为 No。全文自主研究与 LLM 使用已披露；数学和结论未经人类同行评审，数值结论可由附带代码审计。
