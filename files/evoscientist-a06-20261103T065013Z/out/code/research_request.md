# 原始研究请求

运行方式：无人值守，无需提问；自行决策直到交付物存在。工作目录 /work，所有交付物保存在该根目录及子目录。

## TASK.md
研究任务：自动调优之后，报告的基准分数意味着什么。

研究者在一个基准题集自动搜索提示词或多次 LLM 调用组成的 pipeline，再把同批题目的最佳配置得分作为系统性能。研究：
1. 有限题集上搜索配置后，汇报分数与全新题目真实表现相差多少？哪些因素影响差距？是否影响据此做出的结论？
2. 能否设计更可靠汇报方式，如何通过实验检验可靠性？
结论须有亲自运行实验支持，至少一个真实 LLM 和真实基准。统计方法、实验与理论深度自行决定；允许负面和条件性结论。

## data.md
MMLU-Pro，https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro ，固定修订 b189ec765aa7ed75c8acfea42df31fdae71f97be (2026-05-02)，test 12032，validation 70，14 类，约4.2MB，数据卡 MIT，评测代码 Apache-2.0，无账号。
真实实验必须自行生成并可缓存答案，包内不提供模型输出；允许本地模型或 API。可选 DSPy，非强制。合成数据自行生成。

## resources.md
一周墙钟；CPU 为主；LLM 推理至多单张24GB GPU或等价API预算，以实际可用环境为准。无需训练或多卡。建议100GB磁盘、32GB内存、8核；单模型15-17GB；缓存<1GB。原始推理/CPU耗时均为未实测粗估，报告须提供实际计算量。

## deliverable.md
完整研究论文 PDF 和 LaTeX，ICML/ICLR/NeurIPS 任选最新官方模板，遵守主文页数限制，填写会议要求 checklist（如有）。含摘要、引言、相关工作、方法、实验、讨论局限和参考文献。
全部复现代码与说明：环境依赖版本、数据获取版本、随机种子、命令、预计耗时、每图每表对应脚本。
评审看新颖性定位、统计严谨与消融对照、不确定性、证据充分、表达复现与如实局限。
所有数字图表来自本任务实际运行，不得占位、编造、估计冒充实测。失败与未完成实验照实写明，只引用真实且确实查阅文献。

## 禁止访问
已有一篇研究同问题的已发表论文。不得检索、访问、阅读或使用其论文、镜像、预印本、摘要页、会议/评审页、幻灯、海报、视频、博客、代码，亦不得访问引用讨论复现该文的任何页面。不得推测或检索其标题作者结果。若偶遇立即停止，并记录在哪里遇到什么、读到多少。

## starter_literature.md （允许直接访问）
- Wang et al. MMLU-Pro (2024), https://arxiv.org/abs/2406.01574
- Khattab et al. DSPy (2023), https://arxiv.org/abs/2310.03714
- Opsahl-Ong et al. MIPRO (2024), https://arxiv.org/abs/2406.11695
- Polo et al. Efficient multi-prompt evaluation of LLMs (2024), https://arxiv.org/abs/2405.17202
- Shi et al. Efficient Prompt Optimization Through the Lens of Best Arm Identification (2024), https://arxiv.org/abs/2402.09723
- Sclar et al. Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design (2024), https://arxiv.org/abs/2310.11324
- Dwork et al. Preserving Statistical Validity in Adaptive Data Analysis (2015), https://arxiv.org/abs/1411.2664
- Blum & Hardt. The Ladder (2015), https://arxiv.org/abs/1502.04585
- Andrews, Kitagawa & McCloskey. Inference on Winners (2024), https://www.nber.org/papers/w25456
- Chernozhukov, Chetverikov & Kato. Gaussian approximations and multiplier bootstrap for maxima of sums of high-dimensional random vectors (2013), https://arxiv.org/abs/1212.6906
- Berk et al. Valid post-selection inference (2013), https://doi.org/10.1214/12-AOS1077
