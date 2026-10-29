# Release and final version review: approve

## Inspected revision and scope

Paper-repo pull requests #7 (`main` into `release`) and #8 (`main` into `final`) both have exact head `5825e7bcd3f33ae5ecfbed4a5900fa1ca516a7d6`. I fetched both pull-request heads and confirmed the identity using Git and the live API. This decision applies only to that head.

Re-read Research objective #1, the frozen task, my commitment, experiment-repo's Brief, and both owners' commitment issues. Read paper-repo's answer to my delivery request #2. The task is a complete program plus its executed six-score JSON; no manuscript, figures, statistical inference, or external references are requested.

Inspected every file at the exact head:

- `.forgejo/CODEOWNERS`: experiment-repo owns the allocation and both program/results directories; paper-repo owns the venue declaration, consistent with the settled split.
- `README.md`: initial role identification, with no scientific claims or unresolved artifacts.
- `venue-artifacts.json`: valid JSON declaring both exact required user artifacts, both present and nonempty.
- `workspace/pred_programs/pred_h_importances.py`: complete Python implementation, source read in full. Four correctly named input files; first/second columns; plain dot products without normalization; pooled versus group-specific denominators as requested; output directory creation; native float JSON serialization; executable entry point.
- `workspace/pred_results/jnmf_h_importances.json`: valid JSON, all six verbatim factor names mapped to finite numbers.

The full tree has no figures, tables, report, symlinks, placeholders, copied inputs, or protected task metadata. No delivered visual remains to inspect. Both requested absolute task paths resolve correctly through the world's delivered-root mapping. As documented, run from `/workspace` to obtain `/workspace/pred_results/jnmf_h_importances.json`.

## Execution and independent arithmetic

Archived the exact head into `/hutian/review-paper-5825e7bc` and ran in the foreground:

```text
python3 checks/verify_delivery.py /hutian/review-paper-5825e7bc
```

The checker invokes the exact delivered source in a fresh temporary working directory with the default frozen dataset path, so no existing output can substitute for a successful run. It succeeded without an environment restart or additional packages, created the relative requested JSON, and regenerated exactly the same dictionary as the delivered output.

Independent arithmetic uses scalar Python lists and `math.fsum` for sums/products, with no calls to the program's computation or its NumPy sum/dot implementation. All six values agree within 3.34e-16 absolute difference, below the 1e-12 review tolerance. Common and distinct importance sum to one within floating-point precision. The run log `paper-5825e7bc-check.log` records each score, independent reference, input SHA-256 hashes, actual matrix shapes, and Python/NumPy versions.

The required system status on this exact head is `hutian/delivery: success`; the recorded live status summary is `paper-5825e7bc-status.json`. Both target branches and open head identities were checked live before the approval record.

## External-reader judgement and decision

The output dictionary directly answers each of the six requested quantities. Each number can be checked against the supplied data by running the complete delivered program. No interpretation requiring inference or additional evidence is attached to the output. Literal factor names are appropriate because the objective specifies no other key convention. Relative output is appropriate under the explicitly documented `/workspace` invocation.

No open actionable findings or unmet objective requirements. Approve both #7 and #8 at the inspected head after this record is pushed. Assembly/release merges remain paper-repo's responsibility and must use merge commits; this review does not perform them.
