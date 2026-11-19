"""Check all executed support counts with independent integer inequalities.

This replays saved assignment seeds and sparse integer neighbor counts only;
there is no model fitting or new noise simulation. It also measures how often
normalizing before summation would cross the declared rational boundaries.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
from gatebench.run import build_graph
from gatebench.core import assignment

p=argparse.ArgumentParser();p.add_argument('--root',default='.')
p.add_argument('--partial',action='store_true',help='Checkpoint-only validation; not final completion evidence')
a=p.parse_args();root=Path(a.root).resolve();code=root/'code' if (root/'code/configs').exists() else root
notes=root/('analysis' if code!=root else 'notes');total=0;records=[]
os.environ.setdefault('GATEBENCH_DATA_DIR',str(code/'data'))
for stage in ['core','noise','imbalance']:
    config=json.loads((code/f'configs/production_{stage}.json').read_text())
    specs={hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest()[:16]:s for s in config['graphs']}
    for file in sorted((root/config['output']).glob('*.parquet')):
        if file.name.endswith('.tmp.parquet') or not file.with_suffix('.json').exists(): continue
        frame=pd.read_parquet(file)
        # Pick one of the72copies sharing each actual assignment.
        rows=frame.drop_duplicates('pairing_id')
        g=build_graph(specs[file.stem.split('_')[0]],config.get('data_dir','data'))
        d=g.degree.astype(np.int64);denominator=np.maximum(d,1)
        record=dict(panel=stage,cell_id=file.stem,assignments=len(rows),
                    parquet_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                    metadata_sha256=hashlib.sha256(file.with_suffix('.json').read_bytes()).hexdigest(),
                    old_normalized_threshold_disagreements=0,old_normalized_tail_disagreements=0,
                    old_normalized_threshold_assignment_disagreements=0,old_normalized_tail_assignment_disagreements=0)
        for row in rows.itertuples():
            z=assignment(g,np.random.default_rng(int(row.assignment_seed)),row.design,row.p)
            k=np.asarray(g.adjacency@z).ravel().astype(np.int64)
            k=np.where(d==0,z.astype(np.int64),k)
            threshold=4*k>=3*denominator;tail=20*k>17*denominator
            assert int(threshold.sum())==row.threshold_active,(file,row.replicate,'threshold')
            assert int(tail.sum())==row.tail_active,(file,row.replicate,'tail')
            exact=k/denominator
            assert row.exposure_max==float(exact.max()) and row.exposure_min==float(exact.min())
            old=np.asarray(g.transition@z).ravel()
            nstep=int(np.count_nonzero((old>=.75)!=threshold));ntail=int(np.count_nonzero((old>.85)!=tail))
            record['old_normalized_threshold_disagreements']+=nstep
            record['old_normalized_tail_disagreements']+=ntail
            record['old_normalized_threshold_assignment_disagreements']+=int(nstep>0)
            record['old_normalized_tail_assignment_disagreements']+=int(ntail>0)
        records.append(record);total+=len(rows)
    print(f'HUTIAN_WAKE: exact rational boundary audit completed {stage}',flush=True)
if not a.partial:assert len(records)==102 and total==40800
report=dict(status='partial passed' if a.partial else 'passed',cells=len(records),assignment_replays=total,model_refits=0,
            script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            method='Integer inequalities4k>=3d and20k>17d with isolate self-treatment convention; check stored maxima and support counts for every saved assignment.',
            cells_checked=records)
(notes/('checkpoint_boundary_audit.json' if a.partial else 'boundary_audit.json')).write_text(json.dumps(report,indent=2))
print(f'HUTIAN_WAKE: rational-boundary checks passed assignments={total} complete={not a.partial}',flush=True)
