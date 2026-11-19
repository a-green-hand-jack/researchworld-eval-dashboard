# figures/ (figtab-repo)

Generator: `make_figures.py` (uses `style.py`, `common.py`). Run from the repository root of the delivery tree:

    python3 -I figures/make_figures.py          # reads results/, writes figures/rendered/ (about 20 s, 1 core)

Needs matplotlib 3.11, pandas 3.0, numpy 2.4. Randomness: only the jitter of F7 and a 800-point display subsample in F6
(seeds fixed in the script); no number in a table or interval depends on it.
`rendered/PROVENANCE.json` lists, per figure/table, the `results/` files read and their sha256, and the seed/code commit of each (from `results/MANIFEST.json`).

| output (`rendered/`) | claim of PLAN.md section 5 | reads (`results/`) |
|---|---|---|
| `f1_fragility.pdf` | 1 fragility of C1/C2/C4 on s1, per family P1-P3 | `kstar_units`, `kstar_full` |
| `f2_worst_vs_random.pdf` | 2 worst case vs random edits vs resampling | `random_curve`, `boot_flip`, `kstar_full` |
| `f3_scales.pdf` | 3 the same P1 result on k*, s1, s2, s3 | `kstar_units`, `kstar_full` |
| `f4_size_control.pdf` | 3 s4: size/sparsity-matched Arena vs MT-Bench, NBA | `matched_arena`, `kstar_units` |
| `f5_matched_mtbench.pdf` | 3 matched human vs GPT-4 contrast on identical resampled questions | `paired_mt` |
| `f8_crowd_vs_judges.pdf` | 3 matched crowd vs LLM-judge contrast on the same 49,938 Arena battles (k*, paired log ratio, unperturbed z) | `kstar_judges`, `paired_mt` |
| `f6_predictors.pdf` | 4 what predicts k* (z, N_local, design) | `kstar_units`, `scaling_fit` |
| `f7_search_validity.pdf` | 4 where the method is loose (linearisation, greedy vs exhaustive) | `approx_check`, `exact_check`, `kstar_full` |
| `t1_data_summary.tex` | context | `data_summary` |
| `t2_headline.tex` | 1-3 numbers behind F1/F3 | `kstar_units`, `kstar_full` |
| `t3_sensitivity.tex` | 5 ties, home advantage, playoffs, pooled NBA | `sensitivity`, `kstar_units` |

Conventions in every figure: one colour and marker per evaluation design (Arena blue circle, MT-Bench human vermillion square, MT-Bench GPT-4 orange open triangle,
NBA green diamond); the censored searches (`found=False`, none in the main tables except a few NBA C2 rows) enter at their cap k_max as in `summary_claims.csv`;
the bars are 2.5-97.5 percentile ranges over the replicate units of one dataset (NBA: 69 seasons; Arena: 60 battle bootstraps; MT-Bench: 200
question-cluster bootstraps), pooled over the claim instances of that claim; they are not design-level confidence intervals. k* is a verified upper bound on the
true minimum edit count. Widths are the NeurIPS 2026 text width (5.5 in); tables carry `\footnotesize` and need `booktabs`.

Known display choices: F1/F3 pool the adjacent pairs C2 (r<=10) and C4 pairs of a board with its replicates, so the bar mixes pair-to-pair and replicate-to-replicate spread;
the full-data tick shows the single actual fit (Arena, MT-Bench only; NBA has no single full fit). T3 decodes `unit_id` of the NBA variant rows to the season from the job order in
`code/run_sens.py` (asserted in the script), because `sensitivity.csv` stores the job index there.

F8: the paired intervals are over 40 shared battle bootstraps (`paired_mt.csv`, rows a = arena49k_h); P1 and P2 are both shown, P3 was not run for the judge boards. Tie rates differ (human 31%, judges 4-26%), stated in the caption.
