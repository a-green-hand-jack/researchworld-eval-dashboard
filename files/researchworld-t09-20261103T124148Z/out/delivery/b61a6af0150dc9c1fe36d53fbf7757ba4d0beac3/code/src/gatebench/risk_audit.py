"""Time exact HT tail-risk evaluation independently of Monte Carlo production."""
import json
from pathlib import Path
import resource
import sys
import time
from .run import build_graph
from .core import noise_operator
from .ht_risk import exact_ht_risk

config=json.loads(Path(sys.argv[1]).read_text())
output=Path(sys.argv[2]); output.parent.mkdir(parents=True,exist_ok=True)
rows=[]
for spec in config['graphs']:
    graph=build_graph(spec,config.get('data_dir','data'))
    for design in config.get('designs',['bernoulli','cluster']):
        start=time.perf_counter();cpu=time.process_time()
        row=dict(graph=graph.name,design=design,
                 **exact_ht_risk(graph,design,.5,noise_operator(graph,0.),'linear',gamma=1.))
        row.update(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,
                   peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        rows.append(row)
        output.write_text(json.dumps(rows,indent=2))
        print('HUTIAN_WAKE: exact HT risk '+json.dumps(row),flush=True)
