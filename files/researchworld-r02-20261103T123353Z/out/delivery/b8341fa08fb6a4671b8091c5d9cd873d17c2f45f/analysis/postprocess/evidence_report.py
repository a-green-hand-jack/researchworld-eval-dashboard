#!/usr/bin/env python3
"""Traceable analysis handoff; presentation and manuscript remain with owners."""
import hashlib
import json
from pathlib import Path
import pandas as pd

analysis=Path(__file__).resolve().parents[1];root=analysis/'results/confirmatory'
s=pd.read_csv(root/'summary/summary.csv');a=pd.read_csv(root/'numerical_allowance/area_contrasts_with_numerical_allowance.csv')
p=pd.read_csv(root/'summary/paired_contrasts.csv');sens=pd.read_csv(root/'derived/paired_sensitivity_contrasts.csv')
audit=json.load(open(root/'final_audit.json'));resources=json.load(open(analysis/'results/scientific_resources.json'))
records=[]
def estimate(cell,method,group='all',metric='coverage'):
    r=s[(s.cell==cell)&(s.method==method)&(s.group==group)&(s.metric==metric)].iloc[0]
    key=':'.join([cell,method,group,metric]);records.append(dict(evidence_key=key,source='summary/summary.csv',**r.to_dict()))
    return f"{r['mean']:.6f} [{r.ci_low:.6f}, {r.ci_high:.6f}]"
def area(cell,method,reference):
    r=a[(a.cell==cell)&(a.group=='all')&(a.method==method)&(a.reference==reference)].iloc[0]
    records.append(dict(evidence_key=':'.join([cell,method,'minus',reference,'all','mean_volume']),source='numerical_allowance/area_contrasts_with_numerical_allowance.csv',**r.to_dict()))
    return f"{r['mean']:.6f} [{r.enlarged_ci_low:.6f}, {r.enlarged_ci_high:.6f}] (allowance {r.empirical_allowance:.6f}; {'resolved at practical margin' if r.practically_rankable else 'no practical ranking'})"
def paired(cell,method,reference,group='all',metric='coverage'):
    r=p[(p.cell==cell)&(p.method==method)&(p.reference==reference)&(p.group==group)&(p.metric==metric)].iloc[0]
    records.append(dict(evidence_key=':'.join([cell,method,'minus',reference,group,metric]),source='summary/paired_contrasts.csv',**r.to_dict()))
    return f"{r['mean']:.6f} [{r.ci_low:.6f}, {r.ci_high:.6f}]"
lines=['# Executed analysis evidence and limits','',
'All results below come from the frozen observed-composition study. This is the analysis owner’s numerical handoff; the report and final figures are delivered by their owners.','',
f"## Inventory and audit\n\nAll {audit['expected_trials']:,} trials in 19 frozen cells completed: 100 independent regenerated/refitted trials per cell, with 2,000 test observations each. Canonical exports have {audit['rows']:,} method/group rows ({audit['numeric_rows']:,} defined procedure rows, {audit['applicability_rows']:,} explicit unsmoothed-ILR inapplicability rows). Pilots are excluded. Scientific generation/audit source pin is `{audit['source_commit']}`. Complete seed/input/fit and checkpoint hashes are retained in results/confirmatory/.",
'',f"The prescribed audit covers {audit['audited_regions']:,} matched method/center regions and {audit['matched_center_contrasts']:,} paired numerical contrasts: every K3 cell, repeats 0/25/50/75, first four centers per observed X group, four independent power16 scrambles. Recalculation of every allowance differs by at most {audit['paired_allowance_recalculation_max_difference']:.3g}. Maximum measured allowance is {audit['max_empirical_allowance']:.6f}, not the .001 floor. Of {audit['area_contrasts']} reported cell/group method-area contrasts, {audit['numerically_unresolved_area_contrasts']} remain numerically/statistically unresolved and {audit['practically_rankable_area_contrasts']} pass the frozen geometric resolution and practical-effect rule. These flags alone never make an under-covering control preferable.",
'',
'`final_audit.json` verifies full trial inventory, no duplicate rows, all source/config hashes against the frozen git object, identical source across shards, the exact complete method/center audit key set, matching main areas, every raw scramble summary, paired allowance recomputation/interval enlargement and the 32 measured case memberships. It is a reproducibility/consistency audit, not independent report approval.','',
'## Reliability and the coordinate control','',
'| Cell | Naive coordinate joint coverage | Bonferroni joint coverage | Operative ILR joint coverage |','| --- | --- | --- | --- |']
for cell in ['interior_k3','interior_k10','boundary_k3','boundary_k10','dirichlet_k3','dirichlet_k10','zeros_k3','zeros_k10']:
    ilr='ilr_smoothed' if cell.startswith('zeros') else 'ilr'
    lines.append(f'| {cell} | {estimate(cell,"coordinate_naive")} | {estimate(cell,"coordinate_bonferroni")} | {estimate(cell,ilr)} |')
