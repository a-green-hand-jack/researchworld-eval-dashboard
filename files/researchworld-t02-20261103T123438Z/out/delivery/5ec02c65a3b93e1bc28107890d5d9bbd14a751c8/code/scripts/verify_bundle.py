"""Check a complete204 derived handoff without re-estimating scientific statistics."""
import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, default=Path('.'))
p.add_argument('--output', type=Path, required=True)
p.add_argument('--reference-revision', help='Optional previously published primary analysis, from the source Git repository')
a = p.parse_args()
root = a.root.resolve()
load = lambda path: json.loads((root / path).read_text())
digest = lambda path: hashlib.sha256((root / path).read_bytes()).hexdigest()
registry = load('configs/confirmatory.json')['runs']
registered = {r['name'] for r in registry}
expected_cells = Counter((r['family'], r['width']) for r in registry)
assert len(registry) == len(registered) == 204 and len(expected_cells) == 23
manifest = load('results/manifest.json')
assert manifest['registered_matrix_sha256'] == digest('configs/confirmatory.json')
assert manifest['registered_completed'] == 204 and not manifest['registered_not_started']
for entry in manifest['files']:
    path = root / entry['path']
    assert path.stat().st_size == entry['bytes'] and digest(entry['path']) == entry['sha256'], entry['path']
raw = [r for r in manifest['actual_raw_runs'] if r['kind'] == 'confirmatory']
assert {r['name'] for r in raw} == registered and len(raw) == 204 and all(r['completed'] for r in raw)
audit = load('results/registered-audit.json')
assert audit['status'] == 'PASS' and audit['completed_audited'] == 204
assert set(audit['passed']) == registered and not audit['missing'] and not audit['incomplete']

cpu = []
def check_analysis(directory, canonical=False):
    records = load(directory + '/runs.json')
    assert {Path(r['path']).name for r in records} == registered and len(records) == 204
    provenance = load(directory + '/analysis.json')
    assert provenance['completed'] == 204 and not provenance['incomplete'] and not provenance['absent_registered_runs']
    cells = load(directory + '/cells.json')
    assert Counter({(c['family'], c['width']): c['n'] for c in cells}) == expected_cells and len(cells) == 23
    first8 = load(directory + '/cells-first8.json')
    assert len(first8) == 23 and all(c['n'] == 8 and c['blocks'] == list(range(8)) for c in first8)
    for cell in cells:
        cohort = [r for r in records if r['family'] == cell['family'] and r['width'] == cell['width']]
        assert cell['valid_events'] == sum(r['valid_event']['observed'] for r in cohort)
        assert cell['terminal_valid_events'] == sum(r['valid_event']['terminal_above'] for r in cohort)
        sampling = cell['cpu100_sampling']
        available = sum(r['cpu100_step'] is not None for r in cohort)
        assert sampling['available_n'] == available and sampling['total_n'] == len(cohort)
        assert sampling['incomplete_accounting'] == sum(r['cpu_accounting_incomplete'] for r in cohort)
        assert (cell['cpu100_acc'] is None) == (available != len(cohort))
        assert all(not r['cpu_accounting_incomplete'] or r['cpu100_step'] is None for r in cohort)
        if canonical:
            cpu.append(dict(family=cell['family'], width=cell['width'], n=cell['n'], **sampling,
                all_block_mean_available=cell['cpu100_acc'] is not None))
    predictions = load(directory + '/predictions.json')
    assert all(c['complete'] and c['n_pairs'] == 8 for c in predictions['scope_width_contrasts'])
    assert all(c['complete'] and c['n_pairs'] == 8 for c in predictions['decay_contrasts'])
    assert predictions['P1']['complete'] and predictions['P1']['n_pairs'] == 12
    assert predictions['P2']['complete'] and predictions['P2']['n'] == 12
    assert predictions['P3']['complete'] and predictions['P3']['n_blocks'] == 8
    return predictions

primary = check_analysis('results/confirmatory-analysis', canonical=True)
sensitivity = load('results/sensitivity/sensitivity.json')
assert sensitivity['number_variants'] == len(sensitivity['variants']) == 13
assert sensitivity['matrix_sha256'] == digest('configs/confirmatory.json')
for variant in sensitivity['variants']:
    assert variant['complete']
    directory = 'results/sensitivity/' + variant['name']
    assert digest(directory + '/runs.json') == variant['run_statistics_sha256']
    check_analysis(directory)
with (root / 'reproduction/run_inventory.csv').open() as stream:
    inventory = [r for r in csv.DictReader(stream) if r['kind'] == 'confirmatory']
assert {r['name'] for r in inventory} == registered and all(r['run_status'] == 'completed' for r in inventory)
unchanged = None
if a.reference_revision:
    source = Path(__file__).resolve().parents[2]
    prior = json.loads(subprocess.check_output(['git', 'show', a.reference_revision + ':results/confirmatory-analysis/predictions.json'], cwd=source))
    unchanged = {key: prior[key] == primary[key] for key in ['P1', 'P2', 'P3']}
    assert all(unchanged.values())
report = dict(checked_utc=datetime.now(timezone.utc).isoformat(), kind='Complete scientific bundle membership/hash/count/accounting consistency;not independent paper approval or new estimation',
    registered_runs=204, registered_cells=23, sensitivity_variants=13, manifest_files_verified=len(manifest['files']),
    matrix_sha256=digest('configs/confirmatory.json'), manifest_sha256=digest('results/manifest.json'),
    all_primary_variant_inventory_audit_memberships_equal=True, registered_cell_n_and_first8_equal=True,
    reference_revision=a.reference_revision, unchanged_primary_objects=unchanged,
    inventory_attempt_status_counts=dict(Counter(r['attempt_status'] for r in inventory)),
    cpu_sampling_by_cell=cpu, float64_prediction_disagreement_runs=[r['name'] for r in audit['split_diagnostics'] if r['numerical_precision']['total_prediction_differences']],
    generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    note='Raw independent checks are in registered-audit.json;this verifies supplied consistency,retains unknown attempts/missing CPU,and estimates no new interval.')
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:report[k] for k in ['registered_runs','registered_cells','sensitivity_variants','manifest_files_verified','inventory_attempt_status_counts']}))
