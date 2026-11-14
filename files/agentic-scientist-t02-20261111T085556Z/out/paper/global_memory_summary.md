# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T00:00:00Z | step=idea | scope=idea
  - summary: Selected memorization-capacity crossover hypothesis: delay = t_gen - t_mem, t_mem falls fast with width, t_gen weakly; critical width d*(f) ~ linear in train fraction. gate=kept; trigger=none; reason=no results yet to distill.
  - evidence: Alternatives: lazy-to-rich monotone decrease, circuit-efficiency wd-scaling. Chosen for multiple quantitative falsifiable predictions and CPU-cheap sweeps.
- unknown_ts | step=implement | scope=unknown_scope
  - summary: program_1: last-position-only forward (equivalent), init scale 0.5, added offline grok_sweep.py; not evaluated
  - evidence: (missing evidence)
- 2026-11-11T10:29:17.046949+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.7976868327402136, correct=True; scientific acceptance passed; search metrics (data): {"censored_fraction": 0.6666666666666666, "combined_score": 0.7976868327402136, "control_max_val_acc": 0.022775800711743774, "correct": true, "final_val_acc_mean": 0.9805456702253854, "missing_episodes": 0}
- 2026-11-11T11:00:00+00:00 | step=idea | scope=idea
  - summary: Selected width-aware output scaling (muP-like) idea; gate=kept; trigger=none; reason=no refinement from single evaluation
  - evidence: cycle1 score 0.7977, censored_fraction 0.667
- unknown_ts | step=program_1_implemented | scope=unknown_scope
  - summary: (missing summary)
  - evidence: (missing evidence)
- 2026-11-11T10:40:37.986318+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.828466629206468, correct=True; scientific acceptance passed; search metrics (data): {"censored_fraction": 1.0, "combined_score": 0.828466629206468, "control_max_val_acc": 0.02206405693950178, "correct": true, "final_val_acc_mean": 0.9443653618030842, "missing_episodes": 0}
- 2026-11-11T10:41:41.606966+00:00 | step=idea | scope=idea
  - summary: Selected hidden-layer W=m*V reparametrization (effective-LR confound) idea; gate=kept; trigger=none; reason=no new evidence warranting conclusion update
  - evidence: rubrics: incumbent_score_improvement(metric), hidden_layer_reparametrization(implementation), effective_lr_ablation_sweep(implementation)
- 2026-11-11T10:42:50+00:00 | step=implement | scope=attempt
  - summary: Added HIDDEN_EXP=0.5 W=hid_mult*V reparametrization (qkv/proj/fc1/fc2) to src/program.py; rewrote src/grok_sweep.py for hidden_exp sweep with bootstrap slopes. No code executed.
  - evidence: (missing evidence)
- 2026-11-11T10:52:10.869397+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.8501467191109446, correct=True; scientific acceptance passed; search metrics (data): {"censored_fraction": 0.6666666666666666, "combined_score": 0.8501467191109446, "control_max_val_acc": 0.022775800711743774, "correct": true, "final_val_acc_mean": 0.9214709371293001, "missing_episodes": 0}
