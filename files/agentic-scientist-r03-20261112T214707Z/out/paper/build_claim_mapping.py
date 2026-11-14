import hashlib
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent


def main():
    # @evidence[[paper_data.json#/final_evaluation]]
    paper = json.loads((ROOT / 'paper_data.json').read_text())
    derived = json.loads((ROOT / 'derived_results.json').read_text())
    references = json.loads((ROOT / 'references_provenance.json').read_text())
    claims = []

    def add(claim, source_ids, evidence_refs, citation_keys=None, **extra):
        claims.append({'claim': claim, 'source_ids': source_ids, 'citation_keys': citation_keys or [],
                       'evidence_refs': evidence_refs, **extra})

    for method, metric in [('latent', 'candidate_mae'), ('greedy_ridge', 'greedy_ridge_mae'),
                           ('random_lowrank', 'random_lowrank_mae'), ('historical_mean', 'historical_mean_mae'),
                           ('score_average', 'observed_copy_mae')]:
        value = paper['final_evaluation']['metrics'][metric]
        add(f'{method} aggregate remaining-target normalized MAE is {value:.5f}.',
            ['final.metric.' + metric], [f'paper_data.json#/final_evaluation/metrics/{metric}'],
            scope='Original non-replay final cases; historical mean and score average use latent-policy remaining sets.')
    add('The latent procedure has lower aggregate remaining-target and common-audit MAE than the two evaluated predictive baseline pipelines; this is descriptive, not an isolated component effect or significance claim.',
        ['final.metric.candidate_mae', 'final.metric.greedy_ridge_mae', 'final.metric.random_lowrank_mae', 'final.evidence.episodes'],
        ['derived_results.json#/aggregate_original', 'build_paper_figures.py'],
        aggregation='Equal original condition-seed cases after equal checkpoint and row/proxy-family means.')
    for method, value in derived['aggregate_original']['audit'].items():
        add(f'{method} aggregate common-audit normalized MAE is {value:.5f}.', ['final.evidence.episodes'],
            ['derived_results.json#/aggregate_original/audit/' + method, 'build_paper_figures.py'],
            derivation='Average original non-replay case audit means; historical mean uses mean_audit_mae in observation records.')
    for case in derived['cases']:
        if case['arm'] != 'original':
            continue
        add(f"Original {case['condition']} split {case['seed']}: latent/ridge remaining MAE "
            f"{case['remaining']['latent']:.5f}/{case['remaining']['greedy_ridge']:.5f}; "
            f"audit MAE {case['audit']['latent']:.5f}/{case['audit']['greedy_ridge']:.5f}.",
            ['final.evidence.episodes'], ['paper_data.json#' + case['pointer']],
            values={'remaining': case['remaining'], 'audit': case['audit']})
    add('Family-disjoint seed 4021 reverses the latent-versus-ridge comparison on both remaining and common-audit targets. No evaluator evidence identifies a validity or adaptivity failure as its cause.',
        ['final.evidence.episodes'], ['derived_results.json#/cases'],
        scope='A measured performance reversal, not a diagnosed mechanism or qualification failure.')
    for condition in ['model_group', 'family_disjoint']:
        for method in ['latent', 'greedy_ridge', 'random_lowrank']:
            for budget in [1, 2, 4, 8]:
                rows = [row for row in derived['audit_budget_curves'] if row['condition'] == condition and row['method'] == method and row['k'] == budget and row['arm'] == 'original']
                mean = sum(row['mae'] for row in rows) / len(rows)
                add(f'{condition}, {method}, k={budget}: descriptive mean common-audit MAE {mean:.5f}.',
                    ['final.evidence.episodes'], ['paper_data.json#' + row['pointer'] for row in rows],
                    individual_split_values={str(row['seed']): row['mae'] for row in rows},
                    derivation='Checkpoint-specific equal-row/model-group or equal-proxy-family/family-disjoint means, then equal split means.',
                    plot_group='common_target_budget_comparison')
    add('Family-disjoint mean audit error at k=2 favors ridge over the latent procedure; average audit error for each method decreases over the measured budgets without establishing universal budget sufficiency.',
        ['final.evidence.episodes'], ['derived_results.json#/audit_budget_curves'])
    for metric in ['permuted_mae', 'permutation_gap']:
        add(f"Latent {metric} is {paper['final_evaluation']['metrics'][metric]:.5f}.",
            ['final.metric.' + metric], ['paper_data.json#/final_evaluation/metrics/' + metric])
    add('Column-permuted history increases common-audit error for the evaluated predictive pipelines; plotted values include every original/permuted split pair and descriptive means. Entire pipelines are refit and retuned, so this is not a covariance-only or adaptation-only ablation.',
        ['final.evidence.episodes'], ['derived_results.json#/cases', 'source_evidence/protocol/evaluate_final.py#permute_history'],
        plot_group='historical_alignment_control',
        plotted_records=[{'seed': case['seed'], 'condition': case['condition'], 'arm': case['arm'], 'audit': case['audit'], 'pointer': case['pointer']} for case in derived['cases']])
    for field in ['status', 'outcome']:
        value = paper['grounding_sources']['final.qualification.' + field]['value']
        add(f'Final evaluation qualification {field} is {value}; operational qualification does not establish generalization, validity beyond checked predicates, or scientific superiority.',
            ['final.qualification.' + field], ['paper_data.json#/grounding_sources/final.qualification.' + field + '/value'])
    add('The final evidence contains three split seeds (4001, 4009, 4021), two holdout conditions, 48 target rows per condition-seed, four checkpoints (1,2,4,8), original/permuted arms, and a zero-weight reset replay.',
        ['final.evidence.episodes'], ['paper_data.json#/final_evaluation/evaluation_evidence/episodes', 'source_evidence/protocol/data_manifest.json#/production'],
        scope='Conditions within one embedding benchmark source, not multiple independent datasets.')
    add('The final source is pinned English MTEB; panels have 48 benchmark-context columns, eight never-queryable audit columns, 88-99 historical rows, and at least four recorded audit cells per held-out row. Availability and content grouping constrain the population; name-defined families are lineage proxies.',
        ['final.evidence.episodes'], ['source_evidence/protocol/data_manifest.json', 'source_evidence/protocol/evaluate_final.py#load_resources', 'source_evidence/protocol/evaluate_final.py#score_cells'],
        source_scope='Final source ID identifies the evaluated observations; readable manifest and evaluator substantively support protocol settings, not the evaluation hash alone.')
    add('Scalar scores are normalized using declared metric bounds, including (s+1)/2 for signed Spearman; dataset revision stays part of column identity, no imputed cell is a scored target, and no held-out extrema define normalization.',
        ['final.evidence.episodes'], ['source_evidence/protocol/evaluate_final.py#score_cells', 'source_evidence/protocol/evaluate_final.py#losses'])
    add('Observed-data factor fitting, Gaussian conditional prediction, bounded mixture median prediction, and moment-matched off-diagonal transfer rules are implemented in the selected preserved source. Equation-level optimality applies to the fitted distribution, not real-data Bayes optimality. Dense row-state covariance storage and rank-one updates have quadratic benchmark-count complexity.',
        ['result.top_program_01', 'final.evidence.episodes'], ['source_evidence/latent/covariance.py', 'source_evidence/latent/mixture.py', 'source_evidence/protocol/selection_manifest.json'],
        source_scope='Registry IDs and selection manifest establish provenance; readable code is the substantive implementation evidence.')
    add('Historical model choice uses ranks 2/4/8, residual shrinkage 2/12, optional mixture sizes 2/4, regularization 2/8, at most twelve validation/profile sweeps, thirty outer fitting sweeps, and twenty-five median bisections; the internal replacement margin is max(1e-4,0.5 paired SE). Further floors, initializations and validation dimensions are described directly from the source, not from unverified runtime diagnostics.',
        ['result.top_program_01'], ['source_evidence/latent/covariance.py', 'source_evidence/latent/mixture.py', 'source_evidence/protocol/evaluate_final.py#main'],
        source_scope='Static settings only; no assertion about realized component, fallback, or selector choices.')
    add('Random low-rank uses masked alternating ridge with ranks 2/4, penalties 0.1/1, eight validation sweeps and thirty final sweeps. Greedy ridge uses overlap-shrunk correlations with at least four pairs, n/(n+10) shrinkage, and penalty 0.1.',
        ['final.evidence.episodes'], ['source_evidence/protocol/evaluate_final.py#factor_fit', 'source_evidence/protocol/evaluate_final.py#tune_fit', 'source_evidence/protocol/evaluate_final.py#native_ridge'],
        source_scope='Readable evaluated baseline implementation, plus retained baseline observation records.')
    add('The designated reset replay matches selected columns and predictions under the evaluator check and is excluded from performance means. Candidate-generated diagnostics are explicitly unverified; no externally verified component ablations or additional dataset evaluations are provided.',
        ['final.evidence.episodes', 'final.qualification.outcome'], ['paper_data.json#/final_evaluation/evaluation_evidence', 'paper_data.json#/ablation_studies', 'source_evidence/protocol/evaluate_final.py#replay_equal'])
    for reference in references['references']:
        add('Literature positioning: ' + reference['title'] + '; consulted scope is recorded and no unrun published method comparison is claimed.',
            [reference['id']], [reference['reading_record'], 'literature/reading_notes.md'],
            citation_keys=[reference['citation_key']])
    allowed = set(paper['grounding_sources']) | {reference['id'] for reference in references['references']}
    for claim in claims:
        assert set(claim['source_ids']) <= allowed
    output = ROOT / 'claims_grounding.json'
    output.write_text(json.dumps({'claims': claims}, indent=2) + '\n')
    sidecars = {'claims_grounding.json': ['paper_data.json', 'derived_results.json', 'references_provenance.json'],
                'paper.tex': ['paper_data.json', 'derived_results.json', 'references.bib', 'source_evidence/latent/covariance.py', 'source_evidence/latent/mixture.py'],
                'references.bib': [reference['reading_record'] for reference in references['references']],
                'references_provenance.json': [reference['reading_record'] for reference in references['references']]}
    for name, inputs in sidecars.items():
        path = ROOT / name
        payload = {'schema_name': 'scientific-evidence.artifact-manifest',
                   'artifact': {'path': name, 'kind': 'manuscript' if name == 'paper.tex' else 'derived',
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
                   'derived_from': ['@' + 'evidence[[' + source + ']]' for source in inputs],
                   'generated_by': {'script_path': 'build_claim_mapping.py'},
                   'notes': 'Mapping/sidecar emission only; paper and consulted references are authored from the listed inputs.'}
        path.with_name(path.name + '.prov.json').write_text(json.dumps(payload, indent=2) + '\n')
    snapshot = {}
    for path in (ROOT / 'source_evidence').rglob('*'):
        if path.is_file() and path != ROOT / 'source_evidence/manifest.json':
            snapshot[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / 'source_evidence/manifest.json').write_text(json.dumps({'files': snapshot,
        'selected_source': 'results/ideas/02_value_adaptive_latent_mixtures_for_absolute_error_benchmark_prediction/program_1',
        'scope': 'Readable copied source supports implementation claims; hashes identify provenance, not scientific behavior.'}, indent=2) + '\n')
    print('Mapped', len(claims), 'claims')


if __name__ == '__main__':
    main()
