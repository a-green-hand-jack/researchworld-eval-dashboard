# Review of paper-repo#29 (interim version into `release`)

Head inspected: `47d5afcfd74658d89261239fd773eae2669fe2e8` (checks: `hutian/delivery` success).

## What I inspected
- Built the PDF from `paper/` at that head: identical text to the committed `paper.pdf` (21 pages; 9 main pages, references p.10, checklist after). `paper/quote_numbers.py` regenerates `quote_numbers.tex` with no diff.
- Opened every main and appendix figure (Figs 1-7) as rendered in the PDF: all labelled, legible, with error bars and captions that match the text (Fig 1 prediction overlay, Fig 2 OFAT panels, Fig 3 claims, Fig 4 real gap, Figs 5-7 appendix).
- Spot-checked quoted values against `results/`: reference cell (naive 4.59 pp, held-out 0.07, coverage 0.759/0.946, conditional width 60.5 pp) match `synth_plan_summary.csv`; real n=200, K=5 rows of Table 2 match `real_summary.csv`; real matrix facts (K=5, 10,000/120,000 outcomes) match `compute_log.json`.
- REPRODUCE.md: versions, data revision, seeds, commands, runtimes, exhibit-to-script map, compute used, forbidden-material log, LLM-use statement present.

## Judgement against the commitment (#2)
Supported as an **interim** version. Q1 (size and drivers of the gap) and Q2 (reporting methods validated against exact truth with Monte-Carlo s.e.) are answered by a 106-cell synthetic study; the decision-impact question is answered (false claims, unequal budgets, ranking). The real-LLM/real-benchmark requirement is met in a minimal way (K=5 configurations, Qwen2.5-0.5B, MMLU-Pro) and the paper says so plainly in abstract, Sec. 1, 4.2 and limitations. No placeholder numbers found; negative results (conditional estimator, bootstrap, cross-fit coverage) reported.

## Open findings for `final` (not blocking this interim release)
1. Real arm is the weakest part: K=5 of 60 configurations, spread 0.8 pp, one 0.5B model; the K-dependence and the spread regime that matter for tuning cannot be assessed. The 5 complete configurations are those that finished first, not a random subset - state this or show the subset is representative. Completing more configurations (or a second model / API model) is what lifts the real claim. Owner: experiment-repo.
2. Conditional (winner-aware) estimator: 60 pp width and -10 pp midpoint bias in the reference cell. The text attributes it to the implementation but did not diagnose it. A known-case check (e.g. K=2, independent Gaussian, compared with closed-form truncated-normal results) would show whether it is a bug or an inherent property before the paper calls it "a limit of our implementation". Owner: experiment-repo.
3. REPRODUCE.md sec. 8 says forbidden-material log is "to be confirmed by idea-repo"; close this before final. Owner: paper-repo/idea-repo.
4. Two run times not recorded (conditional/comparison study, Ladder); 4 of 6 plan-grid shards timed. Say so in the final compute statement or re-time. Owner: experiment-repo.
5. (Checked, no defect) Real-setting false-claim rates in the text (11% at n=200, 16% at n=50) equal `fp_rate` in `real_summary.csv`; the `claim` column (all repetitions) is a different quantity and is not quoted as such.
