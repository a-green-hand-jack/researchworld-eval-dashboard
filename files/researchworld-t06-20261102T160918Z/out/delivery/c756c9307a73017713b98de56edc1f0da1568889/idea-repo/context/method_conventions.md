# Analysis and display conventions supplied by context

These are mathematical/context checks for the owning analysis and presentation positions, not additional empirical results.

## Specify the fitted ranking

For x_i=e_a-e_b and outcome y_i in {0, 1/2, 1}, the current analysis release uses

    L(theta) = sum_i [log(1+exp(x_i' theta)) - y_i x_i' theta]
               + (lambda/2) ||theta||², lambda=1.

The ridge term makes curvature positive definite; stationarity implies centered scores. Report raw logit scores/margins. Multiplying a score by a positive constant and adding a common offset preserves order but changes numerical margin units. Half-win ties enter the fractional logistic objective and are uneditable in the chosen intervention; this is not a probability model distinguishing true ties from order-inconsistent judge outputs.

Loss normalization is essential: lambda=1 on a summed loss is not lambda=1 on a mean loss. Holding a summed-loss penalty fixed across different N changes relative shrinkage. The executed lambda sensitivity checks address this specified convention. Do not imply weighting and regularization were identical to every official platform pipeline. The original Arena paper's uniform-pair target and inverse-sampling weighting are a separate estimand; fixed empirical-schedule fits answer a conditional snapshot question.

## Distinguish replacement influence from deletion influence

Let H=sum_i p_i(1-p_i)x_i x_i' + lambda I at the initial fit, c=e_leader-e_runner and m=c'theta. Reversing y_i to 1-y_i changes the gradient at the old fit by (2y_i-1)x_i. A first-order parameter update is therefore

    Delta theta_i ≈ (1-2y_i) H^(-1) x_i,
    Delta m_i ≈ (1-2y_i) c' H^(-1) x_i.

Helpful rows have a negative predicted Delta m. A sorted prefix or binary-search choice is a heuristic candidate set. Refitting supplies the actual result. This formula follows smooth loss replacement (Koh and Liang §2.2); it is not necessary to copy a deletion-specific published expression. With deletion, the gradient contribution removed includes the residual (p_i-y_i), so the intervention and the candidate ordering are different.

For a successful refit after k edits, the measured effect is a feasible perturbation and k upper-bounds the globally smallest successful cost. The adjoining smaller evaluated prefix does not rule out another subset or establish that the current prefix is globally minimal. No-found-attack within a 5% cap is a search result, not a certified robust region. Failure to reverse with a heuristic cannot establish absence of a one-edit attack in an unexhausted set.

## Units, matching and endpoint selection

Report k, original N, decisive count D, tie count and actual realized edits. A budget k/N including ties differs from k/D among editable rows. Show both counts and fraction; do not quietly change denominators across datasets. Fractions normalize sample size but not information, schedule, model count, score gaps or dependence. Retained N, raw N and matched N are separate quantities.

Fixed initial leader-runner reversal, any global winner change, original leader rank, top-k set overlap and Kendall pair disagreement are distinct outcomes. The runner-up need not become winner after that pair reverses. Global normalized Kendall disagreement has denominator M(M-1)/2 when all M entrants remain in the ranking; differing M and top-k definitions need explicit display context.

MT matching uses question, unordered model pair and turn, with label orientation corrected. One observed human label per cell matches the GPT-4 row schedule/count but samples a mixture of available annotators; it does not turn human labels into independent ground truth. Question resampling should keep its turns/pairs/sources together. Separate a statistic that reselects top pairs in resamples from a fixed original-reference-pair statistic. An already reversed fixed reference pair costs zero further edits. The fixed-reference follow-up is post-hoc according to the analysis release.

NBA requires one outcome per game; each season is its own static-strength fit. Date clusters and a home coefficient address some dependence/misspecification, but not strength drift, roster changes or general causality. Ten seasons are within-design variation, not ten evaluation designs. Arena's missing user identifiers limit clustering and any corruption/account interpretation.

## Uncertainty and figure conventions

Report three separate sources where used: Monte Carlo variation over random edits, cluster-bootstrap variation in the data, and sensitivity to fit/tie/inclusion choices. Deterministic influence output has no Monte Carlo variability. The random-edit event frequency's binomial interval is Monte Carlo uncertainty, not a data-sampling confidence interval. A percentile interval for a selected baseline gap has no automatic simultaneous/post-selection guarantee.

A checkable primary display should identify the original pair and baseline gap uncertainty beside found costs; perturbation curves should separate the targeted endpoint from global disagreement and identify actual budget saturation. Matched MT displays must name fixed versus reselected pair selection and use percentage points for differences of percentages. Censoring, zero-cost bootstrap cases, interval type and number of replicates belong in captions/table notes. No pooled error bar should treat ten seasons or all comparisons as independent evaluation designs.

Prior literature supplies useful display conventions: score intervals and corrected rank uncertainty (Chiang Figure 5); tie-aware agreement tables with explicit setup denominators (Zheng Tables 5–6); fractions of sufficient deletions and gap comparisons (Huang Table 1/Figures 2 and 6). Their guarantees and units do not transfer merely by imitating the graphics. Final layout and figure selection remain figtab-repo's responsibility.
