import argparse
import concurrent.futures
import decimal
import hashlib
import json
import math
import pathlib
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
import pyarrow.parquet as parquet

parser = argparse.ArgumentParser(description='Reacquire pinned public score snapshots and content-cluster split before feature extraction.')
parser.add_argument('--cache', default='/tmp/scaffold-assets')
parser.add_argument('--output_root', default='resources')
arguments = parser.parse_args()
BASE = pathlib.Path(arguments.cache)
ROOT = pathlib.Path(arguments.output_root)
BASE.mkdir(parents=True, exist_ok=True)
for filename, url in [('helm-list.xml', 'https://storage.googleapis.com/crfm-helm-public/?prefix=mmlu/benchmark_output/releases/v1.13.0/groups/json/'), ('helm-summary.json', 'https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/summary.json'), ('contents.parquet', 'https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet')]:
    if not (BASE / filename).exists():
        (BASE / filename).write_bytes(urllib.request.urlopen(url, timeout=120).read())
def canonical(value):
    if isinstance(value, str):
        return ' '.join(unicodedata.normalize('NFKC', value).split())
    if isinstance(value, (float, int)):
        return str(decimal.Decimal(str(value)).normalize())
    if isinstance(value, dict):
        return {canonical(key): canonical(item) for key, item in sorted(value.items())}
    return [canonical(item) for item in value]
def digest(value):
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
keys = [item.text for item in ET.parse(BASE / 'helm-list.xml').getroot().iter() if item.tag.endswith('Key') and '_subject:' in item.text and '/mmlu_mmlu_' not in item.text]
assert len(keys) == 57
def fetch(key):
    local = BASE / key.rsplit('subject:', 1)[1]
    if not local.exists():
        local.write_bytes(urllib.request.urlopen('https://storage.googleapis.com/crfm-helm-public/' + key, timeout=60).read())
    return key, json.loads(local.read_bytes()), hashlib.sha256(local.read_bytes()).hexdigest()
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    subjects = list(executor.map(fetch, keys))
models = {}
for key, subject, content_hash in subjects:
    task = key.rsplit('subject:', 1)[1][:-5]
    assert subject['header'][1]['value'] == 'EM' and subject['header'][1]['lower_is_better'] is False
    for row_index, row in enumerate(subject['rows']):
        specs = row[0]['run_spec_names']
        assert len(specs) == 1
        model = re.search(r',model=([^,]+)', specs[0]).group(1)
        record = models.setdefault(model, {'id': model, 'raw': {}, 'provenance': []})
        assert task not in record['raw']
        record['raw'][task] = row[1]['value']
        record['provenance'].append({'source_url': 'https://storage.googleapis.com/crfm-helm-public/' + key, 'source_sha256': content_hash, 'row_index': row_index, 'run_spec': specs[0]})
helm_tasks = sorted(item[0].rsplit('subject:', 1)[1][:-5] for item in subjects)
oll_tasks = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO']
oll_source = hashlib.sha256((BASE / 'contents.parquet').read_bytes()).hexdigest()
families = {'helm': (helm_tasks, list(models.values()), 1), 'openllm': (oll_tasks, [], 100)}
for index, row in enumerate(parquet.read_table(BASE / 'contents.parquet').to_pylist()):
    families['openllm'][1].append({'id': row['fullname'], 'raw': {task: row[task] for task in oll_tasks}, 'aliases': [row.get('Base Model'), row.get('Model sha'), row['fullname']], 'provenance': [{'source_url': 'https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet', 'source_sha256': oll_source, 'row_index': index, 'eval_name': row['eval_name'], 'model_sha': row['Model sha'], 'base_model': row.get('Base Model')}]})
