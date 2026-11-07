# Conformal uncertainty for compositions: restricted primary-source notes

Prepared 2026-11-02 (UTC). Research/planning only; no experiment implementation or experiment results produced.

## 1. Scope, sources, and identifier correction

Only the four explicitly allowed PDF URLs below were downloaded for topical research. All page numbers below are **one-indexed PDF pages**, not search snippets. These sources were read locally; their references, code links, and datasets were not used as permission to browse elsewhere. This is a restricted-source synthesis, not an exhaustive survey or a novelty assessment.

| ID | Verified title/authors | Downloaded version; pages |
|---|---|---|
| [1] | *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, Anastasios N. Angelopoulos and Stephen Bates | 2107.07511v6, 7 Dec 2022; title page 8 Dec 2022; 51 pp. |
| [2] | *Conformal Prediction Under Covariate Shift*, Ryan J. Tibshirani, Rina Foygel Barber, Emmanuel J. Candès, Aaditya Ramdas | 1904.06019v3, 6 Jul 2020; 17 pp. |
| [3] | *Uncertainty Sets for Image Classifiers Using Conformal Prediction*, Anastasios N. Angelopoulos, Stephen Bates, Jitendra Malik, Michael I. Jordan | 2009.14193v5, 3 Sep 2022; 18 pp. |
| [4] | *Conformalized Credal Set Predictors*, Alireza Javanmardi, David Stutz, Eyke Hüllermeier | 2402.10723v1, 16 Feb 2024; 16 pp. |

**Identifier mismatch:** the allowed URL `https://arxiv.org/pdf/2009.14193` is [3], not a Romano-authored paper. It discusses an antecedent classifier method, but I did not fetch that antecedent or substitute any URL. BibTeX below and in `literature/references.bib` follows the actual PDFs, not the supplied informal attribution. Entries use original arXiv years and explicitly record the consulted versions; no unverified journal/venue metadata is added.

## 2. The three targets are not interchangeable

Write Δ^(K−1) = {z in R^K: z_j ≥ 0, sum_j z_j = 1}.

| Target | Output and coverage event | What is, and is not, justified |
|---|---|---|
| **Discrete outcome Y in {1,…,K}** | A set of labels C_Y(x); P{Y_new in C_Y(X_new)} ≥ 1−α. | Standard APS/RAPS-type coverage. This does **not** cover an unknown vector p*(x) = (P(Y=j given X=x))_j. A set of class indices is not a region in the simplex. [1, pp. 4–5, 7–8; 3, pp. 1–7, Eq. (1), Proposition 1] |
| **Observed composition Z in Δ^(K−1)** | A region C_Z(x) in the simplex; P{Z_new in C_Z(X_new)} ≥ 1−α. | Direct split conformal applies to exchangeable observed vectors. If Z is an annotator-frequency vector or normalized counts, the guarantee concerns that noisy observed vector, including its measurement mechanism. [4, pp. 4–6, Eqs. (7)–(10), Theorem 4.1] |
| **Latent conditional probability p*(x)** | A region C_p(x); desired event p*(X_new) in C_p(X_new). | If exact p*(X_i) is genuinely observed as the calibration response, conformal calibration over these pairs gives marginal vector coverage. With only labels or noisy compositions, that supervision is unavailable: an additional noise/identification argument is required. [4, pp. 3–6, §3–4.1] |

A first-order probability **prediction** is not an observed ground truth probability. Likewise, a Bayesian/Dirichlet distribution over vectors does not automatically supply a distribution-free frequentist confidence region for p*. The credal paper distinguishes zero-order labels, first-order probability vectors, and second-order distributions over vectors [4, pp. 3–5]. Its basic theorem assumes first-order calibration targets; §4.1 explicitly retracts automatic clean-target coverage for noisy ones.

When Z = counts/m, p*(x) can equal E[Z given X=x] under an appropriate repeated-label model, but covering a fresh Z is not the same as covering its conditional mean. Human disagreement may also reflect systematic annotator effects rather than independent draws from one categorical p*. Do not assert this generative interpretation merely from a frequency-vector dataset.

