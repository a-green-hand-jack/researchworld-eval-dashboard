# 用少量基准预测其余基准表现：完整研究与复现包

论文：[`paper/main.pdf`](paper/main.pdf)，LaTeX：[`paper/main.tex`](paper/main.tex)。使用 NeurIPS 2026 最新官方模板的 preprint 模式；正文 8 页，参考文献、附录与填写完整的 16 项官方 checklist 另计。没有投稿或声称获得会议接收。

研究结果来自本目录实际执行的 CPU 实验，没有用合成结果替代榜单实测分数。合成高斯实验单独标记，仅核对理论公式。论文用英文撰写。

## 主要结论及边界

- 对固定版本 MTEB 的 56 项英语任务，用 8 个任务选择性评测，标准化 RMSE 比相同协方差预测器下的随机选择降低 9.8%；发布者聚类 bootstrap 的 95% 区间为 6.8–13.5%。253 个模型贡献历史数据，但只有 63 个完全观测模型能用于完整的新模型测试。
- 独立的生成式模型数据包含 4,442 个模型、6 个基准。它不能证明上百项生成式基准同样可压缩。
- “其余任务”取决于实际选了哪些任务。固定目标任务后，生成式榜单的原始分数误差优势明显收缩；选走难预测任务是有效的操作收益，但不能等同于固定下游任务很容易预测。
- 历史数据进一步稀疏时，低秩方法会超过协方差方法；按每个预算单独调参的低秩基线在较大预算下也能持平。没有证据支持通用的最优方法或通用的足够预算。

## 文件导航

| 路径 | 内容 |
|---|---|
| `paper/main.pdf`、`paper/main.tex`、`paper/references.bib` | 完整论文、源文件及确实查阅的参考文献 |
| `paper/checklist.tex` | 2026 官方 checklist，问题与指南保留，逐项回答 |
| `paper/vendor/` | 原始官方模板 ZIP、style、说明及下载来源页 |
| `scripts/models.py` | 缺失历史协方差、低秩预测、Schur / D-opt / central / 验证集贪心选择 |
| `scripts/predict.py` | 对自有历史矩阵推荐查询任务，并从新模型实测查询分数推断其余分数 |
| `scripts/prepare.py`、`scripts/core.py` | 固定版本获取、逐格来源、预处理和覆盖/版本敏感性队列 |
| `scripts/experiment.py` | 主要交叉验证、按发布者留出、时间留出、固定目标、缺失压力实验 |
| `scripts/fixed_all.py` | 六任务榜单所有 15 个双目标面板的完整审计 |
| `scripts/budget_baseline.py` | 每个预算独立调参的更强低秩基线 |
| `scripts/theory.py` | 明确标记的合成高斯理论核对 |
| `scripts/report.py` | 所有论文表格、图片和实证数字宏；同时输出 `summary.csv`、`paired.csv` |
| `scripts/test_invariants.py`、`scripts/audit.py` | 数值、信息泄漏、划分、损失重算、正文页数、模板完整性审计 |
| `data/processed/` | 分数矩阵、模型元数据、数据审计、MTEB 每个格子的来源 |
| `results/` | 每模型损失、逐任务误差、每折模型划分/查询顺序/超参数和运行资源 |
| `logs/` | 已实际执行运行的日志 |
| `PROTOCOL.md`、`RESEARCH_LOG.md` | 结果前的本地分析设计和完整研究过程/调整/失败记录 |
| `requirements.txt`、`run_all.sh` | 精确 Python 依赖与端到端复现入口 |
| `scripts/package.py`、`MANIFEST.sha256` | 便携交付包及文件校验清单的生成 |

## 环境与完整复现

测试环境：Debian 12、Python 3.11、Intel Xeon Gold 6230 2.10 GHz。无需 GPU、模型权重或付费 API。精确 Python 包版本在 `requirements.txt`。核心实验单进程限制一个 BLAS / OpenMP 线程；可以在四核机器上并行运行独立实验，但同一输出文件不要同时写入。

```bash
cd /work
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
bash run_all.sh
```