lines+=['','The naive coordinate method calibrates each coordinate separately and fails the desired joint event in these cells. Componentwise coverage is in summary/component_coverage_summary.csv; paired component-minus-joint gaps are in derived/coordinate_component_joint_gaps.csv. Bonferroni controls the joint event under the stated assumptions. These tables test the directly observed composition, not a class label or an unobserved probability vector.','',
'## Marginal reliability can conceal minority failure','',
'| Cell | Procedure | Population coverage | Minority coverage | Paired minority improvement over global ILR |','| --- | --- | --- | --- | --- |']
for cell in ['heterogeneous_k3','heterogeneous_k10']:
    for method in ['ilr','ilr_scaled','ilr_mondrian']:
        diff=paired(cell,method,'ilr','minority') if method!='ilr' else 'reference'
        lines.append(f'| {cell} | {method} | {estimate(cell,method)} | {estimate(cell,method,"minority")} | {diff} |')
lines+=['','Global marginal calibration leaves severe high-variance-minority undercoverage. Both fitted scale adaptation and fixed-group calibration improve it, but fitted scaling does not grant group validity and the measured minority mean is below .9 in the core cells. The group theorem averages over within-group calibration values and future observations, not each realized split or every covariate value. Group sizes/fitted scales are in derived/group_denominators_and_fits.csv.','',
'## Conditional geometry ordering and unresolved comparisons','',
'Area is normalized original-simplex Hausdorff area. Each interval below is the paired statistical t95 interval enlarged by the separately measured empirical numerical allowance. A negative value means the first procedure’s region is smaller at the recorded coverage, not universally preferable.','',
'| Cell | Area contrast | Mean and enlarged interval |','| --- | --- | --- |']
for cell in ['interior_k3','heterogeneous_k3','boundary_k3','dirichlet_k3']:
    lines.append(f'| {cell} | ILR minus L2 | {area(cell,"ilr","l2")} |')
for cell in ['interior_k3','boundary_k3','dirichlet_k3','zeros_k3']:
    lines.append(f'| {cell} | TV minus L2 | {area(cell,"tv","l2")} |')
lines += [f'| zeros_k3 | ILR-smoothed minus L2 | {area("zeros_k3","ilr_smoothed","l2")} |',
          f'| heterogeneous_k3 | scaled ILR minus global ILR | {area("heterogeneous_k3","ilr_scaled","ilr")} |',
          f'| heterogeneous_k3 | group ILR minus global ILR | {area("heterogeneous_k3","ilr_mondrian","ilr")} |',
'',
'The ILR-versus-L2 area ordering reverses between interior and boundary/Dirichlet mechanisms. TV versus L2 has no practically resolved ordering in any core K3 mechanism under the frozen rule. ILR versus Hellinger in the interior/heterogeneous mechanisms also remains unresolved. Minority reliability improves with adaptation/group calibration at a measured population-area cost; the small scaled-versus-group area contrast remains unresolved. Any smaller naive-coordinate region is accompanied by joint undercoverage and cannot be presented as better calibrated efficiency. No K10 area was measured. All orderings are conditional on the shared inverse-ILR ridge center and these synthetic mechanisms.','',
'## The specified group-prevalence shift','',
'| Procedure | Shifted population coverage | Shifted minority coverage |','| --- | --- | --- |']
for method in ['ilr','ilr_scaled','ilr_mondrian']:
    lines.append(f'| {method} | {estimate("heterogeneous_shift",method)} | {estimate("heterogeneous_shift",method,"minority")} |')
