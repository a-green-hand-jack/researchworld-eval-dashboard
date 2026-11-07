# Original research request (preserved intake)
研究任务：用少量基准预测大模型在其余基准上的表现。
Given an incomplete historical model-by-benchmark score matrix, select k benchmarks for a genuinely unseen model and predict its remaining scores. Independently review allowed prior work, implement methods, run real public-leaderboard experiments with appropriate baselines and uncertainty, optionally derive and check theory. CPU only; one week; total storage <5GB. Deliver complete paper PDF and LaTeX using latest official ICML/ICLR/NeurIPS template, page limit and checklist; all code, pinned data acquisition, seeds, versions, commands, timings, table/figure mapping.
Success is held-out score accuracy, including negative or conditional findings. Never fabricate results or citations. Only cite actually read works.
No human available; work unattended. Everything delivered saved in workspace root /work or subdirectories.

## Supplied sources and immutable versions
MTEB primary: https://github.com/embeddings-benchmark/results commit 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383, CC0-1.0, embedding not generative models.
Open LLM optional: https://huggingface.co/datasets/open-llm-leaderboard/contents commit 9c09a7cae43334062a82cb164f2ef255013dafa2, dataset license unspecified, 4576 rows six benchmarks.
HELM Lite optional v1.13.0; LiveBench optional 9704e5da7bfbefe75ac1482a13de827127295993; BigCodeBench optional 09dd993f46c3fbf3a799465bb96d524edcb0b199; AlpacaEval optional cd543a149df89434d8a54582c0151c0b945c3d20.

## Allowed starter literature
2009.03300 MMLU; 2210.07316 MTEB; 2211.09110 HELM; 2306.05685 MT-Bench; 2402.14992 tinyBenchmarks; 2407.12844 metabench; 2407.13696 BenchBench; 2405.10938 Observational Scaling Laws; 2412.06540 Sloth; 2406.15877 BigCodeBench.

## Prohibited content and access strategy
An unspecified published paper and all its versions, abstract/review pages, presentations, repositories, and pages citing/discussing/replicating it are forbidden. Do not guess its title/authors/results. To avoid accidental encounter, no topical searches, citation graphs or later-paper searches; only exact starter paper bodies (avoid bibliographies), specified data endpoints, official conference pages and generic software documentation. Any incidental exposure must stop and be logged with extent. Log in literature/access_log.md.
