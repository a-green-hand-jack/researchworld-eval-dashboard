# Pre-registration of hypotheses and predictions (written BEFORE the confirmatory sweeps e1-e7 were run)

Provenance: an exploratory pilot (seeds 0-2, p=53, MLP widths 16-256, 30k steps; transformer pilot still
running at time of writing) produced the *qualitative* pattern that motivates the hypotheses below
(pilot MLP: t_train 750/215/90/40 steps and t_val >30k/>30k/~25k/~17k steps for widths 32/64/128/256).
The confirmatory sweeps use fresh seeds (100+), a wider width range, and additional conditions, so the
pilot-derived directions are re-tested out of sample. Exploratory pilot results are reported as such.

## Explanation under test ("two-clock account")
Grokking delay is the gap between two clocks that depend on scale differently.
* Memorisation clock t_train(w): how fast the model can fit the training labels. It is limited by
  memorisation capacity/speed and gets *faster* with width (more parameters per training example).
* Generalisation clock t_val(w): when the (weight-decay-driven) transition from the memorising solution
  to the generalising one completes. It is set mainly by the optimiser time scale 1/(lr*wd), only weakly by width.
Consequences:
* P1. t_train decreases monotonically with width (log-log slope < 0) in the range where training labels can be fit.
* P2. Relative delay R = t_val/t_train INCREASES with width, while the absolute delay t_val - t_train does
  NOT increase with width (it is flat or decreasing). Hence "grokking is more pronounced at larger scale"
  is true or false depending on whether delay is measured relatively or absolutely.
* P3. Capacity threshold: grokking requires the model to be able to memorise. The smallest width at which
  random labels on the same training set can be fit within budget predicts the smallest width at which
  real labels are fit (within a factor of 1.5 in width), and both thresholds move to larger width as the
  training fraction grows (0.2 < 0.3 < 0.5). Random-label fitting time should track real-label t_train
  across widths (Spearman rho > 0.8 on log scale).
* P4. Optimiser time scale: at fixed width, t_val depends on lr and wd mainly through lr*wd:
  log-log slope of t_val vs lr*wd in [-1.3, -0.7]; and pairs with equal lr*wd (lr differing 4x) have t_val within a factor 1.5.
* P5. Generality: P1 and P2 hold (same sign) for sub, mul, a^2+b^2 and for p=97.
* P6. Architecture: the transformer shows the same P1/P2 signs.
* P7 (exploratory, no directional prediction beyond "not invariant"): changing the width-dependence of lr
  (lr ~ 1/w) changes the width trend of t_train/t_val, i.e. the scale effect is parameterisation dependent.

## Falsification criteria
P1 falsified if t_train is non-decreasing in width over >= 3 consecutive grid points with CI excluding the trend.
P2 falsified if R does not increase with width (Spearman <= 0 over widths above the capacity threshold) or if absolute delay increases monotonically with width.
P3 falsified if thresholds differ by more than a factor of 1.5 in width or do not shift with data fraction.
P4 falsified if slope outside [-1.3,-0.7] or equal-product pairs differ by more than 1.5x.
Primary metrics: t_train, t_val (first eval with acc >= 0.99; censored at max_steps), R, absolute delay.
Uncertainty: median over seeds with bootstrap 95% CI (seed = init + train/val split); censored runs treated as lower bounds.

## Addendum (written after e1-e4,e6,e8-e10 were seen, before e11 was run) -- EXPLORATORY
Observed after the main sweeps: t_val(w) has a local log-log slope that is steep at small width (about -2 between 96 and 128)
and flattens at large width (about -0.3 between 256 and 512), suggesting that t_val saturates at a scale set by the optimiser
time scale at large width. Prediction P8 (exploratory, post hoc): at w=384, raising lr from 1e-3 to 2e-3, or wd from 1 to 3,
reduces median t_val by a factor >= 1.4 (baseline from e1_mlp_width, seeds 100-105). Falsified if the factor is < 1.4 for both.
