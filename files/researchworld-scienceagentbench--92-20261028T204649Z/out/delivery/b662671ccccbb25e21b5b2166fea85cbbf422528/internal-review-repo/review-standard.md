# Review commitment

The frozen objective is `/initial-state/inputs/0/INSTRUCTIONS.md`, also reproduced in issue #1. This is a deterministic programming task; no report, literature comparison, figure, statistical fit, or uncertainty estimate is requested.

I own independent internal and external review, including the exact head of every proposed release/final version. I will not supply the production implementation or replace the analysis owner's results.

## Acceptance standard

- The delivered tree contains a complete, nonempty executable Python program at `workspace/pred_programs/pred_h_importances.py` and its generated JSON at `workspace/pred_results/jnmf_h_importances.json`.
- The program loads all four supplied `.npy` files from `/benchmark/datasets/jnmf_visualization/`, uses the first and second **columns**, and applies the six formulas verbatim. It does not normalize W or substitute row sums or per-matrix denominators for pooled denominators.
- The dictionary contains the six factor names and finite numeric JSON values. Its common/distinct errors are respectively one minus the first-column dot product and the second-column dot product. Its H importance scores use the denominators stipulated in the objective.
- I inspect the production source at the proposed exact commit, run it in the foreground against the supplied data, parse the JSON, and compare all six values to a separately expressed reference computation at floating-point tolerance. I check the delivered JSON matches regenerated output and the documented/default output path matches `/workspace/pred_results/` when deployed.
- The source actually computes from input files, makes output directories as needed, and serializes ordinary numeric values. The program must run successfully with compatible dependencies without a restarted environment.
- The delivered tree preserves inputs and any relative links. Any delivered explanatory claims, tables, or figures must resolve and agree with the evidence; I will open every delivered figure if any are added. None are required by this objective.

Review records will identify the exact inspected paper-repo commit, input provenance, commands/checks and result, every unresolved actionable finding, and the approval decision. Approval follows the pushed review record and is given only to the inspected head.

## Coordination

Experiment-repo owns the study plan, formula interpretation, numerical validation, and proposed path allocation. Paper-repo owns assembly and version proposals. I request their settled split and usable implementation/validation evidence before judging a version. Review records remain in this repository; no review-only file is required in the user's delivered tree.
