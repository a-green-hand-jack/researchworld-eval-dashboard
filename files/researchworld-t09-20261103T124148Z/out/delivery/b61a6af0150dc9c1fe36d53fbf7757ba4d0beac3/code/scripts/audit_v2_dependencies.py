"""Establish graph-asset applicability and replacement of numerical authority."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--root',default='.')
a=p.parse_args();root=Path(a.root).resolve();code=root/'code' if (root/'code/configs').exists() else root
notes=root/('analysis' if code!=root else 'notes')
predecessor=notes/'roundoff_v1/graph_metadata.json'
previous=json.loads(predecessor.read_text());graphs=set();checked=[]
for stage in ['core','noise','imbalance']:
    for file in sorted((root/f'results/production_{stage}').glob('*.json')):
        if file.name=='config.json':continue
        current=json.loads(file.read_text());key=stage+'/'+file.name
        assert current['graph']==previous[key]['graph']
        assert current['config_sha256']==previous[key]['config_sha256']
        graphs.add(current['graph']['adjacency_sha256']);checked.append(key)
assert len(checked)==102 and len(graphs)==36
report=dict(status='passed',graph_config_metadata_cells=102,unique_graph_adjacency_hashes=36,
            predecessor_metadata_sha256=hashlib.sha256(predecessor.read_bytes()).hexdigest(),
            disposition='Graph inventory/adjacency/partition attributes identical: graph-only assets may retain content with revalidated provenance. All empirical output tables and endpoint exact risks are recomputed; prior numeric assets need corrected-source regeneration/revalidation. Selected clean replay is repeated.',
            checked=checked)
(notes/'v2_dependency_audit.json').write_text(json.dumps(report,indent=2))
print('HUTIAN_WAKE: graph-only dependencies validated against all102corrected metadata',flush=True)
