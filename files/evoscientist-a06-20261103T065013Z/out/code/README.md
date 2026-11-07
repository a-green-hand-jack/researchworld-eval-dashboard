# 自动调优后的基准分数：论文与复现包

## 入口

- `paper.pdf`：完整英文研究论文，官方 **ICLR 2027** 模板；正文不超过初投稿9页上限，附参考文献、证明、完整网格、复现/AI披露清单。
- `paper.tex`, `references.bib`, `template/`：完整 LaTeX 源码和原版官方模板。
- `final_report.md`：中文结果摘要、证据范围与局限。
- `plan.md`, `data/freeze_sha256.json`, `deviations.md`：预先冻结的设计、完整性记录和偏离/失败记录。
- `code/`, `tests/`, `data/`, `artifacts/`：代码、实际采集的回答与分析结果。

这是研究任务交付物，不表示已向 ICLR 投稿或通过同行评审。整个任务无人值守、AI辅助完成，尚无人类科研核验。

## 核心解释边界

1. **已知总体真值的合成实验**才能直接测量本文设置下的总体覆盖率。
2. 真实 LLM 回答是本任务实际请求生成的，不是外部已有答案、规则模拟或预训练猜测结果。服务端返回名称 `gpt-5.6-luna` 是未认证的端点别名，不能据此断言模型版本、参数、架构或训练数据。
3. 真实实验针对600题、8提示的**固定回答表**。重复划分的置信覆盖与 MCSE 条件于该表，不代表2000个独立真实基准，也不证明未来题目总体覆盖率。
4. 剩余题池目标和完整题池目标不同。代码对审计区间使用已知选优题目贡献的仿射变换，以比较同一目标。
5. 最后报告卡是预先指定种子的**回放示例**，不是研究者真正盲化的前瞻审计。
6. 固定候选集的集中界不能仅按事后生成的提示数量套用；任意自适应搜索的审计保证要求真正隔离的审计信息流。

## 环境与依赖

实际环境：Python 3.11，CPU分析；无GPU推理。版本见 `requirements-lock.txt`，系统信息见 `artifacts/environment.json`。实际运行使用 NumPy、SciPy、pandas、pyarrow、matplotlib 和 Python标准库HTTP客户端；pypdf用于PDF文字/页数验证，PyMuPDF用于渲染检查。不依赖 torch、DSPy 或训练框架。

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

LaTeX需要 `pdflatex`, `bibtex` 及常规 TeX Live 包（amsmath、booktabs、graphicx、longtable、hyperref、times等）。官方模板在 `template/` 中原样保留。编译脚本设置模板搜索路径，不修改字体、边距或行距。

## 无网络复现论文结果（建议先执行）

在本文件所在工作区根目录执行：

```bash
python tests/test_statistics.py
python code/run_experiments.py synthetic
python code/run_experiments.py real
python code/plot_results.py
python code/budget_matched.py
python code/write_report.py
bash build_paper.sh
python code/verify_delivery.py
```

`data/responses.jsonl` 已包含全部实际端点输出，`real` 模式会从原始文本独立重评分并校验每一条记录，不能以外部得分冒充推理。完整合成网格本环境单线程约1分钟；真实缓存回放与作图通常数十秒。预计不同CPU数分钟；精确实际耗时见运行日志与 `artifacts/*runtime.json`。首次穷举测试约数秒，包含所有小题池、选优/审计组合、边界与解析规则。

完整离线流程可直接运行 `python code/reproduce.py`，会保存每个命令退出码、墙钟、子进程CPU时间和峰值RSS。一次实测完整离线复现为127.6秒墙钟、127.4 CPU秒、峰值子进程RSS433.4 MiB；仅计该次复现，不包括原始推理、之前开发重跑、来源获取或代理计算。详见 `artifacts/reproduction_resources.json`。

不要为了复现统计结果重新请求端点。重新生成 LLM 回答不保证逐字一致，也不保证统计结果完全相同；温度0不保证服务端确定性。

## 数据获取和全新推理

固定数据：`TIGER-Lab/MMLU-Pro`，修订版
`b189ec765aa7ed75c8acfea42df31fdae71f97be`。

```bash
python code/download_data.py  # 读取明确版本，验证parquet的LFS SHA256
python code/prepare.py        # 仅在新实验副本中重新冻结设计
export OPENAI_BASE_URL='https://your-compatible-endpoint.example/v1'
export OPENAI_API_KEY='YOUR_SECRET'
python code/collect.py
```

**在新目录副本中运行全新采集**，先保留本交付物原始缓存。`collect.py` 对已存在的 `data/responses.jsonl` 使用键 `(row,prompt_id)` 续跑，不覆盖已有记录；若缓存完整则不再发请求。不要混用不同模型、数据或提示配置产生的缓存。密钥从环境读取，从未写进交付文件；私有服务端地址不写入论文。

采集预算：600×8=4800个完整得分调用，请求 `max_tokens=192`，8并发，每个传输失败最多4次尝试；不因答错或格式错误重试。采集耗时以 `artifacts/inference_usage.json` 为准，实际本环境40.6分钟。**服务端usage在1292次调用中超过请求的192上限（最大5521），实际总completion tokens为1,282,295；921600只是名义请求上限，不能当作强制生效的真实预算。** 可能包含未暴露的推理或不支持该参数，语义无法核验。服务端没有价格或余额接口，**无法报告真实货币支出，也无法认证与单张24GB GPU的计算等价关系**；不把未知费用估算冒充账单。实际使用量来自响应usage字段，审计见 `artifacts/usage_audit.json`。所有传输错误（若有）记录于 `artifacts/transport_errors.jsonl`。

