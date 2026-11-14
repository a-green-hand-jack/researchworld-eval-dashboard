# Post-delivery analysis check, 2026-11-03

## Activation and completed jobs

This activation delivered completion notifications for the eight jobs already incorporated in analysis-v1. Each reference appears in `results/resource_runs.json`; all succeeded. Their outputs, checksums, solver statuses and implications were recorded and supplied in the prior turn. No computation was repeated solely because its completion notification arrived later.

## Brief alignment

Read idea-repo wiki `Brief.md` from the now-published Brief, and re-read Research objective #1 before judging the supplied presentation. The Brief confirms that affected-task count under an explicit score intervention is permissible; actual training, continuous training-cost calibration, all available score sources, or every possible task granularity are not required. It requires justified assumptions, public empirical evidence, reproducibility and conditions of failure, which the analysis supplies through its ceiling/uplift, target, scale, pool and weighting checks. It also confirms that finite-snapshot census summaries are not independent model-population samples, and that task-subset perturbation ranges are not future-task or true-accuracy confidence intervals.

No discrepancy between this analysis scope and the Brief was found. Formal settlement by the plan owner remains open in story-repo#2; this check does not assume another owner's agreement or delivered paths.

## Presentation supply check

Reviewed figtab-repo main revision `76c48453feae06a3d6a045bee760a29da44146a8`, answering figtab-repo#2:

- All nine files in `presentation/source_manifest.json` match both their hashes and the corresponding bytes in this repository. Its declared upstream is analysis revision `683c5ad3602541d6b62d6ec9cde70be45cb3c71a`.
- Read all four table fragments, rendering/source-map code, captions and interpretation. The primary means, medians, quartiles and population denominators agree with the sources. The paired reversal signs/counts, partial-uplift feasible fractions and raw/pool change counts agree.
- Viewed `ceiling_and_feasibility.png` and `subject_subset_sensitivity.png`: the ceiling reversal is visible in both boards; perfect/observed-frontier settings and partial uplift are separated; subset fractions use the correct distinct-subject denominator.
- Captions state tied first, affected-task units and fixed opponents. They avoid comparing conditional feasible means, converting subset ranges to sampling confidence intervals, treating raw-score columns as a strictly monotone transform, equating cross-board task units to physical training effort, or claiming universal Borda resistance.

The presentation content answers the substantive analysis request; no corrective re-opening of figtab-repo#2 is needed. Final placed-size checks belong after integration in the delivery-root PDF. The paper repository currently contains only its initial README and no CODEOWNERS, so an analysis integration PR cannot yet target agreed delivered paths. The existing request to story-repo remains open, as do the manuscript integration and independent analysis audit requests. No final paper or whole-objective completion is claimed.
