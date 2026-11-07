# Cross-fitted generalized-difference candidate

Status: independently implemented candidate; no claim of prior-art novelty. Standard generalized-difference estimation with a source item-mean predictor is a necessary baseline. Estimator code is `src/benchsmall/estimators.py`; the finite-enumeration check in `tests/test_design.py` verifies the unbiasedness identity under a deliberately unrelated source/target pair.

Let a finite benchmark contain N items and let a new target model have fixed binary outcomes y. A uniform ordered sample S of size k is randomly partitioned into disjoint A and B. Conditional on A, B is a simple random sample from U = all items outside A. Use the source response matrix and observed target responses y_A to produce predictions f_j(A,y_A) for j in U. Then

    T(A,B) = [sum_{j in A} y_j + sum_{j in U} f_j
                + (N-|A|)/|B| sum_{j in B}(y_j-f_j)] / N.

Conditional on A and y_A, the expected residual total over random B equals the exact residual total over U. Therefore E[T(A,B)|A] equals the true full benchmark mean. Average T(A,B) and T(B,A) to use both fits. This does not require source and target models to have the same response distribution; it also does not guarantee small variance, good realized scores, or accurate rankings. Both estimators can predict outside [0,1]. Clipping is an explicitly biased ablation, not part of the unbiased estimator.

Our imputer is multi-output ridge with an intercept, learned from source models: regress each item on source responses at A, then insert target responses y_A. Because ridge is linear in its output, it suffices to regress mean(source outcomes in U) minus mean(source outcomes in B) on source outcomes at A. This computes the identical aggregate without materializing an item-by-item predictor.

Crucial assumptions: S must be uniform without replacement and the split into A/B random. The source matrix is fixed, and the imputer (including regularization) must not depend on B's sampled identities or y_B except through the explicit residual correction. Thus tuning regularization using validation performance on the same realized A/B would invalidate the conditional proof. For full experiments regularization must be selected in advance using independent development item samples, or only from A. A full-source-data hyperparameter choice fixed before evaluation sampling is permitted. Pilot results over a grid are development comparisons and do not assert unbiasedness of an adaptively selected same-sample estimator.

The comparator source-difference estimate is source_mean + mean_{j in S}(y_j - source_item_mean_j), also design-unbiased under uniform sampling. An exact conditional advantage over random mean requires lower across-item variance of these residuals; source assistance is not universally helpful. The study must compare both and report when correction increases error.
