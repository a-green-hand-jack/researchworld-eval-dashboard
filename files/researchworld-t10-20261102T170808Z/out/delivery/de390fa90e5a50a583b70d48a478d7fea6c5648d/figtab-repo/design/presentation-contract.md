# Presentation contract

Status: design only; no measured results have yet been supplied. This is working material, not a delivered figure or table. Ownership is recorded in figtab-repo issue #2; input requests are story-repo #3, experiment-repo #3, venue-repo #2.

## Objective and claims to expose

The frozen objective asks whether intervals can narrow further with labeled observations, unlabeled observations, and a predictor held fixed across compared procedures, while retaining nominal repeated-sampling coverage. Figures must support both the benefit and its conditions, including no gain and failure. The target parameter, sampling law, methods, and guarantee scope come from the analysis and plan owners; presentation does not choose a different inferential problem.

Each result panel must identify its data-generating regime or dataset, estimand, labeled sample size n, unlabeled sample size N, nominal coverage, and repetition count R, in the panel or an unambiguous shared caption. Distinguish fixed within a repetition/across methods from repeated sampling across repetitions; do not describe repeated draws as conditioning on one immutable sample.

## Proposed display family, subject to results and study plan

1. Main paired comparison: aligned coverage and relative-width panels with a common method/scenario ordering. Coverage uses points and Monte Carlo intervals with a labeled nominal reference. Relative mean width uses a reference at 1, clearly names the baseline, and shows paired Monte Carlo uncertainty. Coverage and width remain adjacent so a narrow but under-covering procedure is visible.
2. Conditions and limitations: small multiples over the study's ordered regime parameter (e.g. label count or predictor quality), preserving axis scales across comparable panels. Show the entire tested range, including no-benefit, poor-predictor, and misspecified regimes when those are run. Do not interpolate unsupported settings or select panels solely for the largest gain.
3. Compact results table: absolute mean width in target units, relative width, empirical coverage, uncertainty definitions, R, and n/N. A table can be the primary evidence when there are too few conditions to warrant a figure. Full condition-level results belong in an appendix table if the main display selects conditions.

A method-assumptions comparison table can be rendered if the plan/report owners provide verified content; literature interpretation remains theirs.

## Statistical rendering conventions

- Coverage is hits/R. Use analysis-supplied binomial Monte Carlo intervals with named construction and level, or construct Wilson intervals from integer hits and R solely as a display summary. Their probability concerns Monte Carlo estimation of coverage, not the target-parameter interval. Do not confuse the two.
- The nominal reference is a target, not evidence of exact validity. A point estimate near it or an interval crossing it does not establish a finite-sample theorem. Any tolerance or formal coverage test must be prespecified/approved by the analysis owner; figures will not silently invent one.
- Relative mean width means mean(width_method)/mean(width_baseline), estimated from paired repetitions. It is not mean(width_method/width_baseline); the latter weights small baseline widths differently. Label any alternative explicitly.
- Pairing must survive every uncertainty computation. Prefer analysis-supplied paired bootstrap or delta-method intervals for ratios/differences; keep resampling unit and level in the caption. Do not calculate uncertainty by treating methods' repetitions as independent.
- If width is unbounded, undefined, or a run fails, preserve that outcome and expose its count; do not drop it to create a finite mean. Zero baseline width precludes a ratio without an explicitly justified alternative. Analysis decides how failures affect reported coverage.
- Display all supplied valid/invalid comparison methods with consistent encoding. Do not rank or bold narrower methods as superior unless the coverage claim and uncertainty justify that interpretation. Keep oracle/reference procedures visually distinct from usable methods.
- Width reductions expressed as percentages are 100*(1-relative mean width). Record which ratio, interval transformation, and baseline produce any reported percentage.

## Graphic conventions

Use vector PDF for the manuscript plus PNG previews for inspection; keep the executable generator alongside exports. Use a small colorblind-conscious palette with marker/line redundancy, high-contrast labels, no decorative backgrounds, and consistent method ordering. Coverage axes should show every observed value and uncertainty endpoint; any cropped scale must be plainly labeled. Width axes start at zero for bars; point/interval plots may use a narrower plainly labeled range. A logarithmic ratio axis is useful only when the range warrants it and its reference remains explicit.

Set text and stroke sizes for the venue's actual column dimensions. Avoid rotated labels where short method names or horizontal layouts work. Captions state the estimand, design, pairing, normalization, uncertainty level/construction, and scope of evidence; captions do not claim stronger validity than analysis supplies.

## Reproducibility and inspection

Retain result-source repository/revision, file paths and checksums, generator command, package versions, output names, and deterministic rendering settings. Never put a commit's own SHA into its files. Every output must have an identified generator; generated LaTeX tables must derive numbers from results rather than manually transcribed values. Validate result schema, repetition alignment, finite/nonnegative widths, endpoint order and method/scenario completeness before rendering; unexpected omissions must fail visibly.

Open every exported figure and compiled table at final scale. Check for overlap/clipping, legible uncertainty, consistent encodings, precision, escaping, and captions. Inspect the integrated paper PDF from paper-repo after merge. Re-read Research objective and idea-repo's Brief before delivery; the wiki was not yet available on the initial read.
