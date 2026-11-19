# Original research request (verbatim substantive brief)

## 研究任务：自动调优之后，报告的基准分数意味着什么
在大语言模型的实际使用中，研究者常在一个基准的题目上自动搜索提示词或多调用程序，再把搜索得到的最佳配置在同一批题目上的得分作为性能汇报。

## 研究问题
1. 对一个先在有限题集上搜索配置、再把选出的配置拿去使用的系统，汇报的分数与它在全新题目上的真实表现相差多少？差距受哪些因素影响？是否会影响基于汇报分数做出的结论？
2. 能否设计更可靠的汇报方式？应如何通过实验检验它是否可靠？

## 成功与资源
需要自己运行的实验，至少一个真实 LLM 与真实基准设置。一周墙钟；CPU 为主，至多一张 24 GB GPU 或等价 API 预算。数据：TIGER-Lab/MMLU-Pro，revision b189ec765aa7ed75c8acfea42df31fdae71f97be，test 12032 + validation 70；可合成数据。真实输出必须自行生成缓存。无须训练。

## Deliverables
完整研究论文 PDF 与 LaTeX，选 ICML/ICLR/NeurIPS 最新官方模板、正文页限及 checklist；包含摘要、引言、相关工作、方法、实验、讨论局限、参考文献。完整代码和复现说明，环境依赖版本、获取步骤/数据版本、种子、命令、耗时、图表脚本对应。
全部结果必须实际运行，不得编造或以示意结果代实测；失败、负面、未完成实验如实报告。只引用真实且确实查阅过的来源。

## Independence restriction
不得检索、访问、阅读、使用研究本问题的一篇未具名既有论文或其镜像、摘要、会议评审页、幻灯片、视频、博客、代码；也不得访问引用讨论复现它的页面。不得推测其标题作者结果。仅直接访问 starter_literature 给定原著、无关数据与官方资源，不做科学关键词或引文搜索。偶遇立刻停止并记录位置及已读范围。

## Execution instruction
Unattended; decide feasible details without questions. All deliverables in workspace root /work (subdirectories included).

The user-provided complete task is the controlling specification. This file transcribes its substantive requirements; it is not a claim that every introductory sentence above is a literal quotation.
