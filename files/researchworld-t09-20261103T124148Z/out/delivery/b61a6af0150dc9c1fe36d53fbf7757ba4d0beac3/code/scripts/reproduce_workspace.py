"""Prepare and postprocess a self-contained reproduction without reading source results.

Preparation copies code/configs and labels original documentation/receipts as
reference material. It never copies results. Existing results-only workspaces are
supported; existing code/analysis paths are refused to protect prior receipts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n')


def prepare(workspace):
    source = Path(__file__).resolve().parents[1]
    reference = source.parent/'analysis' if source.name == 'code' else source/'notes'
    if workspace == source or workspace == source.parent:
        raise ValueError('Use a distinct reproduction workspace')
    if (workspace/'code').exists() or (workspace/'analysis').exists():
        raise ValueError('Preparation refuses existing code/analysis; use a new workspace or its already prepared postprocess command')
    workspace.mkdir(parents=True, exist_ok=True)
    code = workspace/'code'
    code.mkdir()
    for name in ['src', 'scripts', 'configs', 'data', 'tests']:
        shutil.copytree(source/name, code/name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.tmp'))
    for name in ['pyproject.toml', 'requirements-lock.txt', 'environment.json']:
        shutil.copy2(source/name, code/name)
    notes = workspace/'analysis'
    notes.mkdir()
    # Original receipts are retained as reference, never installed at fresh receipt paths.
    shutil.copytree(reference, notes/'reference_delivery')
    for name in ['methods.md', 'supplementary_analysis.md', 'exposure_boundary_correction.md', 'delivery_reproduction.md']:
        shutil.copy2(reference/name, notes/name)
    (notes/'roundoff_v1').mkdir()
    shutil.copy2(reference/'roundoff_v1/graph_metadata.json', notes/'roundoff_v1/graph_metadata.json')
    launch = dict(status='prepared reproduction; execution not yet audited',
                  source_sha256={p.name:sha(p) for p in sorted((code/'src/gatebench').glob('*.py'))},
                  configs={p.name:sha(p) for p in sorted((code/'configs').glob('production*.json'))},
                  note='Local source snapshot for checking this workspace; original receipts are reference_delivery only, not fresh execution evidence.')
    write(notes/'execution_manifest.json', launch)
    write(notes/'workspace_preparation.json', dict(status='prepared', workspace=str(workspace),
          code_source=str(source), reference_source=str(reference), copied_results=False,
          prior_results_present=(workspace/'results').exists(), source_snapshot=launch,
          reference_files={str(p.relative_to(notes/'reference_delivery')):sha(p)
                           for p in sorted((notes/'reference_delivery').rglob('*')) if p.is_file()}))
    print('Prepared self-contained code/ and analysis/; no results copied:', workspace, flush=True)


def postprocess(workspace):
    code=workspace/'code'; notes=workspace/'analysis'
    preparation=json.loads((notes/'workspace_preparation.json').read_text())
    # Do not accidentally turn a delivered root into a new run or overwrite fresh receipts.
    if preparation['workspace'] != str(workspace):
        raise ValueError('Preparation workspace identity mismatch')
    if (notes/'workspace_postprocessing.json').exists():
        raise ValueError('Fresh postprocessing already started; preserve its receipts and use a new prepared workspace for another attempt')
    snapshot=json.loads((notes/'execution_manifest.json').read_text())
    assert snapshot['source_sha256']=={p.name:sha(p) for p in sorted((code/'src/gatebench').glob('*.py'))}
    assert snapshot['configs']=={p.name:sha(p) for p in sorted((code/'configs').glob('production*.json'))}
    env=os.environ.copy();env['PYTHONPATH']=str(code/'src')
    env['GATEBENCH_DATA_DIR']=str(code/'data')
    for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:env[key]='1'
    receipts=notes/'workspace_postprocessing.json'
    record=dict(status='running', workspace=str(workspace), stages=[],
                source_snapshot=snapshot, scope='Postprocessing of this workspace only; no new study fits except the selected four-cell replay. Original reference receipts are not fresh evidence.')
    write(receipts,record)
    commands=[
        [sys.executable,'-m','gatebench.summarize','results/production_core','results/production_noise','results/production_imbalance','--output','results/summary'],
        [sys.executable,'-m','gatebench.support_bounds'],
        [sys.executable,str(code/'scripts/finalize_results.py'),'--root',str(workspace)],
        [sys.executable,str(code/'scripts/decomposition_report.py'),'--root',str(workspace)],
        [sys.executable,str(code/'scripts/audit_v2_dependencies.py'),'--root',str(workspace)],
        [sys.executable,str(code/'scripts/replay_selected.py'),'--source',str(workspace),'--workspace',str(workspace/'selected_replay')],
        [sys.executable,str(code/'scripts/final_report.py')],
        [sys.executable,str(code/'scripts/audit_diagnostics.py'),'--root',str(workspace)],
    ]
    try:
        for command in commands:
            start=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN)
            subprocess.run(command,cwd=workspace,env=env,check=True)
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            record['stages'].append(dict(command=command,wall_seconds=time.perf_counter()-start,
                cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                children_cumulative_peak_rss_kib=after.ru_maxrss))
            write(receipts,record)
            print('HUTIAN_WAKE: workspace postprocessing completed '+Path(command[1] if command[1]!='-m' else command[2]).name,flush=True)
        record['status']='passed'
        record['generated_files']={str(p.relative_to(workspace)):sha(p)
            for directory in [notes,workspace/'results/summary',workspace/'results/diagnostics']
            for p in sorted(directory.glob('*')) if p.is_file() and p!=receipts}
        # Preserve original documentation/receipt bytes throughout postprocessing.
        assert preparation['reference_files']=={str(p.relative_to(notes/'reference_delivery')):sha(p)
            for p in sorted((notes/'reference_delivery').rglob('*')) if p.is_file()}
    except Exception as error:
        record['status']='failed';record['error']=str(error)
        raise
    finally:
        write(receipts,record)
    print('HUTIAN_WAKE: portable workspace postprocessing passed',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','postprocess'])
    parser.add_argument('--workspace',required=True)
    args=parser.parse_args()
    globals()[args.action](Path(args.workspace).resolve())