## 3. Split conformal: exact calibration rule and guarantee

Fix all model fitting and score design using a proper training/tuning partition independent of calibration. A smaller score s(x,z) denotes greater conformity. With n exchangeable calibration pairs, compute S_i = s(X_i,Z_i), and set

- k = ceil((n+1)(1−α));
- q = kth smallest of S_1,…,S_n when k ≤ n; otherwise q = +infinity;
- C(x) = {z in Δ^(K−1): s(x,z) ≤ q}.

Then P{Z_new in C(X_new)} ≥ 1−α under exchangeability of calibration and test pairs, conditional on independently fixed training. The probability averages over calibration and the fresh pair. It is **not** pointwise conditional coverage at every x, nor a statement that every realized calibration split achieves coverage ≥1−α. If scores have no ties and k≤n, coverage lies between 1−α and 1−α+1/(n+1). Ties can make deterministic coverage more conservative. [1, pp. 4–6, §1–1.1, Theorem 1; pp. 50–51, Appendix D, Theorems D.1–D.2; 2, p. 2, Lemma 1]

**Finite-sample pitfalls:** do not use an interpolated library percentile without matching this rank; retain the n+1 correction and +infinity case. If α < 1/(n+1), no finite calibration order statistic suffices. Include ties with `≤`; random tie handling requires its own specified protocol. [4, p. 5, Eq. (8)] prints a strict `<`; copying that convention into discrete/tied scores without a correction can under-cover. Count compositions and zero-distance scores make ties especially plausible.

Any fixed scalar score on the **whole vector** can be conformalized. Its validity does not require a perfectly estimated conditional density; its efficiency does depend on the model and score. Intersecting a vector region with the known simplex does not remove a valid compositional target. Separate coordinatewise intervals calibrated at level 1−α do not give joint 1−α vector coverage without a multiplicity correction or a joint max-score calibration.

## 4. Group/Mondrian calibration: useful but not universal conditional coverage

For a fixed group function G(x), calibrate a separate rank q_g within each group using n_g scores, then use C_g(x) = {z: s(x,z) ≤ q_g}. Under within-group calibration/test exchangeability this yields group-conditional coverage for each group with positive probability. Use k_g = ceil((n_g+1)(1−α)), including q_g = +infinity if k_g>n_g. The empty-group fallback is the full target space, unless another fallback has a separately justified guarantee.

This within-group construction is commonly described as group/Mondrian calibration; the tutorial calls it **group-balanced conformal prediction** [1, pp. 16–17, §4.1, Eq. (8), Proposition 1]. Its class-balanced version uses candidate-dependent thresholds q_y, giving label-conditional coverage [1, pp. 17–18, §4.2, Eq. (9), Proposition 2]. An unknown test label cannot be used to pick one threshold before evaluating candidates.

**Limits and design:**
- Predefine groups from domain knowledge or independent training data. Choosing groups or score variants by calibration/test coverage creates selection bias without further protection.
- Sparse groups force coarse quantiles and possibly full-simplex sets; report n_g, not just global coverage.
- Group validity does not imply conditional coverage at every x inside a group; arbitrary covariate-conditional coverage is generally unattainable without additional restrictions [1, pp. 12–13, §3.1, Eq. (7)].
- Overlapping-group simultaneous claims need additional methodology; the simple disjoint-group construction is not enough.
- Label-conditional coverage is about classes, not the latent coordinates of p*(x). Do not turn it into a probability-vector confidence claim.

## 5. Covariate shift: weighted conformal and its assumptions

[2, pp. 3–5, §2.1–2.2, Eqs. (4)–(10), Corollary 1] assumes source P = P_X × P_(response|X), target Q = Q_X × P_(response|X), and Q_X absolutely continuous with respect to P_X. The ratio w(x) = dQ_X/dP_X(x) is known up to a common multiplicative constant. The response mechanism must be unchanged, not merely the label marginal.

For split calibration at target x, define

p_i(x) = w(X_i)/(sum_j w(X_j)+w(x)),
p_new(x) = w(x)/(sum_j w(X_j)+w(x)).

