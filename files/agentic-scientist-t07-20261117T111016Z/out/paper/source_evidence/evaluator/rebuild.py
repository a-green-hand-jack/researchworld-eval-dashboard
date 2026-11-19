"""Rebuild frozen arrays/manifests from pinned local inputs; never used at runtime.

Acquire the task.md commit under --upstream-dir and the harness-supplied raw
column/row provenance tree under --columns-dir. No network access is performed.
Both output planes are evaluator-private, not candidate assets.
"""

import argparse
import ast
import hashlib
import json
import pathlib
import re
import unicodedata

import joblib
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--upstream-dir', required=True)
parser.add_argument('--columns-dir', required=True)
parser.add_argument('--output-dir', required=True)
arguments = parser.parse_args()
EXTRA = pathlib.Path(arguments.columns_dir)
UP = pathlib.Path(arguments.upstream_dir)
DEST = pathlib.Path(arguments.output_dir)
if hashlib.sha256((EXTRA / 'SOURCES.json').read_bytes()).hexdigest() != '6ed297737db27ac59df0cf05f67ec517bba84dd5950abfbd8fca2933122155c1':
    raise ValueError('raw provenance snapshot mismatch')
if hashlib.sha256((EXTRA / 'openllm/models.jsonl').read_bytes()).hexdigest() != '64130c9f6b9265283a002daa850e39e4795d89f89c82077ef06944f06f526e46':
    raise ValueError('lineage metadata snapshot mismatch')
score_hashes = json.loads((EXTRA / 'SOURCES.json').read_text())['upstream']['score_files_sha256']
SEARCH = ['arc_challenge', 'ifeval', 'commonsense', 'gsm']
FINAL = ['bbh', 'gpqa', 'mmlu_pro', 'musr', 'openllm_math', 'legalbench', 'math', 'med_qa', 'mmlu']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).split())

def content(record):
    if 'text' in record:
        text = record['text']
        parts = re.split(r'\s+[A-J][.)]\s+', text)
        stem, options = parts[0], parts[1:]
    else:
        doc = record['doc']
        if isinstance(doc, str):
            doc = ast.literal_eval(doc)
        stem = doc.get('question', doc.get('Question', doc.get('prompt', doc.get('input', doc.get('problem')))))
        if stem is None:
            raise ValueError('unknown raw document schema')
        if 'narrative' in doc:
            stem = doc['narrative'] + '\n' + stem
        options = doc.get('options', doc.get('choices', []))
        if isinstance(options, dict):
            options = options['text']
        if 'choice1' in doc:
            options = [doc[f'choice{index}'] for index in range(1, 5)]
    canonical = json.dumps([norm(stem), [norm(option) for option in options]], ensure_ascii=False, separators=(',', ':'))
    return sha(canonical.encode()), sha(norm(stem).encode())

def model_key(name):
    key = re.sub(r'[^a-z0-9]', '', name.lower())
    for prefix in ['metallama', 'meta', 'huggingface', 'togethercomputer', 'together', 'mistralai', 'google', 'microsoft', 'eleutherai']:
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    key = re.sub(r'(instruct|chat|hf|gptq|awq|gguf|int8|int4|4bit|8bit|turbo|preview)+$', '', key)
    return key

parent = {}
def find(key):
    parent.setdefault(key, key)
    if parent[key] != key:
        parent[key] = find(parent[key])
    return parent[key]

def union(left, right):
    left, right = find(left), find(right)
    if left != right:
        parent[max(left, right)] = min(left, right)

for line in open(EXTRA / 'openllm/models.jsonl'):
    meta = json.loads(line)
    name = model_key(meta['fullname'])
    bases = meta.get('Base Model')
    if isinstance(bases, str) and bases.strip() and bases not in ('None', 'Unknown', 'N/A'):
        union(name, model_key(bases))
    elif isinstance(bases, list):
        for base in bases:
            union(name, model_key(base))

