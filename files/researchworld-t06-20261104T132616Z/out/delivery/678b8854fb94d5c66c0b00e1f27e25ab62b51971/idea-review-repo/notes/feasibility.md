# Feasibility evidence (2026-11-04) — working notes of idea-review-repo
- notes/bench_bt_fit_time.py: Newton BT fit on *synthetic* data of Arena/NBA/MT-Bench size, 2-CPU sandbox:
  N=57k,K=64 cold 0.035 s (6 it), warm refit 0.009 s; N=60k,K=126 cold 0.052 s; N=3.3k,K=6 0.004 s.
  Synthetic timing only; real-data timing is not measured here.
- MT-Bench pinned parquets (HTTP 200 checked): human 3,355 rows / 2,396 unique (question,pair,turn) keys (multiple judges per key);
  gpt4_pair 2,400 rows / 2,400 keys; keys present in both: 1,232. GPT-4 winner: model_b 1610, tie (inconsistent) 380, tie 220, model_a 190.
  Human: model_a 1293, model_b 1282, tie 780. 15 pairs, 150-361 human rows per pair.
- Arena-55k train.csv and nbaallelo.csv at pinned URLs answer HTTP 200.