Take the (1−α) quantile of the discrete measure

sum_i p_i(x) delta_(S_i) + p_new(x) delta_(+infinity),

and include candidates whose scores do not exceed that quantile. The test-point mass at infinity is essential. The threshold depends on x. [2, p. 5, Eq. (10)] gives the residual-interval instance; applying the same rank construction to an observed composition uses a vector score rather than a scalar residual. This is a planning extension of the general score argument, not a claim that [2] experimentally studies compositions.

**Scope limits:**
- Validity is marginal for a target-domain test pair, not conditional at each x or within every subgroup.
- Estimated weights are a practical approximation, not automatically covered by the exact known-ratio theorem. [2, p. 8, Eq. (12)] uses source-vs-target logistic regression or random forests to estimate classifier odds. The class-prior factor is constant in x and cancels in normalized conformal weights; a balanced class sample is not required for that cancellation. For a clean exact-versus-estimated comparison, independently fit the weight estimator and keep the guarantees of each variant distinct.
- Lack of support overlap cannot be repaired by reweighting. Extreme weights produce unstable, large, or full regions. Track the infinity mass and a weight-ESS diagnostic, e.g. (sum_i w_i)^2/sum_i w_i^2, without treating ESS as a replacement coverage theorem.
- Clipping weights changes the guarantee unless bias is explicitly controlled.
- For observed counts/frequencies, a changed number of annotations or changed annotator population can change Z|X, violating the assumption even if Y|X is unchanged.
- Do not combine weighted and group calibration by analogy and assert both guarantees; document the conditional density-ratio assumptions and derive the combined calibration procedure first.

**Reproducible source protocol:** airfoil self-noise data, 1,503 instances, five features, response sound pressure; 25% training/25% calibration/50% test; ordinary least squares; exponentially tilted test covariates; 5,000 repetitions; nominal 90%. Figure 2 reports unweighted shifted coverage 82.2% versus oracle-weighted 90.8%; both logistic-estimated and random-forest-estimated weights achieve 91.0% on average. Figure 1 visualizes the shift rather than the coverage results [2, pp. 5–8, Figures 1–2]. At p. 5, §3, the paper links `http://www.github.com/ryantibs/conformal/`. Availability is only paper-reported; the link was not opened. The random-forest implementation clips estimated class probabilities to [0.01,0.99] to avoid infinite weights, illustrating the distinction between a numerical safeguard and the known-ratio theorem [2, p. 8, footnote 3].

## 6. What the classifier baseline actually establishes

[3] proposes **RAPS**, regularized adaptive prediction sets, for discrete image labels. The score accumulates sorted model probabilities plus a penalty for lower-ranked classes, with a randomization term. Proposition 1 gives marginal label coverage under exchangeability and independently fixed score choices. Proposition 2 gives a set-size bound under specific regularization settings, not universal optimality [3, pp. 4–7, Eqs. (2)–(4), Propositions 1–2]. For a clean reproduction, fit temperature scaling and choose regularization on an independent tuning partition before final conformal calibration. The paper's p. 7 says temperature scaling uses “the calibration set”; do not take this implementation description as permission for unrestricted score fitting on final calibration.

Baselines include naive cumulative-probability sets after Platt scaling, LAC, and APS. Calibration of probabilities alone is not conformal label coverage. The downloaded v5 evaluates ImageNet and ImageNet-V2 at nominal coverage 90% and 95%, over **100 random splits**. It uses 20,000 calibration and 20,000 test examples for ImageNet, and 5,000 calibration and 5,000 test examples for ImageNet-V2 [3, pp. 7–8, §3.1–3.2]. Thus the ImageNet-V2 result is calibrated on its own target dataset, not an uncalibrated transfer guarantee. Section 3.2 explicitly requires calibration from the new distribution [3, p. 8]. For example, Table 1 reports ResNet-152 on ImageNet at 90%: RAPS coverage 0.900 with average set size 2.11, versus APS coverage 0.900 and size 10.4 [3, p. 7]. These are label counts, not simplex volumes.

