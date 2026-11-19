# Measured findings and claim-to-output map

All numeric findings below come from actual completed runs. There are 165,000 independent draw sets across 35 scenario/sample-size cells, and 1,935,000 trial-method records after baselines. The original main grid has 5000 repetitions/cell; bounded and finite-N supplements have 3000/cell. Results are conditional on the declared sampling models and comparator family. Wald coverage compatibility is evidence, not an exact guarantee.

## C1: When a nonlinear score control can help

The variance identities and fixed-basis normal-limit proof are in analysis/proofs.md. They give a conditional mechanism: added basis functions help at population coefficients only through extra projection signal; affine or constant conditional means leave no first-order nonlinear gain in this estimator class. This is not claimed as a new theorem or a universal confidence-interval lower bound.

## C2: Nonlinear gain with coverage compatible with the nominal target

For quadratic Gaussian regression, n=2000, N=20000, cf_cubic / PPI++ mean-width ratio is 0.524803 (paired 95% MC interval [0.524599, 0.525006]). Cubic coverage is 0.9504 (95% Wilson MC interval [0.9440, 0.9561]; 4752/5000 hits); PPI++ coverage is 0.9486 (95% Wilson MC interval [0.9421, 0.9544]; 4743/5000 hits). Thus the measured reduction is about 47.5%, while both coverage estimates are compatible with .95. This remains an asymptotic method, not a finite-sample promise.

Against the unrestricted scalar at the same cell the ratio is 0.524886 (paired 95% MC interval [0.524683, 0.525090]), ruling out clipping alone as the explanation. Full-cell outputs in results/summary.csv and results/paired.csv also include sigmoid, quadratic Bernoulli and heavy-tail settings; the conclusion should not be based on a selected successful replicate.

## C3: No practical gain on the three supplied frozen-score datasets

- galaxies, n=2000, N=20000: cf_cubic / PPI++ ratio 1.001412 (paired 95% MC interval [1.001340, 1.001483]); cubic coverage 0.9488 (95% Wilson MC interval [0.9423, 0.9546]; 4744/5000 hits).
- forest, n=2000, N=20000: cf_cubic / PPI++ ratio 0.998945 (paired 95% MC interval [0.998809, 0.999080]); cubic coverage 0.9474 (95% Wilson MC interval [0.9409, 0.9533]; 4737/5000 hits).
- alphafold, n=2000, N=20000: cf_cubic / PPI++ ratio 1.001498 (paired 95% MC interval [1.001343, 1.001652]); cubic coverage 0.9492 (95% Wilson MC interval [0.9428, 0.9549]; 4746/5000 hits).

These are empirical-population with-replacement benchmarks with truth fixed to the archive mean (results/data_populations.json), not evidence about the natural target populations. The forest reduction is about one tenth of one percent; the other two widen slightly. At n=500 all three widen. Claiming broad real-data gains would contradict the results. Linear/no_signal synthetic regimes also have a small fitting cost instead of a first-order gain.

## C4: Coverage and fit failures remain visible

Rare Bernoulli with p=.01, n=100, N=1000: cubic coverage 0.6346 (95% Wilson MC interval [0.6212, 0.6478]; 3173/5000 hits); label-only Wald coverage 0.6352 (95% Wilson MC interval [0.6218, 0.6484]; 3176/5000 hits); exact Clopper-Pearson coverage 0.9836 (95% Wilson MC interval [0.9797, 0.9868]; 4918/5000 hits). Short Wald intervals here cannot be described as valid precision improvements.

At n=100, forest cubic has median width .131636 but maximum 35.827096; alphafold median .101198 but maximum 8.748830. These values are kept in the mean and MC uncertainty. Results/tail_diagnostics.csv contains all medians and upper-tail quantiles, including degree-12 ablations. Cross-fitting does not prevent poor nuisance estimation or establish finite-sample normality.

The exploratory exact-binomial Holm diagnostic finds significant cubic undercoverage in: alphafold n=100 N=1000, galaxies n=100 N=1000, rare_binary n=100 N=1000, rare_binary n=500 N=5000. A lack of rejection in other cells is not proof of validity; results/coverage_diagnostics.csv includes all raw and adjusted p-values.

## C5: A finite-sample valid but conservative improvement is possible

The bounded high-signal quadratic supplement has Y in [0,1]. At n=10000, N=100000, eb_cubic / eb_label ratio is 0.712791 (paired 95% MC interval [0.712677, 0.712905]); versus the stronger full-label unit-PPI EB it is 0.367128 (paired 95% MC interval [0.367059, 0.367198]); versus split-trained scalar EB it is 0.556815 (paired 95% MC interval [0.556673, 0.556957]). Cubic EB coverage is 1.0000 (95% Wilson MC interval [0.9987, 1.0000]; 3000/3000 hits). All these EB methods have >=95% finite-sample coverage under bounded iid assumptions, independently of the observed hit count. The label-only comparison corresponds to about 28.7% shortening; unit-PPI is weak in this nonlinear setting.

At n=2000, the EB cubic / label-only ratio is 0.993996 (paired 95% MC interval [0.993671, 0.994320]), so the range penalties almost erase the gain. On all three real datasets, EB cubic is wider than EB label, full-label unit-PPI, scalar EB and exact Clopper-Pearson. On the binary nonlinear scenario it can beat unit-PPI EB yet loses to label EB and CP; this is not overall improvement. The finite-sample claim is restricted to the tested EB family, not optimality against every bounded-mean interval. These conservative intervals are much wider than the Wald alternatives.

## C6: Finite unlabeled samples limit the gain

In the follow-up quadratic experiment n=N=2000, cubic / PPI++ ratio is 0.775389 (paired 95% MC interval [0.775185, 0.775593]) and cubic coverage 0.9560 (95% Wilson MC interval [0.9481, 0.9628]; 2868/3000 hits). With N=10n the corresponding measured ratio is 0.524803 (paired 95% MC interval [0.524599, 0.525006]). The exact leading-order predictions in results/theory.csv are approximately .775 and .524. The follow-up also retains its linear and no_signal null comparisons.

## Provenance, uncertainty and delivery limits

Per-repetition endpoints and seeds are in results/synthetic/, results/real/, results/bounded/ and results/ratio1/. The 95% coverage intervals are Wilson Monte Carlo intervals. Width-ratio intervals use the paired delta method for the ratio of mean widths, not a ratio averaged across replicates. All summaries retain failures; results/audit.json records finite values, nonnegative widths, coverage reconstruction and repetition/key checks. No held-out archived label is an estimator input. No prohibited reference was searched for or encountered.

For reporting: use C2 and C5 to distinguish asymptotic empirical evidence from a bounded-data theorem; give C3 and C4 similar prominence. Do not imply that the cubic solves the fixed-input problem universally, improves PPI++ on these real data, or attains exact coverage at every sample size. More flexible bases and regularization were not optimized; a cubic is a deliberately simple fixed inferential basis.
