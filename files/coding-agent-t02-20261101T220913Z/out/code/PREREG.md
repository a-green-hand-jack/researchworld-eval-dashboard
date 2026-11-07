# Pre-registered hypotheses (written while E1 main width sweep was running, before any E1 result was inspected)

Exploratory pilot (1 seed per width, 1-layer transformer p=59 frac=0.4 lr=1e-3 wd=1, `results/pilot2`) was run
*before* this file. It suggested: larger widths fit training data very early (<=100-200 steps) and generalise
earlier in absolute steps; the smallest widths (8,16) fit and generalise jointly (val acc 0.6-0.8 at train fit)
without a long plateau; width 32 was slow. The hypotheses below were formulated after seeing that pilot, so the
*direction* in (S) is not a blind prediction; it is tested on 8 fresh seeds, plus other p / frac / architectures.

Notation: N = #train pairs, P = #parameters, t_fit = first step train acc>=0.99, t_gen = first step val acc>=0.99 (sustained),
D = t_gen - t_fit, R = t_gen/t_fit, "memorise-first" = val acc < 0.5 at t_fit.

H-CAP (capacity threshold). Memorising N random-ish labels needs ~ N log2 p bits, so P must exceed a critical P_mem(N) ∝ N log p.
  C1: below some critical width no run is memorise-first (they either never fit or fit while already generalising); above it, memorise-first runs appear.
  C2: P_mem estimated across (p, frac) grows with N with log-log slope in [0.7, 1.3].  Falsified if slope < 0.3 (threshold set by circuit size, not N)
      or the critical width does not move with N at all.
H-SPEED (above the threshold, bigger is faster).
  S1: at fixed (lr, wd), t_gen decreases with width: log-log slope of median t_gen vs P is negative with a bootstrap CI excluding 0.
  S2: S1 survives per-width tuning of lr (and wd): the best-of-grid t_gen still decreases with width.  If it flattens/reverses, the S1 trend is an optimiser-parametrisation artefact.
  S3: R = t_gen/t_fit *increases* with width (grokking looks more dramatic) even though D decreases, because t_fit falls faster than t_gen.
H-GEN (scope). The qualitative picture (S1,S3) also holds for (a) an MLP, (b) other moduli p / train fractions, (c) deeper transformers.
  Reported as supported/refuted per setting; a refutation in any setting narrows the claim.

## Addendum (written after E1 was ~90% complete and E1 curves were inspected for weight norms; E2/E3/E5 not yet analysed)
Compute note: the container is cgroup-limited to 4 CPUs (cpu.max=400000/100000), not the 40 that nproc reports; all sweeps use 4 single-thread workers.
Post-hoc observation in E1: total parameter L2 norm at t_gen is nearly width-independent (about 26-34 for P from 1.8e3 to 2.1e5) while the
norm at t_fit grows with width (24 -> 48). Hypotheses derived from this observation, to be tested out-of-sample:
  H-NORM.  Generalisation sets in when the *total* parameter norm decays to a critical value that depends on the task/data (N) but not on width.
  M1: ||theta|| at t_gen is invariant to width and to (lr, wd) in E2 (CV across conditions < 20%); a "critical per-parameter RMS" alternative (norm ∝ sqrt(P)) is rejected by the E1 data already.
  M2 (causal, E5): rescaling all parameters by c at the first step where train acc >= 0.99 shifts t_gen - t_fit monotonically (c<1 earlier, c>1 later) at every width.  Falsified if the delay is insensitive to c.
  M3 (clock, E2): at large widths t_gen * lr * wd is roughly constant across the (lr, wd) grid, i.e. log-log slope of t_gen vs lr*wd within [-1.3,-0.7].
