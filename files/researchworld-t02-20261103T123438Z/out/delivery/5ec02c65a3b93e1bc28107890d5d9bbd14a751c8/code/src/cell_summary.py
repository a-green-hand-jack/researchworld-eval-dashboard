"""Seed-level cell statistics shared by primary and matched-subset reports."""
from collections import defaultdict
from events import bootstrap_mean,wilson_interval

CELL_KEYS = ['family','p','task','fraction','activation','width','lr','weight_decay','steps',
    'onset_horizon','eval_every','split_rule','frozen_hidden']
METRICS = ['restricted_train_time','restricted_valid_time','restricted_waiting_time',
    'horizon_train_acc','horizon_valid_acc','horizon_valid_loss','horizon_spectral_fraction',
    'final_train_acc','final_valid_acc','final_valid_loss','final_weight_norm','final_spectral_fraction','cpu100_acc',
    'horizon_valid_zero_acc','horizon_valid_nonzero_acc']


def summarize_cells(records):
    cells = defaultdict(list)
    for record in records:
        cells[tuple(record[k] for k in CELL_KEYS)].append(record)
    output = []
    for key,runs in cells.items():
        pairs = [(r['split_seed'],r['init_seed']) for r in runs]
        if len(set(pairs))!=len(pairs):
            raise ValueError(f'Duplicate seed pair within cell: {key}')
        entry = dict(zip(CELL_KEYS,key))
        entry.update(n=len(runs),blocks=[r['block'] for r in runs],paths=[r['path'] for r in runs],
            train_events=sum(r['train_event']['observed'] for r in runs),
            valid_events=sum(r['valid_event']['observed'] for r in runs),
            delayed_events=sum(r['delayed_event'] for r in runs),
            terminal_train_events=sum(r['train_event']['terminal_above'] for r in runs),
            terminal_valid_events=sum(r['valid_event']['terminal_above'] for r in runs),
            status_counts={s:sum(r['status']==s for r in runs) for s in sorted({r['status'] for r in runs})})
        for event in ['train','valid','delayed','terminal_train','terminal_valid']:
            entry[event+'_event_probability'] = wilson_interval(entry[event+'_events'],len(runs))
        for metric in METRICS:
            values = [r.get(metric) for r in runs]
            entry[metric] = bootstrap_mean(values) if all(v is not None for v in values) else None
        available = [r for r in runs if r['cpu100_step'] is not None]
        entry['cpu100_sampling'] = dict(available_n=len(available),total_n=len(runs),
            min_step=min((r['cpu100_step'] for r in available),default=None),
            max_step=max((r['cpu100_step'] for r in available),default=None),
            min_recorded_s=min((r['cpu100_recorded_s'] for r in available),default=None),
            max_recorded_s=max((r['cpu100_recorded_s'] for r in available),default=None),
            onset_horizon_completed_before_budget=sum(r['horizon_completed_before_cpu100'] for r in runs),
            execution_completed_before_budget=sum(r['execution_completed_before_cpu100'] for r in runs),
            incomplete_accounting=sum(r['cpu_accounting_incomplete'] for r in runs),
            note='Last measured evaluation at/before100 process-CPU seconds within onset horizon; no interpolation or FLOP matching.')
        output.append(entry)
    return output
