# Analysis protocol (written before computing rankings)

Date: 2026-10-28. CPU only; no paid APIs or new model judgments.

Question: How do verified small-edit rank reversals differ between crowdsourced
votes, expert judgments, a fixed model judge, and scheduled sports, and which
comparisons remain after accounting for exposure, score margin, uncertainty,
and matched evaluation items?

Primary data: all 57,477 Arena records; all 3,355 MT human and 2,400 MT GPT-4
records; NBA regular seasons ending 2013, 2014, 2015, deduplicated by _iscopy=0.
No outcome-based participant exclusions. Ties contribute y=0.5, including GPT-4
position-inconsistent judgments. The latter convention is separately ablated.

Estimator: batch Bradley--Terry, centered scores, summed logistic loss, symmetric
ridge lambda=1e-6 for numerical existence. No dynamic Elo/time decay. Separate
season fits for NBA. Baseline order fixes adjacent comparisons before edits.

Primary perturbations: record deletion; decisive-label reversal (ties unchanged).
Rank candidate records by first-order gap decrease for each fixed adjacent pair;
verify every reported successful reversal by a full refit. Search prefixes up to
5% of N. A found edit set is a feasible upper bound on minimum required edits;
search failures are not robustness certificates. Also test direct-pair-only edits
and random edits (200 repetitions) at common global budget fractions.

Outcomes: successful prefix size / N, size / union of incident exposure for target
pair, fraction adjacent boundaries reversed, leader loss, Kendall discordance.
Uncertainty: 400 bootstrap replicates; question clusters for MT, game dates for
NBA, individual records for Arena (no user identifiers). Bootstrap 95% percentile
gap intervals are descriptive and post-selection; no familywise claim.

Controls: evaluate all adjacent boundaries, not only easiest one; compare exposed
vs bootstrap-separated boundaries; same question/turn/model-pair matched human
and GPT-4 comparisons with equal row counts; tie, regularization, home advantage,
and finite-budget approximation checks. No causal claim about annotator quality.

Only direct links to explicitly allowed starter papers and official ICML 2026
formatting/CFP pages will be accessed. No general search, citation chasing, or
access to source repositories of prior ranking-robustness work. Source PDFs are
read locally. This log will record actual deviations and failed runs.
