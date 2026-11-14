import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
payload = json.loads((ROOT / 'paper_data.json').read_text())
episodes = payload['final_evaluation']['evaluation_evidence']['episodes']
# @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
metrics = payload['final_evaluation']['metrics']
# @evidence[[paper_data.json#/final_evaluation/metrics]]
methods = ['candidate', 'random_flip_score', 'degree_matched_score', 'margin_heuristic_score']
summaries = {method: [] for method in methods}
displacement_summaries = []
comparisons = []
for episode in episodes:
    case_means = {method: [] for method in methods}
    displacement_case_means = []
    for case in episode['solution']['cases']:
        participants = case['graph']['participants']
        original = np.asarray(case['original_scores'])[:participants]
        original_rank = np.lexsort((np.arange(participants), -original))
        original_position = np.argsort(original_rank)
        upper, lower = np.triu_indices(participants, 1)
        displacements = []
        for edited, observed in zip(case['edited_scores'], case['candidate_curves']):
            fitted_rank = np.lexsort((np.arange(participants), -np.asarray(edited)[:participants]))
            fitted_position = np.argsort(fitted_rank)
            inversions = np.mean((original_position[upper] < original_position[lower]) !=
                                 (fitted_position[upper] < fitted_position[lower]))
            assert np.isclose(inversions, observed, atol=1e-12)
            displacements.append(float(np.abs(fitted_position - original_position).sum() / (participants * (participants - 1))))
        displacement_case_means.append(float(np.mean(displacements)))
        for method in methods:
            curve = case['candidate_curves'] if method == 'candidate' else case['baseline_curves'][method]
            case_means[method].append(float(np.mean(curve)))
        for method, interval in case['paired_intervals'].items():
            resamples = [resample['paired'][method] for resample in case['bootstrap']]
            assert np.allclose(np.percentile(resamples, [2.5, 97.5]), interval, atol=1e-12)
        assert len(case['selected_indices']) == max(case['counts'])
        assert len(case['selected_indices']) == len(set(case['selected_indices']))
        comparisons.append({'seed': episode['seed'], 'case': case['case'],
                            'all_controls_pass': all(case['controls'].values()),
                            'method_audit': case['method_audit']})
    for method in methods:
        values = case_means[method]
        summaries[method].append(.5 * values[0] + .5 * np.mean(values[1:]))
    displacement_summaries.append(.5 * displacement_case_means[0] + .5 * np.mean(displacement_case_means[1:]))
for method in methods:
    key = 'combined_score' if method == 'candidate' else method
    assert np.isclose(np.mean(summaries[method]), metrics[key], atol=1e-12)
assert all(item['all_controls_pass'] and item['method_audit'] for item in comparisons)
assert np.isclose(np.mean(displacement_summaries), metrics['mean_rank_displacement'], atol=1e-12)
report = {'status': 'pass', 'scope': 'arithmetic replay only; no model fitting or fresh evaluation',
          'aggregates': {method: float(np.mean(values)) for method, values in summaries.items()},
          'mean_rank_displacement': float(np.mean(displacement_summaries)),
          'checked_case_seed_records': len(comparisons), 'checks': comparisons}
(ROOT / 'replay_report.json').write_text(json.dumps(report, indent=2))
sidecar = {'schema_name': 'scientific-evidence.artifact-manifest',
           'artifact': {'path': 'replay_report.json', 'kind': 'verification'},
           'derived_from': ['@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]',
                            '@evidence[[paper_data.json#/final_evaluation/metrics]]'],
           'generated_by': {'script_path': 'replay_checks.py'}}
(ROOT / 'replay_report.json.prov.json').write_text(json.dumps(sidecar, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != 'checks'}, indent=2))