原数据含 `cot_content`，但请求体只构造题干、全部选项及冻结提示，绝不发送标准答案、答案索引或解题解释。所有3--10个选项保留。600题按类别近似比例抽样，真实回放在这个固定队列内做不分层的均匀抽样；不能把其不加权准确率冒充完整MMLU-Pro或类别宏平均。

## 随机种子、统计对象与分析文件

- 默认 `numpy.random.default_rng`，具体版本锁定。
- 队列2201；模拟1101+稳定SHA256场景偏移；回放3301；报告卡4401；乘子5501+场景偏移；请求交错6601。
- 核心模拟36设置，候选数/边界/重复提示压力14设置，敏感性7设置，固定有限池1设置，共58设置。
- 常规每设置2000次，两个n×两个B的4个乘子预算检查各用主设置前200个数据集。不同B的高斯抽样不是嵌套的，这项敏感性比较包含数值MC噪声，不是精确配对同一组高斯权重。
- 主实验同一数据集上比较全部方法；保留单次重复结果 `artifacts/replications/*.npz`。
- 所有覆盖率均有目标标签：`iid_population`, `synthetic_finite`, `real_cache`。
- `synthetic_summary.csv`, `real_summary.csv`：完整方法结果、MCSE和覆盖率的精确二项Monte Carlo置信区间（观测100%时也不误报绝对确定）。
- `guarantee_audit.csv`：精确/保守方法单侧欠覆盖诊断及Holm校正；不是对所有描述性结论做事后显著性筛选。
- `analytic_independent.csv`：独立等质量候选的二项分布最大值解析参照。
- `budget_matched.csv`：**探索性**相同答题预算政策比较，选优96题无额外审计 vs 选优64题+128题对获胜者/基线共同审计。各政策对应各自获胜者，不是同一目标条件下的额外精度比较。
- `report_card.json`：准确率和提升两项headline的联合95%分配；不同于方法对比中各自边际95%。

## 每张图、每个表的来源

所有数字型主文/附录表和宏由 `code/plot_results.py` 从实际CSV生成，只有探索性预算表由 `code/budget_matched.py` 生成；不手填示例结果。

| 论文对象 | 生成脚本 | 输入 / 产物 |
|---|---|---|
| 图1，选优乐观偏差 | `code/plot_results.py` | 两个summary CSV → `artifacts/figures/optimism.pdf/.png` |
| 图2，覆盖-宽度 | 同上 | 主设置行 → `coverage_width.pdf/.png` |
| 图3，边界失效/审计精度 | 同上 | 边界与审计大小行 → `failure_precision.pdf/.png` |
| 附录图，正确性相关 | 同上 | `prompt_correlation.csv` → `correlation.pdf/.png` |
| 主文主设置表 | 同上 | `artifacts/tables/primary.tex` |
| 附录提示结果表 | 同上 | `prompt_summary.csv` → `tables/prompts.tex` |
| 附录消融表 | 同上 | `real_summary.csv` → `tables/ablations.tex` |
| 附录完整核心网格 | 同上 | `synthetic_summary.csv` → `tables/core_grid.tex` |
| 探索性相同预算表 | `code/budget_matched.py` | 原始固定缓存/主模拟生成器 → `tables/budget.tex` |
| 摘要与正文结果宏 | `code/plot_results.py` | `tables/numbers.tex`, `paper_numbers.json` |

定义表、公式、算法预算和参数说明不是虚构实测数字；边界覆盖率等正文具体结果也能由完整summary直接核对。所有图中的误差条是条件MC误差，不是对未来真实基准的不确定性。图表审计见 `artifacts/figure-audit.md`。

## 研究独立性、引用与模板

- **未进行主题搜索、引用图谱搜索、推荐页访问，未尝试识别禁用论文。** 仅直接访问任务允许的起步文献摘要、固定数据源和官方会议模板/规范。未识别到禁用内容的偶遇；不宣称能证明不存在任何未知关联。
- 已读来源、精确URL和摘要范围见 `sources.md` 与 `retrieval.json`。没有读到有用内容的Berk DOI页面不在论文中引用。未访问后续讨论和复现。
- 模板为ICLR官方Master-Template提交 `46ed6f4c6cef5b175dde23639e77d44c3463b230` 下的 `iclr2027/`，官方主文上限9页，参考文献与附录另计；AI-use statement为必需，已填写。官方未要求NeurIPS式checklist，额外附已填写的自愿复现清单。
- `official_retrieval.json`, `official/`, `template/` 提供规范与模板获取记录和校验值。模板文件未修改。不是实际会议投稿。
- 数据集卡注明MIT；模板与原始文献遵循各自许可。原始数据卡和来源记录随包提供。

## 已知不足与失败

完整记录见 `deviations.md`、论文局限和 `artifacts/synthetic_audit.md`。包括端点身份/费用未知、第一版敏感性数据配对bug及修复重跑、源代理过载、无前瞻盲化、无自适应优化器实测、无真实新题总体oracle、无多模型/多数据集重复。乘子方法和经验guard没有通用有限样本保证；guard的混合触发机制没有系统验证。阴性结果和保守区间的低功效均不删去。
