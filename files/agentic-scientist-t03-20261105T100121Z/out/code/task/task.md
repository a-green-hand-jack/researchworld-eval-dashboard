# Goal

**研究任务：表格模型上 SHAP 特征归因的重复运行可靠性**
**问题与动机**
SHAP 被广泛用于为高风险场景（信贷、医疗等）中的模型决策提供理由。在实际部署中，
SHAP 通常依赖随机近似算法估计，并受计算预算限制，因此同一个训练好的模型、同一个
输入实例，多次运行解释器可能得到不同的归因向量。

实践中常见的做法是对一个实例只运行一次解释器，并把所得特征归因作为该预测的依据。
这种做法在什么条件下足够可靠、在什么条件下不够可靠，目前缺少系统的实证证据。
我们希望你研究这一问题，并保留部署中真实的计算预算这一约束。

请自行确定并论证具体的研究问题与方法。研究需要回答：对一个训练好的表格模型，
单次运行所得的 SHAP 特征归因在多大程度上可以被当作该预测的可靠依据；这一判断需要依据
哪些度量和比较标准；结论在哪些条件下成立、在哪些条件下不成立。

**期望**
- 设计可复现的实验方法，在多个公开表格数据集和多种模型上系统验证，
  并把结论表述为可被他人检验的论断。
- 合格的研究给出明确论断及足以支持或反驳它的证据，并报告不确定性；结论可以是
  "足够可靠""视条件而定"或"不可靠"，只要证据充分，都是可接受的结果。
- 明确你的实验设置（数据、模型、计算预算）和统计处理方式，并说明选择理由。
- 如实报告负面或不确定的结果，并指出局限。

**约束**
计算以 CPU 为主，整个任务须在一周内完成，使用公开表格数据（详见 `data.md`、
`resources.md`），产出是一篇论文及全部代码（详见 `deliverable.md`）。

**起步文献（均为公开文献；你可以也应当自行检索更多）**
1. Lundberg, S. M., Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions.* NeurIPS 30.
   https://arxiv.org/abs/1705.07874 —— 说明：提出 SHAP 的加性特征归因框架，并给出包括 Kernel SHAP 在内的估计方法。
2. Krishna, S. et al. (2022). *The Disagreement Problem in Explainable Machine Learning: A Practitioner's Perspective.*
   https://arxiv.org/abs/2202.01602 —— 说明：关于多种事后解释方法在同一模型上给出不一致解释的研究，含对从业者的调研与实证比较。
3. Yuan, H. et al. (2022). *An empirical study of the effect of background data size on the stability of SHapley Additive exPlanations (SHAP) for deep learning models.*
   https://arxiv.org/abs/2204.11351 —— 说明：针对深度学习模型，实证考察估计 SHAP 时所用背景数据的规模与解释稳定性的关系。
4. Musco, C., Witter, R. T. (2024). *Provably Accurate Shapley Value Estimation via Leverage Score Sampling.*
   https://arxiv.org/abs/2410.01917 —— 说明：提出一种 Shapley 值估计算法，并给出估计误差的理论保证。
5. Chen, H., Janizek, J. D., Lundberg, S., Lee, S.-I. (2020). *True to the Model or True to the Data?*
   https://arxiv.org/abs/2006.16234 —— 说明：讨论 Shapley 值类解释在计算时采用不同期望方式所对应的不同含义。
6. Marx, C., Calmon, F., Ustun, B. (2020). *Predictive Multiplicity in Classification.*
   https://arxiv.org/abs/1909.06677 —— 说明：提出并度量“精度相近的多个分类模型对同一样本给出不同预测”的现象，并在多个真实数据集上评估。
7. Nogueira, S., Sechidis, K., Brown, G. (2018). *On the Stability of Feature Selection Algorithms.* JMLR 18(174).
   https://jmlr.org/papers/v18/17-514.html —— 说明：讨论特征选择算法的稳定性度量，给出一种稳定性度量并分析其性质。
8. Webber, W., Moffat, A., Zobel, J. (2010). *A Similarity Measure for Indefinite Rankings.* ACM TOIS 28(4).
   https://doi.org/10.1145/1852102.1852106 —— 说明：提出一种用于比较两个排序（允许长度不等、不完整）的相似度度量，并分析其性质。
9. Ding, F., Hardt, M., Miller, J., Schmidt, L. (2021). *Retiring Adult: New Datasets for Fair Machine Learning.* NeurIPS 34.
   https://arxiv.org/abs/2108.04884 —— 说明：提出基于美国人口普查局 ACS 数据构建的一组表格数据集及其工具包 folktables，用于机器学习研究。
10. Gorishniy, Y., Rubachev, I., Khrulkov, V., Babenko, A. (2021). *Revisiting Deep Learning Models for Tabular Data.* NeurIPS 34.
    https://arxiv.org/abs/2106.11959 —— 说明：系统比较表格数据上的深度学习模型，并提出 ResNet 类和 Transformer 类（FT-Transformer）两种神经网络架构。

**数据**
任务只需公开的表格分类数据集。以下为可用的公开表格分类数据集，标明主数据与可选数据；
你也可以自选其他公开数据集，并说明选择理由。

