# Research request intake (faithful abridgment, 2026-11-02)

The original TASK.md research question is transcribed in TASK.md. This intake condenses the accompanying literature/data/resource/deliverable brief without changing its constraints.

You are running unattended: no human is available to answer questions or to choose between options, so decide yourself and keep going until the deliverables exist. Your working directory is the workspace root; everything that is to be delivered must be saved there.

## TASK.md
# 研究任务：在标注集、未标注集与预测器均固定时的置信区间宽度

在许多科学领域（生态遥感、天文形态分类、人口普查分析等），分析者只有一小份带有金标准标签的样本、一大份只有特征没有标签的样本和一个已经预训练好的不可修改的预测模型。
目标是对某个感兴趣的总体参数（具体估计目标由你选定并说明理由）构造统计上有效的置信区间：名义覆盖率必须成立，同时区间应尽可能窄。
不增加标签、不更换预测器、不增加未标注样本。
核心问题：在标注集、未标注集和预测器都固定、名义覆盖率必须成立的条件下，现有方法给出的置信区间是否还能进一步缩短？能缩短多少？在什么条件下可以，在什么条件下不能？

要求：梳理方法与假设，明确问题；提出并检验路线，与现有有效区间方法比较；公开真实数据或已知真值合成数据；报告证据、局限、有收益和无收益条件；理论须写假设与适用范围并以实验核对。
成功标准：重复抽样经验覆盖率达到名义水平（例如95%）；同样输入平均宽度比较；多次重复及不确定性报告。负面结论可接受。

## starter_literature.md (取证 2026-10-26)
1. Angelopoulos et al. Prediction-Powered Inference. Science 2023. https://arxiv.org/abs/2301.09633
2. Angelopoulos, Duchi, Zrnic. PPI++: Efficient Prediction-Powered Inference. https://arxiv.org/abs/2311.01453
3. Zrnic, Candès. Cross-Prediction-Powered Inference. https://arxiv.org/abs/2309.16598
4. Zrnic, Candès. Active Statistical Inference. https://arxiv.org/abs/2403.03208v2
5. Fisch et al. Stratified Prediction-Powered Inference for Hybrid Language Model Evaluation. https://arxiv.org/abs/2406.04291
6. Chernozhukov et al. Double/Debiased Machine Learning for Treatment and Causal Parameters. https://arxiv.org/abs/1608.00060
7. Ding et al. Retiring Adult. https://arxiv.org/abs/2108.04884
8. Willett et al. Galaxy Zoo 2. https://arxiv.org/abs/1308.3496
9. Cortez et al. Modeling wine preferences by data mining from physicochemical properties. https://archive.ics.uci.edu/dataset/186/wine+quality

## data.md
Main option: ppi-python==0.2.3, GitHub tag v0.2.3 commit 6b8475b, https://github.com/aangelopoulos/ppi_py . Nine Google Drive npz files (~48MB). Code MIT, separate data license not stated. Paired Y/Yhat datasets: galaxies 16743, forest 1596, alphafold 10802, gene_expression 61150, census_income 380091, census_healthcare/census_education 318215, plankton labeled 421238/unlabeled 329832 (different years/distributions), ballots labeled1027/unlabeled78150. census includes X. Optional UCI Wine Quality (CC BY4.0), California Housing (license unclear), ACS via folktables==0.0.12, or fully synthetic data. Do not pool plankton years assuming equal distribution.

## resources.md
CPU only, one week, no paid API; target <8 CPU hours, storage <5GB. Public network permitted except prohibited material.

## deliverable.md
A complete research paper in PDF and LaTeX, choosing latest official ICML/ICLR/NeurIPS template, obey main page limit, complete required checklist if any. Include abstract, introduction, related work, methods, experiments, discussion/limitations, references. All code and reproduction instructions: pinned environment, acquisition/data versions, seeds, commands, runtimes, table/figure-to-script map.
No invented numerical results or references. Every paper number/table/figure must originate in actual runs and bundled reproducible code. Disclose failed/abandoned/incomplete experiments.

Prohibited: the unspecified already-published paper on this precise research question, all mirrors/preprints/abstracts/conference/review pages/slides/posters/videos/blogs/code; all citing/discussing/reproducing pages, including later papers/surveys/notes/aggregators/social media. Do not guess/search its title/authors/results. Starter literature and unrelated works permitted. If accidentally encountered, stop and record exactly where/what/how much read.

## Operational interpretation
The workspace was empty. No human interaction will be requested. No code-agent dispatch is made because code-generation-mode selection cannot be completed with an absent user. Implementations are performed by the main agent. Research uses a direct-URL allowlist, no topical web search or citation expansion. We choose mean estimation, distinguish finite-sample validity from asymptotic validity, and treat post-processing of frozen prediction values as allowed inference (not predictor replacement). Also report the stricter interpretation in which transformations are disallowed.
