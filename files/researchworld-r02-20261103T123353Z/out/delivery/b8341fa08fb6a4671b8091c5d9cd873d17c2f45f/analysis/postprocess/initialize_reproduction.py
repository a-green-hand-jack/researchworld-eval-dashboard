#!/usr/bin/env python3
"""Verify frozen identity and seed only execution provenance into an empty root.

No git object, bundled result directory, scientific import, or network is used.
Keep this helper outside scripts/: the frozen runner hashes scripts/*.py.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ANALYSIS = Path(__file__).resolve().parents[1]


def initialize(root, config):
    root, config = Path(root).resolve(), Path(config).resolve()
    template_path = ANALYSIS / 'provenance/frozen-execution.json'
    template_bytes = template_path.read_bytes()
    template = json.loads(template_bytes)
    if hashlib.sha256(config.read_bytes()).hexdigest() != template['frozen_config_sha256']:
        raise ValueError('Frozen configuration hash mismatch; no output was initialized')
    # Original execution hashes use delivery-root paths. Verify every pinned
    # file, including the shell launch/finalization commands, without git.
    for relative, expected in template['source_hashes'].items():
        source = (ANALYSIS.parent / relative).resolve()
        if not source.is_relative_to(ANALYSIS):
            raise ValueError('Source identity path escapes analysis directory')
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen source hash mismatch: {relative}')
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError('Output root must be absent or empty; refusing to reuse existing results')
    record = {key: template[key] for key in
              ['source_commit', 'accepted_candidate_sha256', 'frozen_config_sha256', 'source_hashes']}
    record.update({
        'status': 'initialized for fresh reproduction; no trial has been executed or validated',
        'provenance_template_sha256': hashlib.sha256(template_bytes).hexdigest(),
        'initialized_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Original immutable study identity only. This fresh root contains no copied scientific outputs, original job outcomes or run-cost records. Completion is established by the subsequent full audit, not this initialization.'})
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'execution.json').open('x') as out:
        json.dump(record, out, indent=2)
        out.write('\n')
    return len(template['source_hashes'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='Absent or completely empty output directory')
    parser.add_argument('--config', default=str(ANALYSIS / 'configs/frozen.json'))
    args = parser.parse_args()
    count = initialize(args.root, args.config)
    print(f'Initialized only execution.json after checking config and {count} frozen source files; no trials run or copied')


if __name__ == '__main__':
    main()
