# Hypothesis and predictions (written 2026-11-01 after a 13-run pilot, BEFORE the main sweeps e1-e8 were analysed)

Pilot (results/pilot.jsonl, 1 seed, p=53, frac=0.5, lr=1e-3, wd=1) suggested: t_fit (first step with train acc>=0.99)
falls very quickly with width, t_gen (first step with val acc>=0.99) falls much more slowly; the smallest widths
never reach 99% train accuracy.

**Two-clocks + capacity-floor hypothesis (H).**
 (H1) Capacity floor: there is a width w_mem(n_train) below which the network cannot interpolate the training set
      (not even random labels). Delayed generalization needs w > w_mem; below it, either no generalisation within
      budget or generalisation that is not preceded by train-set fit.
 (H2) Two clocks: for widths above the floor, the memorisation clock t_fit decreases steeply with width (power law,
      |slope| large), whereas the generalisation clock t_gen is set mainly by the weight-decay / feature-formation
      timescale and depends only weakly on width (|slope_gen| < |slope_fit|). Hence the delay t_gen - t_fit and
      the ratio t_gen/t_fit INCREASE with width: scale amplifies grokking rather than removing it, while the
      absolute time to generalise may still shrink a bit.
 (H3) w_mem scales with n_train: the number of parameters needed to fit grows ~ proportionally to the number of
      training pairs (frac). The minimal width that generalises also moves with frac.
 (H4) t_gen scales roughly as 1/(lr * wd) at fixed width (the weight-decay clock) and this does not change the
      qualitative width trend.
 (H5) Generality: the sign of the width trend of t_gen/t_fit is the same for other operations (sub, mul, x^2+y^2),
      another prime (97), depth-2 MLPs and 1-layer transformers.

**Falsifiers.** H2 is rejected if the bootstrap CI of slope_gen - slope_fit includes 0 (or has the opposite sign),
i.e. t_gen/t_fit is flat or falls with width. H1 is rejected if models far below the random-label interpolation width
nevertheless fit true labels to 99% before generalising / or if random-label interpolation threshold is not
related to the train-fit threshold. H3 rejected if the thresholds do not move with frac in the predicted direction.
H4 rejected if log t_gen vs log(lr*wd) slope is not near -1 (outside [-1.5,-0.5]).
