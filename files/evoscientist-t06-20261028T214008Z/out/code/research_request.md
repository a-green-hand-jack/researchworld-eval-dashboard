# Research request (verbatim summary of the task brief, saved 2026-10-28)

## 研究任务：成对比较排行榜的稳定性
- 问题：基于成对比较（Bradley-Terry 等）的排行榜，其排名对底层比较数据的小幅改动（噪声或有意操纵）有多敏感；
  这种敏感性在不同数据集、不同评测设计（众包投票、专家标注、模型裁判、体育比赛）之间是否不同。
- 要求：自行界定研究问题、数据集、指标、方法与基线；结论基于至少两类不同评测设计的真实数据；
  自行定义改动规模的度量和跨数据集比较方式并说明理由；说明适用条件与局限；负面/"视条件而定"结论可接受。
- 约束：仅 CPU，约一周，公开数据（data.md / resources.md）。
- 产出：一篇研究论文（ICML/ICLR/NeurIPS 最新官方模板，遵守页数，填写会议要求的 checklist；PDF + LaTeX），
  及全部代码与复现说明（环境、依赖版本、数据获取与版本/校验和、随机种子、运行命令、预计耗时、每张图表对应脚本）。
- 如实报告：所有数字来自实际运行；失败/放弃的方案如实报告；只引用真实且查阅过的文献。
- 禁止访问：已发表的、研究过本问题的那篇论文及其任何镜像/讨论/引用页面；不得推测或检索其标题、作者或结果。
  starter_literature.md 中的文献可正常使用。偶然遇到须停止并在复现说明中记录。

## Data options (data.md)
Arena-55k (crowd), Arena-140k (crowd, optional), MT-Bench human + GPT-4 pair judgments (expert / LLM judge),
chatbot-arena-llm-judges (LLM judges on Arena battles, license undeclared), WebDev Arena (license agreement),
FiveThirtyEight NBA Elo (sports). Raw data under data/ and not committed.

## Starter literature
Bradley & Terry 1952; Chiang et al. 2024 (Chatbot Arena); Zheng et al. 2023 (MT-Bench / LLM-as-a-judge);
Koh & Liang 2017 (influence functions); Broderick, Giordano & Meager 2020 (AMIP);
Min et al. 2025 (vote rigging); Singh et al. 2025 (Leaderboard Illusion); Huang et al. 2025 (dropping a handful of preferences).