lines+=['','Only P(G=1) changes from .1 to .4; the complete within-group law stays fixed. The measured marginal failure of global ILR and retained group-calibration coverage support this specific mechanism and the stated group-mixture proof. They do not establish arbitrary covariate- or response-shift robustness. Paired stress-minus-iid effects are in derived/paired_sensitivity_contrasts.csv; shared random-number pairing does not imply identical shifted test arrays.','',
'## Calibration size, nominal level and small-group costs','',
'| Cell | Procedure | Overall coverage | Minority coverage | Minority infinite-threshold frequency |','| --- | --- | --- | --- | --- |']
for cell in ['heterogeneous_ncal99','heterogeneous_k3','heterogeneous_ncal1999','heterogeneous_alpha05']:
    method='ilr_mondrian'
    lines.append(f'| {cell} | group ILR | {estimate(cell,method)} | {estimate(cell,method,"minority")} | {estimate(cell,method,"minority","infinite_threshold_rate")} |')
lines+=['',f"At ncal99, the recorded infinite-threshold frequency corresponds to {int(round(s[(s.cell=='heterogeneous_ncal99')&(s.method=='ilr_mondrian')&(s.group=='minority')&(s.metric=='infinite_threshold_rate')]['mean'].iloc[0]*100))} of 100 minority calibration groups receiving the entire valid target domain, retaining finite-rank conservatism rather than discarding those trials. At ncal1999 the group-calibrated mean is slightly below nominal in this finite run, so do not claim every observed mean is at least .9. Calibration-size and alpha paired contrasts are all retained.",'',
'| Interior cell | ILR coverage | Across-trial SD |','| --- | --- | --- |']
for cell in ['interior_ncal99','interior_k3','interior_ncal1999','interior_alpha05']:
    rr=s[(s.cell==cell)&(s.method=='ilr')&(s.group=='all')&(s.metric=='coverage')].iloc[0]
    lines.append(f'| {cell} | {estimate(cell,"ilr")} | {rr.sd:.6f} |')
lines+=['','More calibration data reduces the observed procedure-to-procedure variation here, with finite-test noise still included. Alpha .05 targets .95 rather than .90. These are outer-trial summaries, not pooled binomial intervals.','',
'## Exact zeros, smoothing and the limitation of area','',
'| Cell | Score | Population coverage | Zero-face coverage | Positive-response coverage | Mean original-simplex area |','| --- | --- | --- | --- | --- | --- |']
for cell,method in [('zeros_k3','l2'),('zeros_k3','hellinger'),('zeros_k3','ilr_smoothed'),('zeros_eps1e-06','ilr_smoothed'),('zeros_eps0.01','ilr_smoothed')]:
    lines.append(f'| {cell} | {method} | {estimate(cell,method)} | {estimate(cell,method,"zero_face")} | {estimate(cell,method,"positive")} | {estimate(cell,method,"all","mean_volume")} |')
