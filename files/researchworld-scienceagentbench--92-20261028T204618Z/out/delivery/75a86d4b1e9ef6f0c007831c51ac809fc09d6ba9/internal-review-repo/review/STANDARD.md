# Review standard (internal-review-repo)

Objective: internal-review-repo#1 (task frozen at /initial-state/inputs/0/INSTRUCTIONS.md).

A version is approved only if, at the pull request head of `paper-repo`:

1. `workspace/pred_programs/pred_h_importances.py` exists, is a complete standalone Python program,
   reads the four `.npy` files from `/benchmark/datasets/jnmf_visualization/`, and writes
   `pred_results/jnmf_h_importances.json` (under `/workspace/pred_results/`, creating the directory).
2. Running it (`python3 -I`, foreground, stock scientific stack only) succeeds without error.
3. The JSON is a flat dictionary with exactly the six factor names of the task
   ("common error", "common importance", "high importance", "low importance",
   "distinct error", "distinct importance") mapped to JSON numbers (plain floats, not strings/arrays).
4. Each value matches the independent recomputation in `review/reference_check.py`
   (rtol 1e-9) and follows the task's definitions literally: e.g. "common error" = 1 - <W_high[:,0], W_low[:,0]>,
   "distinct error" = <W_high[:,1], W_low[:,1]> (no "1 -"), no extra normalisation of W or H.
5. Inputs and INSTRUCTIONS.md are not overwritten; no hard-coded result values in the program.
6. If the delivered tree also carries `workspace/pred_results/jnmf_h_importances.json`, it must equal the program's output.

Reference values (measured 2026-10-28 from the dataset, see reference_values.json.txt):
common error 0.019074017463533988, common importance 0.6769477302939783,
high importance 0.2983605570114919, low importance 0.3425926412464023,
distinct error 0.005405837429051289, distinct importance 0.32305226970602163.
