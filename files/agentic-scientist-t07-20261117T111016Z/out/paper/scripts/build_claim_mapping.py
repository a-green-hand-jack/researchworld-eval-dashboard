"""Map manuscript claims to the immutable registry and inspectable artifacts."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    paper = json.loads((ROOT / 'paper_data.json').read_text())
    stats = json.loads((ROOT / 'analysis/paper_statistics.json').read_text())
    claims = []

    def add(claim, sources, refs=None, evidence=None):
        claims.append(dict(claim=claim, source_ids=sources, citation_keys=refs or [],
                           evidence_refs=evidence or []))

    all_metrics = ['final.metric.' + metric for metric in ['mae', 'rmse', 'spearman', 'kendall',
                   'irt_mae', 'uniform_mae', 'prior_mae', 'anchor_mae']]
    add('Final comparison: MAE 3.90 pp, RMSE 4.84 pp, Spearman 0.816, Kendall 0.672 for the frozen package; baseline MAEs IRT 5.91, uniform 10.52, prior 8.34, anchors 15.67 pp.',
        all_metrics, evidence=['paper_data.json#/final_evaluation/metrics'])
    add('Nine final matrices, seeds 1009/2003/3001, budgets 5/10/25; 81 non-replay normal cells. Normal BBH replay excluded. Final and development results remain separate.',
        ['final.evidence.episodes'], evidence=['analysis/paper_statistics.json#/cell_count'])
    add('Development cases ARC-Challenge, IFEval, Commonsense, and GSM are not pooled into final results.',
        ['result.top_program_01'], evidence=['paper_data.json#/best_correct/evaluation_evidence/episodes'])
    add('Final evaluation completed and qualified; no failed normal cells recorded. This does not establish generality or an unrecorded gate diagnosis.',
        ['final.qualification.status', 'final.qualification.outcome', 'final.evidence.episodes'],
        evidence=['paper_data.json#/final_evaluation', 'analysis/paper_statistics.json#/uncertainty'])
    for method, values in stats['aggregate'].items():
        add(f"Table 1 equal-cell aggregate, {method}: " + json.dumps(values) +
            ('; constant-prior rank correlations omitted as undefined, not interpreted.' if method == 'prior_mae' else ''),
            ['final.evidence.episodes'] + (['final.metric.' + method] if method != 'selected' else all_metrics[:4]),
            evidence=['analysis/paper_statistics.json#/aggregate/' + method])
    for method, values in stats['uncertainty']['comparisons'].items():
        add(f'Paired aggregate difference and conditional 95% interval versus {method}: ' + json.dumps(values),
            ['final.evidence.episodes'], evidence=['analysis/paper_statistics.json#/uncertainty/comparisons/' + method])
    add('200 paired lineage-block percentile draws, within-benchmark resampling, budgets/seeds retained, equal benchmark weights; repeated uncertainty object is used only once. Bootstrap seed 1729. No benchmark resampling or source refitting.',
        ['final.evidence.episodes'], ['Efron1979', 'Efron1987'],
        ['source_evidence/evaluator/evaluate_final.py#L1065', 'analysis/paper_statistics.json#/uncertainty'])
    for budget in stats['budgets']:
        add(f'Budget {budget}, equal benchmark/seed averages: ' + json.dumps(stats['by_budget'][str(budget)]),
            ['final.evidence.episodes'], evidence=['analysis/paper_statistics.json#/by_budget/' + str(budget)])
    for seed in stats['seeds']:
        add(f'Seed {seed}, equal benchmark/budget averages: ' + json.dumps(stats['by_seed'][str(seed)]),
            ['final.evidence.episodes'], evidence=['analysis/paper_statistics.json#/by_seed/' + str(seed)])
    for case in stats['cases']:
        add(f'{case}, complete seed-averaged benchmark-budget MAEs and diagnostic rankings: ' + json.dumps(stats['by_case_budget'][case]),
            ['final.evidence.episodes'], evidence=['analysis/paper_statistics.json#/by_case_budget/' + case])
    add('Local IRT has lower seed-mean MAE on HELM MATH at 5/10/25, LegalBench at 5/25, MedQA at 10/25. The package has lower means on each leaderboard matrix and MMLU at each evaluated budget. No per-cell significance claims.',
        ['final.evidence.episodes'], evidence=['analysis/paper_statistics.json#/local_irt_reversals', 'analysis/paper_statistics.json#/by_case_budget'])
    add('MedQA package MAE rises from 6.68 pp at 5 items to 7.47 at 10, falling to 5.54 at 25; no diagnosed cause.',
        ['final.evidence.episodes'], evidence=['analysis/paper_statistics.json#/by_case_budget/med_qa'])
    add('All-zero target observations give MAE 21.58 pp; independently cyclically shifted source rows give 6.26 pp, versus ordinary-condition 3.90 pp. These are observation/representation interventions, not component ablations or proofs of validity.',
        ['final.metric.constant_mae', 'final.metric.permuted_mae', 'final.metric.mae', 'final.evidence.episodes'],
        evidence=['source_evidence/evaluator/evaluate_final.py#L844'])
    implementation = [
        ('Source counterpart weighted covariance, full-score target, greedy conditional score-covariance criterion, content-group uniqueness, ridge/offset decoder, clipping and zero-query prior; Schur-complement rationale is an algebraic derivation, not an empirical component claim.',
         ['source_evidence/selected/src/surrogate.py#L6', 'source_evidence/selected/src/surrogate.py#L31', 'source_evidence/selected/src/surrogate.py#L75']),
        ('Source counterpart lineage-disjoint refitting/tuning, two folds and 5/10/25 prefixes; optional outer nested decoder tuning.',
         ['source_evidence/selected/src/surrogate.py#L111', 'source_evidence/selected/src/nonlinear_decoder.py#L142']),
        ('Source counterpart optional log-odds shift, prefix-matched residual ridge and linear fallback; per-case activation and isolated benefit unverified.',
         ['source_evidence/selected/src/nonlinear_decoder.py#L18', 'source_evidence/selected/src/nonlinear_decoder.py#L65']),
        ('Settings cap 4 and fitting allowance 200; listed capped hyperparameters, 64 shift iterations, bounded shifts and clipping constants describe supplied counterpart, not selected final branch diagnostics.',
         ['source_evidence/selected/src/nonlinear_decoder.py#L18', 'source_evidence/selected/src/nonlinear_decoder.py#L129', 'source_evidence/selected/src/surrogate.py#L111', 'source_evidence/evaluator/evaluate_final.py#L930']),
        ('Local baselines: content-group-mass weighted clipped uniform estimator, constant prior, normalized response embeddings/farthest-point anchors, logistic IRT with 200 source and 40 target updates and clipped initialization. Not exact published systems.',
         ['source_evidence/evaluator/evaluate_final.py#L580', 'source_evidence/evaluator/evaluate_final.py#L598']),
        ('Lineage-weighted MAE and RMSE, lineage-mean rank correlations, average of cell RMSE rather than pooled RMSE.',
         ['source_evidence/evaluator/evaluate_final.py#L556', 'source_evidence/evaluator/evaluate_final.py#L1014', 'source_evidence/evaluator/evaluate_final.py#L1040']),
        ('Known-lineage and common-stem safeguards are metadata-limited and do not prove undocumented ancestry or pretraining independence; retained-column scores differ from unreconciled originals.',
         ['source_evidence/manifests/bbh_manifest.json#/limitations', 'source_evidence/manifests/bbh_manifest.json#/normalization']),
        ('Readable selection counterpart is supplied, but byte-for-byte source-tree identity is not independently certified. Digests are provenance, not substantive implementation support.',
         ['source_evidence/inventory.json', 'paper_data.json#/final_evaluation/program_tree_sha256']),
    ]
    for claim, artifacts in implementation:
        add(claim, ['final.evidence.episodes'], evidence=artifacts)
    add('No controlled component ablations, per-case branch activation evidence, or new-benchmark interval; conclusions concern recorded packages, not isolated effects or guaranteed transfer.',
        ['final.evidence.episodes'], evidence=['paper_data.json#/ablation_studies', 'paper_data.json#/final_evaluation/evaluation_evidence/candidate_diagnostics_trust'])
    reference_records = json.loads((ROOT / 'references_provenance.json').read_text())['references']
    for record in reference_records:
        add('Literature/software context, limited to the consulted source scope: ' + record['title'],
            [record['id']], [record['citation_key']], [record['consulted_path']])
    allowed_ids = set(paper['grounding_sources']) | {record['id'] for record in reference_records}
    assert all(source in allowed_ids for claim in claims for source in claim['source_ids'])
    (ROOT / 'claims_grounding.json').write_text(json.dumps({'claims': claims}, indent=2) + '\n')
    sidecar = dict(schema_name='scientific-evidence.artifact-manifest',
                   artifact=dict(path='claims_grounding.json', kind='derived'),
                   derived_from=['@' + 'evidence' + '[' * 2 + target + ']' * 2
                                 for target in ['paper_data.json', 'analysis/paper_statistics.json', 'references_provenance.json']],
                   generated_by=dict(script_path='scripts/build_claim_mapping.py'))
    (ROOT / 'claims_grounding.json.prov.json').write_text(json.dumps(sidecar, indent=2) + '\n')
    print(f'Wrote {len(claims)} grounded claim mappings.')


if __name__ == '__main__':
    main()
