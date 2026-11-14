# Reproduction notes

Paper: "How Much of a Tuned Score Survives on Fresh Items? Optimism and Reliable Reporting for Automatically Tuned Prompts and Pipelines" (anonymous NeurIPS 2026 main-track submission build). This file is the reproduction document required by the venue; everything below is stated as it is, including what is unfinished.

## 1. Status and honest scope
- **Synthetic study:** complete (106-cell plan grid, 2000 repetitions in the one-factor-at-a-time and stress cells, 500 in the interaction grid, plus the two-system comparison, Ladder, hybrid-interval and ranking studies).
- **Real-LLM study (Qwen2.5-0.5B-Instruct x MMLU-Pro): full planned scale, K = 60.** All 60 configurations x 2000 items are scored (`results/matrix.npz`, `results/compute_log.json`; `K` and the item count are printed from them in the paper via `paper/quote_numbers.py`). All real result files (`real_summary.csv` with the disjoint and the i.i.d. truth arm and the argmax, successive-halving, successive-rejects and greedy-coordinate procedures, `fresh_protocol_real.csv`, `real_gaussian_max_check.csv`, `generator_*.csv`) are computed from that one matrix; an earlier snapshot with 21 configurations is superseded and nowhere used. Searches are replayed on the cached 0/1 matrix, not run with the LLM in the loop. A real leakage arm, a real two-system comparison and a per-subject analysis were not run.
- **Not done:** an actual DSPy or MIPRO run (the searches are our own re-implementations of search families: best-of-K, successive halving, successive rejects, greedy coordinate ascent). The conditional and hybrid intervals are our own implementations of ideas from the winner's-curse literature, not reproductions of the original estimators.
- **Venue reading:** "latest edition of the main venue" is read as NeurIPS 2026 main track, the newest NeurIPS edition with an official template; the build is the anonymous default submission mode with the unmodified `neurips_2026.sty`.

## 2. Environment (as run)
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, pyarrow 26.0.0, torch 2.14.1+cpu, transformers 5.22.1 (exact record: `results/compute_log.json`). Figures: matplotlib 3.11.2. Paper: TeX Live with `latexmk` and BibTeX. CPU only (2 CPUs / 4 GB per job on a shared host); no GPU, no API calls.

## 3. Data and model
- MMLU-Pro (`TIGER-Lab/MMLU-Pro`), revision `b189ec765aa7ed75c8acfea42df31fdae71f97be`, test split (parquet); the 3-shot demonstrations come from its validation split. Fetch with the Hugging Face hub at that revision. Licence MIT.
- Model: `Qwen/Qwen2.5-0.5B-Instruct`, fp32 on CPU (Apache-2.0). No sampling: the answer is read from the log-probabilities of the option letters at the answer position, so each (configuration, item) outcome is deterministic.
- Configuration pool: `code/configs.py` / `code/config_pool.json` (6 instruction wordings x demonstration set {none, 4 random 3-shot sets, seed 12345} x option layout {plain, reversed} = 60, index = 10*instr + 2*demo_id + layout). Item pool: `code/qidx_pool.npy` (2000 test items of at most 300 tokens, seed 2024).

## 4. Commands
Scoring, assembly and the replay are described in `code/README.md` and `results/README.md`; the order is: (1) `code/score.py` per configuration range (ten parallel jobs of 6 configurations each, 2 threads); (2) `analysis/assemble.py` -> `results/matrix.npz` (all 60 configurations complete on all items); (3) `analysis/run_real.py` and `analysis/make_real_results.py` -> `results/real_*.csv`; (4) the synthetic scripts `analysis/run_synth3.py`, `run_synth2.py`, `run_synth_ladder.py`, `run_hybrid.py`, `run_rank_synth.py` and `analysis/make_synth_results.py` -> `results/synth_*.csv`; (5) `analysis/compute_log.py` -> `results/compute_log.json`.
The ordered, exact commands (arguments, shard counts, M), the seeds of every script and the measured running times are in **`code/README.md`, section "Regenerating `results/`"** (19 steps). Measured there (re-timed where an earlier run was not recorded): plan grid, 6 shards of 493-710 s each; conditional/two-system study (M=500) about 1050 s; Ladder 33 s; synthetic summaries 87-366 s; hybrid study 1325 s; ranking study 382 s; equal-budget synthetic study 1018-1387 s per shard for five shards and 3263 s for one and its ranking part 623 s; real replay at K=60, 5116 s (disjoint) and 6529 s (i.i.d.), both with greedy coordinate search; real fresh-set run 857 s; validation of the conditional/hybrid intervals 2214 s and 614 s; Gaussian-max check on the real matrix 45 s; calibrated generator 113 s; scoring is about 0.19 questions/s per job, 21-35 h of wall-clock per 6-configuration chunk under contention (`compute_log.json`). These are world running times on a shared 2-CPU container, not exclusive-CPU times.

Exhibits, from the committed result files (no model needed):
```
cd figtab && for s in e1_gap_vs_K e2_factor_effects e4_false_claims e4_unequal_budget e4c_ranking e5_reliability e5b_hybrid tables e3_real_gap real_tables; do python3 $s.py; done
python3 -I paper/quote_numbers.py        # writes paper/quote_numbers.tex (all numbers quoted in the text)
sh paper/build.sh                         # builds paper.pdf (anonymous)
```

