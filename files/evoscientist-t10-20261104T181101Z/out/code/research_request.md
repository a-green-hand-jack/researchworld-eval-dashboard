# Original research request (2026-11-04)

研究问题：在标注集、未标注集与不可修改的预测器固定时，构造名义覆盖率成立且尽量窄的总体参数置信区间。独立选择目标、梳理允许文献、提出并检验路线；同一次重复中所有方法使用同样输入，不增加标签、未标注样本或更换预测器。报告何时有收益、何时无收益，并给出重复抽样覆盖率、平均宽度与不确定性；允许负面结论。仅CPU，最多一周，无付费API，可用公开或合成数据。无人值守，自行决策。

交付：完整会议格式研究论文PDF与LaTeX源，选择ICML/ICLR/NeurIPS最新官方模板并遵守正文页数限制及必需checklist；代码、环境版本、数据获取与版本、种子、命令、耗时、每图表对应脚本。所有实测数字必须来自本次实际运行；失败与未完成实验如实报告。

独立性：不得搜索、访问或推测已研究本题的禁止论文，也不得访问其镜像、摘要、会议、讨论、引用或复现页面。仅定向读取起步清单、基础统计与官方模板，若偶遇则立即停止并记录。

允许起步资料：PPI https://arxiv.org/abs/2301.09633 ; PPI++ https://arxiv.org/abs/2311.01453 ; Cross-PPI https://arxiv.org/abs/2309.16598 ; Active Statistical Inference https://arxiv.org/abs/2403.03208v2 ; Stratified PPI https://arxiv.org/abs/2406.04291 ; DML https://arxiv.org/abs/1608.00060 ; folktables https://arxiv.org/abs/2108.04884 ; Galaxy Zoo2 https://arxiv.org/abs/1308.3496 ; UCI Wine Quality https://archive.ics.uci.edu/dataset/186/wine+quality .

数据选项：ppi-python==0.2.3示例(预测已固定)、UCI Wine Quality、California Housing、ACS或已知真值合成数据。PPI数据独立许可不清楚，UCI wine CC BY4.0。资源：CPU，期望<8CPU小时、<5GB。评审重点：新颖性定位诚实、统计严谨、证据充分、可复现、局限透明。

本文件为任务的可操作摘要；原始研究问题单独保存于 TASK.md，起步清单、数据表、资源与产出约束分别保存于 starter_literature.md、data.md、resources.md、deliverable.md。
