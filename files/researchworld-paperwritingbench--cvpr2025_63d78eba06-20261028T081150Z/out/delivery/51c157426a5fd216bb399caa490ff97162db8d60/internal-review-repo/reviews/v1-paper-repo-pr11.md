# Review of paper-repo PR #11 (Version 1) — head c00f2e35a226ce19c0f9dc7e9074603633fcef69 (main -> release)

Conclusion: **changes requested** (small, all actionable now).

## Inspected
- Rebuilt template.tex + references.bib with latexmk from the PR head: compiles, no undefined refs/citations; the rebuilt PDF text is identical to the delivered template.pdf. 7 pages total, main text ends on p. 6 (limit 8), CVPR two-column style, author block = required placeholder, preamble/cvpr.sty untouched, `\newtheorem` added only.
- All 35 bib entries cited and all cite keys resolve; entries are real, none later than 2024-11 (checked titles/authors/venues; foster2024jit = arXiv 2402.01401, the JiT paper).
- Figures: figure_1.png included unchanged with `figures/` prefix, legible; gap_ablations.pdf (Fig. 2) legible, markers + line styles distinguish metrics, matches Tabs 1-2.
- Tables 1-4 recomputed against the experimental log: all cell values and Δ rows correct; mixed-linear gaps recomputed from cells and both references reported (log inconsistency handled well).
- Evidence caveats (single runs, integer %, unrecorded hyperparameters, no theorem for ε_m) are stated honestly.

## Findings
1. Abstract factual error: "against 51.5--52.1% test accuracy for four source-free baselines (NegGrad, Random Labels, JiT, Adversarial)". Random Labels is 20.6% (Tab. 4); the range covers only three. Same slip in Sec. 4.5: "All four baselines lose about 20 points ... (51.5--52.1%)" then Random Labels "collapses" — Random Labels loses ~51 points.
2. Forget-size ablation configuration is asserted, not logged: Tab. 1 caption says 500 perturbations, λ=0 for all sizes (and Sec. 4.1 "default configuration"). The log only shows that the 10% row coincides with the m=500, λ=0 rows; the 5% and 15% settings are not recorded. State that the 10% row coincides with that setting and that the others' m, λ are not recorded.
3. Theory overstatement: abstract/contribution 3 say the distance is bounded by the Hessian error, forget-gradient norm and "1/λ²" and that trends are "as the bound predicts". Prop. 2 gives 1/(λμ) (λ^-2 only if Ĥ ⪰ λI), needs λ>0 (the default experiments use λ=0, where the stated bound does not apply), and the m-dependence is an assumption on ε_m (Assumption 1). Qualify in abstract/intro (e.g. "is consistent with") and note λ=0 lies outside Prop. 2's hypotheses.
4. Housekeeping: `figtab_src/__pycache__/data.cpython-311.pyc` is committed (owner figtab-repo/paper-repo); remove it.
5. Optional: Fig. 1 caption is the supplied one ("comparable to retraining ... successful unlearning") while Sec. 4.2 correctly says CIFAR-100/Dogs/Caltech are several points below Retrained; consider adding one sentence to the caption pointing to this.

## Re-review at head 9c7ff9bffce9c80a8ac800a6a27cbbe1662418e5
Since c00f2e3: generator code and .pyc removed (finding 4 resolved), mixed-linear caption grammar fix. template.tex, references.bib and template.pdf are byte-identical to the previous head, so findings 1, 2 and 3 remain open (finding 5 optional, unchanged). Changes requested again.

## Final review at head 393335d724d7fd0a52d844a07abcaa140d4742bc — APPROVED
Diff vs 9c7ff9b touches only template.tex and template.pdf. Rebuilt from source: compiles, no undefined refs/citations, no "??", rebuilt PDF text identical to delivered template.pdf; 8 pages total, main text ends on p. 6 (references p. 7-8, excluded from the limit).
- Finding 1 fixed: abstract "20.6--52.1%", Sec. 4.5 "NegGrad, JiT and Adversarial lose about 20 points, Random Labels about 51".
- Finding 2 fixed: Sec. 4.1 states 5%/15% m and λ are not recorded, assumed to match default.
- Finding 3 fixed: "consistent with", 1/λ² scoped to λ>0, note that λ=0 lies outside Prop. 2.
- Finding 5 (optional) taken: Fig. 1 caption now carries the caveat for CIFAR-100/Dogs/Caltech.
Everything else as in the earlier review (tables vs log, bib, figures, anonymity, layout). Remaining limitations are disclosed in the paper (single runs, unrecorded hyperparameters, no bound on ε_m).

## Re-review at head 51bc4e2258fb28bbb3356063baa8d5413be618c8 — APPROVED
Changes since 393335d (via 7d515d7): wording calibration from experiment-repo's audit (Unlearned(+) shortfall stated as unexplained rather than attributed to the approximations; "equals ... at whole-percent resolution"; "may grow"; MIA non-monotonicity not separable from unmeasured variance; conclusion notes the 6.6-point mixed-network remaining-accuracy deviation) and Tab. 1/2 captions no longer assert unrecorded settings. All strictly more faithful to the log. Rebuilt from source: compiles, no undefined refs/"??", rebuilt PDF text identical to delivered template.pdf; 8 pages total, main text ends p. 6-7 before References. No new numbers introduced; bib unchanged.

## Final: paper-repo PR #18 (release -> final), head 1b1ab0a00ed8467aac6b8a94bb3450839856dba0 — APPROVED
The tree at this head has no difference from the previously approved 51bc4e2 (git diff empty). Rebuilt from source: compiles, 8 pages, no "??", rebuilt PDF text identical to the delivered template.pdf; template.pdf, template.tex, references.bib, figures/ and tables/ present and nonempty.
