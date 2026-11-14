# 用少量基准预测其余基准：研究与复现

## 交付入口

- **论文 PDF：`paper.pdf`**；LaTeX：`paper/paper.tex`，参考文献：`paper/references.bib`。
- `final_report.md`：中文研究摘要、结果、限制与下一步。
- `src/`：获取、清洗、建模、实验、统计、制图及可实际使用的两阶段预测接口。
- `tests/`：数值不变量、隐藏坐标访问、数据解析、分组缺失占位符和划分测试。
- `artifacts/`：逐次划分、全部查询集合/预测/损失、调参记录、失败记录、审计和绘图输入。
- `code_and_results.zip`：便携的代码、论文源与运行结果包；不含大型原始下载、不含上游论文正文摘录。全部原始下载仍在工作区 `data/`，可按下列命令重新取得。

论文采用**官方 ICML 2026 匿名初稿模板**。正文不超过官方 8 页上限，Impact Statement、参考文献和附录另计；最终页数与构建检查见 `artifacts/build_audit.json`。所查官方说明/模板没有单独 checklist 文件要求，附录填写的是明确标记的**自愿复现与伦理清单**，不冒充官方表单。OpenReview 表单要求未逐项核查。官方模板及来源/哈希在 `paper/template_manifest.json` 和 `artifacts/template_provenance.md`。

## 结论先读

这是对标准 Gaussian 条件预测＋贪心残差迹风险选择的**实证审计**，不是声称全新算法或全面文献覆盖。

- 主数据：278 个嵌入模型、29 个任务，64.71% 格子有分数；60 个完整模型属于19个保守 owner/base 连通分组。仅完整模型作为验证/测试真值，不补造标签。
- 固定主比较预算 k=8，指定划分未测任务 RMSE：**3.08 vs 随机4.72**（原生分数乘100的 score points）。五个重叠划分的全套重建 RMSE：**3.32±0.93 vs 4.65±0.80**，±为划分间样本SD，不是CI。
- 与最大熵/验证贪心等选择器的差距较小。主划分只有6个测试组，八比较 Holm 校正下精确双侧符号随机化检验**结构上不可能拒绝**；不能宣称显著或独占优势。
- 稀疏历史中，33个可执行 Gaussian 压力拟合有18个到200步仍未收敛，另2个 MCAR20% 条件出现整列无观测。均保留、未反复抽掩码直到成功；压力表描述的是有上限的算法，不是收敛估计器鲁棒性证明。
- “全套RMSE≤2且未测RMSE≤3”的预设示例容忍度下，MTEB 没有预算通过验证规则。**没有普适的小 k 结论。** Bootstrap 规则是极端尾部分位数启发式，不是校准保证。
- 补充生成式榜单为独立六任务面板；在自审发现缺失基座占位符分组错误后，已完整纠正并重跑，不能当作未受检查的确认性复现。纠正后的指定划分 k=2：全套3.93 vs 随机6.42；验证规则仅在2/5划分选择k=4。该榜单数据许可未声明，不擅自重新许可。

## 数据版本、尺度和许可

| 输入 | 固定版本 | 处理/许可 |
|---|---|---|
| `embeddings-benchmark/results` | `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383` | CC0-1.0；每任务固定 modal dataset revision、English test/main_score；原生[-1,1]分数乘100，保留负相关，不将缺失当0。MTEB是嵌入模型而非生成式LLM。 |
| `open-llm-leaderboard/contents` | `9c09a7cae43334062a82cb164f2ef255013dafa2` | 六个 `Raw` 列乘100；排除 flagged/merged，确定性去重，完整病例。数据集许可未声明；模型许可列不是数据许可。 |

直接数据 URL 和 SHA256：`data/mteb_manifest.json`、`data/openllm_manifest.json`。冻结任务、面板形成过程、分组：`data/panel_manifest.json`、`data/groups.csv`、`data/openllm_groups.csv`。重复模型版本按覆盖率、版本字符串排序选取，绝不选最高分。相同 owner 与显式 base/adaptation 连通；未知亲缘关系不等于独立。

**重要纠错记录：**首次补充分析把549条 `Base Model="Removed"` 当作共同祖先，错误过度合并。修正后该标记及其他缺失占位符不构成边，真实无斜杠名称仍可构成边；分组381→472。两套分数矩阵和MTEB分组逐字节未变。旧补充结果在 `artifacts/flawed_secondary_v2/`，旧初始运行在 `artifacts/pilot_v1/`，均不作为论文数据。完整时序见 `artifacts/attempt_ledger.md`、`self_review.md`、`revision_response.md`。

## 环境和耗时

- Python **3.11.15**，Linux x86_64；实际依赖逐版本固定在 `requirements-lock.txt`。
- NumPy2.4.6 / SciPy1.17.1 / pandas3.0.6 / matplotlib3.11.2；无需GPU、模型权重或付费API。
- 全部数值实验限制为**1个 BLAS/OpenMP 线程**。最终实测全实验（含合成公式核对、探索性行随机对照）约**101秒墙钟、99秒CPU**，峰值子进程RSS约**220MiB**；精确值见 `artifacts/resource_usage.json`。此耗时**不含**下载、清洗、统计/绘图和LaTeX，更不是实际运行基准的节省。
- 首次395.7MB快照下载本机约77秒、流式筛选JSON约19秒；网络速度不同，建议为下载留2–15分钟。统计/绘图约十余秒，PDF编译通常数秒。工作区实测大小在 `build_audit.json`，远低于5GB；不完整解压2.7GB原始仓库。
- 系统需 TeX Live/MacTeX（含 `latexmk`, `pdflatex`, `bibtex`, `seqsplit`, ICML模板依赖）。不自动以管理员权限安装系统软件。

