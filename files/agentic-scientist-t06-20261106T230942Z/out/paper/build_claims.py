import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
payload = json.loads((ROOT / 'paper_data.json').read_text())
episodes = payload['final_evaluation']['evaluation_evidence']['episodes']
# @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
claims = []


def add(text, sources, pointers=None, citations=None, documentation=None):
    row = {'claim': text, 'source_ids': sources, 'citation_keys': citations or []}
    if pointers:
        row['evidence_refs'] = [f'paper_data.json#{pointer}' for pointer in pointers]
    if documentation:
        row['implementation_evidence'] = documentation
        row['support_scope'] = 'Registered final evidence identifies the evaluated condition; readable documentation, not hashes or metric values, supports implementation specifics.'
    claims.append(row)


for episode_index, episode in enumerate(episodes):
    for case_index, case in enumerate(episode['solution']['cases']):
        pointer = f'/final_evaluation/evaluation_evidence/episodes/{episode_index}/solution/cases/{case_index}'
        add(f"Seed {episode['seed']}, {case['case']}: integer costs {case['counts']}; guided disruption {case['candidate_curves']}; all matched baseline curves and seed-budget means are reported without new measurements.",
            ['final.evidence.episodes'], [pointer + '/counts', pointer + '/candidate_curves', pointer + '/baseline_curves'])
        add(f"Seed {episode['seed']}, {case['case']}: fixed-plan paired percentile intervals {case['paired_intervals']}; figure segments reproduce recorded endpoints without inferred centers.",
            ['final.evidence.episodes'], [pointer + '/paired_intervals', pointer + '/bootstrap'])
        if episode_index == 0:
            add(f"{case['case']}: graph diagnostics {case['graph']}; graph and cost table reproduces these observations.",
                ['final.evidence.episodes'], [pointer + '/graph', pointer + '/counts'])
for metric in ['combined_score', 'random_flip_score', 'degree_matched_score', 'margin_heuristic_score', 'mean_rank_displacement', 'influence_error']:
    name = 'family-balanced budget-averaged disruption' if metric == 'combined_score' else metric
    add(f"Final {name}: {payload['final_evaluation']['metrics'][metric]}; rounded manuscript values are summaries of this final scalar, not search results.",
        [f'final.metric.{metric}'], [f'/final_evaluation/metrics/{metric}'])
add('The final evaluation completed, qualified, and passed the recorded operational/scientific checks. Qualification is not a superiority or publication decision.',
    ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct'],
    ['/grounding_sources/final.qualification.status', '/grounding_sources/final.qualification.outcome', '/grounding_sources/final.qualification.correct'],
    documentation=['source_evidence/task_contract.json:method.final_correct'])
add('Guided original-sample curves coincide across all three seeds on every panel; seed means are descriptive, not independent data replications.',
    ['final.evidence.episodes'], ['/final_evaluation/evaluation_evidence/episodes'])
add('Guided budget-averaged disruption exceeds each comparator on every panel. At the smallest NBA 2014 budget, guidance ties the small-margin control; the other plotted seed-averaged cells favor guidance. This does not imply universally positive paired uncertainty.',
    ['final.evidence.episodes'], ['/final_evaluation/evaluation_evidence/episodes'])
add('All Arena paired intervals are strictly positive; all degree-stratified NBA intervals include zero. NBA 2012 small-margin comparisons are positive for all seeds; NBA 2011 small-margin and NBA 2012 uniform each have one wholly positive interval. NBA 2013–2015 intervals all include zero.',
    ['final.evidence.episodes'], ['/final_evaluation/evaluation_evidence/episodes'])
add('Arena finite-shift discrepancy spans 0.2235–0.3350; NBA spans about 0.00036–0.02274. This is a normalized coefficient-shift diagnostic, not rank error, superiority, or an accuracy threshold.',
    ['final.evidence.episodes', 'final.metric.influence_error'], ['/final_evaluation/evaluation_evidence/episodes'],
    documentation=['source_evidence/task_contract.json:method.audits'])
add('Recorded CPU evaluation durations span approximately 29.6–30.5 seconds per seed evaluation, not method-only timings or speedup measurements.',
    ['final.evidence.episodes'], [f'/final_evaluation/evaluation_evidence/episodes/{index}/duration_seconds' for index in range(len(episodes))])
add('The fixed estimator uses sum logistic loss with unit quadratic ridge, centered participant scores, fractional uneditable ties, and a regularized optional NBA home effect. Nominal fractions .001, .005, .01 use all rows and floor-rounded nested binary flips.',
    ['final.evidence.episodes'], documentation=['source_evidence/flip_search.py:22-44', 'source_evidence/flip_search.py:61-172', 'source_evidence/task_contract.json:method.scientific_workload'])
add('Influence screening uses genuine Hessian derivatives, a frozen top-min(10,p) adjacent contrast, width-two exact-refitted path selection, and up to six nearby contrast proposals. The lexicographic internal objective leads with summed displacement, not the reported inversion fraction.',
    ['final.evidence.episodes'], documentation=['source_evidence/flip_search.py:194-266', 'source_evidence/flip_search.py:510-549'])
add('The available source implements strict complete-path swaps/replacements with sorted original-row prefix caching and incumbent fallback. It uses up to 24 sampled positions, additional refit caps 72 or 24 by dimension, a two-second optional deadline, and 128 proposals; no execution trace establishes accepted exchange counts or isolated exchange benefit.',
    ['final.evidence.episodes'], documentation=['source_evidence/flip_search.py:309-475'])
add('The available solver uses damped Newton/Cholesky with at most 50 Newton steps, L-BFGS fallback and final stationarity rejection at gradient infinity norm above 1e-6; these are code settings, not measured operation counts.',
    ['final.evidence.episodes'], documentation=['source_evidence/flip_search.py:119-172'])
add('Uniform, approximate degree-quartile-stratified and small-margin controls share integer budgets. The three-budget average, equal seeds, half Arena/half equal-season NBA weighting and thirty-resample fixed-plan grouped bootstrap define the reporting protocol.',
    ['final.evidence.episodes'], documentation=['source_evidence/task_contract.json:method.baselines', 'source_evidence/task_contract.json:method.aggregation', 'source_evidence/task_contract.json:method.uncertainty'])
add('Public preparation preserves pinned Arena/NBA snapshots, reciprocal-game checks, content-connected groups, lexicographic participant identities, and home rather than Elo inputs. Source hashes identify files but are not substantive source-code evidence.',
    ['final.evidence.episodes'], documentation=['source_evidence/prepare_data.py:12-147', 'source_evidence/panel_manifest.json', 'source_evidence/source_manifest.json'])
provenance = json.loads((ROOT / 'references_provenance.json').read_text())
used = set()
for group in re.findall(r'\\cite[a-zA-Z*]*\{([^}]+)\}', (ROOT / 'paper.tex').read_text()):
    used.update(key.strip() for key in group.split(','))
for reference in provenance['references']:
    if reference['citation_key'] in used:
        add('Related-work attribution: ' + reference['title'], [reference['id']], citations=[reference['citation_key']])
output = {'claims': claims, 'scope': 'Final measurements only; no development-score comparison or causal component attribution.',
          'documentary_support_policy': 'Implementation evidence paths and locations are substantive inspected support. Registered metric IDs alone do not establish implementation details. Source-copy identity is recorded without claiming an independently reconstructed frozen-tree digest.'}
(ROOT / 'claims_grounding.json').write_text(json.dumps(output, indent=2))
print(f'Wrote {len(claims)} claim mappings.')