Appendix E describes an extra tuning partition held apart from final calibration: m=10,000 for the ImageNet tables and m=1,000 for ImageNet-V2; the authors say about 1,000 is generally sufficient for the rank tuning. The same tuning partition selects k_reg and lambda, while final conformal calibration uses fresh data [3, p. 15]. Reusing final calibration for regularization selection would break that separation. Its code URL is embedded as a hyperlink on PDF p. 1: `https://github.com/aangelopoulos/conformal_classification/`. This was extracted from the allowed PDF, not visited or validated.

**Role in a composition study:** use RAPS only as a separate label-target reference if labels exist. Never rank its label-set size against a vector-region volume as if they measure the same target or uncertainty.

## 7. Credal-set paper: direct relevance and important qualification

### 7.1 Scores, assumptions, and geometry

[4, pp. 4–5, §4, Eqs. (5)–(8), Theorem 4.1] conformalizes first-order probability-vector targets into simplex subsets. Scores evaluated include total variation (TV), first Wasserstein distance (WS), KL divergence, 1 minus inner product, and 1 minus relative second-order likelihood (SO) from a Dirichlet predictor [4, pp. 5, 7, Eqs. (5)–(6), Table 1].

TV, s(x,z)=0.5 sum_j |z_j−g_j(x)|, is a useful transparent first baseline. KL requires a fixed direction and a zero-handling policy (0 log 0 = 0 for a zero target coordinate, but a positive target against a zero predicted probability is infinite). WS on unordered classes requires a defensible ground-cost matrix. An inner-product score is valid as a fixed conformal score, but its sublevel geometry is not a ball around g(x) and should not be interpreted as one. The Dirichlet mode-based relative-likelihood score must obey its parameter/mode conditions; a generic ReLU-output network does not by itself guarantee an interior, finite mode. In particular, inspect positivity and shapes at or below one before dividing by a density supremum. A score set on the simplex is not automatically convex for arbitrary score choices; verify geometry rather than inferring it from the term “credal.” The paper's construction and relative-likelihood definition are on PDF p. 4, Eqs. (5)–(6); no general convexity proposition is stated there.

### 7.2 Noisy annotation vectors are not clean probability vectors

[4, p. 6, Eqs. (9)–(10)] states explicitly that calibration on noisy vectors gives coverage for those noisy vectors only. The suggested intuition that noise may enlarge sets is **not** a formal clean-target guarantee.

The paper then assumes, for the chosen fixed score, P{|s(x,p*(x))−s(x,Z_tilde)|<epsilon} ≥ 1−delta for all x [Eq. (11)]. Theorem 4.2 calibrates the noisy target at alpha_tilde = (alpha−delta)/(1−delta) and expands the threshold by epsilon, reporting latent-vector coverage ≥1−alpha [Eq. (12)]. This requires a meaningful epsilon, delta and alpha>delta; it is not an assumption-free consequence of conformal prediction. Section 6 says selecting useful noise bounds remains difficult/open with limited noise knowledge [4, p. 9].

**Proof-level caution for planning:** Appendix A (PDF p. 13) bounds a noise-violation probability *conditional on successful noisy-set coverage* by delta, citing Eq. (11). Eq. (11), as written, bounds noise probability conditional on x, not on that additional event. Do not silently rely on this conditional-probability step without extra justification. A conservative alternative needing no such event independence is a union-bound budget: noisy-target miscoverage alpha_0 plus score-noise failure delta is at most alpha when alpha_0+delta≤alpha, with the same epsilon expansion. This elementary safety recommendation is not the paper's stated multiplicative formula, and is not a full theorem audit. Neither choice solves the practical task of establishing epsilon/delta from noisy annotation data.

### 7.3 Actionable protocols and reported limitations

**ChaosNLI:** combine chaos-SNLI and chaos-MNLI: 3,113 examples, three labels, 100 annotations per example. A pretrained `cross-encoder/nli-deberta-base` supplies fixed last-hidden-layer embeddings. Randomly split 500 calibration, 500 test, 2,113 training; repeat ten seeds. These counts and embeddings are paper-reported only; no dataset/model pages were opened [4, p. 7, §5.3]. Coverage of 100-annotator empirical vectors must be reported as observed-composition coverage, not independently validated latent p* coverage.

