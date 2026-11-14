"""All-run analysis with onset horizons, explicit failures and seed uncertainty."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from events import summarize_curve
from cell_summary import summarize_cells

parser = argparse.ArgumentParser()
parser.add_argument('root')
parser.add_argument('--output',required=True)
parser.add_argument('--registry')
parser.add_argument('--sustain',type=int,default=3)
parser.add_argument('--train-threshold',type=float,default=.99)
parser.add_argument('--valid-threshold',type=float,default=.95)
parser.add_argument('--thin',type=int,default=1,help='Every Nth scheduled evaluation; only measured points')
args = parser.parse_args()
out = Path(args.output)
out.mkdir(parents=True,exist_ok=True)
registry = {}
if args.registry:
    registered = json.loads(Path(args.registry).read_text())
    registry = {r['name']:r for r in registered['runs']}
records,incomplete = [],[]
for metadata_path in sorted(Path(args.root).rglob('metadata.json')):
    directory = metadata_path.parent
    metadata = json.loads(metadata_path.read_text())
    if not (directory/'summary.json').exists():
        incomplete.append(dict(path=str(directory),metadata=metadata,status='incomplete_execution'))
        continue
    config = metadata['config']
    rows = [json.loads(line) for line in (directory/'curve.jsonl').read_text().splitlines()]
    if not all(a['step']<b['step'] for a,b in zip(rows,rows[1:])) or rows[-1]['step']!=config['steps']:
        raise ValueError(f'Invalid completed curve at {directory}')
    summary = json.loads((directory/'summary.json').read_text())
    horizon = config.get('onset_horizon',config['steps'])
    selected = [r for r in rows if r['step']%(config['eval_every']*args.thin)==0]
    result = summarize_curve(selected,args.train_threshold,args.valid_threshold,args.sustain,horizon)
    before_horizon = [r for r in rows if r['step']<=horizon]
    at_horizon = before_horizon[-1]
    eligible_cpu = [r for r in before_horizon if r['cpu_s']<=100] if not metadata.get('cpu_accounting_incomplete',False) else []
    cpu_row = eligible_cpu[-1] if eligible_cpu else None
    if result['valid_event']['observed']:
        status = 'confirmed_delayed' if result['delayed_event'] else 'other_confirmed_generalization'
        if not result['train_event']['observed'] or result['valid_event']['step']<result['train_event']['step']:
            status = 'unusual_generalization_ordering'
    else:
        status = 'fit_with_generalization_censored' if result['train_event']['observed'] else 'neither_event'
    registered = registry.get(directory.name,{})
    if args.registry and not registered:
        raise ValueError(f'Unregistered run in confirmatory input: {directory}')
    if registered:
        expected = {k:v for k,v in registered.items() if k not in ['name','family','block','stage']}
        if expected!=config:
            raise ValueError(f'Registered config differs from measured metadata at {directory}')
    record = dict(config)
    record.update(path=str(directory),family=registered.get('family','exploratory'),
        block=registered.get('block'),name=directory.name,status=status,
        parameter_count=metadata['parameter_count'],
        trainable_parameter_count=metadata.get('trainable_parameter_count',metadata['parameter_count']),
        split_sha256=metadata['split_sha256'],data_info=metadata.get('data_info',{}),
        n_train=metadata['n_train'],n_valid=metadata['n_valid'],
        realized_fraction=metadata.get('data_info',{}).get('realized_fraction',config['fraction']),
        frozen_hidden=config.get('frozen_hidden',False),split_rule=config.get('split_rule','ordered'),
        onset_horizon=horizon,elapsed_s=summary['elapsed_s'],cpu_s=summary['cpu_s'],**result,
        final_train_acc=rows[-1]['train_acc'],final_valid_acc=rows[-1]['valid_acc'],
        final_valid_loss=rows[-1]['valid_loss'],final_weight_norm=rows[-1]['weight_norm'],
        final_spectral_fraction=rows[-1]['spectral_fraction'],
        horizon_train_acc=at_horizon['train_acc'],horizon_valid_acc=at_horizon['valid_acc'],
        horizon_valid_loss=at_horizon['valid_loss'],horizon_spectral_fraction=at_horizon['spectral_fraction'],
        cpu100_step=cpu_row['step'] if cpu_row else None,cpu100_acc=cpu_row['valid_acc'] if cpu_row else None,
        cpu100_recorded_s=cpu_row['cpu_s'] if cpu_row else None,
        horizon_completed_before_cpu100=at_horizon['cpu_s']<100,
        execution_completed_before_cpu100=summary['cpu_s']<100,
        cpu_accounting_incomplete=metadata.get('cpu_accounting_incomplete',False),
        source_train_sha256=metadata.get('source_train_sha256'),
        curve_sha256=hashlib.sha256((directory/'curve.jsonl').read_bytes()).hexdigest(),
        metadata_sha256=hashlib.sha256(metadata_path.read_bytes()).hexdigest())
    for event in ['train_event','valid_event']:
        event_row = next((r for r in rows if r['step']==result[event]['step']),None)
        record[event+'_cpu_s'] = event_row['cpu_s'] if event_row else None
        record[event+'_wall_s'] = event_row['elapsed_s'] if event_row else None
    for subset in ['zero','nonzero']:
        if f'valid_{subset}_acc' in at_horizon:
            record[f'horizon_valid_{subset}_acc'] = at_horizon[f'valid_{subset}_acc']
            record[f'horizon_valid_{subset}_n'] = at_horizon[f'valid_{subset}_n']
    records.append(record)
(out/'runs.json').write_text(json.dumps(records,indent=2,allow_nan=False)+'\n')
(out/'incomplete.json').write_text(json.dumps(incomplete,indent=2)+'\n')
flat = []
for record in records:
    r = {k:v for k,v in record.items() if k not in ['train_event','valid_event']}
    for event in ['train_event','valid_event']:
        r.update({f'{event}_{k}':v for k,v in record[event].items()})
    flat.append(r)
if flat:
    with (out/'runs.csv').open('w') as f:
        writer = csv.DictWriter(f,lineterminator='\n',fieldnames=list(dict.fromkeys(k for r in flat for k in r)))
        writer.writeheader()
        writer.writerows(flat)
(out/'cells.json').write_text(json.dumps(summarize_cells(records),indent=2,allow_nan=False)+'\n')
first8 = [r for r in records if r['block'] is not None and r['block']<8]
(out/'cells-first8.json').write_text(json.dumps(summarize_cells(first8),indent=2,allow_nan=False)+'\n')
protocol = dict(train_threshold=args.train_threshold,valid_threshold=args.valid_threshold,sustain=args.sustain,
    thin=args.thin,terminal_rule='Last sustain selected evaluations through execution end; distinct from onset by H',
    thinning_boundary_note='Thinning can reduce confirmation coverage near H; no unsampled future observations are invented.',
    bootstrap='percentile, resampling independent seed blocks, 10000 draws seed1701',
    caveat='Single-seed continuous uncertainty unavailable; score intervals concern seed event probabilities.',
    input_root=args.root,registry=args.registry,completed=len(records),incomplete=len(incomplete),
    registered_total=len(registry) if registry else None,
    absent_registered_runs=sorted(set(registry)-{r['name'] for r in records}-{Path(r['path']).name for r in incomplete}) if registry else [])
(out/'analysis.json').write_text(json.dumps(protocol,indent=2)+'\n')
print(json.dumps(protocol))
