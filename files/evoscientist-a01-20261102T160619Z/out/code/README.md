# 多任务排行榜的针对性分数投入

## 交付与主要结论

- **论文**：[`paper.pdf`](paper.pdf)，英文完整稿，ICML 2026 官方匿名模板。正文 **7 页**（上限 8 页）；第 8 页为 Impact Statement 和参考文献；附录含完整证明、局限、复现与填写后的自定义 checklist。总计 15 页。不是已接收论文，也不保证达到录用标准。
- **模板时效核查**：2026-11-02 直接检查官方 ICML 2027 style ZIP 地址返回 404，因此使用已公开的 ICML 2026 官方样式；核查 URL 与状态见 `sources/template_latest_check.json`。
- **LaTeX**：根目录 `paper.tex`、`paper/appendix.tex`、`paper/references.bib`、`paper/generated/`；官方未修改模板在 `paper/template/`。
- **代码与结果**：`code/`、`tests/`、`data/`、`artifacts/`；核心入口 `code/run_all.py`。
- **阅读顺序**：论文 → `final_report.md` → 本文复现说明 → `artifacts/paper_review.md` 及 `artifacts/review_resolution.md`。

这里的“投入”主要指**使目标共享第一所需的最少分数提升任务数**，不是实际训练成本。比较均值、中位数、Borda；目标只能向上改分，其他模型原始分数固定，但 Borda 对手的名次积分随目标变化重算。

核心发现是**条件依赖**：固定同一批可行且原先非第一的目标后，允许提升一半剩余分数空间时，中位数平均需要更少任务；允许提升全部空间时，均值平均需要更少任务。HELM 的 77 个共同非第一目标中，有 64 个“中位数需要改更多任务、但需要的最小总分数增量更低”。没有普遍更抗投入的规则；可行性、并列规则、分数尺度、任务粒度和投入指标必须明确。

## 1. 环境

实测 Python 3.11.15；精确 Python 依赖在 `requirements.txt`，环境记录在 `artifacts/environment.json`。仅 CPU，不调用模型或付费 API。BLAS/OMP/MKL 请求单线程；HiGHS 使用 SciPy 的默认求解器策略，MILP 数值最优间隙要求为 0。

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

绘图的 **PDF 字体使用 LaTeX**，因此完整运行还需要系统命令 `latex`、`pdflatex`、`latexmk`、`bibtex`、`kpsewhich`，及 Times/Helvetica/Courier Type-1 字体。Debian/Ubuntu 可由管理员安装：

```bash
apt-get install texlive-latex-base texlive-latex-recommended \
  texlive-latex-extra texlive-fonts-recommended latexmk
```

这是安装建议，不是本研究重新配置系统的实测命令。当前环境已有 TeX Live 2025/dev。`pypdf` 检查最终 PDF 的所有嵌套图形字体均为嵌入式 Type-1；不存在未解析引文、AUTHORERR 或越栏框。PNG 预览使用 DejaVu Serif，不依赖 dvipng；论文使用矢量 PDF。若只需数值结果，可加 `--no-plots --no-pdf`，无需 TeX。

## 2. 一键复现

从解压后的根目录执行；脚本内部按文件位置定位根目录，不依赖固定的 `/work` 路径。

```bash
# 联网：只获取允许的公开分数和官方模板；不检索任何论文
.venv/bin/python code/run_all.py

# 已有本地原始数据时：完全离线
.venv/bin/python code/run_all.py --offline

# 仅数值实验、证明表和测试
.venv/bin/python code/run_all.py --offline --no-plots --no-pdf
```

严格顺序为：下载/校验 → 整理数据 → 全体目标优化 → 独立验证 → 配对汇总与重采样 → 有限任务删除 → 精确反例 → 证明表 → 7 组测试 → 作图 → PDF 编译/审计。输出覆盖同名派生结果。**请勿把 `--offline` 用于没有原始数据的精简归档**；该归档须先运行下载。

单独步骤：

```bash
.venv/bin/python code/download.py --template
.venv/bin/python code/prepare.py
.venv/bin/python code/run.py
.venv/bin/python code/validate.py
.venv/bin/python code/summarize.py
.venv/bin/python code/task_influence.py
.venv/bin/python code/counterexamples.py
.venv/bin/python code/paper_assets.py
.venv/bin/python -m pytest -q tests
.venv/bin/python code/plot.py
.venv/bin/python code/build_paper.py
```

