# 模型规模与延迟泛化：完整研究交付

## 入口与结论
- **论文 PDF：`paper.pdf`**；LaTeX 主文件：`paper/main.tex`，配套章节与官方样式均在 `paper/`。
- ICML 2026 最新已核实发布的官方模板，匿名投稿格式；正文 **7 页**（上限8页），影响声明、参考文献与附录在后。模板来源/2027尚未发布的核验见 `official_template/PROVENANCE.md`。未实际投稿，也不声称已达到录用标准。
- 研究简报：`final_report.md`；冻结协议：`protocol.md`；探索性扩展：`extension_protocol.md`；完整统计审计：`analysis/independent_audit.md`。

在本研究的平方激活 MLP、全批量 AdamW 和有限训练预算内，增宽能同时加快训练拟合与泛化，但两种加速不同：64→256 的移位时间比只增加约 **15.3%**，否定了预先承诺的“至少翻倍”。是否出现操作性定义下的 grokking 还取决于衰减、数据量、激活及优化器坐标，不存在本实验支持的普适参数量阈值。

**不应忽略的负面结果：**P2 的成功率差≥0.5总体量级仍不确定；随机标签控制略高于机会水平，不能称为干净的阴性对照通过；部分首次持续跨阈值的模型后来退化；无衰减/小宽度的未泛化是预算内观察，不是永不泛化。

## 1. 环境
实测 Python3.11.15，Linux x86_64，Intel Xeon Gold6230；CPU，无GPU。每进程1个PyTorch/BLAS线程，原始实验最多8个独立进程。`hardware.txt` 是主机可见资源，不能据其40CPU宣称持续独占40核。

精确依赖：`requirements.txt`；完整环境：`environment.lock.txt`；TeX版本：`latex_environment.txt`。依赖安装（需要联网，但数据/模型不需下载）：
```bash
python -m venv .venv
source .venv/bin/activate
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
```
PDF编译还需要 `pdflatex`、`bibtex` 及标准LaTeX包（microtype、graphicx、booktabs、hyperref、amsmath、amssymb、natbib等）；原环境为TeX Live2025/dev/Debian。官方ICML样式已随附，无需再次下载。

**路径约定：**命令从仓库根目录执行。原始清单和已完成配置保存绝对根路径 `/work`，以维持冻结哈希。最简单的跨机器复现方式是把本目录挂载为容器/虚拟机的 `/work`。`make_manifest.py` 和 `make_extension.py` 可在另一根目录生成新路径清单；这会改变清单字节哈希，而不改变科学参数，应与原始冻结副本区分。直接重用已有绝对路径配置前请确认路径，不要覆盖原证据。

## 2. 数据、模型与种子
- `train.py:make_data` 在内存穷举全部模加法/乘法输入，不下载数据。数据构造版本 `modular-pairs-v1`；p31有961个有序对，p53有2809个。
- 主协议按交换轨道 `{(a,b),(b,a)}` 分组，选半数轨道训练；其余是留出测试。训练与测试没有逆序对重叠。原始JSON键 `val` 在论文中称test；无第三验证集。只有独立试验种子用于挑选设置，正式测试结果不用于调参或早停。
- 无偏置两层网络 `V(Wx)^2`，参数量3pm；最大47,616参数。CE全批量，AdamW lr=.01、betas(.9,.98)、eps1e-8、12,000更新；每25步记录；最终运行开启CPU次正规数刷新。所有矩阵均衰减。
- 主配对块：初始化100..109 / 划分1000..1009；二级控制取前5块。p53：200..204 / 2000..2004。扩展：300..304 / 3000..3004。W/V master RNG偏移100000/200000；随机轨道标签独立RNG为划分seed+300000。
- 原始探索种子900..904，27次试运行，全部留在 `artifacts/pilot*`；不与确认数据混合。部分早期试运行采用旧初始化，可由缺少 `master_width` 的原配置走保留的旧初始化分支重现。
- 清单、逐次配置、划分哈希、最终模型和完整轨迹均随附。`main_manifest.json`185次，`extension_manifest.json`20次；`protocol_freeze.json`保存原始冻结SHA256。

## 3. 不训练即可重建论文
```bash
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python -m unittest -v test_train
python analyze.py
python analysis/independent_audit_recompute.py
python analysis/independent_audit_supplement.py
python random_label_null.py
python generate_tables.py
python plot.py
python audit_artifacts.py
bash build_paper.sh
```
若审计脚本在编译前执行，已随附的PDF仍可用于版式检查；最终再运行一次 `python audit_artifacts.py`。分析/图表通常为秒至分钟级，不需要重训。训练程序只支持从配置重新开始；**不支持中途优化器状态续训**。

