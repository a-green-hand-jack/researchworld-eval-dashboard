# 多任务排行榜聚合规则与针对性投入：研究与复现

论文：[paper/main.pdf](paper/main.pdf)；LaTeX：[paper/main.tex](paper/main.tex)。
使用 **ICLR 2027 官方模板**，采用首次投稿正文不超过 9 页的限制。报告没有向会议投稿。
随文提供必需的 AI use statement、推荐的伦理和复现声明，以及填写完成的额外报告清单。
完整交付包为 `research_artifact.tar.gz`，旁附其 SHA-256；解压后的
`MANIFEST.sha256` 覆盖代码、数据、论文及结果文件。虚拟环境与 TeX 临时文件不打包。

研究的主要结果是条件性的：满分提升上限与“当前各任务最好分数”上限，会使均值和中位数所需最少修改任务数的比较反转；若投入改按累计分数增量度量，结论又不同。这里只优化公开分数空间中的干预，**不估计训练样本数、token 数、GPU 时间，不指认任何模型存在污染**。

## 环境和最短运行方法

实际环境：Linux、Python 3.11.2、TeX Live 2022、latexmk 4.79。仅需 CPU。
所有 Python 直接和间接依赖精确固定在 `requirements-lock.txt`。
主要依赖为 NumPy 2.2.6、pandas 2.3.3、SciPy 1.15.3、Matplotlib 3.10.7、PyArrow 22.0.0、requests 2.32.5。
PyMuPDF/pypdf 用于 PDF 检查，不参与分数优化。

```bash
cd /work
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
make all
```

在其他目录使用压缩包时先 `tar -xzf research_artifact.tar.gz`，进入解压得到的
`research_artifact/` 后创建环境并运行同样命令。重算前可用
`sha256sum -c MANIFEST.sha256` 检查交付文件。

已有虚拟环境和原始数据时直接运行 `make all`。在别的目录解压也可运行；脚本根据自身位置定位根目录。
请串行运行 `make all`，不要使用 `make -j`，各步骤存在数据依赖。
不使用 `make` 的等价命令为：

```bash
.venv/bin/python -m src.fetch_data
.venv/bin/python -m src.prepare_data
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -m src.run_experiments --task-bootstrap 300
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m src.report
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q
(cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
.venv/bin/python -m src.verify_artifact
```

分析、报告、测试和编译在附带原始数据时可离线执行。`fetch_data` 在文件已存在时只检查本地文件，不访问网络。
全新获取数据需要普通无账号 HTTPS 访问；安装依赖需要 Python 包源。
一次完整实验预计约 **2–4 分钟**；处理、绘图、测试和编译另需约 **1 分钟**，下载时间取决于网络。
实际实验 CPU/墙钟时间与峰值内存见 `artifacts/runtime.json`；最终验证见 `artifacts/verification.json`。
时间记录会随重新运行更新，不应期望 PDF 或 runtime 文件逐字节相同；科学结果和固定种子的扰动结果应保持一致。

## 数据来源、版本、筛选和权利说明

- **HELM–MMLU**：`mmlu/benchmark_output/releases/v1.13.0/`，release 日期 2025-01-10。
  只取 57 张 `mmlu_mmlu_subject:*.json` 学科汇总表、版本 summary 和 release listing。
  从 run-spec 提取模型标识，取 `EM`；79 个模型在 57 学科上完整，无缺失剔除。
  主分析使用学科等权宏均值，不声称是站点全部默认展示规则。按题量加权是单独控制实验。
- **Open LLM Leaderboard contents**：commit
  `9c09a7cae43334062a82cb164f2ef255013dafa2`，最后更新 2025-03-20。
  下载一个 parquet 和该 commit 的 README。原表 4,576 行；剔除 1 条 Flagged 后，
  按 bfloat16、float16、float32、8bit、4bit、其他的优先级，继以 `eval_name` 字典序，
  每个 fullname 留一条；去掉 79 条额外记录，保留 4,496 个模型。
  该选择不读取分数。六个显示归一化分数除以 100；其均值精确等于原表给出的平均分。
  原始 Raw 列与全部 4,575 条未标记评测记录分别作为控制面板。
- 取证/下载日期：**2026-11-02 UTC**。全部实际 URL、逐文件 SHA-256、字节数、版本和时间见
  `data/manifest.json`。`fetch_data.py` 会拒绝已记录文件的校验和不一致。

完整性和筛选审计见 `artifacts/data_audit.json`；处理后的 CSV 在 `data/processed/`。
没有镜像逐运行输出或下载评测问题数据。

**数据许可未明确声明**：已检查的 HELM 得分汇总和 Open LLM 数据集卡没有独立得分数据许可。
模型 Hub License 字段不等于榜单数据许可，HELM 代码 Apache-2.0 也不被自动套用到分数。
这里为研究复现保留公开聚合分数及来源，不宣称获得额外再分发授权；下载脚本支持从原始来源重新取得数据。
第三方模板保持原样，其权利说明以官方文件为准。

## 建模、随机性和统计解释

