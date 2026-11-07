# Fixed-Budget Mean Inference / 固定预算下的均值区间

## 主要提交物

- **论文**：[`paper.pdf`](paper.pdf)，LaTeX 源码 [`paper.tex`](paper.tex)、[`references.bib`](references.bib)。
- **中文报告**：[`final_report.md`](final_report.md)。
- **完整输出**：`results/`（每次重复的端点、覆盖、宽度；全部摘要与配对不确定性）。
- **独立审计**：`artifacts/theory_audit.md`、`artifacts/results_audit.md`、`artifacts/paper_review.md`；修订响应见 `artifacts/review_response.md`。
- **官方模板**：未修改的 ICML 2026 样式；正文含结论在第7页结束，参考文献第7页、附录第8页起；PDF 共19页。使用初投稿8页正文上限。官方要求的 impact statement 已填写；未发现另需随文提交的 NeurIPS 式 checklist，另附复现 checklist。

### 核心结论（请勿混淆有效性层级）

1. 固定样本和预测器，不意味着某一基线已不可改进。但不存在本研究支持的普遍缩短保证。
2. 在强二分层的合成机制中，具有有限样本覆盖保证的精确分层区间比标注集精确二项区间窄 **27.8%**（配对 Monte Carlo 95% 区间 **[27.63%,27.93%]**；n=2000,N=20000）。两者比较的是有相同严格覆盖要求的程序；分层法经验覆盖1.0000，普通精确基线0.9560。
3. 非线性交叉拟合在二次/阶跃机制中分别窄约18%/39%，但其正态区间**仅渐近有效**。阶跃 n=2000 覆盖0.9355；稀有结局 n=30 覆盖0.2645，因此不能将这些宽度收益说成有限样本有效性收益。
4. 在 galaxies、forest 两个经验分布示例中，测试的非线性基没有比更强的无约束标量 PPI++ 获得宽度收益。严格分层法和 EB 安全字典在多数条件下更宽。
5. 理论只优化“固定分数函数的均值修正”这一类估计量。它不是全体置信区间的最优性/不可改进性定理。

## 统计设计与数据边界

- 目标：二元结局总体均值/发生率。假设共同分布的独立 iid 标注和未标注样本，原预测器与推断数据独立。
- 每个重复内全部方法使用**完全相同的输入数组**，不增加标签、记录或预测查询。S 的后处理被定义为推断干扰函数，而不是替换底层预测器；更严格禁止任何输出变换时，不适用该非线性路线。
- 5个已知真值的合成机制，2个真实配对数据快照，32个设置，每个2000次重复，共64,000组抽样数据；精确分层补充实验重放相同输入，**不是额外独立重复**。总884,000条区间记录。
- 真实数据从固定经验联合分布**有放回独立抽样**；目标是该快照的全标签平均值，不是原科学总体或无放回有限总体。评估真值在推断函数外计算，未标注抽样的标签不传给任何可行方法。
- “固定数据”是方法间的输入固定，覆盖率仍定义于重复抽样，不声称给定单份实现数据后的条件覆盖。
- 当 Y 或 S 有界是支持假设，不能把已观测最小/最大值当作未知总体的支持边界。本文真实实验的目标分布是明确的有限经验快照，分数均在[0,1]。

## 环境与复现

