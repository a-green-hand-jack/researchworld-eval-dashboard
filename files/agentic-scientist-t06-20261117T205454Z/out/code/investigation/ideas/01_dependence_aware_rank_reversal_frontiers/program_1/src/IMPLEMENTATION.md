# Dependence-aware influence candidate

## Supported mechanism

The RPC interface is unchanged. A centered Bradley--Terry fit uses the supplied
mean-loss ridge penalty, half-win ties, and all observed pairs. Repeated directed
pairs are compressed into sufficient statistics only during fitting; row keys
and individual outcomes remain intact for influence sorting and export. A
Newton fit with Cholesky solves and backtracking must satisfy a gradient
infinity-norm threshold of `1e-9` before its certificate is exported.

For every clean nonleader, the program solves the prescribed contrast against
the same clean Hessian, computes every row's deletion influence, and orders by
influence rounded to ten decimal places then by the stable row key. Budgets are
exactly the three required floored row counts. The chosen contender's deletion
sets are unmodified nested prefixes; there is no iterative order refinement.

The predeclared contender rule compares clean-Hessian predictions across those
three prefixes. For removed set S of size k from n rows, with row gradients g,
the predicted parameter displacement is

`H^{-1} (sum_{i in S} g_i + k * regularization * theta) / (n-k)`.

The penalty correction follows from retaining the contract's mean loss, not a
sum loss. All predictions use the original fit, original leader, and original
Hessian. They do not refit or retarget after deletions. The selection criterion,
in lexicographically descending order, is:

1. Sum of predicted original-leader rank drops over the three budgets.
2. Number of predicted leader-versus-that-contender gaps below `-1e-8`.
3. Sum of relative target-gap closure, individually clipped to `[0, 2]`, with
   denominator `max(original_gap, 1e-8)` to handle rounded ranking ties.
4. Earlier position in the deterministic original ranking.

This is a network-aware linearized search heuristic, not a reversal certificate,
an optimum, or an uncertainty assessment. Mean-loss rescaling is included only
in contender screening; exported direction and influence obey the unmodified
contract exactly. All output keys, shapes, chunking, reset, release, and token
semantics are inherited from the starter. No diagnostics enter RPC responses.

## Unsupported parts of the research idea

Inputs contain only participant IDs, outcomes, and unique row keys. A row key
is never treated as a question, judge, or session identity. There is no support
for identifying Arena versus MT-Bench, matching questions or turns, clustered
deletion, clustered bootstrap, or reporting confidence intervals. The required
mean-loss objective is not silently replaced by the proposed fixed sum-loss
ridge objective. The allowed budgets are not extended to a research grid.

No data were downloaded, scientific experiments run, literature retrieved,
paper generated, or empirical improvement claimed. The stage forbids project
execution and provides no artifact channel for a paper. Actual deletion
refitting and evaluation belong to the external harness; linear predictions
here must not be reported as their results. No evaluation was launched and no
test, benchmark, or project module was executed during implementation.
