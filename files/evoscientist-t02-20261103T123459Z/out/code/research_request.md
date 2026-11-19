# 原始研究任务（完整任务 brief，按用户提供的文档合并保存）

用户指令：无人值守，无人可以回答问题或选择选项；自行决定并持续到交付物存在。工作目录为 workspace root，全部交付物必须保存于该目录下。

## TASK.md

# 研究任务：模型规模如何影响小型算法任务上的“延迟泛化”

## 背景
在模运算等小型算法任务上，神经网络常出现“延迟泛化”（grokking）：训练集准确率很早就接近100%，而验证集准确率要在训练很久之后才突然上升。已有工作从电路效率、从懒惰状态到丰富状态的训练动力学转变、权重范数等角度解释这一现象。
在模运算类算法任务上，模型规模在延迟泛化中起什么作用，目前缺少系统的实证刻画。

## 研究问题
请自主提出并检验一个关于下述问题的可证伪解释，并用实验支持或反驳它：在模运算类算法任务上，延迟泛化的出现与模型规模之间有什么关系？

## 动机
厘清模型规模对延迟泛化的作用，可以为选择实验设置提供依据，也能约束对这一现象的各种解释。

## 成功如何衡量
明确给出解释和可证伪预测；用本任务内自己运行的实验检验；说明结论适用范围与不成立情形。结论可以是支持、反驳或视条件而定。

## 关键约束与要求
资源与时间预算见resources.md（一周、以CPU为主）；数据为程序合成，见data.md；最终产出为论文及全部代码，见deliverable.md。
研究设计、实验、分析和结论自行决定；不规定方法或预期结果。结论必须有实验证据，并说明统计不确定性。其余约束见下列文档。

## starter_literature.md（给定起步文献，均发表于2025-12-16之前）
1. Power, Burda, Edwards, Babuschkin, Misra. Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets.2022. https://arxiv.org/abs/2201.02177
说明：在小型算法生成数据集（含模运算）上研究神经网络泛化，报告训练集拟合后很久才出现泛化。
2. Nanda, Chan, Lieberum, Smith, Steinhardt. Progress Measures for Grokking via Mechanistic Interpretability. ICLR2023. https://arxiv.org/abs/2301.05217
说明：分析模加法小型Transformer的机理可解释性，定义训练进展度量。
3. Liu, Michaud, Tegmark. Omnigrok: Grokking Beyond Algorithmic Data. ICLR2023. https://arxiv.org/abs/2210.01117
说明：分析损失地形与权重范数，并在图像、语言、分子等任务上实验。
4. Varma, Shah, Kenton, Kramár, Kumar. Explaining Grokking Through Circuit Efficiency.2023. https://arxiv.org/abs/2309.02390
说明：从电路效率解释延迟泛化，并用训练实验检验若干预测。
5. Kumar, Bordelon, Gershman, Pehlevan. Grokking as the Transition from Lazy to Rich Training Dynamics. ICLR2024. https://arxiv.org/abs/2310.06110
说明：联系懒惰到丰富训练动力学转变，在两层网络回归中分析。
6. Davies, Langosco, Krueger. Unifying Grokking and Double Descent.2023. https://arxiv.org/abs/2303.06173
说明：统一框架讨论延迟泛化与双下降。
7. Morris, Sitawarin, Guo, Kokhlikyan, Suh, Rush, Chaudhuri, Mahloujifar. How much do language models memorize?2025. https://arxiv.org/abs/2505.24832
说明：估计模型对数据点所含信息量，在语言模型测量。
8. Tirumala, Markosyan, Zettlemoyer, Aghajanyan. Memorization Without Overfitting: Analyzing the Training Dynamics of Large Language Models. NeurIPS2022. https://arxiv.org/abs/2205.10770
说明：实证研究语言模型训练记忆。
9. Zhang, Bengio, Hardt, Recht, Vinyals. Understanding Deep Learning Requires Rethinking Generalization. ICLR2017. https://arxiv.org/abs/1611.03530
说明：图像网络拟合与泛化关系，显式正则化作用。
10. Nakkiran, Kaplun, Bansal, Yang, Barak, Sutskever. Deep Double Descent: Where Bigger Models and More Data Hurt. ICLR2020. https://arxiv.org/abs/1912.02292
说明：测试表现随规模与训练轮数的双下降。
11. Loshchilov, Hutter. Decoupled Weight Decay Regularization.2017. https://arxiv.org/abs/1711.05101
说明：AdamW，权重衰减与梯度更新解耦。

## data.md
主数据为素数p上模二元运算（如模加法）。全部p²输入对(a,b)可穷举，标签直接计算，格式为整数对到整数的映射，内存生成、体积可忽略。无需下载与账号；无第三方数据与许可证问题，无需固定第三方版本或快照。可按研究需要生成其他合成数据并说明构造。原始定义见起步文献1。

## resources.md
计算优先仅CPU；必要时可用一张GPU、不限型号。具体核数、内存、磁盘依环境。一周时间上限含实验、写作、整理代码。粗略预算：模型不超过10^6量级参数，输入对10^4量级；CPU单次分钟至小时、合计数十CPU小时（未实测）。存储远小于1GB。不需集群或付费API。

## deliverable.md
### 提交物
1. 完整研究论文：PDF与LaTeX源文件。从ICML、ICLR、NeurIPS任选其一，使用最新一届官方模板，遵守正文页数上限，参考文献与附录是否计入按会议规定。要求随文提交的checklist一并填写。至少摘要、引言、相关工作、方法、实验、讨论与局限、参考文献。
2. 全部代码与复现说明：依赖版本、数据获取与版本、随机种子、命令、预计耗时，以及每张表图的生成脚本。

### 评审标准
按所选会议主会标准：新颖性定位清楚；合理基线、对照和消融；多次运行与不确定性；每项结论有充分证据，范围明确；表达完整可复现；如实讨论局限和失效。负面/意外结果同样有价值，证据充分与不确定性完整比正面结论重要。

### 如实报告（禁止编造）
所有论文数字、表、图必须来自本任务实际运行且随附代码可再生；不得用占位、估计或示意合成数字冒充实测。失败、意外结果、放弃方案如实报告；未完成实验不得写为已完成。只引用真实且确实查阅的文献。

### 不得访问内容
问题已有一篇已发表论文研究过。不得检索、访问、阅读或使用该论文及任何镜像、预印本、摘要/会议/评审页面、幻灯片、海报、视频、博客、仓库；也不得接触引用、讨论、复现它的页面（后续论文、综述、笔记、聚合站、社交讨论）。不得猜测或搜索其标题、作者或结果。给定起步文献及与之无关的其他公开文献/数据/代码允许使用。偶遇上述内容应立即停止阅读，在复现说明记录遇到什么、地点与阅读范围。

## 执行边界
以上为用户任务的完整内容性保存（仅合并文档、统一排版）。工作区/work。实际采用更保守的七篇直接原文白名单、不做主题检索；阅读记录见literature_notes.md。无人值守下直接实现代码，不调用需要先询问生成模式的code-agent。实验设计与结果的变更记录见todos.md、protocol.json、experiment_log.md。
