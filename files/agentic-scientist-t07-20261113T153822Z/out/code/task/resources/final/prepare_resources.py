import ast
import hashlib
import json
import pathlib
import re
import unicodedata
import joblib
import numpy as np

import argparse
parser = argparse.ArgumentParser(description='Reconstruct immutable score matrices and document/provenance audit from the pinned upstream clone and supplied raw-column asset; run BEFORE any search. Raw metadata stays private.')
parser.add_argument('--column-asset', required=True)
parser.add_argument('--upstream-clone', required=True)
parser.add_argument('--output-resources', required=True)
arguments = parser.parse_args()
ROOT = pathlib.Path(arguments.column_asset)
UP = pathlib.Path(arguments.upstream_clone)
OUT = pathlib.Path(arguments.output_resources)
if any(OUT.glob('search/*')) or any(OUT.glob('final/*')):
    raise ValueError('Refuse to overwrite frozen resource roots; use a fresh output directory')
SEARCH = ['arc_challenge', 'ifeval', 'mmlu_pro']
FINAL = ['bbh', 'gpqa', 'musr', 'openllm_math', 'commonsense', 'gsm', 'legalbench', 'math', 'med_qa', 'mmlu']

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).replace('\r\n', '\n').replace('\r', '\n').split())

def content(case, record):
    choices = []
    if 'doc' not in record:
        text = record['text']
        parts = re.split(r'\nA\.\s', text, maxsplit=1)
        stem = parts[0]
        if len(parts) == 2 and case not in ('gsm', 'math', 'legalbench'):
            choices = re.split(r'\s+[B-Z]\.\s', parts[1])
    else:
        doc = record['doc']
        if isinstance(doc, str):
            doc = ast.literal_eval(doc)
        if case == 'arc_challenge':
            stem, choices = doc['question'], doc['choices']['text']
        elif case == 'ifeval':
            stem = doc['prompt']
        elif case == 'mmlu_pro':
            stem, choices = doc['question'], doc['options']
        elif case == 'bbh':
            stem = doc['input']
        elif case == 'gpqa':
            stem = doc['Question']
            choices = [doc['choice' + str(index)] for index in range(1, 5)]
        elif case == 'musr':
            stem, choices = doc['narrative'] + '\n' + doc['question'], doc['choices']
        elif case == 'openllm_math':
            stem = doc['problem']
        else:
            raise ValueError('unknown adapter')
    stem = norm(stem)
    if not stem:
        raise ValueError('empty stem')
    choices = [norm(choice) for choice in choices]
    return { 'stem_hash': sha(stem.encode()),
             'ordered_hash': sha(json.dumps([stem, choices], ensure_ascii=False, separators=(',', ':')).encode()),
             'unordered_hash': sha(json.dumps([stem, sorted(choices)], ensure_ascii=False, separators=(',', ':')).encode()) }

metadata = [json.loads(line) for line in (ROOT/'openllm/models.jsonl').open()]
parents = {}
def find(key):
    parents.setdefault(key, key)
    if parents[key] != key:
        parents[key] = find(parents[key])
    return parents[key]
def union(left, right):
    left, right = find(left), find(right)
    parents[max(left, right)] = min(left, right)
def family(name):
    lower = name.lower()
    for label, pattern in [('llama', r'llama|vicuna|alpaca|wizardlm|tulu|nous-hermes|openbuddy|synthia'), ('qwen', r'qwen'), ('mistral', r'mistral|mixtral|zephyr|dolphin'), ('gemma', r'gemma'), ('yi', r'(^|[/_-])yi[-_0-9]'), ('phi', r'phi[-_0-9]'), ('gpt', r'gpt|text-davinci|text-curie|text-babbage|text-ada'), ('claude', r'claude'), ('bloom', r'bloom'), ('falcon', r'falcon'), ('pythia', r'pythia|stablelm|dolly'), ('olmo', r'olmo'), ('mpt', r'mpt'), ('opt', r'(^|/)opt[-_]'), ('palm', r'palm|text-bison'), ('command', r'command')]:
        if re.search(pattern, lower):
            return 'family:' + label
    return 'provider:' + lower.split('/')[0].split('_')[0]
for entry in metadata:
    name = entry['fullname'].lower()
    union(name, family(name))
    base = entry.get('Base Model')
    if isinstance(base, str) and '/' in base:
        union(name, base.lower())
        union(base.lower(), family(base))

