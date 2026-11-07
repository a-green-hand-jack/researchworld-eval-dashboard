"""Freeze completed registered inputs, retaining a superseded copy in published Git.

No training or analysis is run. The output is a partial input snapshot, not evidence
of full-study completion. Retention refusal occurs before old-copy removal.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--target', type=Path, required=True)
p.add_argument('--record', type=Path, required=True)
p.add_argument('--superseded-record', type=Path)
p.add_argument('--retention-record', type=Path)
a = p.parse_args()
root, target = a.root.resolve(), a.target.resolve()
if target.exists() or target.parent != root.parent or not target.name.startswith('experiment-checkpoint-'):
    raise ValueError('Use a new sibling experiment-checkpoint-* directory')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)

revision = git('rev-parse', 'HEAD').decode().strip()
if a.superseded_record:
    if not a.retention_record:
        raise ValueError('A retention output is required with a superseded record')
    previous = json.loads(a.superseded_record.read_text())
    old = Path(previous['snapshot_checkout']).resolve()
    if old == target or old == root or old.parent != root.parent or not old.name.startswith('experiment-checkpoint-'):
        raise ValueError('Invalid superseded checkpoint path')
    refs = list(dict.fromkeys([previous['source_revision'], revision]))
    maps = []
    for ref in refs:
        mapping = {}
        for entry in git('ls-tree', '-rz', ref).split(b'\0'):
            if entry:
                info, name = entry.split(b'\t')
                mapping[name.decode()] = info.split()[2].decode()
        maps.append(mapping)
    files = []
    for path in sorted(old.rglob('*')):
        if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        relative = str(path.relative_to(old))
        data = path.read_bytes()
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        retained = next((ref for ref, mapping in zip(refs, maps) if mapping.get(relative) == oid), None)
        if retained is None:
            raise ValueError('Not retained in published Git: ' + relative)
        files.append(dict(path=relative, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), published_revision=retained))
    a.retention_record.parent.mkdir(parents=True, exist_ok=True)
    a.retention_record.write_text(json.dumps(dict(checked_utc=datetime.now(timezone.utc).isoformat(),
        kind='Exact published-Git retention verification before superseded worktree removal', directory=str(old),
        reference_revisions=refs, matched_files=len(files), files=files,
        exclusions='Git worktree pointer and generated Python caches; no scientific content excluded'), indent=2) + '\n')
    if (old / '.git').exists():
        subprocess.run(['git', 'worktree', 'remove', '--force', str(old)], cwd=root, check=True)
    else:
        shutil.rmtree(old)

target.mkdir()
# Stream directly; do not create a second temporary archive on disk.
with subprocess.Popen(['tar', '-x', '-C', str(target)], stdin=subprocess.PIPE) as extract:
    archive = subprocess.run(['git', 'archive', revision], cwd=root, stdout=extract.stdin, check=False)
    extract.stdin.close()
    extracted = extract.wait()
    if archive.returncode or extracted:
        raise RuntimeError('Archive/extraction failed; snapshot is not valid')
shutil.rmtree(target / 'results/confirmatory')
(target / 'results/confirmatory').mkdir()
registry_path = root / 'configs/confirmatory.json'
runs = json.loads(registry_path.read_text())['runs']
completed = [r['name'] for r in runs if (root / 'results/confirmatory' / r['name'] / 'summary.json').exists()]
for name in completed:
    shutil.copytree(root / 'results/confirmatory' / name, target / 'results/confirmatory' / name)
record = dict(snapshot_kind='Immutable completed-run input freeze for reproducible partial derived pipeline;live executions excluded',
    created_utc=datetime.now(timezone.utc).isoformat(), source_revision=revision,
    completed_names=completed, completed_count=len(completed), snapshot_checkout=str(target),
    registry_sha256=hashlib.sha256(registry_path.read_bytes()).hexdigest(),
    live_incomplete_excluded=[r['name'] for r in runs if (root / 'results/confirmatory' / r['name'] / 'metadata.json').exists() and r['name'] not in completed],
    generator='code/scripts/freeze_completed.py', generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
a.record.parent.mkdir(parents=True, exist_ok=True)
a.record.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'completed_names'}), flush=True)
