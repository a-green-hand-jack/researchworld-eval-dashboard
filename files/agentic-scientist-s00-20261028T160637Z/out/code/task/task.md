# Goal

**研究任务：小图上随机游走覆盖时间的简单预测**
**背景**
在无向连通图上，从某个顶点出发的简单随机游走访问完所有顶点所需的期望步数称为覆盖时间。
理论上有以顶点数和边数表示的上界，但对规模很小的具体图，上界往往很松。

**研究问题**
> 对顶点数不超过 30 的连通图，能否用图的少数几个易计算的统计量（如顶点数、边数、
> 平均度、最大度、直径）给出比通用上界更准确的覆盖时间预测？预测误差与图的类型有何关系？

**动机**
给出一个可测量、可复现的经验预测，并说明它在哪类图上可靠、在哪类图上失效。

**要求**
- 方法、实验设计和结论由你自行决定；
- 结论必须有本任务内自己产生的实验证据，并报告蒙特卡洛不确定性；
- 其余约束见同目录的 `starter_literature.md`、`data.md`、`resources.md`、`deliverable.md`。

**起步文献**
- Aleliunas, Karp, Lipton, Lovász, Rackoff. Random walks, universal traversal sequences, and the complexity of maze problems. FOCS 1979.
- Feige, U. A tight upper bound on the cover time for random walks on graphs. Random Structures & Algorithms, 1995.
- Lovász, L. Random walks on graphs: a survey. Combinatorics, Paul Erdős is Eighty, 1993.

**数据**
不需要外部数据。图可程序化合成（路径、环、星、完全图、网格、随机图等），无需下载或账号。

**资源与预算**
- 计算：仅使用 CPU；全部实验应在数分钟内完成。
- 时间上限：本任务是连通性冒烟测试，请在尽量短的时间内完成，不要做大规模扫描。
- 不需要付费 API 之外的任何资源。

**产出要求**
1. 一篇简短的研究论文（4 页以内即可）：从 ICML、ICLR、NeurIPS 中任选其一，使用该会议的官方 LaTeX 模板，
   包含摘要、引言、方法、实验、讨论与局限、参考文献。
2. 可运行的代码和复现说明（环境、命令、随机种子）。
3. 论文中的结论须有本任务内的实验证据支持，并报告不确定性。
4. 禁止访问的内容类别（须在过程中遵守）：回答本研究问题的原始论文本身及其任何镜像，
   以及引用或讨论该原始论文的任何页面。

# Rubrics

No rubric is provided for this task; the requirements stated above apply.
