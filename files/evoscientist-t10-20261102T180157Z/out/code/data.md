# 数据与获取方式（任务输入摘要）

任务允许：ppi-python==0.2.3的九个配对示例（galaxies、forest、alphafold、gene_expression、census_income、census_healthcare、census_education、plankton、ballots）；UCI Wine Quality；California Housing；ACS PUMS/folktables==0.0.12；自行生成合成数据。

本任务实际仅获取galaxies和forest，保留原预测，不训练底层模型。代码包MIT，示例NPZ独立许可未声明。其余数据未下载、未报告为已实验。

实际原始数据ID、版本、SHA-256、EDA及目标定义：data/manifest.json、download_data.py、README.md。实际合成数据定义：run_experiments.py的conditional_mean和moments，五种条件Bernoulli机制、真值解析可知。

选择经验分布目标以进行可验证的重复抽样评估，不假装具有原科学总体的真实参数。不要将plankton两年的分布差异当成iid；本任务未使用它。