**Learner:** hidden sizes 256/64/16 with ReLU, dropout 0.3 before output; Adam learning rate 1e−4; softmax plus cross-entropy for first-order prediction, ReLU output plus negative log-likelihood for second-order [4, pp. 6–7, §5.1]. Check the Dirichlet parameter conditions separately when reproducing SO.

**Synthetic:** X in R^10 has independent standard-normal coordinates, beta is a 10×K standard-normal matrix, and p*(x)=softmax(x^T beta); K in {3,4,6,8,10}; N=1,500. Draw m in {1,5,10,100} categorical labels from each p* and use frequencies as noisy vectors. Train/calibration/test are equal thirds; repeat ten seeds. Nominal 90% for Figure 5. This setup permits separate noisy-vector and oracle latent-vector evaluation, unlike ChaosNLI [4, pp. 7–9, §5.4, Figure 5]. Report the paper's mostly adequate latent coverage as an empirical observation, not a general theorem for m=1.

**Metrics:** coverage plus fraction of simplex grid points in each region (the paper reports resolution 0.005 and M=19,969 points for its low-dimensional construction). For K>3 it reports the calibration-score quantile instead of volume [4, pp. 6, 8]. Quantiles in different score units are not directly comparable efficiencies. A grid fraction is only a discretization-dependent volume approximation; grid resolution, boundary treatment, and numerical membership must be documented. High-dimensional gridding is not scalable; the paper itself identifies representation and numerical cost as limitations [4, p. 9, §6].

**Code:** `https://github.com/alireza-javanmardi/conformal-credal-sets`, explicitly printed in footnote 1 on PDF p. 6. Not opened, audited, or executed.

## 8. Recommended next experiments (planning only)

1. **Target-separation benchmark first.** Reuse [4]'s synthetic generator, dimensions, m values, and 500/500/500 split. Calibrate on noisy vectors and evaluate **two** coverage events on the same test covariates: observed noisy composition and known latent p*. Add an oracle-calibration control using exact p*. This isolates what conformal calibration guarantees from what noisy supervision happens to recover. Expect reliable observed-vector marginal coverage under exchangeability; do not prespecify latent coverage as guaranteed.
2. **Minimal geometry comparison.** Hold the predictor and splits fixed; compare TV, a fixed joint max-coordinate score, and the paper's KL/SO choices with explicit boundary conventions. Include a full-simplex sanity control. Report coverage, normalized volume (or a common documented Monte Carlo volume estimator), coordinate widths and runtime. Use one fixed volume measure across methods; do not compare raw q values across scores. Treat additional score choices here as proposed controls, not claims from the sources.
3. **Group stress test.** Fix groups before calibration, e.g. annotation count or a training-defined difficulty bin. Compare pooled and within-group quantiles; report group sizes, coverage uncertainty, and full-region frequency. Expect group calibration to trade smaller-group efficiency for group validity; no per-x claim.
4. **Shift stress test.** Change only X's distribution with a known density ratio and unchanged vector-response mechanism. Compare unweighted, true-weight, and independently estimated-weight calibration. Log support overlap, weight ESS, infinity mass, coverage and efficiency. Separately shift annotation count/annotator mechanism as an intentionally invalid negative control; weighting only X should not be advertised as repairing it.
5. **Real-data confirmation after the synthetic gate.** Follow the 3,113-example ChaosNLI protocol if the dataset is later authorized. Declare the 100-annotation composition as the observed response. If latent claims are desired, add a justified sampling/noise model or additional labels and a noise-bound analysis before changing the target statement.

Across experiments, freeze all preprocessing, model fitting, hyperparameter/score selection, and any weight estimation before final calibration. Use disjoint test data and record split seeds. Report per-split coverage and efficiency, aggregation across at least the source's ten seeds, and uncertainty intervals; distinguish test-sampling uncertainty conditional on a fitted region from calibration-split variability. An interval on pooled coverage alone can hide severe subgroup or split failures [1, pp. 12–15, §3]. No multiple-seed empirical result replaces the exchangeability/noise assumptions of the claimed theorem.

