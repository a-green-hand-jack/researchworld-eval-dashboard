"""Render the output-only audit from the computed CSVs; no method execution."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

A = Path('/work/artifacts')
D = pd.read_csv(A/'results_audit_metrics.csv', keep_default_na=False, dtype={'p_undercoverage_sci':str,'p_holm_tier_sci':str})
P = json.loads((A/'results_audit_provenance.json').read_text())
O = pd.read_csv(A/'results_audit_oracle.csv', keep_default_na=False)

def f(x, digits=12):
    return format(float(x), f'.{digits}g')

def row(scenario,n,method,ratio=10):
    z=D[(D.scenario==scenario)&(D.n==n)&(D.method==method)&(D.ratio==ratio)]
    assert len(z)==1
    return z.iloc[0]

def ci(r, lo='cov_lo', hi='cov_hi', digits=9):
    return f"[{f(r[lo],digits)}, {f(r[hi],digits)}]"

def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x) for x in r)+' |' for r in rows])

s = row('step',2000,'cf_rich')
q = row('quadratic',2000,'cf_rich')
e = row('step',2000,'eb_select')
c = row('forest',100,'cp')
finite = D[D.tier=='finite']
asym = D[D.tier=='asymptotic']
ora = D[D.tier=='oracle']
select = D[D.method=='eb_select']
core_rich = D[(D.method=='cf_rich') & (D.grid=='core') & D.scenario.isin(['quadratic','step'])]
real_rich = D[(D.method=='cf_rich') & D.scenario.isin(['galaxies','forest'])]
rare = D[(D.method=='cf_rich') & (D.scenario=='rare')]
rej = D[D.undercoverage_reject_holm05]

parts = [f'''# Results audit: fixed-budget confidence-interval study

## Scope and executive conclusions

Output-only audit dated 2026-11-02. Read the frozen plan/amendment, `results/config.json`, `summary.csv`, `oracle.csv`, and **only** the 32 main `results/raw/*.csv.gz` files. Inspected the existing runner for sampling/provenance, checked frozen hashes, and checked the two empirical data arrays for truth and hashes. No CI method was implemented, imported or rerun; no code agent, web access, supplemental comparator, supplemental configuration, supplemental logs or partial supplemental results were used.

- **Complete and internally consistent:** {P['cells']} cells × 2,000 repetitions = {P['replicates']:,} paired experiment repetitions; {P['method_cells']} method-cells and {P['intervals']:,} intervals. All expected files/methods/replicate indices exist; zero invalid endpoints and zero coverage-flag disagreements.
- **Undercoverage is real in many finite-n cells:** Holm detects {int(asym.undercoverage_reject_holm05.sum())}/{len(asym)} asymptotic-tier method-cells (including {int(D[D.negative_control].undercoverage_reject_holm05.sum())} negative-control cells), {int(ora.undercoverage_reject_holm05.sum())}/{len(ora)} oracle cells, and {int(finite.undercoverage_reject_holm05.sum())}/{len(finite)} finite-guarantee cells. The absence of a rejection is **not** evidence proving nominal validity.
- **Nonlinear savings are synthetic and conditional, not uniform:** `cf_rich` at quadratic/n=2000 has width ratio {f(q.width_ratio_ppipp)}; step/n=2000 has ratio {f(s.width_ratio_ppipp)}, but coverage {f(s.coverage)} (Wilson {ci(s)}). The latter is an unadjusted undercoverage warning, **not** a rejection after the requested tier-wide Holm adjustment (p={s.p_holm_tier_sci}).
- **No nonlinear width gains on either empirical distribution:** `cf_rich` is wider than unrestricted `ppipp` in all six empirical cells; its ratios range {f(real_rich.width_ratio_ppipp.min())}–{f(real_rich.width_ratio_ppipp.max())}. `cf_poly2` also has point ratios ≥1 in all six; this does not say scalar PPI fails to improve on labeled-only inference.
- **EB is strongly conservative and inefficient relative to CP here:** EB-PPI and EB-selection cover all 2,000 repetitions in every cell. EB-selection is wider than CP in all 32 cells, and improves on standalone labeled EB only in step/n=2000 (ratio {f(e.width_ratio_eb_labeled)}). These are observations, not universal dominance statements.

## 1. Frozen design and completeness

The pre-run amendment supersedes the initial plan: rich basis p=4 (not p=7), epsilon_n=1e-4/n, value-independent index-mod5 folds, corrected fold/unlabeled covariance recipe, stronger step and quadratic mechanisms, clipping to [0,1], and expanded n grid. All 21 core cells and 11 stress cells in config are present, including n=2000, n=30, and the planned N/n∈{{1,100}} stress cells. No planned amended cell was dropped. There are 26 synthetic cells with 13 methods each and six empirical cells with 12 methods each; oracle is unavailable on empirical data by design, not an incomplete run.

All CSV reads used **`keep_default_na=False`**, preserving the legitimate `null` scenario. There are four `null` cells and no missing-scenario imputation. Within each cell every method has exactly the sorted and saved sequence rep=0,…,1999; there are no duplicate `(method,rep)` keys, no method omissions, and no metadata/truth inconsistencies. Summary has 410 distinct matching keys. The cell-level checks are in `results_audit_cells.csv`.

**Pairing verification boundary:** saved replicate indices align exactly across all methods. The frozen runner constructs one labeled/unlabeled sample per replicate and passes the same arrays into one `all_intervals` call. Seed recipe is `SeedSequence([20261102, sid, n, ratio])`, with sid determined by `['linear','quadratic','step','null','rare','galaxies','forest']`; the 32 tuples are distinct and independent of worker scheduling. However, **raw output contains no labeled/unlabeled sampled-row indices, RNG states, or per-replicate sample hashes**. Thus output-index alignment is verified; underlying sampled-row alignment is supported by source inspection but cannot be independently certified from saved numeric outputs alone. No replay was performed.

Empirical label arrays are binary. Galaxies: {P['data']['galaxies']['size']:,} paired rows, truth {P['data']['galaxies']['truth']:.17g}; forest: {P['data']['forest']['size']:,} rows, truth {P['data']['forest']['truth']:.17g}. Both data SHA-256 hashes match config. The target is the empirical-distribution mean under independent with-replacement draws, **not** conditional coverage on one split or validity for the original scientific population. Independent draws can share source rows; disjoint RNG draws do not mean nonoverlapping row identities.

## 2. Numeric integrity and recomputation

Across all 820,000 saved intervals:

- Nonfinite endpoints/widths/raw-widths: 0; lower>upper: 0; endpoints outside [0,1]: 0; negative reported or raw widths: 0.
- Recomputed inclusive truth containment, using analytic synthetic truths and full-precision empirical label means, agrees with all saved `covered` flags. Using rounded saved truth instead gives identical events. Coverage counts and rates reproduce summary exactly.
- Maximum |saved width − (upper−lower)| is {f(D.width_endpoint_max_abs.max(),17)}. Maximum discrepancies against unrounded summary are {f(P['max_summary_absolute_differences']['width'],17)} for mean width, {f(P['max_summary_absolute_differences']['raw_width'],17)} for raw mean width, and {f(P['max_summary_absolute_differences']['width_ratio_ppipp'],17)} for the paired mean-width ratio. Coverage/Wilson differences are ≤{f(max(P['max_summary_absolute_differences']['cov_lo'],P['max_summary_absolute_differences']['cov_hi']),17)}. These are consistent with raw CSV export at 12 significant digits, not substantive contradictions.
- All finite-dictionary indices are in {{0,…,4}}, and other methods record −1. Selection is predominantly zero-control: 60,471/64,000 replicates; step-indicator control: 3,529/64,000; other controls: 0. Step/n=500 chooses indicator 1,529/2,000 times; step/n=2000 chooses it 2,000/2,000 times. All other cells choose zero-control exclusively.
- Zero-width intervals are **not automatically invalid endpoints**: they are counted as misses if they exclude truth. Every such interval here is collapsed at 0; all truths are strictly interior. Counts and raw-versus-reported collapse diagnostics are retained in the metrics CSV. `cf_rich` has one positive-raw-width collapse on forest/n=100; the unsafe in-sample negative control has six there. Raw endpoint pairs and point estimates were not saved, so untruncated containment, estimator bias/MSE and the precise original disjoint endpoints cannot be recovered from raw widths alone.

## 3. Metrics, uncertainty, and multiplicity

For each method-cell, R=2,000. Definitions:

- **Coverage**: k/R, k=Σ1{{lower≤truth≤upper}}. Descriptive MC SE is sqrt(p̂(1−p̂)/R); reported 95% coverage intervals are Wilson intervals, not simultaneous intervals. At nominal p=.95 the MC SE is {f(np.sqrt(.95*.05/2000))} (about 0.487 percentage points). At 2,000/2,000 hits the plug-in MC SE is zero, but Wilson interval is [0.998082952719,1]; zero observed failures does not imply zero failure probability.
- **Width**: upper−lower after the frozen [0,1] intersection/collapse, computed from the saved `width` column and checked against endpoints to raw-export precision. Report mean, MC SE=s_w/sqrt(R), descriptive mean±1.95996398454 SE, SD and empirical 2.5/25/50/75/97.5 percentiles. `raw_width` is the separately saved untruncated width; use both, because clipping can mask very wide intervals.
- **Paired width effect**: mean width difference versus unrestricted `ppipp`, with SE=s_(w−w_ppipp)/sqrt(R). **Width ratio** is mean(w)/mean(w_ppipp), not mean(w/w_ppipp), which is undefined in zero-width replicates. Paired delta-method SE uses influence values `(w−ratio*w_ppipp)/mean(w_ppipp)` and their sample SD/sqrt(R). Ratio intervals are descriptive normal 95% MC intervals. Also save ratios and paired delta-method SE versus CP and labeled EB. These width comparisons do not establish coverage-matched efficiency.
- **Paired coverage difference** versus `ppipp`: average of the within-replicate indicator differences, with corresponding paired MC SE and descriptive normal interval.
- **One-sided exact-binomial undercoverage diagnostic**: H0: true repeated-sampling coverage≥.95, H1:<.95; boundary p-value `P[Binomial(R,.95)≤k]`. This is an exact discrete-binomial test under independent repetitions, not a normal approximation. Very small tails are evaluated via log-sum-exp of binomial log-PMFs. CSV includes `log10_p_*` and scientific-string columns; numeric p columns can underflow to zero and **must not be quoted as mathematically zero**.
- **Holm**, FWER .05, is applied jointly over every method-cell hypothesis in each tier, **not separately within each method**. Finite family: 4×32=128 (`cp`, `eb_labeled`, `eb_ppi`, `eb_select`). Asymptotic/unsafe family: 8×32=256 (all other non-oracle methods, explicitly including unsafe `insample_rich`). Oracle family: 26 synthetic cells, separately; no invented oracle cells for real data. Holm remains valid with dependent paired methods. Each tier is a separate family, not one overall FWER guarantee across all 410 tests. No additional confirmatory width-significance tests were performed; normal MC intervals are descriptive and not multiplicity-adjusted.

**Status:** designs/recipes and primary coverage/width metrics were frozen before the study. Exact test direction and tier-wide families are requested by this audit, not a retroactive preregistration. Highlighted cell explanations, paired coverage contrasts, quantiles and failure-pattern discussions are exploratory diagnostics. Tests can flag finite-n undercoverage; they cannot prove validity, establish uniformity across distributions, or refute an asymptotic theorem solely because a finite n fails.
''']

parts += ['### Tier-wise test summary\n\n'+table(['Tier','Hypotheses','Holm rejections','Interpretation'],[
['Finite',len(finite),int(finite.undercoverage_reject_holm05.sum()),'No detected deficit; not proof of validity'],
['Asymptotic + unsafe negative control',len(asym),int(asym.undercoverage_reject_holm05.sum()),'49 non-negative-control + 10 negative-control cells'],
['Oracle',len(ora),int(ora.undercoverage_reject_holm05.sum()),'Oracle control does not make Wald intervals finite-safe']])]
parts += ['### All-method descriptive ranges\n\nRanges span different cells, not pooled coverage estimates.\n\n'+table(['Method','Cells','Coverage min–max','Mean-width ratio/ppipp min–max','Holm rejections'],[[method,len(g),f'{f(g.coverage.min())}–{f(g.coverage.max())}',f'{f(g.width_ratio_ppipp.min())}–{f(g.width_ratio_ppipp.max())}',int(g.undercoverage_reject_holm05.sum())] for method,g in D.groupby('method',sort=True)])]
parts += [f'''## 4. Claims that the numbers do and do not support

### A. Nonlinear synthetic savings; special caution for step/n=2000

Core-grid `cf_rich` results (all N/n=10):

'''+table(['Scenario','n','Hits/2000','Coverage [Wilson95%]','Width ratio/ppipp [MC95%]','One-sided p','Tier Holm p'],[[r.scenario,int(r.n),int(r.covered_count),f'{f(r.coverage)} {ci(r)}',f'{f(r.width_ratio_ppipp)} {ci(r,"ratio_ci_lo","ratio_ci_hi")}',r.p_undercoverage_sci,r.p_holm_tier_sci] for _,r in core_rich.iterrows()])+f'''

At step/n=2000, width is {f(s.width)} with MC SE {f(s.width_se)}, versus `ppipp` {f(row('step',2000,'ppipp').width)}; reduction is {f(100*(1-s.width_ratio_ppipp))}%. The ratio MC interval is {ci(s,'ratio_ci_lo','ratio_ci_hi',12)}. However, `cf_rich` misses 129/2000; coverage is **1.45 percentage points below nominal**. Its Wilson upper bound is below .95 and raw one-sided p={s.p_undercoverage_sci}, but tier Holm p={s.p_holm_tier_sci}. `ppipp` coverage in the same cell is {f(row('step',2000,'ppipp').coverage)}; paired coverage difference is {f(s.paired_coverage_diff)} with MC SE {f(s.paired_coverage_diff_se)}. That contrast is descriptive/exploratory, not a separately multiplicity-adjusted superiority test. Do not claim “nominal coverage at every n” or “significant tier-wise undercoverage at step/n=2000.” Both overstate the evidence in opposite directions.

At quadratic/n=2000 the width reduction is {f(100*(1-q.width_ratio_ppipp))}%, with coverage {f(q.coverage)} and no Holm deficit detection. Width savings do not establish exact finite-sample coverage. Linear/null signals exhibit small-sample overhead (e.g., cf_rich ratios at n=30 are {f(row('linear',30,'cf_rich').width_ratio_ppipp)} and {f(row('null',30,'cf_rich').width_ratio_ppipp)}); quadratic/n=30 ratio is {f(row('quadratic',30,'cf_rich').width_ratio_ppipp)}, so even nonlinear gains are not uniform over n.

Analytic `oracle.csv` at N/n=10 gives width ratios {f(O[(O.scenario=='quadratic')&(O.ratio==10)].iloc[0].oracle_width_ratio)} (quadratic) and {f(O[(O.scenario=='step')&(O.ratio==10)].iloc[0].oracle_width_ratio)} (step); linear/null/rare ratio is 1 (up to floating point). Its 15 rows have nonnegative variance gaps; sqrt(nvar_score_oracle/nvar_scalar) reproduces the saved ratios to {f(P['oracle_ratio_max_abs_difference'],17)}. Agreement of the large-n learned width ratio with a theoretical oracle benchmark is **not** a proof that the learned interval is valid or globally optimal. Oracle normal intervals themselves reject undercoverage in six cells.

### B. Rare-event failures are substantial, but not universal across methods

`rare` has Bernoulli mean .01. All cf_rich rare cells are shown, not only the failures:

'''+table(['n','N/n','cf_rich hits/2000','Coverage [Wilson95%]','Holm p','Wald zero-width count','PPI λ=1 coverage','CP coverage'],[[int(r.n),int(r.ratio),int(r.covered_count),f'{f(r.coverage)} {ci(r)}',r.p_holm_tier_sci,int(row('rare',int(r.n),'wald',int(r.ratio)).zero_width),f(row('rare',int(r.n),'ppi',int(r.ratio)).coverage),f(row('rare',int(r.n),'cp',int(r.ratio)).coverage)] for _,r in rare.iterrows()])+f'''

Core n=100 `cf_rich` covers 1262/2000={f(row('rare',100,'cf_rich').coverage)}; n=500 covers 1757/2000={f(row('rare',500,'cf_rich').coverage)}. At stress n=30 it covers 529/2000=.2645 (Holm p={row('rare',30,'cf_rich').p_holm_tier_sci}). Wald has 1469/2000 zero-width [0,0] intervals at n=30, 732 at n=100, and 16 at core n=500. These failures are consistent with no-positive-label events and degenerate variance estimates; labels are not retained per replicate, so that mechanism is not independently counted from sampled labels here. Failures at n=500 also substantially exceed zero-width events, so the problem is broader than only zero variance. More unlabeled data (ratios 1,10,100 at n=500) does not repair sparse-label normal-approximation failure.

Do **not** write “every method fails on rare events”: fixed λ=1 PPI ranges .934–.955 over the six rare cells and has no tier-Holm rejection there (it is wider); CP ranges .956–.9965; all three EB recipes have full observed rare-cell coverage. At n=2000, cf_rich coverage is .9435 with Wilson {ci(row('rare',2000,'cf_rich'))}; no adjusted deficit is detected. That is not a validity certificate either.

### C. Empirical data: no incremental nonlinear width benefit

'''+table(['Scenario','n','cf_rich coverage [Wilson95%]','Width ratio/ppipp [MC95%]','ppipp coverage'],[[r.scenario,int(r.n),f'{f(r.coverage)} {ci(r)}',f'{f(r.width_ratio_ppipp)} {ci(r,"ratio_ci_lo","ratio_ci_hi")}',f(row(r.scenario,int(r.n),'ppipp').coverage)] for _,r in real_rich.iterrows()])+f'''

For forest/n=100, rich intervals are {f(100*(row('forest',100,'cf_rich').width_ratio_ppipp-1))}% wider than ppipp and {f(100*(row('forest',100,'cf_rich').width_ratio_cp-1))}% wider than labeled CP. Their widths are {f(row('forest',100,'cf_rich').width)} (MC SE {f(row('forest',100,'cf_rich').width_se)}) versus ppipp {f(row('forest',100,'ppipp').width)}. Their improved point coverage cannot be separated from this substantial widening by a raw-width comparison. Forest/n=100 ppipp coverage .9065 has Holm p={row('forest',100,'ppipp').p_holm_tier_sci}; Wald, PPI, ppipp_pkg, cf_linear, cf_poly2 and unsafe in-sample rich also reject there, whereas cf_rich does not. This is finite-n undercoverage, not failure of the empirical resampling definition.

The simpler nonlinear `cf_poly2` has no point width gain over ppipp in these six cells either (ratios {f(D[(D.method=='cf_poly2')&D.scenario.isin(['galaxies','forest'])].width_ratio_ppipp.min())}–{f(D[(D.method=='cf_poly2')&D.scenario.isin(['galaxies','forest'])].width_ratio_ppipp.max())}); some tiny differences are within MC uncertainty. Claims of nonlinear real-data efficiency improvement or broad real-world coverage validation are unsupported. Scope any empirical claim to these two finite paired distributions and frozen scores.

### D. Finite-safe tiers: conservative EB, useful CP comparator, no general dominance

'''+table(['Method','Coverage range','Total misses (descriptive)','Width/CP range','Width/labeled-EB range'],[[method,f'{f(g.coverage.min())}–{f(g.coverage.max())}',int(g.miss_count.sum()),f'{f(g.width_ratio_cp.min())}–{f(g.width_ratio_cp.max())}',f'{f(g.width_ratio_eb_labeled.min())}–{f(g.width_ratio_eb_labeled.max())}'] for method,g in finite.groupby('method',sort=False)])+f'''

EB-labeled has only eight misses in 64,000 intervals across different cells; EB-PPI and EB-selection have none. These totals describe these allocations, not one homogeneous binomial experiment. In step/n=2000, EB-selection width is {f(e.width)} (SE {f(e.width_se)}) versus labeled EB {f(row('step',2000,'eb_labeled').width)}, ratio {f(e.width_ratio_eb_labeled)} with paired ratio SE {f(e.ratio_eb_labeled_se)}: {f(100*(1-e.width_ratio_eb_labeled))}% narrower. This is the **only** cell where selected EB beats standalone labeled EB, and it is still {f(e.width_ratio_cp)} times as wide as CP (paired ratio SE {f(e.ratio_cp_se)}). In the other 31 cells selection is wider than labeled EB; selection's union-bound budget explains why a zero-control option does not imply dominance over standalone labeled EB at alpha.

EB-PPI is wider than labeled EB in all 32 cells. Clipping matters: the largest raw mean width is {f(D.raw_width.max())} (EB-PPI, null/n=30), reported as width 1. Both reported and raw widths must accompany discussions of conservatism. The 2000/2000 observed hits per cell do not prove universal finite-sample validity; that requires the external bound assumptions and implementation proof.

CP's lowest coverage is forest/n=100: 1878/2000=.939, Wilson {ci(c)}, raw one-sided p={c.p_undercoverage_sci}, but all finite-family Holm p-values are 1. Thus neither “CP invalid because its point coverage is .939” nor “simulation proves CP valid” is warranted. All outcomes are binary in this study; these results do not transfer CP to nonbinary bounded outcomes. Conservative width comparisons alone also do not make EB unnecessary on nonbinary problems.

### E. Unsafe negative control and package baseline

`insample_rich` has ten Holm-detected undercoverage cells and must remain labeled **unsafe**, never counted as a legitimate finite-safe comparator merely because it is narrow. `ppipp` and `ppipp_pkg` are distinct frozen baselines: unrestricted paper mean recipe versus clipped-weight/package variance conventions. All width ratios in this audit use unrestricted `ppipp`, not the package replica. Package reproduction does not establish equivalence to the unrestricted recipe.
''']

parts += ['## 5. Complete familywise-significant undercoverage list\n\nAll 65 rejected method-cells, including unsafe and oracle tiers. Full-precision audit calculations from the rounded raw data, MC SEs and Wilson intervals are in the metrics CSV; extremely small p-values below are nonzero log-domain calculations.\n\n'+table(['Tier','Scenario','n','N/n','Method','Hits/2000','Coverage','One-sided p','Holm p'],[[r.tier,r.scenario,int(r.n),int(r.ratio),r.method,int(r.covered_count),f(r.coverage),r.p_undercoverage_sci,r.p_holm_tier_sci] for _,r in rej.iterrows()])]
parts += ['''## 6. Publication claim guidance

| Claim | Decision / defensible wording |
| --- | --- |
| “Nonlinear score controls reduce width beyond scalar PPI++.” | Supported for specified synthetic nonlinear cells; report n, ratio, coverage and MC uncertainty. Not universal. |
| “cf_rich maintains 95% finite-sample coverage.” | Unsupported; large rare-event deficits, and a step/n=2000 warning. Crossfit intervals belong to the asymptotic tier. |
| “Step/n=2000 is a Holm-confirmed violation.” | Unsupported in the requested 256-test family; raw p=.0023948 becomes .4693801. Disclose the deficit without either suppressing or upgrading it. |
| “No adjusted rejection means validity.” | False. MC power is finite; neither non-rejection nor all observed hits proves validity. |
| “Nonlinear inference improves the real-data examples.” | No incremental width benefit versus ppipp observed on either empirical distribution. Coverage sometimes improves with wider intervals. |
| “The finite-safe nonlinear method is uniformly narrower.” | Unsupported: EB-selection beats labeled EB in only one cell and never beats CP here. |
| “Oracle supplies exact-coverage intervals.” | Unsupported: the oracle control is used inside normal intervals, with six detected finite-n deficits. |
| “Every rare-event method fails.” | Unsupported: distinguish sparse-label asymptotic estimators from PPI λ=1, CP and EB. |
| “Theory is globally optimal / empirical evidence validates arbitrary populations.” | Unsupported by this design; frozen scalar-score, empirical-distribution and bounded/binary assumptions must be explicit. |

## 7. Reproducibility findings and limitations

1. **No missing cells or integrity corruption detected.** All five frozen SHA-256 checks match (`methods.py`, runner, tests, plan, amendment), both empirical data hashes match, and per-input current hashes are saved in `results_audit_provenance.json`. Matching current hashes establishes consistency with the frozen manifest; it does not independently certify the timestamp/order of that manifest or inspect every method formula.
2. **Numeric raw export is rounded** (`%.12g`), whereas summary was computed before rounding. Exact saved-data coverage counts reproduce, and tiny width/ratio mismatches are expected. Preserve 17-digit floats/binary arrays in future runs. “Exact values” here means values recomputed from the saved numeric output, not recovery of lost unrounded endpoints.
3. **No saved sampling IDs.** Preserve per-replicate labeled/unlabeled row indices or sample-array hashes and explicit child seeds to independently validate pairing without replay. Current shared-array source and rep indices are consistent, but output files alone cannot establish row identity or disjointness.
4. **No saved untruncated endpoint pairs, estimates, SEs or sample outcome counts.** Raw widths permit width auditing but not original-interval containment, point-estimate bias/MSE or direct zero-label-event auditing. These metrics cannot be invented.
5. **Summary `seconds` is cumulative since cell start at the time each method is summarized**, not that method's isolated runtime. Do not plot it as a per-method speed benchmark. Config reports overall experiment wall time; no timing experiment was rerun.
6. **Seed per cell, not a stored independent seed per replicate.** Reproducibility relies on fixed scenario ordering, loop order, RNG implementation, data hashes and dependency versions. Existing 32 seed tuples are unique. Raw file hashes are audit snapshots, not a new independent replication.
7. **MC scope and design:** repetitions are fixed at 2,000, no adaptive extension occurred here; pointwise descriptive error bars are not simultaneous. Binary target mechanisms and two empirical distributions do not span all bounded outcomes, covariate shifts or scientific populations. Model-training leakage/provenance of frozen real scores is not independently audited here.
8. **No supplemental evidence was incorporated.** A separately running exact comparator is outside this audit. Do not imply its efficiency, coverage or completion. This report makes no novelty or universal optimality claim from its absence.

## 8. Recommended next experiments (proposed only; not run)

1. Predeclare an independent, larger-seed validation of step/n=2000 and nearby n for cf_rich/oracle, with the comparison family fixed before results; include target MC precision and save sample hashes, raw endpoints and labeled event counts. Do not simply continue the current stream until a desired p-value occurs.
2. In a separate frozen rare-event study, stratify diagnostics by labeled positive count to separate zero-variance collapse from nondegenerate normal-approximation failures; retain all sparse-label cells and exact-safe comparators. No new CI recipe is justified by this analysis alone.
3. Once the independent exact-comparator study is complete, evaluate its final frozen output separately against CP/labeled EB at the same budget. Treat it as supplemental, not as part of the original confirmatory evidence. On real data, prioritize checking the near-zero incremental nonlinear benefit rather than claiming a gain.

## Artifacts and reproducible commands

- `/work/artifacts/results_audit.md`: this report.
- `/work/artifacts/results_audit_metrics.csv`: all 410 method-cells; coverage counts, uncertainty, endpoint/selection/collapse checks, width quantiles, paired effects and exact-binomial/Holm results.
- `/work/artifacts/results_audit_cells.csv`: all 32 completeness and rep-alignment checks.
- `/work/artifacts/results_audit_undercoverage.csv`: all 65 Holm-rejected method-cells.
- `/work/artifacts/results_audit_oracle.csv`: all 15 analytic rows with variance-gap/ratio arithmetic checks.
- `/work/artifacts/results_audit_provenance.json`: environment, input hashes, frozen checks, truth checks and maximum summary discrepancies.
- `/work/artifacts/audit_existing_results.py` and `/work/artifacts/render_results_audit.py`: analysis and report-rendering scripts. Reproduce with `python /work/artifacts/audit_existing_results.py` followed by `python /work/artifacts/render_results_audit.py`. Neither imports the study's methods or touches supplemental results.
- No figures were produced: this request was for an output-only audit; the machine-readable tables retain all cells without figure-level cherry-picking.
''']

(A/'results_audit.md').write_text('\n\n'.join(parts)+'\n')
print('Saved',A/'results_audit.md')
