# jnmf_visualization importance factors

Delivered tree (paths relative to the caller's root `/`):

- `workspace/pred_programs/pred_h_importances.py` — the requested program. It loads
  `fit_result_conscientiousness_{W_high,W_low,H_high,H_low}.npy` from
  `/benchmark/datasets/jnmf_visualization/` (falling back to the relative
  `benchmark/datasets/jnmf_visualization/`), computes the six factors exactly as the
  task defines them, and writes `pred_results/jnmf_h_importances.json` relative to
  its working directory (`/workspace`). Requires only NumPy and the standard library.
- `workspace/pred_results/jnmf_h_importances.json` — the output of running
  `cd workspace && python3 pred_programs/pred_h_importances.py` on the supplied
  dataset (NumPy 2.4.6, Python 3.11.2).

Input shapes: W_high, W_low 576×2 (columns are unit-norm to ~1e-6); H_high 46×2;
H_low 60×2. As a consistency check, common importance + distinct importance = 1,
since H has two columns.
