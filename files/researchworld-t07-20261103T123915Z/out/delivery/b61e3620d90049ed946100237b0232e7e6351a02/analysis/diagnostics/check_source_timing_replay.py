"""Check whole-command source timing replay against original source artifacts."""
import argparse, hashlib, json, pathlib
import numpy as np

root = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--replay-root', type=pathlib.Path, default=root.parent/'source-timing-replay')
args = p.parse_args()
original = root/'results/study'
replay = args.replay_root/'results/study'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
fits, cases, loss_discrepancies = [], [], []
for path in sorted((original/'fits').glob('*/*/*.json')):
    other = replay/path.relative_to(original)
    a, b = json.loads(path.read_text()), json.loads(other.read_text())
    for key in ['benchmark','scenario','stage','source_hash','source_rows','dimension']:
        assert a[key] == b[key], (path, key)
    assert b['fit_info']['converged']
    for key in ['seed','regularization','iterations','attempts']:
        assert a['fit_info'][key] == b['fit_info'][key], (path, key)
    assert abs(a['fit_info']['objective']-b['fit_info']['objective']) <= 1e-6
    largest = 0.
    with np.load(path.with_suffix('.npz')) as x, np.load(other.with_suffix('.npz')) as y:
        assert set(x.files) == set(y.files)
        for key in x.files:
            np.testing.assert_allclose(x[key], y[key], atol=1e-10, rtol=1e-10)
            largest = max(largest, float(np.abs(x[key]-y[key]).max()))
    fits.append({'path':str(path.relative_to(root)), 'source_hash':a['source_hash'],
        'original_objective':a['fit_info']['objective'], 'replay_objective':b['fit_info']['objective'],
        'max_parameter_abs_difference':largest, 'replay_elapsed_seconds':b['seconds'],
        'original_json_sha256':sha(path), 'replay_json_sha256':sha(other),
        'original_parameters_sha256':sha(path.with_suffix('.npz')),
        'replay_parameters_sha256':sha(other.with_suffix('.npz'))})
for path in sorted((original/'development').glob('*/*.json')):
    other = replay/path.relative_to(original)
    a, b = json.loads(path.read_text()), json.loads(other.read_text())
    for key in ['benchmark','scenario','n_history','n_target_reserved','n_train','n_validation','refit_dimensions']:
        assert a[key] == b[key], (path, key)
    assert a['selection'].keys() == b['selection'].keys()
    for budget in a['selection']:
        assert a['selection'][budget]['parameters'] == b['selection'][budget]['parameters']
        assert a['selection'][budget]['development_losses'].keys() == b['selection'][budget]['development_losses'].keys()
        for method in a['selection'][budget]['development_losses']:
            before=np.asarray(a['selection'][budget]['development_losses'][method])
            after=np.asarray(b['selection'][budget]['development_losses'][method])
            assert before.shape==after.shape and np.array_equal(before[:,0],after[:,0])
            delta=float(np.max(np.abs(before[:,1]-after[:,1])))
            if delta>1e-12:
                loss_discrepancies.append({'benchmark':a['benchmark'],'scenario':a['scenario'],
                    'budget':int(budget),'method':method,'max_abs_loss_difference':delta,
                    'original_losses':before.tolist(),'replay_losses':after.tolist()})
    cases.append({'path':str(path.relative_to(root)), 'original_sha256':sha(path), 'replay_sha256':sha(other)})
assert len(fits) == 219 and len(cases) == 45
executions = {key:json.loads((original/'execution'/f'source_replay_{key}.json').read_text()) for key in ['A','B']}
assert all(r['exit_code'] == 0 for r in executions.values())
# Confirm that the original immutable evidence has not been replaced by replay artifacts.
manifest = json.loads((original/'final_evidence_manifest.json').read_text())
for name, expected in manifest.items():
    assert sha(root/name) == expected, name
record = {'scope':'Isolated exact source-only refit/tuning timing replay; scientific original fits/selections/predictions not replaced',
    'fits_checked':fits, 'cases_checked':cases,
    'total_source_command_cpu_seconds':sum(r['child_user_cpu_seconds']+r['child_system_cpu_seconds'] for r in executions.values()),
    'source_command_elapsed_seconds':{k:r['elapsed_seconds'] for k,r in executions.items()},
    'peak_process_rss_kib':max(r['peak_child_rss_kib'] for r in executions.values()),
    'command_measurements':executions,
    'all_fits_and_selected_parameters_reproduced_within_declared_tolerances':True,
    'all_development_losses_reproduced_within_1e_12':not loss_discrepancies,
    'development_loss_discrepancies':loss_discrepancies,
    'loss_discrepancy_interpretation':'Record every discrepancy; unchanged chosen hyperparameters and all fitted arrays justify a same-configuration cost proxy, not exact reproduction of every development loss. No primary artifact is replaced.',
    'original_evidence_manifest_sha256':sha(original/'final_evidence_manifest.json'),
    'original_evidence_files_unchanged':len(manifest)}
(original/'source_timing_replay_audit.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
print('HUTIAN_WAKE: source replay verifies219 fits/45 selected-parameter cases; development-loss discrepancies='+str(len(loss_discrepancies)), flush=True)
