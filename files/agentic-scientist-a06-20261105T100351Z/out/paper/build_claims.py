import json
from pathlib import Path


def main():
    # @evidence[[paper_data.json#/final_evaluation]]
    # @evidence[[analysis/summary.json]]
    data = json.loads(Path('paper_data.json').read_text())
    summary = json.loads(Path('analysis/summary.json').read_text())
    references = json.loads(Path('references_provenance.json').read_text())
    claims = []

    def add(claim, source_ids, evidence_refs=None, citation_keys=None):
        claims.append({'claim': claim, 'source_ids': source_ids, 'citation_keys': citation_keys or [],
                       'evidence_refs': evidence_refs or ['paper_data.json#/final_evaluation/evaluation_evidence/episodes']})

    for episode_index, episode in enumerate(data['final_evaluation']['evaluation_evidence']['episodes']):
        for case_index, case in enumerate(episode['solution']['cases']):
            add(f'Complete seed-table and machine-readable result row, seed {episode["seed"]}, condition {case["case"]}: {json.dumps(case["metrics"], sort_keys=True)}.',
                ['final.evidence.episodes'],
                [f'paper_data.json#/final_evaluation/evaluation_evidence/episodes/{episode_index}/solution/cases/{case_index}',
                 'analysis/condition_results.csv', 'tables/seed_results.tex'])

    for label, metrics in summary['condition_means'].items():
        add(f'{label}: equal-seed means for all reported condition metrics: {json.dumps(metrics, sort_keys=True)}.',
            ['final.evidence.episodes'], [f'analysis/summary.json#/condition_means/{label}',
                                         'paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
        add(f'{label}: protected relative error reduction versus same-winner reuse is {summary["reductions_percent"][label]:.8f} percent.',
            ['final.evidence.episodes'], [f'analysis/summary.json#/reductions_percent/{label}', 'build_artifacts.py'])
    for regime, metrics in summary['regime_means'].items():
        add(f'Synthetic regime {regime}: all condition means, including bias, optimism, interval coverage, and width: {json.dumps(metrics, sort_keys=True)}.',
            ['final.evidence.episodes'], [f'analysis/summary.json#/regime_means/{regime}', 'analysis/regime_results.csv'])
    for observation in summary['audit_differences']:
        add('Paired selected-minus-fixed audit comparison: ' + json.dumps(observation, sort_keys=True),
            ['final.evidence.episodes'], ['analysis/summary.json#/audit_differences',
                                         'source_evidence/evaluate_final.py#L987'])
    final = data['final_evaluation']
    for metric in ['report_mse', 'reuse_mse', 'full_budget_naive_mse', 'honest_half_mse',
                   'fixed_prompt_mse', 'random_prompt_mse', 'control_failure_rate', 'replay_discrepancy']:
        add(f'Equal-weight supplied aggregate {metric} = {final["metrics"][metric]}.', ['final.metric.' + metric],
            ['paper_data.json#/final_evaluation/metrics/' + metric])
    add('Protected mean error is lower than same-winner reuse in both sixteen-prompt conditions in each evidence family, but full reuse has lower mean error in every synthetic condition. Fixed/random and alternative-half comparisons use their own prompt targets and do not isolate a reporting component.',
        ['final.evidence.episodes', 'final.metric.report_mse', 'final.metric.reuse_mse', 'final.metric.full_budget_naive_mse'],
        ['analysis/summary.json#/condition_means', 'source_evidence/evaluate_final.py#L760'])
    add('Eight of ten K=16 selected-minus-fixed audit intervals include zero; both positive exclusions are seed 5059. All K=1 paired differences are identically zero. All ten K=16 report intervals contain the finite audit reference; one K=1 real interval does not.',
        ['final.evidence.episodes'], ['analysis/summary.json#/audit_differences', 'analysis/condition_results.csv'])
    add('The strict sign-disagreement diagnostic compares protected selected-prompt report minus all-question fixed score with the reference selected-minus-fixed accuracy. Four of five real K16 seeds at n64 and one of five at n256 disagree. Ties contribute zero while remaining in the denominator; this is not a naive-claim reversal probability.',
        ['final.evidence.episodes', 'final.metric.decision_reversal_rate'],
        ['source_evidence/evaluate_final.py#L779', 'analysis/summary.json#/condition_means'])
    add(f'{summary["seed_count"]} evaluation seeds, eight conditions per seed, n in {{64,256}}, K in {{1,16}}; synthetic regimes each use 1024 matrices; real audits have 512 questions and one realized comparison per condition/seed.',
        ['final.evidence.episodes'], ['source_evidence/evaluate_final.py#L899', 'analysis/condition_results.csv'])
    add('Synthetic construction crosses marginal truths 0.6 or linspace(0.4,0.8,K), with the K=1 graded truth 0.4, and coupling probabilities 0.1/0.9; the coupling parameter is not uniformly an exact Pearson correlation.',
        ['final.evidence.episodes'], ['source_evidence/evaluate_final.py#L938'])
    add('Frozen sixteen-prompt bank, seeded half partition, uniform report weights, fixed tie order, and a 95 percent Wilson interval; all comparators and per-method targets follow the inspected evaluator.',
        ['study.selection_kind', 'final.evidence.episodes'], ['source_evidence/downstream/program/src/program.py#L55',
                                                              'source_evidence/downstream/program/src/program.py#L78',
                                                              'source_evidence/evaluate_final.py#L746'])
    add('CPU float32 SmolLM2-135M-Instruct at fixed model revision and pinned MMLU-Pro; deterministic one-legal-letter generation, batch limit eight, input limit 2044 tokens, invalid/overflow counted as errors, with question/prompt caching.',
        ['final.evidence.episodes'], ['source_evidence/resources/runtime_manifest.json', 'source_evidence/resources/split_manifest.json',
                                    'source_evidence/evaluate_final.py#L574'])
    add('Dataset preparation records 4096 retained final examples, 11711 normalized groups, allocation seed 732091 and NFKC/whitespace/option-content overlap checks; shared-pool and pretraining limitations remain.',
        ['final.evidence.episodes'], ['source_evidence/resources/examples.json', 'source_evidence/resources/split_manifest.json',
                                    'source_evidence/evaluate_final.py#L694'])
    add('The supplied dependency versions and runtime specification are documented, but no separate actual-loaded package inventory is asserted; answer worker uses two tensor and one interoperation thread, with float64 statistics.',
        ['final.evidence.episodes'], ['source_evidence/requirements.txt', 'source_evidence/resources/runtime_manifest.json', 'source_evidence/evaluate_final.py#L574'])
    add('Audit uncertainty is a non-simultaneous 95 percent subject-bootstrap percentile interval using 200 draws, fixed selected prompt, seed plus 76531; it is not a validated population coverage guarantee.',
        ['final.evidence.episodes'], ['source_evidence/evaluate_final.py#L987'])
    add(f'Recorded wall durations are {summary["episode_durations_seconds"]} seconds, sum {summary["duration_sum_seconds"]} seconds, or {summary["duration_sum_seconds"]/3600} hours; not CPU-hours or inference-only accounting.',
        ['final.evidence.episodes'], ['analysis/summary.json#/episode_durations_seconds'])
    add('No scored search replacement was found: retained baseline, zero scored alternatives and three unscored alternatives; these do not establish measured losses or successful allocation ablations.',
        ['study.selection_kind', 'study.investigation_outcome', 'study.attempts.scored', 'study.attempts.unscored'],
        ['paper_data.json#/downstream_study'])
    add(f'Independent final qualification is {final["status"]}/{final["outcome"]}/{final["correct"]}; no failed final qualification is present. Qualification does not establish superiority or general validity. Candidate-origin diagnostics remain unverified and absent gate details unknown.',
        ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct', 'final.evidence.episodes'],
        ['paper_data.json#/final_evaluation'])
    add('Constant, copied-column, deliberately contaminated-report, effective permutation and replay checks are implementation diagnostics, not generalization proof; deliberate contamination correctly records false independence.',
        ['final.evidence.episodes', 'final.metric.control_failure_rate', 'final.metric.replay_discrepancy'],
        ['source_evidence/evaluate_final.py#L785', 'paper_data.json#/final_evaluation/evaluation_evidence/episodes'])
    for reference in references['references']:
        add('Literature positioning limited to the consulted original abstract or original page: ' + reference['title'],
            [reference['id']], [reference['consultation_path']], [reference['citation_key']])
    Path('claims_grounding.json').write_text(json.dumps({'claims': claims}, indent=2) + '\n')
    print('Mapped', len(claims), 'claims')


if __name__ == '__main__':
    main()
