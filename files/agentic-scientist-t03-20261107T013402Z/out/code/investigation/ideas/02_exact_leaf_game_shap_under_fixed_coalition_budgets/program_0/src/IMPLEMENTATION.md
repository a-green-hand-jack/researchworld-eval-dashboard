# Fixed-budget single-call audit

This candidate preserves the starter RPC operations and exact response keys.
Only the supplied frozen model, original scalar-encoded feature groups, query,
background and budget are used. No reference target or additional request field
is assumed. The unchanged starter `kernel_shap` function remains available as
the original baseline; the response path uses `explain_fixed_game`.

## Budget and estimation

For a nonexhaustive budget `b` and `d` features, preallocate
`floor(b / (4*(d-1)))` independent uniform complete permutation paths, provided
this is at least two. A path costs `d-1` nontrivial coalition observations.
Allocate the remainder to kernel-distributed subsets with complement pairing.
Pairing is used only for regression, never for the independent path bound.
The total sampled nontrivial coalitions is at most `b`; query-local deterministic
caching can reduce the actual prediction count. Empty/full endpoints are not
nontrivial coalitions. Every coalition averages the entire supplied background.
No new background is sampled. A fixed quarter allocation is an untested design
choice, not a measured optimum; it can reduce fidelity relative to the starter.

Path prefixes are uniform over subsets conditional on size, with uniform size
frequency. Kernel samples have size probability proportional to `1/(s*(d-s))`.
Importance weights correct this mixture for the kernel objective. An orthonormal
sum-zero basis imposes efficiency without privileging the final coordinate in
underdetermined least squares. Regression coefficients carry no certificate.

If the budget covers every nontrivial subset, compute exhaustive original-column
Shapley values with an efficiency assertion. This exact estimate is not an
independent reference experiment. Affine fixtures use their analytic solution.
All forest predictions retain the starter's float32 input comparison semantics.

## Certificate and scope

For a fixed game each coordinate of an independent path marginal vector lies
in `[-1,1]` and has expectation equal to its Shapley value. Apply the two-sided
empirical Bernstein bound for range width two, with conservative logarithm
`log(4*d/alpha)`, and union-bound the coordinate failure events. The radius is
`sqrt(2*s_j^2*log(4*d/alpha)/m) + 14*log(4*d/alpha)/(3*(m-1))`.
On simultaneous coverage, strict separation between selected lower absolute
bounds and excluded upper absolute bounds identifies the exact absolute top-k;
selected intervals excluding zero establish signs. Stable original-column order
breaks estimated ties; a true boundary tie cannot pass the strict criterion on
the coverage event. Here `k=min(3,d-1)` and `alpha=0.05` are fixed in advance.

The wrong-certificate probability is at most alpha per prespecified fixed-game
call. It is not a bound on conditional accepted-call error, simultaneous error
across RPC calls, background sensitivity, causal validity or fairness. Nothing
is certified about fallback regression outputs. When accepted, the returned
vector is the certified path mean, not the regression vector. A conservative
bound may never accept under these budgets; no coverage is claimed.

## Unavailable research mechanisms and validation

The transport contains already encoded columns, not raw pandas data or a frozen
preprocessing pipeline. Consequently this implements masking of the supplied
groups, not the proposed raw-data masking API. The harness supplies neither
dataset identities and splits nor per-instance reference failures. No German,
ACS or Pima experiments, independent reference study, bootstrap confidence
interval, paper, figures or performance improvement are claimed. The RPC has no
certificate/artifact response field, so decisions and measured prediction-row
counts remain internal to the query-local computation and are not persisted.

No candidate code, tests, benchmark, network access, literature search or
evaluation was executed during preparation, per the stage restrictions. Runtime
checks cover bounded path increments, complete-path efficiency and exhaustive
efficiency when those branches are exercised later; these are not a substitute
for additive-game tests or independent statistical validation. No external
literature was accessed and no prohibited paper was encountered.
