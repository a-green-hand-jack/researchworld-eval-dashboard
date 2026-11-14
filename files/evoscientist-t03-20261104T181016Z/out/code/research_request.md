# Original research request

运行方式：无人值守；自行决定并继续，全部提交物保存于工作区根目录 /work 及其子目录。

# 研究任务：表格模型上 SHAP 特征归因的重复运行可靠性

SHAP 被广泛用于为高风险场景（信贷、医疗等）中的模型决策提供理由。在实际部署中，SHAP 通常依赖随机近似算法估计，并受计算预算限制，因此同一个训练好的模型、同一个输入实例，多次运行解释器可能得到不同的归因向量。

实践中常见的做法是对一个实例只运行一次解释器，并把所得特征归因作为该预测的依据。这种做法在什么条件下足够可靠、在什么条件下不够可靠，目前缺少系统的实证证据。研究需回答：对一个训练好的表格模型，单次运行所得的 SHAP 特征归因在多大程度上可以被当作该预测的可靠依据；这一判断需要依据哪些度量和比较标准；结论在哪些条件下成立、在哪些条件下不成立。

期望：可复现的实验方法，多个公开表格分类数据集、多种模型；明确可检验论断，足以支持或反驳的证据及不确定性；明确数据、模型、计算预算和统计处理及选择理由；如实报告负面、不确定结果及局限。CPU为主，一周内，约24 CPU小时，数据结果小于数GB，不需付费API。

## 给定数据
- 主：UCI Statlog German Credit，https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data ，DOI 10.24432/C5NC77，CC BY 4.0，1000×20。
- 主：ACS收入，folktables 0.0.12；https://github.com/socialfoundations/folktables ，US Census ACS PUMS，公开数据，须读使用条款；单州年度数万到数十万。
- 可选：OpenML diabetes id37 v1，Public，768×8；Give Me Some Credit id46929 v1，Public，150000×10；UCI Arrhythmia，CC BY4.0，452×279。允许自选公开数据并论证。

## 起步文献（允许访问）
1. Lundberg & Lee (2017), A Unified Approach to Interpreting Model Predictions. https://arxiv.org/abs/1705.07874
2. Krishna et al., The Disagreement Problem in Explainable Machine Learning: A Practitioner's Perspective. https://arxiv.org/abs/2202.01602
3. Yuan et al., An empirical study of the effect of background data size on the stability of SHAP for deep learning models. https://arxiv.org/abs/2204.11351
4. Musco & Witter, Provably Accurate Shapley Value Estimation via Leverage Score Sampling. https://arxiv.org/abs/2410.01917
5. Chen et al., True to the Model or True to the Data? https://arxiv.org/abs/2006.16234
6. Marx et al., Predictive Multiplicity in Classification. https://arxiv.org/abs/1909.06677
7. Nogueira et al. (2018), On the Stability of Feature Selection Algorithms. https://jmlr.org/papers/v18/17-514.html
8. Webber et al. (2010), A Similarity Measure for Indefinite Rankings. https://doi.org/10.1145/1852102.1852106
9. Ding et al. (2021), Retiring Adult: New Datasets for Fair Machine Learning. https://arxiv.org/abs/2108.04884
10. Gorishniy et al. (2021), Revisiting Deep Learning Models for Tabular Data. https://arxiv.org/abs/2106.11959

## 提交要求
完整研究论文PDF与LaTeX，ICML/ICLR/NeurIPS中最新一届官方模板，正文页数合规，填写要求的checklist；至少摘要、引言、相关工作、方法、实验、讨论局限、真实参考文献。全部代码、环境版本、数据获取与版本、种子、运行命令及耗时，各图表生成脚本映射。每个数字图表均来自实际运行，禁止占位、捏造或合成冒充。报告失败、放弃、未完成；只引用确实查阅文献。

## 独立研究禁区
已有一篇已发表论文研究此问题，但不得推测或检索其标题、作者或结果；不得访问论文、镜像、预印本、摘要页、会议评审页、幻灯片、海报、视频、博客、代码，以及任何引用、讨论、复现该论文的页面。起步文献及无关公开资料允许。偶遇立即停读并在复现说明记录URL与阅读范围。采取严格定向允许列表，不进行主题发现检索。