## 5. Table and figure -> script map
Every numbered exhibit, with the script that draws it and the result file(s) it reads (`figtab/MAP.md` has the caption facts):

| Exhibit in the paper | Script | Input |
|---|---|---|
| Fig. gap vs K (main) | `figtab/e1_gap_vs_K.py` | `results/synth_theory_prediction.csv` |
| Fig. factor effects (main) | `figtab/e2_factor_effects.py` | `results/synth_plan_summary.csv` |
| Fig. claims (a) one tuned system, (b) unequal budgets (main) | `figtab/e4_false_claims.py`, `figtab/e4_unequal_budget.py` | `synth_plan_summary.csv`, `synth_compare_summary.csv` |
| Table 1 reference cell (appendix) | `figtab/tables.py` -> `paper/tables/t1_reference_cell.tex` | `synth_plan_summary.csv` |
| Equal-total-item protocol tables: T7 synthetic reference cell (appendix; Table 2), T8 real replay (appendix, when included) | `figtab/fresh_tables.py` -> `paper/tables/t7_fresh_protocol.tex`, `t8_fresh_real.tex` | `results/fresh_protocol_summary.csv`, `results/fresh_protocol_real.csv` |
| Appendix tables (gap by n and K; stress cells; unequal budgets) | `figtab/tables.py` -> `t4_gap_by_n_K.tex`, `t2_stress_cells.tex`, `t3_unequal_budget.tex` | `synth_plan_summary.csv`, `synth_compare_summary.csv` |
| Appendix figs: hybrid intervals, ranking, reliability | `figtab/e5b_hybrid.py`, `e4c_ranking.py`, `e5_reliability.py` | `synth_hybrid_summary.csv`, `synth_ranking_summary.csv`, `synth_plan_summary.csv` |
| Real-LLM figure: gap vs n and K, procedures, Gaussian-max prediction, i.i.d. arm (main) | `figtab/e3_real_gap.py` | `results/real_summary.csv`, `results/real_gaussian_max_check.csv` |
| Generator calibrated to the real matrix (appendix) | `figtab/real_tables.py` | `results/generator_calibration.csv`, `generator_pairwise_fit.csv`, `generator_vs_real_gap.csv`, `synthetic_phi_map.csv` |
| Real-LLM table: nine reporting methods (appendix); setup and compute record (appendix) | `figtab/real_tables.py` -> `paper/tables/t5_real_methods.tex`, `t6_setup_compute.tex` | `real_summary.csv`, `matrix_spread.csv`, `compute_log.json` |
| Every number in the running text, including the reliability-criterion counts (bias, under- and over-coverage per method) and the Gaussian-max agreement counts | `paper/quote_numbers.py` | `results/*.csv` (incl. `synth_cell_pass_fail.csv`, `synth_pass_fail_by_method.csv`, `synth_theory_vs_sim.csv`, `synth_claim_margin_summary.csv`, `synth_compare_margin_summary.csv`, `fresh_protocol_summary.csv`, `ranking_equal_budget_summary.csv`, `validation_cond_hybrid.csv`, `validation_lead.csv`, `synth_hybrid_summary.csv`, `real_gaussian_max_check.csv`, `generator_*.csv`, `synthetic_phi_map.csv`, `fresh_protocol_real.csv`), `compute_log.json` |
| Exact definitions of generators, procedures and estimators (appendix) | text only; code in `analysis/synth.py`, `analysis/lib.py`, `analysis/run_grid.py` | |

## 6. Seeds
Full table in `code/README.md` (section Seeds): configuration demonstration sets 12345; item pool 2024; synthetic pools seed 7 (plan grid, comparison, Ladder, theory table), 300+1000*tau (hybrid), 400+1000*tau (ranking); replication seeds 100+cell index (plan grid), 21, 77, 11, 21 and 5 (real replay); cells are seeded independently by a hash of the cell tag.

## 7. Compute actually used
Real scoring: ten parallel CPU jobs (2 threads each) on a shared host; the running time and an upper bound of CPU-hours (running seconds x 2 CPUs per job) are in `results/compute_log.json` (`scoring_jobs`, and the wall-clock per scoring chunk in `scoring_wall_clock`); the effective CPU use was lower because the host was shared. Synthetic and replay runs: CPU only, running times in Sec. 4. No GPU and no paid API were used.

## 8. Forbidden-material log
The task reserved one published paper (and anything citing or discussing it). Literature was searched with topical queries only (winner's curse, adaptive data analysis, selection bias in prompt optimisation, post-selection inference), and the cited sources are the starter-list items and independently found literature. No search result or source matched the reserved paper, so the reserved material was not read or used. Result: **none encountered**, and none was logged by any contributor to the project.

## 9. Use of LLMs and agents
The system under tuning is a language model (Qwen2.5-0.5B-Instruct, described above); no LLM proposer was used. The study, code, analysis and this paper were produced by AI agents (Claude models) working under human-specified tasks; no agent is listed as an author, and every number in the text is generated from the committed result files.