原始完整分析约 105 秒、独立验证约 148 秒；这两项不是全部工作耗时。含测试、作图和编译，预计单 CPU 约 **5–10 分钟**，网络与依赖安装另计，硬件不同会变化。完整清洁复算的实测耗时、CPU 时间和峰值进程内存在 `artifacts/reproduction_check.json`。另将精简提交归档解压到新目录，从公网重新取得并校验原始分数，执行完整 `run_all.py`（含证明表、7 组测试、图和 PDF），**307.08 秒 wall / 292.27 CPU 秒**全部通过并与提交数值相符；见 `artifacts/archive_reproduction_check.json`。未做模型训练，无 GPU 要求，规模远低于一周预算。

## 3. 清洁环境检查

已单独建立无 system-site-packages 的 `.repro_venv` 并按同一 `requirements.txt` 安装依赖；安装日志 `artifacts/clean_environment_install.log`。下面的脚本在新目录里从原始文件重新产生全部分数矩阵、主实验/敏感性、独立验证、配对统计、任务删除、反例、测试和图形，并与提交结果逐行比较：

```bash
.venv/bin/python code/reproduce.py
```

它复制本地原始文件，不进行联网抓取；联网可用性由下载阶段另外验证。比较允许 1e-12 相对、1e-14 绝对数值容差；任务数、可行性与对象标识不应变化。MILP 可有多个同样最优的端点集合，因此不要求不同求解版本选出相同 mask；每个新 witness 都独立核验。重采样、敏感性和汇总也比较。原始 `reproduce.py` 清洁运行覆盖数值分析和图形；PDF 由 `build_paper.py` 另行编译审计，精确证明表由 `paper_assets.py` 另行生成。最终一次运行记录以日志为准，不把依赖安装、审稿或下载计入数值计时。

## 4. 数据、单位与校验和

### HELM

- 公共桶 `https://storage.googleapis.com/crfm-helm-public/`。
- `mmlu/benchmark_output/releases/v1.13.0/`；`summary.json` 的日期为 **2025-01-10**。
- 只下载 57 个 `groups/json/mmlu_mmlu_subject:*.json` 学科汇总，不镜像逐运行记录。
- 每个学科使用 EM 列，全精度分数按模型显示标签对齐；79×57，无缺失/越界，无分数行重复；原始 run spec、样本量保存在审计文件。
- 构造的是等学科权重排行榜，不冒称官方 HELM 总分。

### Open LLM

- `https://huggingface.co/datasets/open-llm-leaderboard/contents`
- 固定提交 `9c09a7cae43334062a82cb164f2ef255013dafa2`，源快照最后更新 2025-03-20（任务提供的版本日期）；本次获取 2026-11-02。
- 文件 `data/train-00000-of-00001.parquet`：4,576×6，IFEval、BBH、MATH Lvl 5、GPQA、MUSR、MMLU-PRO。
- **Raw 已是 0–1 小数，不除以 100**；官方 normalized 列才是百分比。原计划中的 Raw 单位措辞错误，数据整理前已更正，不曾使用错误单位产生结果。
- 所有完整配置保留；54 个重复分数行、1 条 Flagged、1,683 条不可用 Hub 元数据不被当成作弊证据。另做去重和可用/未标记模型池敏感性。
- 分数矩阵 `data/processed/*.csv`；元数据、原始 SHA、模型标识均保留。不同配置不合并为同一模型家族。

`data/manifest.json` 记录每个下载地址、字节数、获取时间和 SHA-256；冻结校验基准为 `data/reference_manifest.json`。下载器对已存在或重新下载的原始数据核验冻结 hash；分数内容变更则报错，不能静默换版本。HELM 版本名本身不保证不可变，hash 才是本研究的内容标识。

- Open parquet SHA-256：`f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5`
- HELM summary SHA-256：`d4eb487e79bcdd7329bdcb10f5116364c2501842fe5e58da6e0bd717f90ee71e`

### 许可和归档范围

两个分数导出均无已核实的独立数据许可。**公开可访问不等于许可任意再分发**；HELM 软件 Apache-2.0、模型 Hub License 均不能代替分数数据许可。工作区保留本次研究所需原始与派生材料，外部分发前应另行确认权限。精简提交归档排除第三方原始分数和文献全文缓存，保留下载器、manifest、派生统计、代码、论文与来源阅读记录；不以本代码许可覆盖第三方材料。

## 5. 图表与代码对应

