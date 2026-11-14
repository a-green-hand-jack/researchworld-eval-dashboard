# Paired binary interval, selected before confirmatory outcomes

2026-11-03, before any registered block 1100+j/2100+j is run or read.

For secondary paired incidence contrasts, use the full 2x2 paired table and a conservative exact confidence interval for the marginal probability difference. Let n_plus count (reference event=0, changed condition event=1), n_minus count (reference event=1, changed condition event=0). The difference is (n_plus-n_minus)/n. The pair, not an input example, is the replication unit.

Construct separate two-sided 97.5% Clopper–Pearson intervals for p_plus and p_minus (tail probabilities 0.0125 and 0.9875). Each discordance count has a binomial marginal over independent seed blocks; their within-block mutual exclusivity is retained in the table. Bonferroni guarantees joint coverage of the two intervals of at least 95% without assuming independence of their counts. The difference interval is [lower_plus-upper_minus, upper_plus-lower_minus]. This is a valid, conservative exact paired interval. It is wider than optimized paired-score intervals, particularly at n=8. It avoids certainty when there are zero discordances. It does not permit a claim of equality from a zero observed difference.

Implementation: `code/src/events.py::paired_binary_interval`. Uses SciPy beta quantiles with exact boundary handling at counts zero and n. Synthetic tests check no-discordance uncertainty, all-plus positive direction, all-minus negative direction. Raw paired tables accompany every reported difference. Continuous P1/P3 contrasts retain the registered paired percentile bootstrap (10000 draws, seed1701).