编译还需要 `pdflatex`、`bibtex`、`latexmk` 和标准 LaTeX 包。Debian 可安装 `latexmk texlive-latex-extra texlive-fonts-recommended`。这些工具在本次工作环境中已存在。单独重新生成图表及 PDF：

```bash
.venv/bin/python scripts/report.py
make -C paper
.venv/bin/python scripts/audit.py
```

不需重新下载数据即可重跑；`prepare.py` 对已存在的固定文件使用本地副本。需要全新下载时，将两个原始数据文件移至其他位置后重跑 `scripts/prepare.py`。下载约 378 MiB 的 MTEB 压缩包及约 1.1 MB 的 OLL parquet；MTEB 按 tar 流读取，不解压整库历史。无需 GitHub/Hugging Face 账号。存储预算含本地 Python 环境、原始压缩包、结果与文稿，当前小于 5 GB。源代码打包文件不包含 Python 环境、受版权约束的文献 PDF 或原始数据压缩包；下载脚本和所有分析代码均包含。

对新模型使用方法时，先在历史验证集选择 alpha，再推荐任务（下面的 `0.1` 只是命令参数示例，不代表所有数据的最优值）：

```bash
.venv/bin/python scripts/predict.py --history data/processed/mteb.csv --budget 8 --alpha 0.1 --output queries.json
# 实际运行推荐任务后，把同单位分数写为 {"TaskName": 0.75, ...} 的 JSON。
.venv/bin/python scripts/predict.py --history data/processed/mteb.csv --budget 8 --alpha 0.1 --scores measured_scores.json --output prediction.json
```

该示例命令不会伪造新模型的实测分数；第二步需要使用者自己的真实评测记录。预测文件将实测与推断字段分开。

本次最终实验各阶段 wall time 合计约 7.3 分钟（记录见 `*_runtime.json`；该数不包含下载、安装、绘图、文稿编译、烟雾测试和中断的开发检查）。最大已记录实验进程 RSS 约 854 MiB。新机器首次完整复现建议预留 10–20 分钟再加下载与依赖安装；实际耗时取决于 CPU/网络。论文中的运行时间是实际记录，不是该建议时间。详细环境和总目录大小见 `results/audit.json`。绘图/审计可临时使用更多内存，仍在任务建议的 16 GB 内。

## 数据固定版本、处理和许可

1. MTEB：`https://codeload.github.com/embeddings-benchmark/results/tar.gz/6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`
   - Git 提交：`6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`
   - 压缩文件 SHA256：`84773e577197630206eacc1790c5fd793d21393b698f6562b0a8f0a1ea31002f`
   - 仓库元数据声明 CC0-1.0，记录在 `data/raw/mteb_repo_metadata.json`；固定归档没有独立 LICENSE 文件。模型自己的许可不用于重标分数数据。
   - 原始英语 56 任务，CQADupstack 合并成一项；只取英语 `main_score`，test 划分（MSMARCO 用 dev）。多个模型 revision 取覆盖最多的一个，平手按字符串排序。至少 10 项有分数才纳入历史。相关系数允许负值，保留原始单位，不截到 [0,1]；分数点误差是原始单位乘 100。
2. Open LLM Leaderboard：`https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet`
   - 数据集提交：`9c09a7cae43334062a82cb164f2ef255013dafa2`
   - 文件 SHA256：`f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5`
   - 数据卡没有声明数据集许可。这一未解决问题在论文与 checklist 中明确说明；本目录 MIT 许可不覆盖该数据。未将 `Hub License` 模型许可列当作数据集许可。
   - 使用 IFEval、BBH、MATH Lvl 5、GPQA、MUSR、MMLU-PRO 的 `Raw` 列；删除 flagged，按 fullname 去重，优先 bfloat16/float16/float32，再删除完全相同分数行。

完整 MTEB 历史本身存在任务数据集 revision 差异。`mteb_cell_provenance.csv` 保留来源和 revision，`mteb_modal` 只保留每个任务最常见 revision，作为探索性敏感性实验，不宣称统一了所有评测协议。MTEB-core 的 30 个任务仅按原始可观测覆盖率 ≥70% 选择。不要把这些重叠队列当作独立复制数据。