| 论文对象 | 生成脚本 | 输入/中间产物 | 输出 |
|---|---|---|---|
| Table 1：可行目标数 | `code/summarize.py` | `artifacts/results_*.csv` | `paper/generated/feasibility.tex` |
| Table 2：固定目标的均值/中位数比较 | `code/summarize.py` | `fixed_cohort.csv`、`cohort_ids.json` | `paper/generated/fixed_cohort.tex` |
| Appendix Table 3：精确反例最优任务数 | `code/counterexamples.py` + `code/paper_assets.py` | `counterexamples.json`，Fraction 精确运算 | `paper/generated/exact_supports.tex` |
| Appendix Table 4：Borda 精确 witness | `code/paper_assets.py` | 四个明确合成矩阵和给定任务集合，重新算所有对手积分 | `paper/generated/exact_borda_witnesses.tex`、`exact_table_values.json` |
| Appendix Table 5：敏感性 | `code/summarize.py` | 主实验与变体，匹配同一 target IDs | `paper/generated/sensitivity.tex` |
| Figure 1：全体目标的预算/成功曲线 | `code/plot.py --figure feasibility` | HELM/Open 主实验 CSV | `artifacts/figures/feasibility/plot.{pdf,png}` |
| Figure 2：固定群体的上限变化 | `code/plot.py --figure fixed_cohort` | `artifacts/fixed_cohort.csv` | `artifacts/figures/fixed_cohort/plot.{pdf,png}` |
| Figure 3：任务数 vs 总增量 | `code/plot.py --figure magnitude` | HELM rho=1 的 K、独立最优 L1 | `artifacts/figures/magnitude/plot.{pdf,png}` |

每张图目录还有可单独执行的 `plot.py`、规格说明和审计记录。所有数字来自实际结果或明确标注的精确合成数学反例；不将合成例子冒充公开榜单观测。

## 6. 统计和求解约定

- Primary：共享第一、rho=0.5；rho∈{0.25,0.5,1} 是敏感性，非调参。
- `K` 缺失加 `status=infeasible` 表示不可行，**不是任务数为零**；现有共享冠军 K=0。
- `witness_L1` 是选中任务一律提升到上限的费用；**不是 `L1_min`**。后者只为均值和奇数任务中位数独立求解（已有第一时零费用亦有效）。`L1_attained=False` 表示严格第一只有下确界；不可行时两者均缺失。
- 奇数中位数的可行最优任务数由跨越冠军阈值的数量决定，允许上限提高后保持平台；偶数中位数不得套用该公式。6 任务逐一枚举 64 子集。
- Borda 为整数双倍 midrank points，目标向上改分后对手也掉分。HELM 的 57 任务 Borda 是数值 MILP：全对手独立 witness 检查、0 gap、匹配 lower bound；不是有理数形式化证书。没有超时/未解决案例。
- 基数分数比较容差 1e-12；重算 0 和 1e-10 没有改变主结果。此检查不等于分数舍入或测量噪声实验，后两者**未运行**。
- Bootstrap：目标经验重采样，每种 seed 17/29/43 各 2,000 次，合并 6,000 次取 95% percentile；竞争矩阵不重建。仅描述性 empirical target-resampling intervals，**无总体覆盖或显著性主张**。模型家族相关性未被假定消除。
- 有限任务影响诊断：12 个预选 mean-rank 分层目标；Open 六种删一任务从 6→5，HELM 六组预选删两学科从 57→55。HELM 删一后的 56 任务常规中位数未实现，未假称已完成。Open 部分共同可行群体为空/仅 1 个对象，均如实保留。

## 7. 受限文献访问与失败记录

遵守任务的独立研究限制：没有主题关键词检索、猜测禁读文章身份、引用追踪或打开推荐结果。只按给定精确地址读取允许的原始文献。`sources/literature_notes.md` 明确哪些读了原始正文片段、哪些仅摘要/元数据；`sources/access_log.md` 逐项记录请求、范围和偶然预览。解析时偶然展示的开头引言、四条短 reference-like 标题行和软件日志前缀均未跟进，未被识别为禁读文章；由于身份未指定，不能声称完成了基于身份的排除认证。未尝试识别。精简归档不再分发文献全文缓存。

失败/修正见 `experiment_log.md`：最初数据目录误选了两套同内容学科表导致计数断言，已改为指定前缀；试探 ICLR 文件名返回 404，改用官方 ICML 2026；LaTeX 图形初始字体依赖失败，改为 Times/Helvetica/Courier Type-1 PDF，未升级权限；匿名模板缺少 corresponding-author 声明导致 AUTHORERR，已修复并由 PDF 检查防回归。这些都不是伪装为成功的实验。

## 8. 研究与交付边界

这是一篇可检查的独立研究稿，不是现实污染攻击、开发者行为指控或训练费用估计。评审仍可能认为数学工具简单、实际训练关联弱或文献覆盖受限；这些风险在审稿报告与修订说明中保留，不靠扩大结论掩盖。未来若研究实际资金/数据/算力投入，必须另行估计可实现的分数响应和跨任务影响。