cases = {}
source_info = json.loads((ROOT/'SOURCES.json').read_text())
for case in SEARCH + FINAL:
    domain = 'openllm' if (ROOT/'openllm'/case).is_dir() else 'helm'
    folder = ROOT/domain/case
    columns = [json.loads(line) for line in (folder/'columns.jsonl').open()]
    rows = json.loads((folder/'rows.json').read_text())
    rows = rows['rows'] if isinstance(rows, dict) else rows
    raw = (UP/'data/scores'/f'{case}.jbl').read_bytes()
    assert sha(raw) == source_info['upstream']['score_files_sha256'][case + '.jbl']
    matrix = np.asarray(joblib.load(UP/'data/scores'/f'{case}.jbl'))
    assert matrix.ndim == 2 and np.isin(matrix, [0, 1]).all()
    assert matrix.shape == (len(rows), len(columns))
    assert [entry['col'] for entry in columns] == list(range(len(columns)))
    assert [entry['row'] for entry in rows] == list(range(len(rows)))
    model_file = UP/'data/scores'/f'{case}_models.jbl'
    if model_file.exists():
        assert list(joblib.load(model_file)) == [entry['model'] for entry in rows]
    identities = {}
    for row in rows:
        name = row['model'].lower()
        union(name, family(name))
        identity = row.get('details_repo', name)
        if identity in identities:
            union(name, identities[identity])
        identities[identity] = name
    hashes = [content(case, record) for record in columns]
    cases[case] = (matrix.astype(np.uint8), columns, rows, hashes, domain, sha(raw), sha((folder/'columns.jsonl').read_bytes()), sha((folder/'rows.json').read_bytes()))

reserved = {value for case in FINAL for entry in cases[case][3] for value in entry.values()}
summary = {}
for plane, names in [('search', SEARCH), ('final', FINAL)]:
    target = OUT/plane
    target.mkdir(parents=True, exist_ok=True)
    manifest = {'schema_version': 1, 'plane': plane, 'normalization': 'NFKC; canonical line endings; Unicode whitespace collapse; SHA256 UTF8; stem-only conservative duplicate exclusion plus ordered and sorted-choice signatures; HELM reference/explanation suffix stripped at newline A. for gsm/math/legalbench.', 'split_rule': 'provenance union of base-model edges, alias/details identities, broad named family; otherwise provider; SHA256(seed,group) ordered 70/30; all eligible rows', 'cases': {}, 'limitations': ['Family grouping is a conservative heuristic; metadata cannot prove all model training lineages.', 'Column alignment relies on supplied SOURCES reconstruction attestations and pinned raw checksums, not newly downloaded model outputs.', 'Raw text is not redistributed; adapters are fixed at staging. Hashes and mappings retained; task-author-supplied metadata needed to independently repeat raw audit.', 'No novel-method superiority gate; valid negative results remain eligible.', 'Bootstrap treats benchmark item universes as fixed; no population-of-items claim or independent-benchmark significance claim is supported.']}
    for case in names:
        matrix, columns, rows, hashes, domain, original_sha, cols_sha, rows_sha = cases[case]
        keep = [index for index, entry in enumerate(hashes) if plane == 'final' or not (set(entry.values()) & reserved)]
        assert len(keep) >= 32
        selected = matrix[:, keep]
        groups = [find(row['model'].lower()) for row in rows]
        assert len(set(groups)) >= 5, (case, set(groups))
        np.savez_compressed(target/f'{case}.npz', responses=selected)
        audit = {'source_commit': '55faff496947789f94e6b5908c77cbc3e84f81ad', 'original_matrix_sha256': original_sha, 'raw_columns_sha256': cols_sha, 'raw_rows_sha256': rows_sha, 'original_shape': list(matrix.shape), 'kept_columns': keep, 'removed_columns': sorted(set(range(matrix.shape[1])) - set(keep)), 'content': [{**hashes[index], 'original_col': index, 'source_id': str(columns[index].get('id', (columns[index].get('subtask'), columns[index].get('doc_id')))), 'original_doc_hash': columns[index].get('doc_hash')} for index in keep], 'rows': [{**row, 'group': groups[index], 'response_fingerprint': sha(matrix[index].tobytes())} for index, row in enumerate(rows)]}
        (target/f'{case}.json').write_text(json.dumps(audit, ensure_ascii=False, separators=(',', ':'))+'\n')
        manifest['cases'][case] = {'domain': domain, 'shape': list(selected.shape), 'matrix_sha256': sha((target/f'{case}.npz').read_bytes()), 'audit_sha256': sha((target/f'{case}.json').read_bytes()), 'removed': matrix.shape[1]-len(keep)}
        summary[case] = [*selected.shape, len(set(groups)), matrix.shape[1]-len(keep)]
    manifest['cross_plane_content_disjoint'] = True
    (target/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))+'\n')
    license_file = next(UP.glob('LICENSE*'), None) or next(UP.glob('LICENCE*'), None)
    assert license_file
    (target/'UPSTREAM_LICENSE.txt').write_bytes(license_file.read_bytes())
search_hashes = {value for case in SEARCH for entry in json.loads((OUT/'search'/f'{case}.json').read_text())['content'] for key,value in entry.items() if key.endswith('_hash') and key != 'original_doc_hash'}
assert not search_hashes & reserved
print(json.dumps(summary, indent=2))

print("Matrix and raw-audit reconstruction only. Protocol manifests additionally bind the frozen seeds, split indices, operation table and claim policy described in the evaluators/contract; do not overwrite published resources.")