## 9. Exact evidence map

- [1]: PDF pp. 1–8 (metadata, target, quantile, Theorem 1, classification); pp. 12–15 (§3, evaluation and conditional-coverage caveats); pp. 16–18 (§4.1–4.2, groups/classes); pp. 50–51 (Appendix D, Theorems D.1–D.2, rank proof). Additional locally consulted context: pp. 10–11, 20. No external references followed.
- [2]: PDF pp. 1–8 (metadata, Lemma 1, shift assumptions, Eqs. (4)–(10), Corollary 1, Figures 1–2, estimated weights, §3 code pointer). No external data/code followed.
- [3]: PDF pp. 1–9 (metadata, Eqs. (1)–(4), Propositions 1–2, protocols and Table 1); pp. 14–17 (appendix context, tuning split and algorithm notes). External links embedded in the allowed PDF were extracted locally, not fetched.
- [4]: PDF pp. 1–9 (metadata, target hierarchy, Eqs. (5)–(12), Theorems 4.1–4.2, Table 1, protocols and limitations); p. 13 (Appendix A proof and Appendix B introduction); p. 14 (additional synthetic figure). Pages 11–12 were also read while locating Appendix A; these are inside the explicitly allowed PDF, not external citing pages.

## 10. BibTeX

The complete machine-readable entries are in `literature/references.bib`. To avoid attributing an unvisited publication record, these are arXiv entries with verified authors/titles/identifiers and consulted-version notes, not invented venue/DOI records.

```bibtex
@misc{angelopoulos2021gentle,
  title = {A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification},
  author = {Angelopoulos, Anastasios N. and Bates, Stephen},
  year = {2021}, eprint = {2107.07511}, archivePrefix = {arXiv}, primaryClass = {cs.LG},
  url = {https://arxiv.org/pdf/2107.07511},
  note = {Consulted arXiv:2107.07511v6, 7 December 2022; title page 8 December 2022}
}
@misc{tibshirani2019covariateshift,
  title = {Conformal Prediction Under Covariate Shift},
  author = {Tibshirani, Ryan J. and Barber, Rina Foygel and Cand{\`e}s, Emmanuel J. and Ramdas, Aaditya},
  year = {2019}, eprint = {1904.06019}, archivePrefix = {arXiv}, primaryClass = {stat.ME},
  url = {https://arxiv.org/pdf/1904.06019},
  note = {Consulted arXiv:1904.06019v3, 6 July 2020}
}
@misc{angelopoulos2020uncertaintysets,
  title = {Uncertainty Sets for Image Classifiers Using Conformal Prediction},
  author = {Angelopoulos, Anastasios N. and Bates, Stephen and Malik, Jitendra and Jordan, Michael I.},
  year = {2020}, eprint = {2009.14193}, archivePrefix = {arXiv}, primaryClass = {cs.CV},
  url = {https://arxiv.org/pdf/2009.14193},
  note = {Consulted arXiv:2009.14193v5, 3 September 2022; not a Romano-authored paper}
}
@misc{javanmardi2024credal,
  title = {Conformalized Credal Set Predictors},
  author = {Javanmardi, Alireza and Stutz, David and H{\"u}llermeier, Eyke},
  year = {2024}, eprint = {2402.10723}, archivePrefix = {arXiv}, primaryClass = {stat.ML},
  url = {https://arxiv.org/pdf/2402.10723},
  note = {Consulted arXiv:2402.10723v1, 16 February 2024}
}
```

### Sources
[1] Angelopoulos and Bates, *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*: https://arxiv.org/pdf/2107.07511

[2] Tibshirani et al., *Conformal Prediction Under Covariate Shift*: https://arxiv.org/pdf/1904.06019

[3] Angelopoulos et al., *Uncertainty Sets for Image Classifiers Using Conformal Prediction*: https://arxiv.org/pdf/2009.14193

[4] Javanmardi et al., *Conformalized Credal Set Predictors*: https://arxiv.org/pdf/2402.10723
