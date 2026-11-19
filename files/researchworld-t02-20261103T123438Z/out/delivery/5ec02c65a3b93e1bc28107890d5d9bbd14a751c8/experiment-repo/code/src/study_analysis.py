"""Registered P1/P2/P3 and scope analyses, with block-level provenance."""
from collections import defaultdict
from events import bootstrap_mean,wilson_interval,paired_binary_interval


def direction(interval,prediction='negative'):
    if interval is None or interval.get('ci_low') is None:
        return 'unresolved'
    lo,hi = interval['ci_low'],interval['ci_high']
    if hi<0:
        return 'supported' if prediction=='negative' else 'contradicted'
    if lo>0:
        return 'contradicted' if prediction=='negative' else 'supported'
    return 'unresolved'


def indexed(records):
    lookup = {}
    for r in records:
        key = (r['family'],r['width'],r['block'])
        if key in lookup:
            raise ValueError(f'Duplicate analysis key {key}')
        lookup[key] = r
    return lookup


def paired(lookup,family,low_width=32,high_width=512,blocks=range(12)):
    pairs,missing = [],[]
    for block in blocks:
        low = lookup.get((family,low_width,block))
        high = lookup.get((family,high_width,block))
        if low is None or high is None:
            missing.append(block)
        else:
            if low['split_sha256']!=high['split_sha256']:
                raise ValueError('Mismatched paired splits')
            pairs.append((block,low,high))
    return pairs,missing


def width_contrast(lookup,family,blocks):
    pairs,missing = paired(lookup,family,blocks=blocks)
    result = dict(family=family,direction='width512 minus width32',n_pairs=len(pairs),
                  missing_blocks=missing,complete=not missing)
    if pairs:
        for metric in ['restricted_valid_time','restricted_train_time','restricted_waiting_time',
                       'horizon_valid_acc','cpu100_acc']:
            diffs = [hi[metric]-lo[metric] for _,lo,hi in pairs
                     if lo[metric] is not None and hi[metric] is not None]
            result[metric] = bootstrap_mean(diffs) if len(diffs)==len(pairs) else None
        result['seed_deltas'] = [dict(block=b,delta_rg=hi['restricted_valid_time']-lo['restricted_valid_time'],
             low_rg=lo['restricted_valid_time'],high_rg=hi['restricted_valid_time'],
             low_event=lo['valid_event']['observed'],high_event=hi['valid_event']['observed'],
             low_path=lo['path'],high_path=hi['path']) for b,lo,hi in pairs]
    return result


def study_analysis(records):
    lookup = indexed(records)
    main = width_contrast(lookup,'main',range(12))
    main['interpretation'] = direction(main.get('restricted_valid_time')) if main['complete'] else 'incomplete'
    endpoint = [lookup[('main',512,b)] for b in range(12) if ('main',512,b) in lookup]
    delayed = dict(prediction='P2: more than half of main width512 blocks meet declared delay criteria',
                   n=len(endpoint),complete=len(endpoint)==12,interpretation='incomplete',
                   paths=[r['path'] for r in endpoint])
    if endpoint:
        delayed['interval'] = wilson_interval(sum(r['delayed_event'] for r in endpoint),len(endpoint))
        bounds = delayed['interval']
        delayed['interpretation'] = ('supported' if bounds['ci_low']>.5 else
            'contradicted' if bounds['ci_high']<.5 else 'unresolved') if delayed['complete'] else 'incomplete'
        delayed['zero_clock_boundary_blocks'] = [r['block'] for r in endpoint if r['zero_clock_boundary']]
        delayed['conditional_observed_pairs'] = [
            dict(block=r['block'],lag=r['event_delay'],log2_ratio=r['log2_event_time_ratio'])
            for r in endpoint if r['event_delay'] is not None]
        delayed['censored_fit_pairs'] = [
            dict(block=r['block'],lag_lower_bound=r['censored_lag_lower_bound'],
                 ratio_lower_bound=r['censored_ratio_lower_bound'])
            for r in endpoint if r['censored_lag_lower_bound'] is not None]
    p3 = dict(prediction='P3: full-minus-frozen endpoint width interaction is negative',
              required_blocks=list(range(8)),complete=False,interpretation='incomplete')
    block_records = []
    for b in range(8):
        keys = [(f,w,b) for f in ['main','frozen'] for w in [32,512]]
        if all(k in lookup for k in keys):
            full_low,full_high,frozen_low,frozen_high = [lookup[k] for k in keys]
            if len({r['split_sha256'] for r in [full_low,full_high,frozen_low,frozen_high]})!=1:
                raise ValueError('Unmatched split in frozen interaction')
            block_records.append(dict(block=b,
                full_delta=full_high['restricted_valid_time']-full_low['restricted_valid_time'],
                frozen_delta=frozen_high['restricted_valid_time']-frozen_low['restricted_valid_time'],
                frozen_low_fit=frozen_low['train_event']['observed'],
                frozen_high_fit=frozen_high['train_event']['observed'],
                full_low_fit=full_low['train_event']['observed'],
                full_high_fit=full_high['train_event']['observed'],
                paths=[lookup[k]['path'] for k in keys]))
    p3.update(n_blocks=len(block_records),complete=len(block_records)==8,blocks=block_records)
    if block_records:
        values = [r['full_delta']-r['frozen_delta'] for r in block_records]
        p3['difference_of_differences'] = bootstrap_mean(values)
        p3['fit_counts'] = {key:sum(r[key] for r in block_records) for key in
            ['frozen_low_fit','frozen_high_fit','full_low_fit','full_high_fit']}
        p3['fit_gate_passed'] = p3['complete'] and p3['fit_counts']['frozen_low_fit']>=6 and p3['fit_counts']['frozen_high_fit']>=6
        p3['statistical_direction'] = direction(p3['difference_of_differences'])
        p3['interpretation'] = ('incomplete' if not p3['complete'] else
            p3['statistical_direction'] if p3['fit_gate_passed'] else 'unresolved: frozen fit comparability gate failed')
    scope = []
    for family in ['decay','frozen','lr-low','lr-high','orbit','multiply']:
        scope.append(width_contrast(lookup,family,range(8)))
    decay = []
    for width in [32,128,512]:
        matches = [(lookup[('main',width,b)],lookup[('decay',width,b)]) for b in range(8)
                   if ('main',width,b) in lookup and ('decay',width,b) in lookup]
        entry = dict(width=width,direction='decay0.1 minus decay1',n_pairs=len(matches),complete=len(matches)==8)
        if matches:
            if any(a['split_sha256']!=b['split_sha256'] for a,b in matches):
                raise ValueError('Unmatched split in decay comparison')
            entry['generalization_incidence'] = paired_binary_interval(
                [a['valid_event']['observed'] for a,b in matches],
                [b['valid_event']['observed'] for a,b in matches])
            entry['restricted_generalization_time'] = bootstrap_mean(
                [b['restricted_valid_time']-a['restricted_valid_time'] for a,b in matches])
            entry['paths'] = [[a['path'],b['path']] for a,b in matches]
        decay.append(entry)
    if main.get('interpretation')=='supported' and delayed.get('interpretation')=='supported' and p3.get('interpretation')=='supported':
        account = 'All three predictions supported within the registered recipes/window; unique mechanism not identified.'
    else:
        account = 'Complete account not established; retain individual supported, contradicted and unresolved predictions.'
    return dict(P1=main,P2=delayed,P3=p3,scope_width_contrasts=scope,decay_contrasts=decay,
        complete_account=account,
        warning='Partial outputs are progress, not final inference. Secondary intervals are pointwise. Censoring does not establish never-generalizes.')
