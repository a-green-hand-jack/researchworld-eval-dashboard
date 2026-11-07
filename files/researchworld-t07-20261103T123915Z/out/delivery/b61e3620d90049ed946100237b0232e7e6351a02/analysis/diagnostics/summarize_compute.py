"""Summarize measured reproduction cost without inventing original source CPU."""
import datetime, hashlib, json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
out = root/'results/study'
audit_path = out/'source_timing_replay_audit.json'
audit = json.loads(audit_path.read_text())
anchor_path=out/'anchor_reproduction_audit.json'
anchor=json.loads(anchor_path.read_text())
assert len(anchor['final_anchor_checks'])==78
assert all(r['items_exactly_equal'] and r['same_budget_prediction_max_abs_difference']==0 for r in anchor['final_anchor_checks'])
assert audit['all_fits_and_selected_parameters_reproduced_within_declared_tolerances']
names = ['source_replay_A','source_replay_B','predict_A','predict_B','scoring_canonical']
records = {name:json.loads((out/'execution'/f'{name}.json').read_text()) for name in names}
assert all(r['exit_code'] == 0 for r in records.values())
rows = []
for name, r in records.items():
    rows.append({'stage':name, 'cpu_seconds':r['child_user_cpu_seconds']+r['child_system_cpu_seconds'],
        'elapsed_seconds':r['elapsed_seconds'], 'peak_process_rss_kib':r['peak_child_rss_kib']})
source_cpu = sum(r['cpu_seconds'] for r in rows[:2])
predict_cpu = sum(r['cpu_seconds'] for r in rows[2:4])
score_cpu = rows[4]['cpu_seconds']
start = min(datetime.datetime.fromisoformat(records[n]['started_utc']) for n in names[:2])
end = max(datetime.datetime.fromisoformat(records[n]['ended_utc']) for n in names[:2])
inputs = [audit_path,anchor_path,out/'source_anchor_thread_diagnostic.json']+[out/'execution'/f'{name}.json' for name in names]
record = {'scope':'Measured reproduction-workload proxy: isolated same-configuration source replay + original frozen cached predictions + corrected scoring; stages executed at different times',
    'stage_measurements':rows, 'source_replay_cpu_seconds':source_cpu,
    'final_anchor_selections_and_mean_predictions_exactly_reproduced':len(anchor['final_anchor_checks']),
    'source_replay_observed_parallel_wall_span_seconds':(end-start).total_seconds(),
    'source_replay_fits_verified':len(audit['fits_checked']), 'source_replay_tuning_cases_verified':len(audit['cases_checked']),
    'source_replay_development_loss_discrepancies':audit['development_loss_discrepancies'],
    'source_replay_all_development_losses_reproduced':audit['all_development_losses_reproduced_within_1e_12'],
    'prediction_cpu_seconds':predict_cpu, 'canonical_scoring_cpu_seconds':score_cpu,
    'reproduction_workload_cpu_seconds':source_cpu+predict_cpu+score_cpu,
    'largest_stage_process_rss_kib':max(r['peak_process_rss_kib'] for r in rows),
    'original_source_end_to_end_cpu_seconds':None,
    'limits':['Original source commands did not measure full CPU; replay is a new measurement, not recovery of the suspended run.',
        'Total combines phases measured at different times. No measured original end-to-end wall time is claimed.',
        'Excludes acquisition, pilots, discarded raw-tie scoring, diagnostic audits, formula reporting, rendering and dependency setup.',
        'Process peak RSS is not aggregate concurrent-job memory. CPU/elapsed change with hardware and shared-host contention.',
        'One GSM development anchor-ridge loss grid is thread-sensitive:1-thread checks reproduce replay values,2-thread checks reproduce original values; chosen alpha unchanged. Historical effective library thread count was not measured.'],
    'input_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
(out/'compute_accounting.json').write_text(json.dumps(record, indent=2, sort_keys=True)+'\n')
lines = ['# Measured source replay and reproduction workload', '', record['scope']+'.', '',
    '| Stage | CPU seconds | Elapsed seconds | Peak process RSS (KiB) |', '| --- | ---: | ---: | ---: |']
for r in rows:
    lines.append(f"| {r['stage']} | {r['cpu_seconds']:.3f} | {r['elapsed_seconds']:.3f} | {r['peak_process_rss_kib']} |")
lines += ['', f'The two source commands completed all219 fits and45 tuning cases in an observed parallel wall span of{(end-start).total_seconds():.3f}s, using{source_cpu:.3f} CPU seconds. Their fitted parameter arrays, convergence attempts, objectives and chosen parameters agree with the original source artifacts under the explicit checks in `diagnostics/check_source_timing_replay.py`. The complete original scientific evidence manifest remains unchanged.', '',
    f'The source replay plus original prediction and corrected-scoring commands sum to{source_cpu+predict_cpu+score_cpu:.3f} CPU seconds ({(source_cpu+predict_cpu+score_cpu)/60:.2f} CPU minutes) as a reproduction-workload proxy. The phases were measured at different times; this is not an original end-to-end timing. All measurement inputs are hash-pinned in `results/study/compute_accounting.json`.', '']
lines += [x+'\n' for x in record['limits']]
lines += ['', 'Development-loss discrepancies are retained in the audit and compute JSON. One GSM/main/k30 correctness-anchor ridge loss grid differs (maximum0.004511713 in accuracy units, or0.4511713pp); its selected alpha remains1. All45 selected-parameter packages and219 MIRT fits match. The replay is a same-configuration workload measurement, not an exact replay of every development quantity. A bounded1/2-thread diagnostic reproduces both loss grids exactly:1 thread matches the replay and2 threads match the original, with one of30 development representatives changed and alpha1 retained. This establishes numerical thread sensitivity; the original effective thread-pool count was not recorded, so historical execution settings are not inferred as fact. All original primary code and results are preserved.', '', 'Source-only replay commands and exact inputs are documented in `notes/source_timing_replay_ledger.json` and the reproduction README. Scientific original caches and predictions are never replaced by replay outputs. Retain `notes/timing_caveat.md` and the original suspension-affected record when reporting compute.']
(root/'notes/compute_accounting.md').write_text('\n'.join(lines)+'\n')
print('Summarized measured reproduction workload with explicit original-source timing limits.', flush=True)
