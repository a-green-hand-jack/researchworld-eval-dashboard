"""Claim inputs: @evidence[[paper_data.json]] and @evidence[[derived/summary.json]]."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'paper_data.json').read_text())
SUMMARY = json.loads((ROOT / 'derived/summary.json').read_text())
EPISODES = 'final.evidence.episodes'
CLAIMS = []

def claim(text, sources, citations=(), paths=()):
    CLAIMS.append({'claim': text, 'source_ids': list(sources), 'citation_keys': list(citations),
                   **({'implementation_evidence': list(paths)} if paths else {})})

def method_claim(text, paths, citations=()):
    claim(text, [EPISODES, 'result.top_program_01'], citations, paths)

for case_index, name in enumerate(SUMMARY['labels'].values()):
    entries = []
    for method in ('euclidean', 'ilr', 'adaptive'):
        coverage = SUMMARY[method]['coverage']['mean_by_condition'][case_index]
        volume = SUMMARY[method]['volume']['mean_by_condition'][case_index]
        entries.append(f'{method}: coverage={coverage:.9f}, volume={volume:.9f}')
    claim(name + ' held-out condition means in the abstract, main text, Table 1 and Figure 2: ' + '; '.join(entries), [EPISODES])

claim('Adaptive volume is smaller than both references in every held-out heteroskedastic seed; this is an empirical configuration comparison, not population or component superiority.', [EPISODES])
claim('Abstract and all held-out plots use five seeds, six conditions, three methods, nominal coverage 0.90, and all retained seed observations; Figure 3 shows four overlapping descriptive sign strata in C2 and C4.', [EPISODES], paths=['source_evidence/evaluate_final.py:34-45', 'source_evidence/evaluate_final.py:924-928'])
claim('Every entry in the supplementary complete seed-level table, including all coverage Wilson intervals and volume Monte Carlo standard errors, is copied from released final episodes; complete_results.json preserves per-anchor rates and paired errors.', [EPISODES], paths=['build_artifacts.py', 'derived/complete_results.json', 'tables/seed_results.tex'])

metrics = DATA['final_evaluation']['metrics']
for metric in ('marginal_coverage', 'normalized_volume', 'coverage_gap_vs_euclidean', 'volume_gain_vs_euclidean', 'coverage_gap_vs_ilr', 'volume_gain_vs_ilr'):
    claim(f'Equal-weight six-condition final {metric} = {metrics[metric]:.12f}. Coverage contrasts are adaptive minus reference; volume reduction is reference minus adaptive.', ['final.metric.' + metric, EPISODES])

for name, interval in zip(('coverage vs Euclidean', 'volume reduction vs Euclidean', 'coverage vs ILR', 'volume reduction vs ILR'), SUMMARY['paired_bootstrap_95']):
    claim(f'Aggregate paired percentile bootstrap 95% interval for {name}: {interval}. Five seed blocks, 2000 resamples, all six conditions retained; not per-condition or simultaneous.', [EPISODES], ('Efron1979', 'Davison1997'), ('source_evidence/evaluate_final.py:1266-1294',))

for condition in ('C2', 'C4'):
    for method in ('euclidean', 'ilr', 'adaptive'):
        rows = []
        for episode in DATA['final_evaluation']['evaluation_evidence']['episodes']:
            record = next(case for case in episode['solution']['cases'] if case['case'] == condition)
            result = record['details']['candidate'] if method == 'adaptive' else record['details']['baselines'][method]
            rows.append(result['strata'])
        means = [sum(row[index] for row in rows) / len(rows) for index in range(4)]
        claim(f'{condition} {method} mean descriptive sign-stratum coverages in order x1<0, x1>=0, x2<0, x2>=0: {means}; no simultaneous conditional guarantee.', [EPISODES])

claim('The retained worst-stratum summary is 0.0; negative-sign masks in the constant-input control are empty and encoded as zero. It is not an observed zero-coverage subgroup; per-mask sample counts are absent from episode records.', ['final.metric.worst_stratum_coverage', EPISODES], paths=['source_evidence/evaluate_final.py:924-928', 'source_evidence/evaluate_final.py:1254-1263'])
claim('Final evaluation completed and qualified; operational checks do not establish scientific superiority, conditional validity or a comprehensive adaptivity audit. Unknown diagnostics are not inferred.', ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct', EPISODES])
claim('Observed singleton/full-simplex checks report coverage/volume 0/0 and 1/1; query invariance, matched interventions and replay complete in retained records.', [EPISODES], paths=['source_evidence/evaluate_final.py:945-961', 'source_evidence/evaluate_final.py:1189-1229'])

method_claim('Problem is a continuous positive composition in dimensions 3 or 8 with five covariates; target alpha=0.1. No structural zeros, latent-vector coverage or categorical label-set target was evaluated.', ['source_evidence/adaptive.py:1-41', 'source_evidence/evaluate_final.py:776-814'])
method_claim('All location fits use quadratic features: intercept, five inputs, five squares and ten cross-products, 21 columns. Ridge location penalty 0.01 including intercept.', ['source_evidence/adaptive.py:78-89', 'source_evidence/evaluate_final.py:640-650'], ('HoerlKennard1970',))
method_claim('References fit on the first 75% of training rows. Euclidean predictions are clipped at 1e-12 and renormalized; ILR reference uses a raw ILR residual norm.', ['source_evidence/evaluate_final.py:653-680', 'source_evidence/evaluate_final.py:887-903'])
method_claim('Adaptive fit uses deterministic index-modulo-four held-out residuals and a location refit on all rows; variance ridge penalty 5, log-square offset 0.02, prediction clipping [-6,5], standardized-residual clipping [-1000,1000].', ['source_evidence/adaptive.py:108-123'], ('Stone1974', 'Geisser1975'))
method_claim('Shapes are uncentered standardized-residual second moments with identity weight 8 and group-to-pooled weight 32; training-frozen predicted-minimum-component tertiles and right-sided routing select a Cholesky factor. Shapes are not group calibration.', ['source_evidence/adaptive.py:90-131', 'source_evidence/adaptive.py:190-198'], ('SchaferStrimmer2005', 'Chen2010'))
method_claim('For fewer than four training rows a full-data location, zero variance coefficients and identity group factors are used; full-sized evaluated data do not exercise this branch.', ['source_evidence/adaptive.py:103-114'])
claim('Independent score calibration uses ceil((ncal+1)(1-alpha)) with infinity if the rank exceeds ncal; exchangeable frozen-score rank argument gives marginal coverage at least 1-alpha, not a realized finite-test or conditional bound.', [EPISODES, 'ref.Lei2018', 'ref.Angelopoulos2021'], ('Lei2018', 'Angelopoulos2021'), ('source_evidence/evaluate_final.py:859-864',))
claim('Each final condition has 4096 training, 2048 calibration and 3840 test rows; calibration rank 1845; seed labels 1009,2027,3049,4051,5059.', [EPISODES], paths=['source_evidence/final_resource_manifest.json', 'source_evidence/evaluate_final.py:34-45'])
claim('Complete synthetic generator parameters and row provenance in the main text and Supplementary Information are transcribed from inspected code and frozen manifests, including all Gaussian scales, nonlinear means, Dirichlet concentrations, redraw limits and shift settings.', [EPISODES], paths=['source_evidence/evaluate_final.py:776-814', 'source_evidence/final_resource_manifest.json'])
claim('C5 replaces all C2 covariates with zero; C6 cyclically deranges only training covariate rows. These are shared-response matched controls rather than independent tasks.', [EPISODES], paths=['source_evidence/evaluate_final.py:1007-1036'])
claim('Common-volume fractions use 64 evenly indexed anchors and 4096 Dirichlet(1,...,1) probes per anchor; shared membership probes and sample-variance formulas give conditional paired integration errors.', [EPISODES], paths=['source_evidence/evaluate_final.py:907-938', 'source_evidence/evaluate_final.py:1033-1036', 'source_evidence/evaluate_final.py:1206-1229'])
claim('Wilson 95% intervals condition on fitted/calibrated regions and finite test data; conditional Monte Carlo errors do not include fitting or anchor variability. These differ from seed-block bootstrap uncertainty.', [EPISODES, 'ref.Brown2001'], ('Brown2001', 'Efron1979', 'Davison1997'), ('source_evidence/evaluate_final.py:871-880', 'source_evidence/evaluate_final.py:907-938'))
claim('The development-selection utility formula in the main text and supplement is 1-0.8*max(0,0.9-coverage)/0.9-0.2*volume, equal-weighted across specified cases and seeds; it is not a hard coverage constraint or proper distribution forecast score.', [EPISODES], ('Gneiting2007',), ('source_evidence/evaluate_final.py:932-938', 'source_evidence/evaluate_final.py:1245-1263'))

claim('There are three measured development configurations with shared seeds 101,211,307 and counts 2048/1024/2048; auxiliary figures use development data only. The single-split contrast bundles residual data allocation and full-training location refitting.', ['result.total_attempts', 'result.total_evaluated_programs', 'result.top_program_01', 'result.top_program_02', 'result.top_program_03'], paths=['source_evidence/search_resource_manifest.json', 'source_evidence/single_split.py:108-131', 'source_evidence/adaptive.py:108-131', 'derived/search_comparison.json'])
claim('Interpolated covariance uses frozen training quantiles 1/6,1/2,5/6, averages duplicate anchors, clamps endpoints, convexly interpolates shapes and applies Cholesky afterward; no consistent advantage is established by the retained development comparison.', ['result.top_program_01', 'result.top_program_02', 'result.top_program_03'], paths=['source_evidence/interpolated.py:121-151', 'source_evidence/interpolated.py:200-240', 'derived/search_comparison.json'])
claim('No isolated shrinkage, Hellinger, group-calibration, structural-zero, real-data or full-data-refit evaluation supports broader attribution; shifted conditions alter the sampling law and cannot validate exchangeability-based or conditional claims.', [EPISODES, 'result.top_program_01', 'result.top_program_02', 'result.top_program_03'], ('Tibshirani2019', 'Barber2023', 'Barber2021Limits'), ('source_evidence/evaluate_final.py:776-814',))
durations = SUMMARY['duration_seconds']
claim(f'Observed retained seed duration totals range from {min(durations):.9f} to {max(durations):.9f} seconds; not end-to-end or hardware-specific reproduction timings.', [EPISODES])
claim('The evaluated NumPy requirement is 2.2.6; exact resource recreation is not possible from public seed labels alone because private entropy is used. Replay requires frozen NPZ arrays and manifests. Readable evaluated copies, not hashes alone, support implementation facts.', [EPISODES, 'result.top_program_01'], paths=['source_evidence/requirements.txt', 'source_evidence/manifest.json', 'source_evidence/final_resource_manifest.json', 'source_evidence/evaluate_final.py:768-814'])

claim('Foundational related-work distinctions: compositional log-ratio representation and logistic-normal modeling; regression split calibration; quantile adaptation; label-set prediction; cross-fitting versus jackknife+; marginal versus conditional validity; shift correction; proper probabilistic scores.', ['ref.' + key for key in ['Aitchison1982','Egozcue2003','AitchisonShen1980','Pawlowsky2011','Vovk2005','Papadopoulos2002','Lei2018','Romano2019','Romano2020','Ding2023','Barber2021Jackknife','Vovk2012','Barber2021Limits','Tibshirani2019','Barber2023','Gneiting2007']], ['Aitchison1982','Egozcue2003','AitchisonShen1980','Pawlowsky2011','Vovk2005','Papadopoulos2002','Lei2018','Romano2019','Romano2020','Ding2023','Barber2021Jackknife','Vovk2012','Barber2021Limits','Tibshirani2019','Barber2023','Gneiting2007'])

claim('Related Work positions joint covariate-residual Mahalanobis ellipsoids with exchangeability-preserving covariance estimation and covariate-dependent centers/radii against the distinct training-frozen ILR construction. This is literature positioning only, not an evaluated baseline or transferred efficiency guarantee.', ['ref.Henderson2024'], ['Henderson2024'], ['literature/Henderson2024/reading.json', 'literature/Henderson2024/method_excerpt.txt'])

(ROOT / 'claims_grounding.json').write_text(json.dumps({'claims': CLAIMS}, indent=2) + '\n')
print(f'Wrote {len(CLAIMS)} grounded claim groups.')
