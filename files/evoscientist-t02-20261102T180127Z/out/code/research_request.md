# Original research request (2026-11-02)

研究任务：模型规模如何影响小型算法任务上的“延迟泛化”。自主提出可证伪解释，用本任务实际运行的实验检验；结论可支持、反驳或有条件。必须报告统计不确定性、适用范围和失效情形。

## Supplied task brief
- 数据：素数 p 的模二元运算，穷举 p² 个整数对，标签程序生成，无外部数据或许可证；可增加合成对照。
- 资源：以 CPU 为主，最多单 GPU；总时间不超过一周；模型不超过约 10^6 参数，数据约 10^4，存储远小于 1 GB。
- 产出：完整论文 PDF 与 LaTeX，ICML/ICLR/NeurIPS 最新官方模板、正文页限、所需 checklist；全部代码、依赖版本、数据步骤、种子、命令、预计耗时、每个图表生成脚本。
- 数字、图表必须来自实际运行，不编造；报告失败/放弃/未完成；仅引用实际查阅的真实文献。
- 独立研究：禁止检索、访问、阅读、使用题目所述既有特定论文及镜像、摘要、评审、讨论、引用该论文的页面等；不得猜测其身份。偶遇立即停止阅读并记录来源与程度。
- 无人值守：不等待用户决定，完成产出并保存在工作区根目录树。

## User-provided starter bibliography (allowlist, not all necessarily cited)
1. Power et al. 2022, https://arxiv.org/abs/2201.02177
2. Nanda et al. 2023, https://arxiv.org/abs/2301.05217
3. Liu et al. 2023, https://arxiv.org/abs/2210.01117
4. Varma et al. 2023, https://arxiv.org/abs/2309.02390
5. Kumar et al. 2024, https://arxiv.org/abs/2310.06110
6. Davies et al. 2023, https://arxiv.org/abs/2303.06173
7. Morris et al. 2025, https://arxiv.org/abs/2505.24832
8. Tirumala et al. 2022, https://arxiv.org/abs/2205.10770
9. Zhang et al. 2017, https://arxiv.org/abs/1611.03530
10. Nakkiran et al. 2020, https://arxiv.org/abs/1912.02292
11. Loshchilov & Hutter 2017, https://arxiv.org/abs/1711.05101

## Operational interpretation
No topic web searches: only direct listed PDFs and official conference template/instructions. No external model code. All model implementation is performed by the main agent (no code-agent delegation, hence no unattended code-mode choice required). Literature/template research can be delegated. Initial pilots explicitly exploratory, later protocols frozen and recorded before multi-seed sweeps. Raw held-out complements used during pilots are not final-test evidence. Conference chosen: NeurIPS 2026 (official package acquired).
