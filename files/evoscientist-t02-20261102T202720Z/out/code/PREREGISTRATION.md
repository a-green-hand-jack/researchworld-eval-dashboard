# Hypotheses and predictions (written before the main sweeps were run)

Status of prior information: a 10-run exploratory pilot (`pilot.py`, seed 0, p=53, results/pilot.jsonl) was run
before this file was finalised. It showed (single seed, treat as anecdotal): at train fraction 0.5, d>=32 reach 99% train
accuracy within a few hundred steps and reach 99% validation accuracy 1.2k-3k steps later; d=16 and d=8 fit the training set
(or nearly so) while validation accuracy rises concurrently, then saturates below 99%; at train fraction 0.3 no width
reached 99% validation accuracy within 20k steps. The main sweeps use seeds 1-5 (disjoint from the pilot seed 0).

## Explanation under test: "capacity-gated delay"

Let N = number of training pairs, p = modulus, n = number of trainable parameters.
Memorising N random labels needs ~ N log2 p bits (Morris et al. 2025 estimate ~3.6 bits/parameter for LMs, a heuristic
only). Hypothesis H: *the delay between fitting the training set and generalising is created by spare capacity.*
A model with n well below ~N log2 p / c cannot afford a lookup-table solution, so the only way it lowers training loss is
by learning shared structure, and training and validation accuracy rise together (no delay; possibly incomplete
generalisation because it is also too small to represent the full algorithm). A model with n >> N log2 p / c memorises
quickly and then must be pushed by weight decay to the (more efficient) general circuit, which takes long: delay grows
with excess capacity rho = n / (N log2 p).

Metrics (all in optimiser steps, full-batch AdamW): T_fit = first step with train acc >= 0.99; T_v(tau) = first logged
step (every 50 steps) with val acc >= tau; delay ratio D(tau) = T_v(tau) / T_fit (censored at the step budget if never
reached). A run "groks" if D(0.99) >= 3 with T_v(0.99) observed.

## Falsifiable predictions (primary = P1, P2; secondary = P3-P5)

* P1 (width monotonicity of the delay): at fixed task and train fraction, D(0.9) is non-decreasing in width d, and at the
  smallest widths D(0.9) is close to 1 or undefined (val never reaches 0.9) whereas at the largest widths D(0.9) >> 3.
  Falsified if D(0.9) is flat or decreasing in d (Spearman correlation between log d and log D not significantly
  positive across seeds-aggregated cells).
* P2 (T_fit shrinks with width, T_gen less so): T_fit decreases with d; T_v(0.99) decreases more slowly than T_fit (so
  the delay ratio grows). Falsified if T_v(0.99) falls at least as fast as T_fit.
* P3 (data-scaling of the threshold): the width/parameter count at which D(0.9) first exceeds 3 scales roughly
  proportionally with N (log-log slope of n* vs N in [0.5, 1.5]); equivalently curves of D vs rho = n/(N log2 p) collapse
  better than curves of D vs n. Falsified if n* is independent of N (slope ~0) or the rho-collapse is no better than
  the n-collapse. N is varied (a) by train fraction at p=53, (b) by modulus p at train fraction 0.5.
* P4 (architecture): P1 holds for a 2-hidden-layer MLP on concatenated embeddings.
* P5 (robustness): the qualitative width trend of P1 survives changing weight decay (0.3, 3), init scale (0.5, 2) and
  the operation (subtraction, multiplication).

Alternative explanations the data can favour instead: (A1) delay is set by optimiser timescales (lr*wd) and not by
capacity - would predict that the width trend of D vanishes or reverses when wd changes; (A2) larger width makes the
generalising circuit easier to find (lazy->rich, Kumar et al.), so T_v(0.99) falls with d at least as fast as T_fit and
D is flat or decreasing (opposite to P1/P2).

All analyses of these predictions are in `analyze.py`; any analysis not listed here is labelled exploratory in the paper.
Multiple-comparison note: P1-P5 are 5 pre-specified families; Holm correction is applied across the primary tests.
