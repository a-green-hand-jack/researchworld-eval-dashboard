"""Rerun unchanged cells with corrected count-then-divide exposure boundaries.

Independent shards own disjoint cells; each uses the original complete config
for hashing and seed generation. There is no partial-config or seed amendment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import time
from gatebench.run import run_cell, build_graph
from gatebench.core import noise_operator
from gatebench.ht_risk import exact_ht_risk

p=argparse.ArgumentParser();p.add_argument('--workspace',required=True)
p.add_argument('--shard',type=int,required=True);p.add_argument('--shards',type=int,default=3)
a=p.parse_args();assert 0<=a.shard<a.shards
code=Path(__file__).resolve().parents[1];workspace=Path(a.workspace).resolve()
workspace.mkdir(exist_ok=True,parents=True)
os.environ['GATEBENCH_DATA_DIR']=str(code/'data')
source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
started=time.time();global_index=0;done=[]
for stage in ['core','noise','imbalance']:
    config_file=code/f'configs/production_{stage}.json'
    config=json.loads(config_file.read_text());output=workspace/config['output']
    output.mkdir(parents=True,exist_ok=True)
    # Every writer emits the same complete config bytes atomically to its own
    # temporary filename before replacing the common identical config file.
    temp=output/f'config.shard{a.shard}.tmp';temp.write_bytes(config_file.read_bytes());temp.replace(output/'config.json')
    for spec in config['graphs']:
        key=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:16]
        for design in config['designs']:
            for probability in config['probabilities']:
                for rho in config['rhos']:
                    for gamma in config['gammas']:
                        index=global_index;global_index+=1
                        if index%a.shards!=a.shard:continue
                        cell=f'{key}_{design}_p{probability}_rho{rho}_gamma{gamma}'
                        run_cell(config,spec,design,probability,rho,gamma,output)
                        exact=output/'exact_ht';exact.mkdir(exist_ok=True)
                        file=exact/(cell+'.json')
                        if not file.exists():
                            graph=build_graph(spec,config.get('data_dir','data'))
                            noise=noise_operator(graph,rho);rows=[]
                            for mechanism in ['no_interference','linear','hidden_tail']:
                                start=time.perf_counter();cpu=time.process_time()
                                risk=exact_ht_risk(graph,design,probability,noise,mechanism,gamma=gamma)
                                rows.append(dict(cell_id=cell,graph=graph.name,design=design,p=probability,rho=rho,gamma=gamma,
                                                 endpoint_family=mechanism,**risk,wall_seconds=time.perf_counter()-start,
                                                 cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
                            temp=file.with_suffix('.tmp');temp.write_text(json.dumps(rows,indent=2));temp.replace(file)
                        done.append(dict(panel=stage,cell_id=cell))
                        if len(done)%10==0:
                            print(f'HUTIAN_WAKE: corrected shard{a.shard} completed {len(done)} cells with exact HT',flush=True)
assert global_index==102 and len(done)==34
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
(workspace/f'shard{a.shard}_receipt.json').write_text(json.dumps(dict(status='completed',shard=a.shard,shards=a.shards,
    cells=done,source_sha256=source_hash,started_at=started,finished_at=time.time()),indent=2))
print(f'HUTIAN_WAKE: corrected shard{a.shard} all34cells and exactHT complete',flush=True)