实测 Python **3.11.15**，Linux x86 CPU，主机报告40个逻辑CPU；仅使用4个进程、每个单线程BLAS。无GPU、无付费API。

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python download_data.py
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest tests -q
python run_experiments.py --reps 2000 --jobs 4
python run_stratified.py --jobs 4
python analyze.py
python plot.py
latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
python validate.py
```

- `requirements.txt`：直接依赖的实测固定版本；`requirements-lock.txt`：最终环境完整 `pip freeze`。需联网安装依赖；安装耗时随网络而变。
- PDF构建需 `latexmk`、`pdflatex`、`bibtex`，常用 TeX Live 宏包。`plot.py` 的论文 PDF 图片通过 PGF/pdflatex 输出嵌入 Type1 字体，PNG 使用常规 Matplotlib 后端；均为相同数据和图形。
- 目前提供的 CSV/图表允许跳过模拟直接运行 `analyze.py`、`plot.py`、LaTeX。所有图表均由已运行结果生成，不是示意图。
- 同一CPU环境主实验实际 **127.2秒**，精确分层重放 **12.1秒**；全流程（不含安装/下载）通常数分钟。不同主机耗时会变；摘要列 `seconds` 是累计单元耗时，**不能**做逐方法速度比较。
- 小规模启动检查：`python run_experiments.py --reps 30 --jobs 1 --smoke`。**该命令覆盖 results/ 中部分主结果和配置**；仅在另一个工作目录副本运行。最终分析脚本要求完整32单元×2000次，不将 smoke 冒充完整实验。
- 输出相对各脚本所在目录，运行命令应在本项目根目录。主流程会覆盖同名结果，保留归档后再重跑。

### 随机数、数据与版本

- 基础seed：20261102。每单元用 `SeedSequence([base_seed, scenario_id, n, N/n])`；方法无内部随机抽样。分折为 iid 记录顺序的索引mod5，与分数/标签无关。
- 数据来自 `ppi-python==0.2.3` 的原始数据ID；下载器见 `download_data.py`。原包版本和数据SHA-256在 `data/manifest.json` 与 `results/config.json`；若下载字节变化，下载器报错，不静默继续。
- `galaxies.npz`：16,743个二元标签及原预测；`forest.npz`：1596个。检查无缺失，分数位于[0,1]。原包代码MIT，示例 `.npz` 独立许可未声明；不要据此假定可重新公开分发数据。复现包提供获取脚本与哈希。
- 原数据、数据EDA、原模型训练来源/选择偏差并不因重抽样消失；科学总体外推不在保证范围内。

## 代码与图表映射

| 文件 | 内容 / 论文产物 |
|---|---|
| `methods.py` | Wald、PPI、原论文无约束PPI++、精确匹配包默认PPI++、三种CF基、unsafe in-sample、精确二项、EB及安全字典 |
| `exact_stratified.py` | 二分层精确二项区间；随机分层计数与池化分数质量的不确定性均计入 |
| `run_experiments.py` | 主32设置，`results/raw/*.csv.gz`、`summary.csv`、`oracle.csv`、`config.json` |
| `run_stratified.py` | 原输入确定性重放，`supplement_raw/`、`stratified_summary.csv` |
| `analyze.py` | 全部4张论文表、数值宏；`all_summary.csv`、`paired_comparisons.csv`、5块重复稳定性、质量检查 |
| `plot.py` | 图1 `figures/efficiency/plot.*`、图2 `figures/validity/plot.*`、图3 `figures/coverage_all/plot.*` |
| `tables/main_asymptotic.tex` | 论文表1：n2000渐近层，7分布 |
| `tables/main_exact.tex` | 论文表2：n2000有限样本层，7分布 |
| `tables/ablation.tex` | 论文表3：n500固定基消融，20行 |
| `tables/full_results.tex` | 论文表4：全部442个方法×设置结果及不确定性 |
| `tables/numbers.tex` | 摘要及正文的26个自动生成数值，避免手工抄数 |
| `tests/`、`validate.py` | 公式、包端点、协方差、边界、精确枚举、对数p值及产物校验 |

## 正确解读输出

- 每个原始区间文件有 `rep,method,truth,lower,upper,width,raw_width,covered` 等字段。`selected`只对EB字典有意义。
- `width_ratio_ppipp` 是**平均宽度之比**，不是逐重复比值的平均。`ratio_se`利用配对信息。
- 覆盖误差条为Wilson95%；平均宽度有MC SE，配对比值有delta-method MC SE。
- 显式多重覆盖诊断分有限层160项、渐近/unsafe层256项和oracle26项，以单侧精确二项检验及Holm校正。未拒绝不证明有效性。
- CSV务必 `pd.read_csv(..., keep_default_na=False)`，否则合法场景名`null`会被当作缺失值。
- 极端p值在普通浮点数下会下溢。`all_summary.csv`额外提供log概率、log10概率、科学计数字符串与`below_float`标记。科学计数字符串读取时显式 `dtype={'under_p_scientific':str,'under_holm_scientific':str}`，不要把浮点0解释为数学上的0。
- 原始端点输出保留12位有效数字，摘要在舍入前计算，因此从CSV重算有约1e-12差异是正常的。
- 主运行未保存抽样行ID；代码中同一次调用共享输入、输出rep键以及抽样确定性重放提供配对证据，不声称存在未保存的ID日志。独立审稿抽查全部32单元前3次共96组数据，1326个端点三元组均在输出精度内重现。

## 预先计划、调整、失败与缺失比较

- `todos.md`、`artifacts/prerun_amendment.md`、`artifacts/prerun_sha256.json`保留统计代码冻结记录；只属于本地记录，不是独立时间认证的注册研究。
- 精确分层基线在完整结果尚未读取时另行声明，见 `artifacts/exact_baseline_addition.md`。它不是根据结果搜索的阈值。
- 从多项式到rich同时增加三次项和阈值项，**不能证明阈值项的独立必要性**；论文已收窄表述，未伪造额外消融。
- 初次依赖检查、PDF提取程序缺失、测试端点形状不一致、浮点绘图误差条、字体/表题格式、p值下溢均如实记录在 `experiment_log.md`；方法层面不按结果调参。
- 未实现原PPI的betting型有限样本MeanCI；不宣称本文精确/EB比较覆盖全部有效PPI方法或达到有限样本SOTA。没有运行的东西不报告成已完成。

## 文献访问与禁读边界

只直接阅读允许的五篇起步原文及2009年的经验Bernstein原文；不做主题检索、推荐扩展或引用链搜索。实际页码/哈希/URL见 `literature/allowed_sources.md`、`literature/access_log.jsonl`、`literature/main_thread_access.md`。代码/数据仅取固定原包和指定Drive文件，模板仅取ICML官方页面。未识别出禁读材料，也未试图推断其身份；由于禁读论文未命名，不能证明不存在未知重叠。没有已识别的偶然接触需要报告，详见 `literature/incident_log.md`。

**学术定位**：已交付完整可复现论文与代码，但独立审稿仍认为技术新颖性及实证外部价值不足以保证ICML主会接收；不将“构建成功、数字正确”写成“已达接收标准”。
