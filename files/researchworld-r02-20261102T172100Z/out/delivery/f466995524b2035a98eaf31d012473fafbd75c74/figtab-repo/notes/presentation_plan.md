# Presentation specification

Settled against objective #1 and frozen deliverable.md on 2026-11-02. Only observed compositional-response coverage is displayed; class-label coverage is a different estimand. Experiment's two-rep pilot is not confirmatory evidence.

## Main claims and encodings (pending story decision)

1. Joint reliability: dot-and-horizontal-interval display for all seven methods, dimensions 3/10 and homogeneous/heterogeneous cells. Calibration n=499 is a proposed main view, with all n=99/499 values tabulated. Horizontal axis is simultaneous coverage in [0,1]; dashed .90 nominal line. Absolute scale avoids disguising severe joint failure of the naive coordinatewise control.
2. Conditional/shift reliability: in each dimension, paired method rows show iid group-0 and group-1 coverage and shifted marginal coverage. Color plus distinct marker shape distinguishes quantities. The shift raises group-1 probability .2 to .8 while preserving within-group laws. Caption must state this special shift, never claim arbitrary-shift robustness.
3. Efficiency: at K=3 only, uniform Euclidean simplex area fraction averaged over anchors. Same positive reference measure across all geometries; smaller area only interpretable alongside coverage. Show absolute means and pointwise intervals, plus supplied paired area differences versus Aitchison. Coordinatewise naive is explicitly a negative control, so its small sets cannot establish superior efficiency. Do not rank clr and raw radii, or report unresolved K=10 areas.
4. Exact numbers: machine-readable all-cell table and standalone booktabs TeX panels, carrying pointwise intervals and independent-replication counts through provenance/captions. Main manuscript table density and selection await paper decisions. NeurIPS 2026 gives 5.5-inch single-column width; use 8 pt plot labels and embedded TrueType.

## Uncertainty and provenance

Use experiment's summary estimates and pointwise 95% t intervals across independent dataset replications. These describe uncertainty of the replication mean, not a prediction interval for an individual calibration run. Coverage, anchors and area Monte Carlo variability enter the independent-replication variability. Supplied paired contrasts preserve shared data within each replication. No extra significance stars, post-selection hypothesis tests or pooled pseudo-replicates. Keep interval endpoints untruncated; any plotted endpoint outside probability bounds must be visible or explicitly disclosed.

Every artifact keeps generator source, exact input SHA-256 and source commit; PNG is for visual inspection, PDF for manuscript. Confirmatory output must only follow an actual completed analysis handoff. Pilot render checks stay outside delivered paths. Open every output before handoff and verify the integrated paper PDF when available.

## Implementation check (not evidence)

On 2026-11-02 the generator ran successfully against experiment's two-rep pilot at analysis commit `87564dc3792f24099f10ff47c3daa1a7b7fb9a0a`. Three diagnostic PNGs were opened and inspected outside delivered paths. This exposed pointwise t intervals outside [0,1] at n=2; axes now retain full endpoints rather than clip them. Diagnostic content supports no scientific ranking or conclusion. Final figures must be rendered from completed confirmatory summaries and inspected again.

Venue input was answered and closed in venue-repo#3. The rendered PDFs use embedded TrueType fonts (`pdf.fonttype=42`). Main labels have been shortened only where necessary: “Coord. naive” denotes per-coordinate alpha, “Coord. Bonferroni” denotes per-coordinate alpha/K; full definitions belong in captions. Diagnostic wide t intervals are retained with adaptive tick spacing; no interval is silently truncated.

## Settled scope (activation 3570d8c)

Read the objective again, the now-available idea-repo wiki Brief, story protocol v1.1, verified venue package and paper-repo request #3. Paper main CODEOWNERS now assigns `figures/`, `tables/`, `presentation/` to this position. Final presentation also includes the approved oracle known-ratio weighted Aitchison method, paired iid-to-shift changes, a replication ECDF/tail diagnostic, and rank/boundary sensitivity assets when supplied. Each figure caption is owner-authored TeX under `figures/`; table captions under `tables/`. They preserve estimand/uncertainty definitions for paper integration. No final assets precede confirmatory evidence.

The diagnostic generator was also compiled in the actual official NeurIPS 2026 style: main numeric table plus four figures and their captions. All five pages were opened in a contact sheet; no overfull/underfull boxes were reported, and `pdffonts` found only embedded Type 1/CID TrueType fonts. `\caption{\input{...}}` initially failed because file input is fragile in a moving argument; use `\caption[Short caption]{\input{...}}`. This check concerns rendering only and used the pilot, not scientific evidence.

## Prior-score extension (activation b99fa4a)

Read story-repo#4, protocol v1.2 and input_alignment.md. Final evidence includes TV/forward KL matched-seed supplements, with K=3 TV explicitly identified as the same region as raw maximum. Oracle weights remain known-generator information. Prior-source overlap precludes first-composition-region framing. Final evidence is not yet supplied in experiment main. Supplementary code now follows documented rank/zero/diagnostic/shift schemas; syntax checked only. The original-target clr diagnostic rejects boundary points and differs from transformed coverage and inverse-image guarantees. Final captions use the implemented max-and-reclose transform, not an additive replacement. PR paper-repo#8 has merged, supplying the required nonempty presentation/README.md path.

## First measured-asset handoff (activation 4029c345)

Completed core/oracle and rank/boundary evidence arrived at experiment revision recorded in `presentation/artifact_manifest.json`. Rendered six figures and 19 table bodies with captions, retained paired shift/epsilon and zero-prevalence values, and recorded exact source hashes. Opened all PNGs and all 25 pages of an official-template component layout PDF. Inspection details are delivered in `presentation/inspection.md`. TV/KL evidence is still absent, requested in experiment-repo#8; figtab #4 remains open. Component handoff can proceed independently of that supplement so paper can integrate actual evidence now. Integrated PDF check remains due after placement.


## Completed source controls and zero-region clarification

All ten main methods are now supplied by experiment revision c0c1daf95ec55259ec22ad85455b65bb22baa03c. The final displays include TV and forward KL, keep K3 TV explicitly identical to raw maximum, preserve all paired comparisons and numerical area-resolution diagnostics, and present area alongside subgroup/shift failures. Boundary displays label transformed and inverse-image original-target coverage as exactly the same event, distinguish direct original-clr membership, and make no inverse-image area claim. Final integrated-document inspection follows report placement.
