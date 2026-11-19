"""Exact rare-exposure risk checkpoints for the frozen production cells."""
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
from .run import build_graph
from .core import noise_operator
from .ht_risk import exact_ht_risk

config=json.loads(Path(sys.argv[1]).read_text())
output=Path(config['output'])/'exact_ht'
output.mkdir(parents=True,exist_ok=True)
for spec in config['graphs']:
    graph_key=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:16]
    for design in config.get('designs',['bernoulli','cluster']):
        for p in config.get('probabilities',[.5]):
            for rho in config.get('rhos',[0.]):
                for gamma in config.get('gammas',[1.]):
                    cell_id=f'{graph_key}_{design}_p{p}_rho{rho}_gamma{gamma}'
                    file=output/f'{cell_id}.json'
                    if file.exists():
                        continue
                    graph=build_graph(spec,config.get('data_dir','data'))
                    noise_map=noise_operator(graph,rho)
                    rows=[]
                    for mechanism in ['no_interference','linear','hidden_tail']:
                        start=time.perf_counter();cpu=time.process_time()
                        risk=exact_ht_risk(graph,design,p,noise_map,mechanism,gamma=gamma)
                        rows.append(dict(cell_id=cell_id,graph=graph.name,design=design,p=p,rho=rho,gamma=gamma,
                                         endpoint_family=mechanism,**risk,
                                         wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,
                                         peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
                    temp=file.with_suffix('.tmp')
                    temp.write_text(json.dumps(rows,indent=2));temp.replace(file)
                    print('Exact HT risk completed '+cell_id,flush=True)
print('HUTIAN_WAKE: exact HT risk complete '+config['output'],flush=True)
