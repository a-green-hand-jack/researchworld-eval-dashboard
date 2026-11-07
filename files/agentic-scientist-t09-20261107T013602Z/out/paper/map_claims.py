import json
from pathlib import Path


def main():
    # @evidence[[analysis/summary.json]]
    summary = json.loads(Path('analysis/summary.json').read_text())
    references = json.loads(Path('references_provenance.json').read_text())['references']
    claims = []

    def add(claim, source_ids=None, evidence_refs=None, citation_keys=None):
        claims.append({'claim': claim, 'source_ids': source_ids or ['final.evidence.episodes'],
            'citation_keys': citation_keys or [], 'evidence_refs': evidence_refs or [],
            'scope': 'Recorded fixed benchmark or explicitly conditional source-based specification; no causal component attribution'})

    add('The final evaluation completed and reports qualified; this does not establish statistical superiority or validity under arbitrary interference.',
        ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct'],
        ['paper_data.json#/grounding_sources/final.qualification.status',
         'paper_data.json#/grounding_sources/final.qualification.outcome'])
    add('There are 24 seed blocks, four families, six conditions and 576 completed scientific cases; none of their errors was clipped.',
        evidence_refs=['analysis/summary.json', 'paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    for method_index, method in enumerate(summary['methods']):
        values = {name: summary[name][method_index] for name in ['rmse', 'absolute_bias']}
        values['rmse_ci'] = [bound[method_index] for bound in summary['rmse_ci']]
        values['absolute_bias_ci'] = [bound[method_index] for bound in summary['absolute_bias_ci']]
        add(method + ' equal-cell summaries: ' + json.dumps(values),
            evidence_refs=['analysis/summary.json#/rmse', 'analysis/summary.json#/absolute_bias',
                           'analysis/summary.json#/rmse_ci', 'analysis/summary.json#/absolute_bias_ci'])
    add('Endpoint-tuned minus one-hop OLS mean cell RMSE is ' + str(summary['endpoint_minus_onehop_rmse']) +
        ' with 95% paired seed-block interval ' + str(summary['endpoint_minus_onehop_rmse_ci']) +
        '; endpoint-tuned point RMSE is lower in only three of 24 cells, without multiplicity-adjusted win claims.',
        evidence_refs=['analysis/summary.json#/endpoint_minus_onehop_rmse',
                       'analysis/summary.json#/favorable_cells_vs_onehop'])
    for family_index, family in enumerate(summary['families']):
        for condition_index, condition in enumerate(summary['conditions']):
            values = dict(zip(summary['methods'], summary['cell_rmse'][family_index][condition_index]))
            values['endpoint_signed_bias'] = summary['cell_signed_bias'][family_index][condition_index][0]
            values['mean_observed_fit_rmse'] = summary['mean_fit_rmse'][family_index][condition_index]
            add(family + ', ' + condition + ': ' + json.dumps(values),
                evidence_refs=['analysis/summary.json#/cell_rmse', 'analysis/summary.json#/cell_signed_bias',
                               'analysis/summary.json#/mean_fit_rmse'])
    add('Observed-assignment fitted residual RMSE spans ' + str(summary['fit_rmse_range']) +
        ', near unit noise, while threshold and two-hop endpoint errors are substantial; this is descriptive, not causal.',
        evidence_refs=['analysis/summary.json#/fit_rmse_range', 'analysis/observations.csv'])
    for family in summary['families']:
        for condition in [2, 5]:
            support = summary['support'][family + ':' + str(condition)]
            add(family + ' ' + summary['conditions'][condition] + ' seed-mean exposure support: ' +
                json.dumps({field: values['mean'] for field, values in support.items()}),
                evidence_refs=['analysis/summary.json#/support'])
    add('Ratio plots divide cell RMSEs and bootstrap complete seed blocks. The resampling uses 10000 draws, seed 20261107, and 95% percentile intervals. Intervals quantify fixed-benchmark Monte Carlo variation, not causal coverage or graph-population generalization.',
        evidence_refs=['analysis/summary.json#/bootstrap', 'build_paper_artifacts.py'])
    add('The benchmark uses 4096-node synthetic SBM, BA and WS graphs, and fixed Stanford3 with 11586 nodes and 568309 undirected edges. SBM uses four blocks with probabilities .04/.002; BA attachment is five; WS neighborhood is ten with rewiring .15. Covariates have one column. Synthetic topologies vary by seed and Stanford3 topology does not.',
        evidence_refs=['source_evidence/benchmark_manifest.json#/generator',
                       'source_evidence/benchmark_manifest.json#/records',
                       'reproducibility/resources/final/benchmark.npz'])
    add('The outcome model is .5*x + z + spillover + unit Gaussian noise. Six spillovers are 0, .25*e, 2*e, 2*I(e>=.75)+z*e, 2*h, and 2*e under cluster assignment. Recorded GATEs are respectively 1, 1.25, 3, 4, 3, 3. Two-hop exposure includes backtracking; isolates have zero exposure.',
        evidence_refs=['source_evidence/evaluate_final.py#L676-L694',
                       'source_evidence/benchmark_manifest.json#/mechanisms',
                       'paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    add('Individual assignment is Bernoulli(.5). The cluster design uses 32 deterministic balanced graph-BFS clusters and independent Bernoulli(.5) cluster assignment; it changes the joint assignment distribution rather than exposure support alone.',
        evidence_refs=['source_evidence/benchmark_manifest.json#/mechanisms'])
    add('The inspected associated estimator has quadratic one-hop features, saved observed-data standardization, SVD, endpoint-contrast risk grid n*{0,1e-6,1e-4,1e-2,1}, and deterministic minimum selection. Source association is not an independently reconstructed executable-identity proof.',
        ['result.best_correct_score', 'final.evidence.episodes'],
        ['source_evidence/estimator.py#L83-L160', 'source_evidence/program_spec.toml'])
    add('The fixed-penalty risk expression equals squared bias plus contrast variance only under the stated correct-reference and noise assumptions. The selected minimum is not an unbiased selected-risk estimate; empirical calibration is unmeasured.',
        ['result.best_correct_score'], ['source_evidence/estimator.py#L127-L151'], ['Stein1981', 'Efron1986'])
    add('Rank tolerance is max(design shape)*machine epsilon*smax, contrast residual tolerance 1e-8*max(1,norm(q)), residual df n-r-1. The fallback uses hinges .25,.5,.75, ridge 1e-3, and unpenalized intercept. Exact-constant outcomes have zero contrast. Fallback and penalty frequencies are unavailable.',
        ['result.best_correct_score'], ['source_evidence/estimator.py#L69-L81',
         'source_evidence/estimator.py#L119-L158', 'source_evidence/estimator.py#L199-L213'])
    add('The three substantive comparators are difference in means, covariate-adjusted own-treatment OLS and linear one-hop OLS, evaluated on matched cases. OLS endpoint contrast accounts for nonisolated-node fraction.',
        evidence_refs=['source_evidence/evaluate_final.py#L371-L392'])
    add('Component ablations, same-reference GCV comparison, original-hinge matched final comparison, inference coverage, risk calibration and additional noise studies are absent; missing measurements do not establish inferior performance.',
        evidence_refs=['paper_data.json#/ablation_studies', 'paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    add('Recorded control success is 1 and failed-episode fraction 0. Qualification and limited behavioral controls do not establish arbitrary-interference validity; candidate internal diagnostics are unverified.',
        ['final.metric.control_success_fraction', 'final.metric.failed_episode_fraction', 'final.qualification.outcome'],
        ['paper_data.json#/final_evaluation/metrics',
         'paper_data.json#/final_evaluation/evaluation_evidence/candidate_diagnostics_trust'])
    add('The evaluator caps signed errors at magnitude 10 and normalizes by unit noise; it averages cell RMSEs and absolute biases equally, not pooled squared errors.',
        ['final.metric.mean_capped_normalized_rmse', 'final.metric.mean_absolute_capped_normalized_bias', 'final.evidence.episodes'],
        ['source_evidence/benchmark_manifest.json#/aggregation', 'analysis/summary.json'])
    add('Reproduction uses archived PCG64-generated inputs, seed+100003*(family ordinal+1), the listed 24 seeds, declared NumPy1.26.4/SciPy1.13.1/NetworkX3.3, two CPU cores and 8GiB per role, 7200s wall allowance. Recorded elapsed evaluation is approximately629s, not a per-method runtime.',
        ['final.qualification.status'], ['source_evidence/benchmark_manifest.json#/seeds',
         'source_evidence/benchmark_manifest.json#/generator', 'source_evidence/requirements.txt',
         'source_evidence/benchmark_manifest.json#/time_plan', 'source_evidence/final_manifest.json#/compute_usage'])
    for reference in references:
        add('Literature context only: ' + reference['title'] + '. Claims are restricted to the documented reading scope: ' + reference['reading_scope'],
            [reference['id']], [reference['reading_artifact']], [reference['citation_key']])
    Path('claims_grounding.json').write_text(json.dumps({'claims': claims}, indent=2))
    print('Mapped', len(claims), 'claims')


if __name__ == '__main__':
    main()