| 数据集 | 角色 | 获取方式 | 许可证 | 版本 / 规模 |
| --- | --- | --- | --- | --- |
| Statlog (German Credit Data) | 主 | https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data （UCI；DOI 10.24432/C5NC77）；无需账号 | CC BY 4.0（UCI 页面声明） | UCI 页面最后更新 2023-08-10；1,000 条 × 20 个属性；二分类 |
| ACS 收入预测（folktables） | 主 | `pip install folktables`（PyPI 0.0.12，2023-02-08 发布）；https://github.com/socialfoundations/folktables ；数据由 US Census ACS PUMS 下载（https://www.census.gov/programs-surveys/acs/microdata.html ）；无需账号 | folktables 代码为 MIT；ACS PUMS 为美国人口普查局公开数据，census.gov 页面未给出单独的许可证文字（2026-10-27 查阅），使用前请自行阅读该站条款 | 仓库默认分支最新提交 ebace19d（2024-05-15）；ACS PUMS 2024 年度文件的发布时间为 2025-12-04 前（已核实 2024 年 1 年期某州个人记录文件的 Last-Modified）；单个州单个年度的个人记录为数万到数十万条量级 |
| Pima Indians Diabetes | 可选 | OpenML `diabetes`（data id 37，version 1）：https://www.openml.org/d/37 ；亦可用 `sklearn.datasets.fetch_openml(data_id=37)`；无需账号 | OpenML 记录 licence = "Public" | 2014-04-06 上传；768 条 × 8 个数值特征 + 类别 |
| Give Me Some Credit | 可选 | OpenML id 46929（version 1）：https://www.openml.org/d/46929 ；无需账号。原始来源为 Kaggle 竞赛 "Give Me Some Credit"（2011，需 Kaggle 账号并接受规则；核实时 Kaggle 页面对自动请求返回 404，未能确认可用，因此只把 OpenML 作为获取方式） | OpenML 记录 licence = "Public" | 2025-04-30 上传（TabArena 整理版）；150,000 条 × 10 个特征 + 目标，含缺失值；二分类 |
| Arrhythmia | 可选 | https://archive.ics.uci.edu/dataset/5/arrhythmia （UCI；DOI 10.24432/C5BS32）；无需账号 | CC BY 4.0（UCI 页面声明） | UCI 页面最后更新 2024-02-05；452 条 × 279 个特征 |

数据体量为 MB 到数百 MB。表中记录数为原始记录数，各表是否去重或去缺失由使用者决定。
核实日期：2026-10-27。

**资源与预算**
- 计算：以 CPU 为主，预计总算力在约 24 CPU 小时量级（为估算，未实测）；
  可选使用至多一张 GPU，不是必需。
- 估算依据：数据量级为数百到数十万条记录、数个到数百个特征；模型为常见的表格模型，
  单次训练在 CPU 上为秒到分钟量级；解释器调用占主要开销，随被解释的实例数和所需精度增长。
  以上均为估算，未实测。请在论文中说明你的预算选择。
- 时间：整个任务（调研、实验、写作）上限一周。
- 存储：数据与结果合计 < 数 GB。
- 付费 API：不需要。
- 软件：公开开源的 Python 科学计算与机器学习库，具体自选；需要联网获取公开数据和文献。

**产出要求**
**提交物**
1. 一篇完整的研究论文（PDF 与 LaTeX 源文件）。从 ICML、ICLR、NeurIPS 中自选一个会议，使用该会议
   最新一届的官方 LaTeX 模板，遵守其正文页数上限（参考文献、附录是否计入页数按该会议的规定）；
   该会议要求随文提交的 checklist（例如 NeurIPS 的 paper checklist）一并填写。论文至少包含摘要、
   引言、相关工作、方法、实验、讨论与局限、参考文献。
2. 全部代码与复现说明：环境与依赖版本、数据获取步骤和所用数据的版本、随机种子、运行命令和预计
   耗时，以及论文中每张表、每张图由哪个脚本生成。

**评审标准**
论文按所选会议主会的审稿标准评审，重点看：

- 新颖性与定位：贡献是什么，与已有工作的关系和区别是否讲清楚；
- 严谨性：方法和实验设计是否合理，基线、对照和消融是否恰当，是否报告不确定性（多次运行、
  置信区间或显著性检验）；
- 证据是否充分：实验能否支撑论文的每个结论，结论的适用范围是否写清楚；
- 表达：论文是否清楚、完整，他人能否据此复现；
- 局限：是否如实讨论方法和结论的局限与失效情形。

负面结果、与预期不符的结果同样有价值；结论有充分证据、不确定性报告完整，比结论本身是正面还是
负面更重要。

**如实报告（禁止编造）**
- 论文中的每个数字、每张表和每张图都必须来自你在本任务中实际运行、随附代码可以重新产生的结果；
  不得编造数据或结果，不得用占位数字、估计值或"示意"性的合成结果冒充实测结果。
- 失败的运行、与预期不符的结果和放弃的方案如实报告；因预算没有完成的实验写明未完成，不写成
  已完成。
- 只引用真实存在、你确实查阅过的文献，不得编造引用。

**不得访问的内容**
本任务的研究问题已有一篇已发表的论文研究过。为保证研究独立，不得检索、访问、阅读或使用：

- 那篇论文本身，及其任何镜像、预印本、摘要页、会议或评审页面、幻灯片、海报、视频、博客和代码
  仓库；
- 引用、讨论或复现那篇论文的任何页面，包括后续论文、综述、论文笔记、论文聚合站点和社交媒体
  讨论。

也不要尝试推测或检索那篇论文的标题、作者或结果。`starter_literature.md` 中的文献，以及与那篇
论文无关的其他公开文献、数据和代码，可以正常使用。若在检索中偶然遇到上述内容，立即停止阅读，
并在复现说明中如实记录遇到了什么、在哪里遇到、读到了多少。

# Rubrics

No rubric is provided for this task; the requirements stated above apply.
