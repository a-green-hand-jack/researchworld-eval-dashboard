import json
from pathlib import Path


def main():
    data = json.loads(Path('paper_data.json').read_text())
    summary = json.loads(Path('analysis/summary.json').read_text())
    provenance = json.loads(Path('references_provenance.json').read_text())
    evidence_anchor = '@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'
    claims = []

    def add(claim, source_ids=None, supporting_artifacts=None, locator=None, citation_keys=None):
        entry = {'claim': claim, 'source_ids': source_ids or ['final.evidence.episodes'],
                 'citation_keys': citation_keys or []}
        if supporting_artifacts:
            entry['supporting_artifacts'] = supporting_artifacts
        if locator:
            entry['evidence_locator'] = locator
        claims.append(entry)

    add('The independent final evaluation completed, was qualified, and reports successful specified checks; qualification is not a superiority or shifted-validity result.',
        ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct', 'final.metric.control_check_pass_rate'])
    add('The final study comprises eight seeds, six conditions (logistic-normal IID, Dirichlet IID, shifted Dirichlet at K=3 and 8), and alpha=0.05,0.10,0.20. All recorded cases are complete.',
        supporting_artifacts=['source_evidence/evaluate_final.py:37', 'source_evidence/data_manifest.json'],
        locator='/final_evaluation/evaluation_evidence/episodes')
    add('Final seeds are 1009,1013,1019,1021,1031,1033,1039,1049; train/calibration/test sizes are 1024/512/2048 with six covariates.',
        supporting_artifacts=['source_evidence/data_manifest.json', 'source_evidence/evaluate_final.py:727'])
    implementation_claims = [
        ('Positive observed continuous compositions, not categorical labels or latent probabilities, are the response. The fixed Helmert ILR basis has K-1 coordinates.', 'source_evidence/selected_model.py:37'),
        ('The design uses intercept, raw features, squares, sines and x0*x1. Center and log-residual ridge penalties are 1 and 10; intercept penalty is 1e-8; residual floor is .02.', 'source_evidence/selected_model.py:98'),
        ('Centers are clipped to [-100,100] and positive base and corrected scales to [1e-4,100]. The base log-residual fit uses in-sample residuals; correction moments are cross-fitted.', 'source_evidence/selected_model.py:114'),
        ('Three-fold training permutations use random seed 0. Moment features use standard deviation floor 1e-8; standardized residuals use scale floor 1e-4; queries are batched in 128 rows.', 'source_evidence/selected_model.py:109'),
        ('Local moments average squared standardized ILR residuals over K-1 coordinates, Gaussian-smooth them over standardized covariates, and shrink the ratio toward 1 by prior mass.', 'source_evidence/selected_model.py:133'),
        ('Moment ratios are clipped to [.25,4]; a common row-scalar multiplies all ILR scales, preserving their within-row ratios. The correction blends are 0,.5,1; bandwidths .5*sqrt(6),sqrt(6); prior masses 10,50.', 'source_evidence/selected_model.py:172'),
        ('Nested three-fold training selection uses swapped pseudo-calibration/evaluation halves; the row-weighted alpha-averaged log arithmetic mean ILR-box volume is minimized, with smaller blend breaking ties.', 'source_evidence/selected_model.py:275'),
        ('The selector uses exact finite ranks, Gaussian-loss fallback for unavailable ranks or invalid radii/objectives, and a neutral tiny-sample fallback. Realized fallback frequencies and selected settings are not retained.', 'source_evidence/selected_model.py:188'),
        ('Global constant scale multiplication cancels its conformal radius, apart from clipping. At alpha .05, 18 internal calibration observations are insufficient for a finite rank; 19 suffice. Numerical invariance assertions are source checks, not a scientific ablation.', 'source_evidence/selected_model.py:237'),
        ('Independent final calibration uses ceil((m+1)*(1-alpha)) order statistic with infinity when unavailable, and closed membership. It is not selected on calibration labels.', 'source_evidence/evaluate_final.py:836'),
        ('The unscaled ILR comparator sets scales to one at the same center. Simplex max uses a joint coordinate maximum. Bonferroni calibrates K simplex coordinates at alpha/K, not ILR coordinates.', 'source_evidence/evaluate_final.py:857'),
        ('Mass is uniform-simplex probability content estimated at 128 test contexts using 1024 shared Dirichlet(1) probes; utility equals (1-mass)*max(0,1-absolute_coverage_error/(1-alpha)). Errors are absolute before averaging.', 'source_evidence/evaluate_final.py:727'),
        ('IID covariates are uniform on [-1.5,1.5]^6, logistic-normal noise standard deviation is .25, Dirichlet concentration is 4+35/(1+exp(2*x0)), and gamma coordinates are floored at 1e-12 before closure.', 'source_evidence/evaluate_final.py:727'),
        ('The fixed mean is .7*sin(XW)+.3*x0*cos(j), with W[l,j]=sin(l*(K-1)+j+1)/3. Shift changes only test X to clipped N(.8,1) in [-2.5,3], changing covariate support as well as frequency.', 'source_evidence/evaluate_final.py:727'),
        ('Independent random streams use SeedSequence([seed,case,split,202611]); reference split index is 3. Frozen resources are checked for numeric row-content disjointness, positivity, closure and hashes.', 'source_evidence/evaluate_final.py:727'),
        ('Per-context mass resolution is 1/1024. Zero hits have a one-sided .95 upper bound 1-.05**(1/1024)=.00292124, not zero mass. Averaged plugin context standard errors do not quantify joint mass uncertainty.', 'source_evidence/evaluate_final.py:905'),
        ('The evaluator resamples seed blocks 20000 times using RNG seed 62845. Paired utility intervals have optional tail probability .05/(2*54); volume intervals are unadjusted. Repeated uncertainty summaries are deduplicated.', 'source_evidence/evaluate_final.py:1036'),
        ('Constant-input queries use training-mean features; nonidentity permutations rotate calibration and test rows separately. Whole-simplex and zero-radius references are degenerate metric controls, not useful calibrated baselines.', 'source_evidence/evaluate_final.py:929'),
        ('The evaluated environment requires CPython 3.11 or 3.12 and NumPy 1.26.4 with native Linux isolation. No external dataset is downloaded for the synthetic study.', 'source_evidence/evaluate_final.py:1186'),
    ]
    for text, artifact in implementation_claims:
        add(text, ['final.evidence.episodes', 'result.top_program_01'], [artifact])
    add('The matched final evidence does not contain a selector-only Gaussian-versus-rank comparison or an original-initializer comparison. The earlier configurations are development evidence, not final ablations.',
        ['final.evidence.episodes', 'result.top_program_01', 'result.top_program_02', 'result.top_program_03'],
        ['source_evidence/selected_model.py:275', 'source_evidence/development_gaussian.py:185',
         'source_evidence/development_joint.py:152', 'paper_data.json'])
    add('IID and shifted scaled-ILR absolute coverage errors are 0.013562011718750005 and 0.13034261067708333, respectively.',
        ['final.metric.iid_coverage_error', 'final.metric.shift_coverage_error'])
    add('The scaled-ILR mean utility is 0.661819668104677, mass 0.3034934467739529, and aggregate utility gap to the strongest standard comparator is 0.011594669497844157.',
        ['final.metric.final_score', 'final.metric.mean_volume', 'final.metric.baseline_utility_gap'])
    for method, values in summary['methods'].items():
        add('Main summary table, ' + method + ': ' + json.dumps(values),
            supporting_artifacts=['analysis/summary.json', 'build_analysis.py'], locator='analysis/summary.json#/methods/' + method)
    for baseline, values in summary['paired_overall'].items():
        add('New retained-data descriptive paired aggregate utility contrast, scaled ILR minus ' + baseline + ': ' + json.dumps(values),
            supporting_artifacts=['analysis/summary.json', 'build_analysis.py'], locator='analysis/summary.json#/paired_overall/' + baseline)
    for case, values in summary['coverage'].items():
        rows = []
        for alpha_index, alpha in enumerate(summary['alphas']):
            per_seed = [next(item for item in episode['solution']['cases'] if item['case'] == case)['methods']['scaled_ilr'][alpha_index]
                        for episode in data['final_evaluation']['evaluation_evidence']['episodes']]
            rows.append({'alpha': alpha, 'mass': sum(item['volume'] for item in per_seed)/len(per_seed),
                         'utility': sum(item['utility'] for item in per_seed)/len(per_seed)})
        add('Supplementary scaled-ILR mass and utility means for ' + case + ': ' + json.dumps(rows),
            supporting_artifacts=['analysis/coverage_table.tex', 'build_analysis.py'])
        add('Coverage figure, text and extended table for ' + case + ': ' + json.dumps(values),
            supporting_artifacts=['analysis/summary.json', 'build_analysis.py'], locator='analysis/summary.json#/coverage/' + case)
        for baseline, comparisons in summary['retained_uncertainty'][case]['paired_baselines'].items():
            add('Complete paired utility/mass contrasts for ' + case + ', scaled ILR minus ' + baseline + ': ' + json.dumps(comparisons),
                supporting_artifacts=['analysis/summary.json'],
                locator='/final_evaluation/evaluation_evidence/episodes/0/solution/seed_block_uncertainty/' + case + '/paired_baselines/' + baseline)
    for group, values in summary['feature_groups_alpha_010'].items():
        add('Descriptive sign-of-x0 group mean coverage at alpha .10, ' + group + ': ' + json.dumps(values),
            supporting_artifacts=['analysis/summary.json', 'build_analysis.py'])
    add('Additional coverage, overall utility and group intervals resample all seed blocks jointly 20000 times at bootstrap seed 20261117, retaining condition and level dependence.',
        supporting_artifacts=['analysis/summary.json', 'build_analysis.py'])
    add('Favorable simplex-baseline contrasts concentrate in IID Dirichlet K8; all shifted utility differences are negative and all shifted mass differences positive. This is not uniform dominance.',
        supporting_artifacts=['analysis/summary.json#/retained_uncertainty'])
    add('Joint unscaled maximum-residual and coordinatewise Bonferroni rectangles are described by Fan and Sesia, Algorithms S2 and S1 respectively; simplex intersection is imposed by this evaluation, not attributed to that source.',
        ['ref.openalex.W7116099311', 'final.evidence.episodes'],
        ['literature/FanSesia2025.json', 'source_evidence/evaluate_final.py:857'],
        locator='literature/FanSesia2025.json#/excerpts/algorithms_S1_S2', citation_keys=['FanSesia2025'])
    for reference in provenance['references']:
        add('Background citation: ' + reference['title'] + '; access scope: ' + reference['read_scope'],
            [reference['id']], [reference['read_artifact']], citation_keys=[reference['citation_key']])
    add('Independent split-conformal marginal coverage follows the standard exchangeable-score rank argument conditional on training, not exact realized, feature-conditional, or shifted coverage.',
        ['ref.Lei2018', 'ref.Angelopoulos2021'], ['source_evidence/evaluate_final.py:836'], citation_keys=['Lei2018'])
    claims_path = Path('claims_grounding.json')
    claims_path.write_text(json.dumps({'claims': claims}, indent=2))
    sidecar = {'schema_name': 'scientific-evidence.artifact-manifest',
               'artifact': {'path': 'claims_grounding.json', 'kind': 'derived'},
               'derived_from': [evidence_anchor, '@evidence[[analysis/summary.json]]',
                                '@evidence[[references_provenance.json]]', '@evidence[[source_evidence/selected_model.py]]'],
               'generated_by': {'script_path': 'build_claims.py'}}
    Path('claims_grounding.json.prov.json').write_text(json.dumps(sidecar, indent=2))
    print('Mapped', len(claims), 'claims; qualification independently:', summary['qualification'])


if __name__ == '__main__':
    main()