records = []
counts = {}
for family, (tasks, rows, scale) in families.items():
    eligible = []
    for row in rows:
        if set(row['raw']) != set(tasks) or any(type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= scale for value in row['raw'].values()):
            continue
        row['family'] = family
        row['raw_hash'] = digest(row['raw'])
        eligible.append(row)
    counts[family] = {'source_rows': len(rows), 'eligible_rows': len(eligible), 'excluded_rows': len(rows) - len(eligible)}
    records.extend(eligible)
parents = list(range(len(records)))
def find(index):
    while parents[index] != index:
        parents[index] = parents[parents[index]]
        index = parents[index]
    return index
def model_alias(value):
    value = canonical(value).lower()
    if '/' not in value and '_' in value:
        value = value.replace('_', '/', 1)
    if value.startswith('meta/'):
        value = 'meta-llama/' + value[len('meta/'):]
    if value.endswith('-turbo'):
        value = value[:-len('-turbo')]
    if value.startswith('meta-llama/') and value.endswith('-hf'):
        value = value[:-len('-hf')]
    return value
seen = {}
for index, row in enumerate(records):
    aliases = ['hash:' + row['raw_hash'], 'id:' + canonical(row['id']).lower(), 'model:' + model_alias(row['id'])]
    for alias in row.get('aliases', []):
        if alias and canonical(alias).lower() not in ('none', 'unknown', 'n/a'):
            aliases.extend(['alias:' + canonical(alias).lower(), 'id:' + canonical(alias).lower(), 'model:' + model_alias(alias)])
    row['model_aliases'] = sorted(set(aliases))
    for alias in aliases:
        if alias in seen:
            parents[find(index)] = find(seen[alias])
        else:
            seen[alias] = index
groups = {}
for index, row in enumerate(records):
    groups.setdefault(find(index), []).append(row)
partitions = {'search': {'helm': [], 'openllm': []}, 'final': {'helm': [], 'openllm': []}}
for group in groups.values():
    cluster = hashlib.sha256(('split-20261027:' + min(row['raw_hash'] for row in group)).encode()).hexdigest()
    plane = 'search' if int(cluster[:16], 16) / 2**64 < .4 else 'final'
    for row in group:
        row['cluster'] = cluster
        partitions[plane][row['family']].append(row)
search_hashes = {row['raw_hash'] for family in partitions['search'].values() for row in family}
final_hashes = {row['raw_hash'] for family in partitions['final'].values() for row in family}
assert not search_hashes & final_hashes
for row in records:
    tasks, _, scale = families[row['family']]
    row['scores'] = [row['raw'][task] / scale for task in tasks]
for plane, family_rows in partitions.items():
    directory = ROOT / plane
    directory.mkdir(parents=True, exist_ok=True)
    for family, rows in family_rows.items():
        unique = {}
        for row in sorted(rows, key=lambda row: (row['raw_hash'], row['id'])):
            if row['raw_hash'] not in unique:
                unique[row['raw_hash']] = row
            else:
                unique[row['raw_hash']]['provenance'].extend(row['provenance'])
        payload = {'schema_version': 1, 'family': family, 'tasks': families[family][0], 'scale': families[family][2], 'rows': list(unique.values()), 'source_counts': counts[family], 'duplicate_rows_collapsed': len(rows) - len(unique), 'split': {'seed': 20261027, 'algorithm': 'NFKC whitespace/Decimal stable raw-score hashes; union exact content, fullname, known base model and model-sha aliases before hash-threshold 40/60 assignment', 'cross_plane_raw_overlap': 0, 'cross_plane_cluster_overlap': 0}, 'license': 'No separate score-data license declared by source; public research analysis with attribution. Code/per-model licenses do not license these data. Redistribution permission uncertain; frozen minimal score excerpts for isolated research runtime. Reacquire via source URLs for reproduction; seek permission before public redistribution.', 'acquired_utc': '2026-11-07'}
        (directory / (family + '.json')).write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n')
        print(plane, family, len(unique), len(families[family][0]), counts[family])
print('raw_overlap', len(search_hashes & final_hashes))
