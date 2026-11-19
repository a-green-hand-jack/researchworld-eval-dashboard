import json
from pathlib import Path


def main():
    # @evidence[[paper_data.json#final_evaluation/evaluation_evidence/episodes]]
    summary = json.loads(Path('analysis_summary.json').read_text())
    references = json.loads(Path('references_provenance.json').read_text())
    claims = []

    def add(text, ids, artifacts=None, citations=None):
        record = {'claim': text, 'source_ids': ids, 'citation_keys': citations or []}
        if artifacts:
            record['evidence_refs'] = artifacts
        claims.append(record)

    final_id = ['final.evidence.episodes']
    for condition, values in summary['conditions'].items():
        methods = values['methods']
        add(condition + ': ' + str(summary['n_repeats']) + ' complete paired repetitions; final interval widths, coverage counts, simultaneous bounds and zero-width counts: ' + json.dumps(methods, sort_keys=True),
            final_id, ['paper_data.json#final_evaluation/evaluation_evidence/episodes/*/solution/cases/'+condition+'/observations', 'analysis_summary.json#conditions/'+condition])
        for comparator, comparison in values['comparisons'].items():
            ratio = comparison['mean_candidate_width']/comparison['mean_baseline_width']
            add(condition + ': frozen method versus '+comparator+', ratio of mean widths '+str(ratio)+', stored ratio interval '+str(comparison['ratio_interval'])+', paired difference interval '+str(comparison['difference_interval'])+'.',
                final_id, ['paper_data.json#final_evaluation/evaluation_evidence/episodes/0/solution/summary/'+condition+'/paired_widths/'+comparator])
    gene = summary['conditions']['gene_expression']['methods']
    reduction = 100*(1-gene['candidate']['mean_width']/gene['ppi_plus_plus']['mean_width'])
    add('Gene-expression mean width reduction versus PPI++ is '+str(reduction)+' percent; it is narrower than all three references. All six other conditions have strictly positive paired width-difference intervals versus PPI++.', final_id, ['analysis_summary.json'])
    add('Frozen-method condition-wise coverage ranges from 0.95 to 0.98; all simultaneous lower endpoints are below 0.95. No point estimate or qualification establishes a finite-sample coverage theorem.',
        final_id+['final.metric.empirical_coverage', 'final.metric.minimum_case_coverage', 'final.metric.nominal_coverage'], ['analysis_summary.json'])
    add('Final assessment completed, with outcome qualified and no recorded failures; scientific-validity value zero is conservative non-certification, not evidence of a diagnosed coverage or adaptivity failure.',
        ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct', 'final.metric.failure_fraction', 'final.metric.scientific_validity'],
        ['paper_data.json#final_evaluation', 'source_evidence/resource_manifest.json#scientific_limits'])
    add('Final assessment: 400 seeds 1000 through 1399, seven conditions, nominal coverage 0.95, 128 labeled observations and 8192 unlabeled scores per condition; all methods have paired inputs.',
        final_id+['final.metric.nominal_coverage'], ['source_evidence/evaluate_final.py#L861-L895', 'source_evidence/resource_manifest.json#raw_shapes'])
    add('Stored reporting protocol: simultaneous Clopper-Pearson coverage bounds over seven conditions and four methods; 512 paired bootstrap resamples with random seed 79231 and width comparison quantiles at 0.05/42 and 1-0.05/42.',
        final_id, ['source_evidence/evaluate_final.py#L920-L974', 'source_evidence/resource_manifest.json#uncertainty'], ['ClopperPearson', 'Efron', 'EfronTibshirani', 'Dunn'])
    add('Synthetic targets: linear and uninformative 0.5, nonlinear 0.1+0.8/3, rare outcome 0.01+0.08/3. Constant and permuted controls reuse nonlinear outcomes; constant scores equal 0.5. Gene-expression target is the mean of the final unique-record empirical source, not external biological truth.',
        final_id, ['source_evidence/evaluate_final.py#L861-L895', 'source_evidence/resource_manifest.json#source'], ['Vaishnav'])
    add('Reported main estimand is ratio of mean widths; secondary per-repetition ratio aggregate is capped at 100 and is not interpreted as a percentage width increase. Five rare-outcome PPI++ intervals have zero width.',
        final_id+['final.metric.mean_width_ratio'], ['analysis_summary.json', 'source_evidence/evaluate_final.py'])
    implementation_id = ['result.top_program_01']
    details = [
        ('Selected readable source uses K=min(5,floor(n/2)) outer folds, three shared inner folds, zero/affine/nonlinear selection, and no unlabeled values in fitting or selection.', 'source_evidence/program.py#L154-L267'),
        ('Nonlinear basis contains linear, quadratic and positive-part terms at normalized knots -0.5, 0, 0.5; diagonal ridge penalties 0.1, 2, 4, 4, 4; training quantiles 0.1, 0.9; binary calibrations clipped before signed multiplier.', 'source_evidence/program.py#L69-L151'),
        ('Finite-N multiplier uses covariance divided by (1+n/N) times control variance; inner criterion adds residual variance and n/N times control variance; paired excess-risk plus one standard error must be negative.', 'source_evidence/program.py#L154-L200'),
        ('Returned moments center residuals within folds and take the variance of the weighted combined controls on the shared unlabeled pool, including cross-fold covariance.', 'source_evidence/program.py#L215-L267'),
        ('Student critical value has max(2,n-6) degrees of freedom; binary endpoints are clipped; constant scores and binary counts with fewer than ten successes or failures use label-only inference.', 'source_evidence/program.py#L270-L305'),
        ('Internal bounded certificate uses alpha/(2K) allocation, signed control bounds and a variance-sensitive bounded-mean radius; it is not the returned interval.', 'source_evidence/program.py#L201-L305'),
        ('Deterministic control and fixed-fold variance identities, oracle nonlinear/affine headroom identities, and fold-offset invariance hold within their stated moment and independence assumptions; learned-fold coverage additionally requires stability and a common deterministic L2 limit.', 'source_evidence/METHOD.md#L80-L183'),
    ]
    for text, artifact in details:
        add(text+' The selection record identifies the inspected source location; source content, not the score or tree digest, supports these details. Independently verified byte identity to the final frozen tree is not asserted.', implementation_id, [artifact])
    add('Reference mean intervals use ppi-python 0.2.3, lam=1 versus lam=None, optimized coefficient clipped to [0,1], and normal-approximation mean intervals; sample-variance and return conventions differ from the frozen method.',
        final_id, ['source_evidence/evaluate_final.py#L754-L809', 'source_evidence/ppi.py#L135-L229', 'source_evidence/ppi.py#L1754-L1825'], ['PPI', 'PPIPlus'])
    add('No controlled component ablation or additional task results are supplied; information controls are not component ablations. Observed configuration differences do not identify which component caused the empirical-source gain.',
        final_id, ['paper_data.json#ablation_studies', 'paper_data.json#final_evaluation'])
    add('Original declared environment and analysis-only figure environment use NumPy 1.26.4 and SciPy 1.12.0; Matplotlib figure version is 3.8.4; full original declarations are preserved without claiming they were all installed.',
        final_id, ['source_evidence/requirements.txt', 'REPRODUCIBILITY.md'])
    for reference in references['references']:
        add('Restricted topic-level citation of '+reference['title']+' ('+str(reference['year'])+'); exact-work metadata and available abstract consulted, without following citation graphs.',
            [reference['id']], [reference['consulted_file']], [reference['citation_key']])
    Path('claims_grounding.json').write_text(json.dumps({'claims': claims}, indent=2))
    print('Wrote', len(claims), 'claim mappings.')


if __name__ == '__main__':
    main()
