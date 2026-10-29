# Analysis of the supplied experimental log: what it supports and what it does not

No new experiments were run: the task says every reported result must match the supplied log, and the log has no code, data or seeds. This repository therefore audits the log and says exactly which claims it can carry. Files (all built by `analysis/build_results.py`, `analysis/figure1_readoff.py`):

- `results/log_numbers.csv`: every number of the log, transcribed (accuracy / MIA, in %).
- `results/gap_audit.csv`: each "Performance Gap" row of the log recomputed.
- `results/baseline_gaps_cifar10.csv`: distances to Retrained for the baseline table (derived).
- `results/figure1_readoff_approx.csv`: bar heights read from `figure_1.png` by pixel measurement, accurate to about ±1 point; not log numbers, use only as approximate/qualitative.
- `results/binomial_se_assumed.csv`: sampling-noise scale, derived under an assumed 50k/10k CIFAR-10 split (the log does not state split sizes).

## Findings that change what the paper may say

1. **The mixed-linear-network gap rows are relative to Unlearned(+), not Retrained.** All 12 numbers of the 3 gap rows match |Unlearned(-) − Unlearned(+)| and none match Retrained. The log's "gap 0.1–0.5% on test accuracy" therefore says Unlearned(-) ≈ Unlearned(+), not ≈ Retrained. Versus Retrained the test-accuracy gaps are 2.2 / 1.7 / 0.9 points (20% / 15% / 10% forget). All other tables' gap rows are relative to Retrained (verified).
2. **Remaining accuracy of Unlearned(-) exceeds Retrained** on the mixed-linear network at 20% and 15% forget (70.0 vs 65.7, 70.1 vs 68.9) and falls below it at 10% (70.1 vs 72.0). Gaps up to 4.3 points; the (-) model is also above Unlearned(+) at 20% and 15%. Report as is; do not call it "closely matching" without these numbers.
3. **Baseline table, MIA:** Adversarial (50.0) and JiT (49.1) are closer to 50% than Unlearned(-) (51.4); NegGrad 48, Random Labels 47 are farther. The log's "MIA close to 50%" holds, but Unlearned(-) is not best on MIA. The utility claim is strongly supported: baselines lose ~20 points (Random Labels ~51) of test accuracy versus Retrained, Unlearned(-) loses 2.
4. **Forget-size trend** (5%→10%→15%): gap in test accuracy 0 → 2 → 14, MIA gap 0 → 1.4 → 5.8. It is a sharp, non-linear breakdown between 10% and 15%; at 5% Unlearned(-) is identical to Retrained in all four metrics including MIA (49.4 = 49.4). The log's "aligns with our theoretical bound" cannot be checked: no bound is stated in the materials. Say "consistent with the expectation that error grows with forget-set size", nothing more.
5. **Perturbations:** gap shrinks monotonically 250 → 500 → 1000 (test gap 15 → 2 → 0). Supported, with three points and one run. The 500-perturbation row is the same configuration as the 10% forget-size row and the λ=0 row (identical numbers 70/71/68/51.4): it is the default setting, not an independent run. Perturbation count and λ are varied separately; it is not stated at which λ the perturbation ablation was run (identical numbers imply λ=0).
6. **λ:** test/remaining/forget gaps shrink monotonically with λ (2→1→0, 3→2→1, 4→1→0). The MIA gap is **not** monotone (1.4 → 0.2 → 0.9). The "inversely proportional to λ²" bound is a theoretical statement outside the supplied materials and the data do not test its functional form (three λ values, one of them 0, for which such a bound would be vacuous). Claim only the empirical trend.
7. **Figure 1 vs log (mixed-linear table):** the CIFAR-100 panel of Figure 1 (read-off: Retrained ≈ 56 test, Unlearned(±) ≈ 50–51) does not match the CIFAR-100 mixed-linear table (62.2 / 60.1 / 60.0 at 20%; 63.7 / 63.3 / 62.8 at 10%). The log does not say that Figure 1 uses a different model (presumably the linear classifier on frozen features). The paper must not present them as the same experiment. The CIFAR-10 panel agrees with the log (72/74/72/50; 70/–/68/51.4). For CIFAR-100, StanfordDogs and Caltech256 the log gives only qualitative statements; the only quantitative source is the figure, with a visible gap between Retrained and both Unlearned variants: test accuracy 4–6 points lower (CIFAR-100), ≈4–5 (Dogs), ≈5–7 (Caltech) than Retrained; and Unlearned(-) is slightly closer than Unlearned(+) on test/forget there. "Closely matching Unlearned(+)" is supported; "comparable to Retrained" is true for MIA and weaker for accuracy on the three harder datasets (≥4 points below). The paper should say this.
8. **No variance information at all.** One number per cell, integer-rounded in the CIFAR-10 tables, no seeds, no confidence intervals. With an assumed 10k test set the binomial standard error alone is ≈0.45 points and ≈0.65 on a 10% forget set (`binomial_se_assumed.csv`), and run-to-run variation is unknown, so differences of 1–2 points (λ rows, 5% vs 10%, all MIA differences below ~2) are not distinguishable from noise. State "single run" in the paper and avoid ranking within ±2 points.
9. The "Performance Gap" for **Retrained rows differs between ablations** (test 73 / 72 / 73): they come from different forget draws or retrain runs; the log does not say. Compare each Unlearned(-) row only with the Retrained row printed with it.
10. **Unlearned(+) is absent from the CIFAR-10 tables** (only in the mixed-linear table and Figure 1), and the forget-set sizes 5/10/15/20% are not all used together on one dataset (CIFAR-10: 5/10/15; CIFAR-100: 10/15/20). No results exist for Stanford Dogs / Caltech-256 beyond Figure 1 at 10%.

## Claim ledger (log claim → verdict)

| Claim in the log | Verdict |
|---|---|
| Unlearned(-) ≈ Unlearned(+) across 4 datasets at 10% | Supported (Figure 1, approx.; CIFAR-10 exact). Within ~2 points except Caltech forget acc (~3.5) |
| Unlearned(-) comparable to Retrained | Supported for CIFAR-10 at ≤10% forget and for MIA everywhere; ≥4 points lower accuracy on the other three datasets (read-off); fails at 15% on CIFAR-10 linear |
| Gap widens with forget size | Supported (CIFAR-10); non-linear, one run |
| More perturbations help | Supported (3 points, one run) |
| Larger λ shrinks gap | Supported for accuracy metrics; not for MIA; λ² form untested |
| Works on mixed linear networks | Supported vs Unlearned(+) (≤0.5 on test); vs Retrained 0.9–2.2 on test, up to 4.3 on remaining accuracy |
| Outperforms source-free baselines on utility | Strongly supported (CIFAR-10, 10%, linear classifier) |
| …while MIA close to 50% | Supported (51.4), but Adversarial/JiT are closer |