lines+=['','Unsmoothed ILR is explicitly inapplicable to the entire true-zero arm; no zero response is silently dropped. The smoothed score is evaluated on original candidates and both arguments use the same fixed transform. Response-defined zero/positive slices are descriptive audits, not test-observable groups with a conditional theorem. Full-dimensional area assigns zero measure to faces; nearly full area can coexist with substantial face noncoverage.','',
f"At epsilon1e-6 the estimates saturate at normalized area one. {len(audit['numerical_range_warnings'])} cell/trial/method/group mean estimates slightly exceed one (largest {max(w['value'] for w in audit['numerical_range_warnings']):.9f}); they are retained unclipped as numerical warnings. Do not interpret a value above one, a tiny difference at this saturation, or a QMC estimate near one as an exact full-domain certificate. Cross-cell epsilon-area contrasts are descriptive statistical estimates and have no cross-cell area-ranking flag from the within-cell numerical allowance. Exact full-domain/unknown bounds and infinity remain separately saved.",
'',
'## Uncertainty, contradictions and numerical limits','',
'All displayed brackets are pointwise Student-t 95% intervals over independently regenerated/refitted trials, except explicitly enlarged area intervals. Trial SD and percentile bootstrap intervals (5,000 draws, seed90210) are retained alongside. They are not simultaneous familywise intervals, conditional-on-calibration guarantees, equivalence tests or p-value-selected findings. Positive-group missing area propagates undefined; zero-count groups have zero aggregate weight.','',
'Not every finite-run joint-score interval contains nominal. Small pointwise shortfalls occur, including interior K10 L2, interior ncal99 ILR and some ncal1999 heterogeneous procedures; every estimate remains supplied. These pointwise outcomes across many correlated descriptive comparisons do not establish failure of the finite-rank exchangeability theorem. Scale adaptation does not eliminate all measured group gaps. No universal method winner is supported.','',
f"Precision flags in derived/coverage_gaps_and_precision.csv mark minority mean halfwidth>.02 (including heterogeneous ncal99 global ILR/Hellinger and the Bonferroni control, plus heterogeneous alpha05 Hellinger). Wide intervals do not establish equivalence. Bootstrap/t sensitivity is in derived/bootstrap_interval_sensitivity.csv. Numerical allowances are finite representative diagnostics, not uniform or simultaneous numerical-error bounds; {audit['numerically_unresolved_area_contrasts']} area contrasts remain unresolved and must stay so.",'',
'## Cost, failures, provenance and reproduction','',
f"The two scientific jobs, including all prescribed audits, used {resources['scientific_jobs_cpu_seconds']:.3f} resource CPU seconds total and a creation-to-end parallel wall window of {resources['complete_main_and_audit_creation_to_end_window_seconds']:.3f} seconds. Main-run elapsed times were {resources['main_runner_elapsed_seconds'][0]:.3f} and {resources['main_runner_elapsed_seconds'][1]:.3f} seconds; peak main-run RSS was {max(resources['main_runner_peak_rss_kib'])} KiB. This replaces the pilot-derived runtime forecast. Both jobs succeeded and no scientific trial failed. Resource-clock, main-timer and CPU definitions are kept distinct in results/scientific_resources.json and resource_jobs.json; postprocessing costs are separate.",
'',
'Historical failures/changes remain in DECISIONS.md, REPRODUCE.md and results/run_failures.json: the pre-pilot Jacobian normalization correction, a failed preconfirmatory launcher with a missing sandbox /tmp file (zero scientific trials affected), and a historical exploratory-pilot postprocessing check lacking input provenance. They are not measured negative scientific findings. No extra refits/trials were run to obtain final significance or reverse a null result.','',
'REPRODUCE.md gives ordinary CPU and tracked-job commands, environment versions and exact source/config/input seeds. No external data acquisition or third-party dataset license is involved; generator/config/source hashes define the synthetic data version. All nine positions’ dated source-access/retrieval statements are attributed in provenance/access-inventory.json. None is converted into independent blanket certification.','',
'Figure/table ownership stays with figtab-repo and final report/venue integration with their owners. Use results/confirmatory/summary/, numerical_allowance/, derived/, region_cases.jsonl and this evidence map. The measured case selector was frozen at core K3 trial0/test0; `compbench.conformal.contains_case` evaluates the actual recorded regions. Every table/figure must identify its actual sources and rendering script.','',
'Scope: observed compositions; five synthetic mechanisms; shared fitted center; CPU-run finite study. No latent-probability, label-set, real-data, geometry-specific optimal-center, priority, universal-ranking or arbitrary-shift claim follows.']
(analysis/'EVIDENCE.md').write_text('\n'.join(lines)+'\n')
pd.DataFrame(records).drop_duplicates('evidence_key').to_csv(root/'key_evidence.csv',index=False)
inputs=[root/'summary/summary.csv',root/'summary/paired_contrasts.csv',root/'numerical_allowance/area_contrasts_with_numerical_allowance.csv',root/'final_audit.json',analysis/'results/scientific_resources.json',Path(__file__)]
(analysis/'results/evidence_report_metadata.json').write_text(json.dumps({'input_and_code_sha256':{str(p.relative_to(analysis)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'generated_markdown_sha256':hashlib.sha256((analysis/'EVIDENCE.md').read_bytes()).hexdigest(),'interpretation':'Analysis-owner claim/evidence handoff, not final report or presentation'},indent=2)+'\n')
print(f'Wrote traceable evidence text and {len(records)} numeric lookups')