records = {}
for case in SEARCH + FINAL:
    category = 'openllm' if (EXTRA / 'openllm' / case).exists() else 'helm'
    root = EXTRA / category / case
    columns = [json.loads(line) for line in open(root / 'columns.jsonl')]
    assert [entry['col'] for entry in columns] == list(range(len(columns)))
    hashes = [content(entry) for entry in columns]
    raw_rows = json.load(open(root / 'rows.json'))
    rows = raw_rows['rows'] if isinstance(raw_rows, dict) else raw_rows
    score_path = UP / 'data/scores' / (case + '.jbl')
    if sha(score_path.read_bytes()) != score_hashes[case + '.jbl']:
        raise ValueError('pinned score digest mismatch')
    matrix = np.asarray(joblib.load(score_path))
    assert matrix.shape == (len(rows), len(columns)), (case, matrix.shape, len(rows), len(columns))
    assert np.isfinite(matrix).all() and np.isin(matrix, [0, 1]).all()
    matrix = matrix.astype(np.uint8)
    if category == 'openllm':
        if sha((UP / 'data/scores' / (case + '_models.jbl')).read_bytes()) != score_hashes[case + '_models.jbl']:
            raise ValueError('pinned model-list digest mismatch')
        names = list(joblib.load(UP / 'data/scores' / (case + '_models.jbl')))
        assert names == [row['model'] for row in rows]
    for row in rows:
        find(model_key(row['model']))
    records[case] = (columns, hashes, rows, matrix, category)

final_content = {digest for case in FINAL for pair in records[case][1] for digest in pair}
summary = {}
for case in SEARCH + FINAL:
    columns, hashes, rows, matrix, category = records[case]
    plane = 'search' if case in SEARCH else 'final'
    keep = [index for index, pair in enumerate(hashes) if plane == 'final' or not set(pair) & final_content]
    source_rows, target_rows, source_groups, target_groups = [], [], [], []
    seen = set()
    duplicates = []
    for index, row in enumerate(rows):
        root = find(model_key(row['model']))
        fraction = int(sha(('t07-lineage-v1' + root).encode()), 16) / 2**256
        role = ('search_source' if fraction < .30 else 'search_target' if fraction < .45
                else 'final_source' if fraction < .80 else 'final_target')
        identity = row.get('details_repo', row['model'])
        if identity in seen:
            duplicates.append(index)
            continue
        seen.add(identity)
        if role == plane + '_source':
            source_rows.append(index)
            source_groups.append(root)
        elif role == plane + '_target':
            target_rows.append(index)
            target_groups.append(root)
    mapping = {}
    item_groups = [mapping.setdefault(hashes[index][1], len(mapping)) for index in keep]
    source = matrix[np.ix_(source_rows, keep)]
    target = matrix[np.ix_(target_rows, keep)]
    folder = DEST / plane
    folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(folder / (case + '.npz'), source=source, target=target,
                        item_groups=np.array(item_groups), source_groups=np.array(source_groups),
                        target_groups=np.array(target_groups))
    selected_columns = [dict(columns[index], normalized_content_sha256=hashes[index][0],
                             normalized_prompt_sha256=hashes[index][1]) for index in keep]
    with open(folder / (case + '_columns.jsonl'), 'w') as stream:
        for column in selected_columns:
            stream.write(json.dumps(column, ensure_ascii=False) + '\n')
    manifest = dict(case=case, shape=list(matrix.shape), retained_columns=keep,
                    source_rows=[dict(rows[index], lineage=group) for index, group in zip(source_rows, source_groups)],
                    target_rows=[dict(rows[index], lineage=group) for index, group in zip(target_rows, target_groups)],
                    duplicate_provenance_rows=duplicates,
                    upstream_sha256=sha((UP / 'data/scores' / (case + '.jbl')).read_bytes()),
                    columns_sha256=sha((EXTRA / category / case / 'columns.jsonl').read_bytes()),
                    rows_sha256=sha((EXTRA / category / case / 'rows.json').read_bytes()),
                    normalization='t07-content-v1 NFKC, whitespace collapse; ordered options; common stem without administrative IDs or answer fields; conservative prompt-only grouping and cross-plane removal',
                    lineage_policy='t07-lineage-v1 + canonical metadata-unioned base root; hash intervals .30/.45/.80; normalized official aliases; ambiguous declared multi-base union',
                    limitations=['Metadata-limited lineage grouping cannot prove absence of undocumented derivatives.',
                                 'Common-stem reconciliation is conservative, not proof of semantic equivalence or pretraining disjointness.'])
    (folder / (case + '_manifest.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    summary[case] = dict(source=source.shape, target=target.shape,
                         source_groups=len(set(source_groups)), target_groups=len(set(target_groups)),
                         content_groups=len(mapping), removed=len(columns)-len(keep))
    print(case, summary[case], flush=True)
    assert len(keep) >= 250 and len(mapping) >= 25
    assert len(set(source_groups)) >= 8 and len(set(target_groups)) >= 5, (case, summary[case])
    assert source.shape[0] <= 512 and target.shape[0] <= 512 and source.shape[1] <= 65536
for case in SEARCH:
    for index in json.load(open(DEST / 'search' / (case + '_manifest.json')))['retained_columns']:
        assert not set(records[case][1][index]) & final_content
print(json.dumps(summary, indent=2))