**权威端点：**五个连续评估点≥99%，跨度100更新；C=11900。`analysis/runs.csv` 和 `audit_endpoints.csv` 从 `metrics.jsonl` 重算。原始 `summary.json` 的快速端点采用3点，其 `t_val`、`ratio`、`delay` 不能当作论文的冻结端点；差异已审计并披露。

主统计在 `analysis/audit_checks.json`：时间效应用完整加权经验bootstrap枚举，避免全局Monte Carlo RNG因是否包含扩展而产生区间抖动；这是经验重采样分布的精确计算，不是精确总体置信覆盖。原始20,000次重采样输出仍可重现。P2同时给非退化保守界；不得把全为+1时的bootstrap[1,1]解释为总体无不确定性。修正记录见 `analysis/CORRECTIONS.md`。

## 4. 重新训练
已完成的配置相同时，`launch.py` 会跳过。**现有目录运行launcher不是一次新的重训。**完整重训请保留本交付物，复制到独立环境/目录，移走副本中的 `artifacts/frozen`、`artifacts/extension` 到副本之外再运行：
```bash
python make_manifest.py
python launch.py main_manifest.json --workers 4
python make_extension.py
python launch.py extension_manifest.json --workers 4
```
或者在独立输出目录把单个配置的 `out` 改为新目录，运行：
```bash
python train.py --config NEW_CONFIG.json
```
`bash reproduce.sh` 执行单元测试、两清单、分析/审计/绘图/编译；默认重用已有结果，不擅自删除证据。最终生成文件SHA清单由 `python package_results.py` 重建。

**实测成本：**205次最终运行共2,460,000更新，训练进程CPU时间总计5941.946秒（1.65 CPU小时），单次elapsed17.4–270.2秒，CPU13.6–135.7秒；耗时依赖主机负载、BLAS与刷新设置。首次185次后台批次约1725秒；探索扩展20次随后执行。过程elapsed总和3.39小时不是并行墙钟时长。以上均不含27次试运行、安装、文献读取、统计、写作。保守预计其他CPU上全套需要数小时；未声称跨平台位级一致。

## 5. 每张图表的来源
| 论文对象 | 文件 | 生成入口 / 数字来源 |
|---|---|---|
| 图1，宽度与两种时钟 | `figures/scaling.{pdf,png}` | `plot.py`；runs/curves/audit_checks |
| 图2，衰减与坐标 | `figures/coordinates.{pdf,png}` | `plot.py`；逐次曲线及分组bootstrap |
| 图3，适用范围 | `figures/scope.{pdf,png}` | `plot.py`；p53及控制/扩展 |
| 附录诊断图 | `figures/diagnostics.{pdf,png}` | `plot.py`；固定块100 |
| 附录退化案例 | `figures/regressions.{pdf,png}` | `plot.py`；弱衰减100、克隆/配方102 |
| 附录全部主实验曲线 | `figures/allseeds_primary.{pdf,png}` | `plot.py`；全部60次 |
| 附录全部迁移曲线 | `figures/allseeds_transfer53.{pdf,png}` | `plot.py`；全部20次 |
| 表1，宽度扫描 | `analysis/main_table_full.tex` | `analyze.py`；精确保留半步中位数 |
| 表2，坐标对照 | `paper/results.tex` | `analysis/independent_audit_supplement.py` → `audit_secondary_comparisons.csv`，按4位小数排版 |
| 附录时钟区间表 | `paper/main.tex` | `analysis/independent_audit_recompute.py` → audit_checks，按6位小数排版 |
| 附录全部单元表 | `analysis/all_cells_table.tex` | `generate_tables.py`；group_summary |

`analysis/curves.csv`保留98,605个评估点；`runs.csv`保留全部205次而非只成功者；各表的n是独立联合种子块，不是检查点数。次级比较未进行多重检验校正，不作确认性显著性主张。

## 6. 文献独立性与访问披露
仅直接读取用户起步列表中的5篇原始PDF（Power、Varma、Kumar、Liu、Loshchilov/Hutter），未执行本题主题检索、引文追踪、未指明论文身份推断或代码仓库读取。PDF和版本/哈希在 `literature/`。

**必须披露的处理例外：**研究子代理在允许的Varma等 arXiv:2309.02390 PDF中探测附录边界时，意外显示了数行参考文献。精确行数未记录；未把这些行用作证据，未跟随引用，未打开其他论文。未进一步识别它们是否涉及被禁内容，也不据此推测被禁论文身份。已停止该边界输出方式；后续阅读副本排除参考文献。不能宣称“零参考文献暴露”或穷尽文献/首创性已核验。详情 `literature/notes.md`。

官方会议页面仅用于模板与规则核验，不作为新学术文献。公开ICML2026材料中未找到随论文必填checklist；未核验投稿系统表单。论文包含强制影响声明及一份明确标为自愿的已填写复现/主张清单，并非冒充官方清单。
