#!/usr/bin/env python3
"""Verify archival core aggregation from complete trial rows, with original order.

No fitting, trial generation, outcome selection or alternate interval estimator.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pandas as pd

ANALYSIS=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,help='Complete fresh canonical trials.jsonl')
    parser.add_argument('--core',default=str(ANALYSIS/'results/core_interim'))
    parser.add_argument('--output',required=True,help='New verification directory')
    args=parser.parse_args();out=Path(args.output);core=Path(args.core);source=Path(args.input)
    if out.exists() and any(out.iterdir()):raise ValueError('Use an absent or empty verification output directory')
    meta=json.loads((core/'metadata.json').read_text());order={}
    for i,entry in enumerate(meta['checkpoint_manifest']):
        cell,repeat=Path(entry['path']).stem.rsplit('__',1)
        key=(cell,int(repeat));assert key not in order;order[key]=i
    assert len(order)==1000
    lines=[]
    with source.open() as f:
        for line in f:
            row=json.loads(line);key=(row['id'],row['repeat'])
            if key in order:lines.append((order[key],line))
    assert len(lines)==meta['rows']==22600
    lines.sort(key=lambda item:item[0]) # stable; preserve saved within-checkpoint method/group order
    out.mkdir(parents=True,exist_ok=True);reordered=out/'core_in_original_order.jsonl.gz'
    with gzip.open(reordered,'wt') as f:
        for _,line in lines:f.write(line)
    for script in [ANALYSIS/'scripts/summarize.py',ANALYSIS/'postprocess/study_summaries.py']:
        expected=json.loads((core/'derived/metadata.json').read_text())['inputs_and_code_sha256']
        matching=[v for k,v in expected.items() if k.endswith('/'+script.name)]
        assert len(matching)==1 and digest(script)==matching[0],script
    subprocess.run([sys.executable,str(ANALYSIS/'scripts/summarize.py'),'--input',str(reordered),'--output',str(out/'summary')],check=True)
    subprocess.run([sys.executable,str(ANALYSIS/'postprocess/study_summaries.py'),'--input',str(reordered),'--summary',str(out/'summary'),'--config',str(ANALYSIS/'configs/frozen.json'),'--output',str(out/'derived')],check=True)
    checks=[]
    for folder in ['summary','derived']:
        for original in sorted((core/folder).glob('*.csv')):
            actual=out/folder/original.name
            try:
                a,b=pd.read_csv(original),pd.read_csv(actual)
            except pd.errors.EmptyDataError:
                assert original.read_bytes()==actual.read_bytes(),original
                checks.append({'path':str(original.relative_to(core)),'rows':0,'bootstrap_columns':[],
                               'max_numeric_difference':0,'max_bootstrap_difference':0})
                continue
            pd.testing.assert_frame_equal(a,b,check_exact=False,rtol=0,atol=1e-12)
            numerical=[c for c in a if pd.api.types.is_numeric_dtype(a[c])]
            differences=[float((a[c]-b[c]).abs().max()) for c in numerical if a[c].dtype!='bool']
            boot=[c for c in a if 'bootstrap' in c]
            checks.append({'path':str(original.relative_to(core)),'rows':len(a),'bootstrap_columns':boot,
                           'max_numeric_difference':max([d for d in differences if pd.notna(d)],default=0),
                           'max_bootstrap_difference':max([float((a[c]-b[c]).abs().max()) for c in boot],default=0)})
    report={'status':'passed','source_trial_sha256':digest(source),'core_metadata_sha256':digest(core/'metadata.json'),
            'helper_sha256':digest(Path(__file__)),'checkpoint_order':'exact checkpoint_manifest list order, stable within each checkpoint',
            'core_trials':len(order),'core_rows':len(lines),'checks':checks,'tolerance':{'absolute':1e-12,'relative':0},
            'new_scientific_trials':0,'interpretation':'Replays original fixed-seed aggregation order only. Does not loosen final-export uncertainty checks or modify any result.'}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('HUTIAN_WAKE: archival core order replay passed all summaries and derived exports',flush=True)


if __name__=='__main__':main()
