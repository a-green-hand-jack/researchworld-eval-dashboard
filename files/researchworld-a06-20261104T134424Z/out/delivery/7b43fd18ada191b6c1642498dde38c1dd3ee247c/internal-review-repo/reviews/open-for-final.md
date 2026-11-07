# Checklist I will apply to the `final` pull request (as of v2)

Real LLM (external #3, #4): frozen result at materially larger K, or every real claim rescoped (title "Reliable Reporting", abstract, intro, discussion); iid arm shown; real gap vs K with Gaussian-max overlay; real-matrix check of the formula (n=50/100/200/400) with a delivered script; generator calibration check; no forward reference to results not in the delivery (the Table 3 note in v2 still says its values "are regenerated with the K=21 replay" - I did not flag this in my v2 approval; it must go in a frozen paper); the withheld real conditional/hybrid bias/RMSE cells and the coverage/width cells of those rows regenerated with the current `lib.py` (experiment-repo#16).
Protocol comparison (external #6): Table 1 note must say which configuration the split row's truth refers to.
Run times for unrecorded steps (external #11). Premise/novelty paragraph verified as closed by the external reviewer (#10).