## 评估协议和随机性

- 外层随机行划分和按发布者 namespace 分组的五折，分别使用种子 `17, 29, 43`。发布者分组不是经过核验的模型家族留出。
- 内层用 20% 历史行/组作验证；只有完全观测验证行进入验证损失；最终在全部外层历史上重拟合。测试模型只有完全观测行，测试分数不进入拟合、标准化、调参或选择。
- 常规低秩与协方差的共享预算超参数由三个随机顺序、最小四个非零预算的验证误差确定。独立预算调参基线另存于 `budget_baseline_*`。
- 随机选择使用十个顺序，匹配同一折中的不同预测器。完整的实际顺序和每折成员在 `*_designs.json`。不依赖“当前最新版”划分行为，精确 scikit-learn 版本已固定。
- 首先对同一模型的随机查询顺序及重复划分损失平均，再跨模型平均并开平方。标准化分母来自训练模型；同时报告原始分数点 RMSE 和 MAE。
- 置信区间使用发布者聚类成对 bootstrap，2,000 次、种子 `20261102`。这是给定已拟合模型/查询顺序的条件区间，没有包括完整重新训练不确定性、没有多重比较校正。
- 时间留出依 Submission Date 的 60% / 80% 分位数划分，同日不拆分；缺失日期不进入时间实验。实际日期界限和人数在 `results/audit.json`。
- 理论模拟种子 `20261102`，50,000 个高斯测试向量；只用于检验解析风险与边界，不能当成真实模型得分结论。

## 论文每张表和图的生成映射

所有最终 LaTeX 表、数值宏和绘图由 `scripts/report.py` 生成。下面列出它消费的实验输出；每个损失文件都能由对应脚本重建。

| 论文对象 | 生成文件 | 上游脚本/结果 |
|---|---|---|
| 表 1 数据概况 | `paper/generated/data_table.tex` | `prepare.py`、`core.py`；`data/processed/*_audit.json` |
| 表 2 主要成对区间 | `paired_table.tex` | `experiment.py` 的 random / publisher main losses |
| 表 3 基线比较 | `comparison_table.tex` | 主实验 + `budget_baseline.py` |
| 表 4 敏感性 | `sensitivity_table.tex` | fixed、missing、core、modal、temporal；`fixed_all.py` |
| 表 5 预算阈值 | `budget_table.tex` | 主实验 Schur 的已测试预算点，非插值 |
| 表 6 理论模拟 | `theory_table.tex` | `theory.py`；`results/theory.csv` |
| 表 7 逐任务误差 | `tasks_table.tex` | `mteb_random_main_tasks.csv`；只统计未选中任务 |
| 附录完整对照表 | `full_table.tex` | 主实验及预算独立调参低秩基线 |
| 图 1 误差曲线 | `figures/curves.pdf` | 主实验 + 预算独立调参低秩基线 |
| 图 2 固定目标与缺失 | `figures/audits.pdf` | MTEB fixed/missing；Open LLM exhaustive fixed pairs |
| 图 3 理论核对 | `figures/theory.pdf` | `theory.py` |
| 图 4 原始误差与覆盖 | `figures/raw_calibration.pdf` | 主实验逐模型误差和条件区间覆盖 |
| 正文实证数字 | `paper/generated/numbers.tex` | 同一结果表和实际 runtime 文件 |

## 独立性、透明度和可用性

没有主题文献搜索；只直接读取任务提供的五篇起步文献、Gaussian Processes for Machine Learning 第二章、固定数据及官方会议材料。没有尝试识别禁止论文，未遇到已知禁止内容。具体阅读版本、下载失败、实现修正、中断检查和结果后新增审计见 `RESEARCH_LOG.md`。这是本地设计记录，不是外部预注册。

研究设计、代码、分析和写作由自主 LLM 研究代理完成；没有独立人类审核。交付代码包含测试和重新计算审计，可用于进一步复核。任何推断分数都应与实测分数区分，不能用本研究为未测安全能力背书。