## 完整复现（在工作区根执行）

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt

# 网络步骤：仅固定数据源，已存在的快照不会重复下载
python src/data.py --source all
python src/prepare.py

# 回归测试
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests

# 全数值实验 + 统计/表格/图 + 实测资源记录
python src/reproduce_measured.py

# 编译；latexmk 自动处理参考文献和交叉引用
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/paper.tex
python src/audit_build.py
```

也可分阶段运行：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run.py --dataset mteb --stage main
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run.py --dataset mteb --stage stress
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run.py --dataset openllm --stage main
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run.py --stage synthetic
python src/analyze.py
python src/supplement.py
```

不要并发启动两次复现：文件会被覆写。若要保存旧运行，先复制对应目录。源码由 `Path(__file__)` 定位根目录，不要求固定为 `/work`。

## 方法与评估设置

- 种子 **11、23、37、53、71**；seed11为指定主比较，其余重叠划分仅看稳健性，不当5个独立测试样本。
- MTEB完整锚点组分配7训练/6验证/6测试；其他组按60/20/20分配，其不完整行只在该组属训练时进入历史数据。所有变换、均值、协方差与因子只拟合训练行。
- 主预算`0,1,2,4,8,14,29`；补充`0,1,2,3,4,6`。20条相同随机嵌套查询路径用于随机基线；**平均损失再开方，不平均预测，也不平均RMSE**。
- Gaussian每轮对角收缩，候选`.1,.3,.6,.9`，最大200步/相对变化`1e-5`；Factor观测格ALS40步，rank`2,4,8`（维度裁剪）、ridge`.01,.1`。验证调参用前5随机路径及非平凡预算；不以测试选参。
- 对照：随机/方差/相关中心性/最大熵/训练内三折OOF贪心＋相同Gaussian；独立任务均值；随机和相同风险查询的低秩因子。
- 对每个组先平均其模型和任务的平方误差，再跨组等权平均后开方。主全套损失将实测坐标误差置0；固定k时未测MSE=全套MSE×p/(p-k)。另提供两选择器共同未测任务比较以暴露目标集合变化。
- 不确定性：2000次组块bootstrap（条件于拟合，不覆盖训练/亲缘/面板选择不确定性）；配对组MSE符号随机化、8比较Holm。补充检验属于纠错后的探索分析。所有掩码、k、规则均公布。

## 实际使用：先选择，再传入实测分数

输入历史CSV第一列为model，列为task，空白为缺失；groups CSV须有`model,group`。用户应在历史验证集独立选择收缩系数，而不是盲用示例默认值。

```bash
python src/predict.py select --history data/panel.csv --groups data/groups.csv \
  --k 8 --shrink 0.1 --out artifacts/my_policy
# 按 artifacts/my_policy/tasks_to_measure.csv 实际评测；写 measured.csv，列为task,score。
python src/predict.py predict --fit artifacts/my_policy/fit.npz \
  --measured measured.csv --output artifacts/my_policy/new_model_scores.csv
```

输出区分`measured/predicted`，附模型内条件SD，**不是校准置信区间**。分数单位必须与历史一致；计数预算不等于实际耗时预算。`artifacts/cli_demo/`提供从主划分训练历史产生、与已存预测核对过的真实数据接口示例。

## 每张图表的生成脚本

| 论文对象 | 生成代码 | 文件 |
|---|---|---|
| 主结果表 | `src/analyze.py: tables` | `paper/tables/main.tex` |
| 压力/消融表 | 同上 | `stress.tex` |
| 主划分配对效应与检验表 | `analyze.py: inference,tables` | `inference.tex` |
| 共同未测目标比较 | `analyze.py: evaluate输出汇总,tables` | `common.tex` |
| 各种子结果、划分/参数表 | `analyze.py: tables` | `per_seed.tex`, `splits.tex` |
| 验证预算选择/测试描述 | `analyze.py: policy_audit` | `adequacy.tex` |
| 冻结策略测试CI | `src/supplement.py` | `policy_test.tex` |
| Gaussian校准表 | 同上 | `calibration.tex` |
| 收敛/保留率/支持数表 | 同上 | `convergence.tex` |
| 图1缺失掩码 | `analyze.py: plots` | `paper/figures/missingness.pdf` |
| 图2预算风险曲线 | 同上 | `risk_curves.pdf`（同名PNG） |
| 图3稀疏历史与风险校准 | 同上 | `stress_calibration.pdf`（同名PNG） |
| 合成公式核对（非实榜结果） | `src/run.py: synthetic` | `artifacts/theory_check.csv` |

`src/analyze.py: verify_predictions`从已存预测重算主损失，要求与全精度统计误差<1e-4，并核对实测坐标完全一致；`analysis/prediction_verification.csv`给出逐运行最大差异。

## 独立阅读边界与失败披露

研究论文只直接查阅起步清单中的5篇；不开放式检索，不追随引用、推荐或后续论文。书目、实际版本、阅读深度及初始两篇中读到的相关工作段落见 `artifacts/literature.md`。没有识别或刻意检索禁止论文；没有检测到需要停止阅读的可识别禁止内容，但不声称获准正文绝不会间接提到它。模板和数据来源访问另列，不把未经阅读的论文写进参考文献。

原始文献摘录是工作取证文件，不随便携包再分发。旧失败/错误分析不会被删掉伪装成一次完美运行。最终结论仅适用于公布的面板、分组近似、计分单位和准确查询/等成本假设。
