"""Inventory actual attempts, registered nonstarts, hashes and reproducibility sources."""
import argparse
import csv
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--root',default='.')
args = parser.parse_args()
root = Path(args.root)
registry_file = root/'configs/confirmatory.json'
registry = {r['name']:r for r in json.loads(registry_file.read_text())['runs']}
rows = []
actual_names = set()
raw_runs = []
for path in sorted((root/'results').rglob('metadata.json')):
    directory = path.parent
    meta = json.loads(path.read_text())
    config = meta['config']
    relative = str(directory.relative_to(root))
    name = directory.name
    is_registered = relative.startswith('results/confirmatory/') and name in registry
    if is_registered:
        actual_names.add(name)
    summary = json.loads((directory/'summary.json').read_text()) if (directory/'summary.json').exists() else None
    attempts = [json.loads(line) for line in (directory/'attempts.jsonl').read_text().splitlines()] if (directory/'attempts.jsonl').exists() else []
    ended = [a for a in attempts if a.get('event')!='started']
    starts = {a.get('attempt_id'):a for a in attempts if a.get('event')=='started'}
    ended_ids = {a.get('attempt_id') for a in ended}
    unknown = [a for key,a in starts.items() if key not in ended_ids]
    if not ended and not unknown:
        ended = [dict(status='completed' if summary else 'incomplete',end_step=summary['final']['step'] if summary else None,
                      segment_wall_s=summary['elapsed_s'] if summary else None,
                      segment_cpu_s=summary['cpu_s'] if summary else None)]
    if is_registered:
        kind = 'confirmatory'
    elif 'implementation-checks' in relative:
        kind = 'software_validation'
    elif 'gate-benchmarks' in relative:
        kind = 'nonconfirmatory_cost_benchmark'
    else:
        kind = 'exploratory_pilot'
    for index,attempt in enumerate(ended+unknown):
        rows.append(dict(name=name,kind=kind,registered=is_registered,run_status='completed' if summary else 'incomplete_execution',
            attempt=index+1,attempt_status=attempt.get('status','unknown_after_process_interruption'),
            attempt_id=attempt.get('attempt_id'),output_path=relative,config_path=str(path.relative_to(root))+'#config',
            source_train_sha256=meta.get('source_train_sha256'),source_git_commit=meta.get('source_git_commit'),
            parameter_count=meta['parameter_count'],trainable_parameter_count=meta.get('trainable_parameter_count',meta['parameter_count']),
            start_step=attempt.get('start_step',0),end_step=attempt.get('end_step'),
            segment_wall_s=attempt.get('segment_wall_s'),segment_cpu_s=attempt.get('segment_cpu_s'),
            split_seed=config['split_seed'],init_seed=config['init_seed'],task=config['task'],width=config['width'],
            frozen_hidden=config.get('frozen_hidden',False),split_rule=config.get('split_rule','ordered')))
    raw_runs.append(dict(name=name,path=relative,kind=kind,completed=summary is not None,
        source_git_commit=meta.get('source_git_commit'),source_train_sha256=meta.get('source_train_sha256'),
        config_sha256=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        split_sha256=meta['split_sha256']))
for name,config in registry.items():
    if name not in actual_names:
        rows.append(dict(name=name,kind='confirmatory',registered=True,run_status='registered_not_started',attempt=0,
            attempt_status='not_attempted',output_path='results/confirmatory/'+name,config_path='configs/confirmatory.json#'+name,
            split_seed=config['split_seed'],init_seed=config['init_seed'],task=config['task'],width=config['width'],
            frozen_hidden=config['frozen_hidden'],split_rule=config['split_rule']))
inventory = root/'reproduction/run_inventory.csv'
with inventory.open('w') as stream:
    writer = csv.DictWriter(stream,lineterminator='\n',fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
    writer.writeheader()
    writer.writerows(rows)
files = []
live_files_omitted = []
for path in sorted((root/'results').rglob('*')):
    if not path.is_file() or path==root/'results/manifest.json':
        continue
    if path.name.endswith('.tmp'):
        continue
    raw_parent = next((parent for parent in path.parents if (parent/'metadata.json').exists()),None)
    if raw_parent is not None and not (raw_parent/'summary.json').exists():
        live_files_omitted.append(str(path.relative_to(root)))
        continue
    files.append(dict(path=str(path.relative_to(root)),bytes=path.stat().st_size,
                      sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
manifest = dict(schema_version=1,generated_utc=datetime.now(timezone.utc).isoformat(),
    generator='code/scripts/inventory.py',generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    registered_matrix='configs/confirmatory.json',registered_matrix_sha256=hashlib.sha256(registry_file.read_bytes()).hexdigest(),
    registered_total=len(registry),registered_completed=sum(r['completed'] for r in raw_runs if r['kind']=='confirmatory'),
    registered_not_started=sorted(set(registry)-actual_names),actual_raw_runs=raw_runs,files=files,live_files_omitted=live_files_omitted,
    scientific_vs_execution_note='Right-censored event outcomes are derived from completed curves; incomplete execution is never a valid scientific non-event.',
    archive_provenance='code/archive/provenance.json')
(root/'results/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(actual_raw_runs=len(raw_runs),attempt_inventory_rows=len(rows),registered_total=len(registry),
                      registered_started=len(actual_names),files_hashed=len(files))))