只允许目标模型的被选坐标提高；对手固定，无跨任务收益或遗忘。独立可控的提升盒为
`u = x + rho * (c - x)`，`c` 是 1 或该任务全榜最大值，`rho` 为 0.1、0.25、0.5、0.75、1。
这是假设，不是从训练干预中估计的响应模型。

聚合规则为算术均值、通常定义的中位数（偶数维取中间两项平均）、几何均值（保留零）和最小值。
主要度量 `K` 是最少改变任务数；`C` 是平均分数增量最小值。
HELM 奇数维上的均值和中位数还计算精确混合开销 `J(lambda)`。
全文主要比较使用**四种规则下都不已是第一的相同模型集合**：HELM 77、Open LLM 4,493；各规则对手仍包括全部模型。

主要规则允许并列第一；控制实验要求领先 `1e-6`。数值比较容差 `1e-12`。
连续几何均值的单变量求根绝对容差 `1e-14`。
存储中不可行的 `K` 用 `d+1` 编码；它不是有限投入。不可行 `C` 为 infinity。
所有论文平均任务成本仅来自 `rho=1` 可行场景；较弱响应报告可行比例。

- 种子 **20261102**：随机任务顺序基线。HELM 每个目标 256 个排列；Open LLM 六维枚举全部子集得到精确期望。
  HELM 表中 `±` 是蒙特卡洛标准误，只反映这些排列采样。
- 种子 **20261103**：每个面板 300 个有放回任务多重集；每次对全部模型使用同一任务抽样，并重算 caps 和对手阈值。
  原始共同目标集合固定。
- 种子 **20261104**：2,000 次 owner 分组重加权，完整组一起抽样；HELM 用首个 `_` 前的供应者前缀，Open LLM 用 `/` 前命名空间。

这些中央 95% 区间是有限榜单的**敏感性范围**，不是独立模型总体、未知任务或真实准确率的置信区间。
分组只是谱系的粗代理。没有例题级不确定性或训练响应因果置信区间；数据不足以识别它们。

## 每张表、每张图的生成关系

所有排版表格与图统一由 **`python -m src.report`** 生成；参数和原始实验由
`src/run_experiments.py` 计算，精确算法见 `src/attacks.py`。

| 论文对象 | 输入 | 生成文件 |
|---|---|---|
| Table 1：最少任务数 | `artifacts/support.csv` | `paper/generated/support.tex` |
| Table 2：最少平均分数增量 | `artifacts/mass.csv` | `paper/generated/mass.tex` |
| Table 3：分组/任务敏感性 | support、task_bootstrap、处理元数据 | `paper/generated/uncertainty.tex` |
| Table 4：初始榜首和阈值 | `data/processed/{helm,oll}.csv` | `paper/generated/leaders.tex` |
| Table 5：目标、Raw、全记录控制 | support | `paper/generated/cohorts.tex` |
| Table 6：正领先幅度 | support | `paper/generated/ties.tex` |
| Table 7：学科题量加权 | `artifacts/weighting.csv` | `paper/generated/weighting.tex` |
| Table 8：投入策略基线 | baselines、support | `paper/generated/baselines.tex` |
| Figure 1：任务预算前沿 | support | `paper/figures/frontiers.pdf` |
| Figure 2：提升幅度与可行性 | support | `paper/figures/reachability.pdf` |
| Figure 3：任务开销与分数增量混合成本 | support、mass | `paper/figures/mixed_cost.pdf` |
| Figure 4：连续成本前沿 | mass | `paper/figures/mass.pdf` |
| Figure 5：任务构成扰动 | `artifacts/task_bootstrap.csv` | `paper/figures/task_perturbations.pdf` |

`paper/generated/numbers.tex` 由同一脚本生成正文中的经验数值宏。
`artifacts/mixed_cost.csv` 和 `mixed_crossovers.csv` 保留混合成本曲线和逐目标切换权重。
`artifacts/summary.json`、`table_support.csv`、`table_mass.csv` 提供易读汇总。
`artifacts/witnesses.json` 给出若干最优任务选择及修改前后分数；`witness_audit.json` 记录 109,800 个核查案例。
全逐目标结果保留在 CSV 中，可追溯所有汇总。

## 验证和访问纪律

`tests/test_attacks.py` 用穷举子集独立核查支持度求解、对中位数连续成本枚举排序后调用 LP、
对几何均值连续成本调用独立约束优化器；也核查相同榜单上的上限反转和混合成本的共同最优性。
`src/verify_artifact.py` 核对原始校验和、结果完整性、主结论、未修改模板、PDF 页数和引用。

查阅文献限于给定起步文献的指定条目、直接访问的一篇较早选举贿选论文，以及官方数据/模板/政策资料。
没有按研究问题进行开放式搜索，没有前向/后向引用扩展，没有尝试识别或访问被排除论文。
访问和阅读范围、失败链接、开发运行和未完成事项见 `RESEARCH_LOG.md`。
引文均对应实际下载并查阅的文献；数学构造例子未混入实证数据。

本研究全部由自主 AI agent 完成；未声称经过人类独立审查，也没有实际训练实验。
