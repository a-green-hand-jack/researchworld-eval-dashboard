"""Run checkpointed cells. Usage: PYTHONPATH=src python -m gatebench.run CONFIG."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import time
import numpy as np
import pandas as pd
from .core import (assignment, outcome_mean, true_gate, noise_operator, exposure,
                   contrast_weights, features, regression, exposure_probabilities,
                   full_exposure_estimates)
from .graphs import synthetic, public_facebook, graph_summary

SOURCE_HASHES={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
               for name in ["core.py","graphs.py","run.py"]}


def seed_for(master, namespace, *parts):
    digest = hashlib.sha256(json.dumps([master,namespace,*parts],sort_keys=True).encode()).digest()
    return int.from_bytes(digest[:8],"little")


def build_graph(spec, data_dir):
    data_dir=os.environ.get("GATEBENCH_DATA_DIR",data_dir)
    if spec["kind"] == "facebook":
        return public_facebook(Path(data_dir)/"facebook_combined.txt.gz",spec.get("seed",1),spec.get("cluster_size",32))
    return synthetic(spec["kind"],spec["n"],spec["degree"],spec.get("seed",1),spec.get("cluster_size",32),spec.get("mixing",.15))


def run_cell(config, spec, design, probability, rho, gamma, output):
    start=time.perf_counter()
    cpu_start=time.process_time()
    g=build_graph(spec,config.get("data_dir","data"))
    b=noise_operator(g,rho)
    probabilities=exposure_probabilities(g,design,probability)
    summary=graph_summary(g)
    summary.update(graph_seed=spec.get("seed",1), cluster_size=spec.get("cluster_size",32))
    graph_key=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:16]
    cell_id=f"{graph_key}_{design}_p{probability}_rho{rho}_gamma{gamma}"
    file=output/f"{cell_id}.parquet"
    if file.exists():
        print(f"SKIP completed {cell_id}",flush=True)
        return
    rows=[]
    models=config["models"]
    for rep in range(config["replicates"]):
        # Assignment/noise streams are independent, shared across models/mechanisms.
        ass_seed=seed_for(config["master_seed"],"assignment",graph_key,design,probability,rep)
        noise_seed=seed_for(config["master_seed"],"noise",graph_key,design,probability,rep)
        prediction_seed=seed_for(config["master_seed"],"prediction",graph_key,design,probability,rep)
        z=assignment(g,np.random.default_rng(ass_seed),design,probability)
        eps=b@np.random.default_rng(noise_seed).normal(size=g.n)
        prediction_rng=np.random.default_rng(prediction_seed)
        z_test=assignment(g,prediction_rng,design,probability)
        eps_test=b@prediction_rng.normal(size=g.n)
        s,_=exposure(g,z)
        fitted={model:contrast_weights(g,z,model) for model in models}
        prediction_features={model:features(g,z_test,model) for model in models}
        common=dict(cell_id=cell_id,pairing_id=f"m{config['master_seed']}_{graph_key}_{design}_p{probability}_r{rep}",
                    graph=g.name,graph_kind=spec["kind"],graph_seed=spec.get("seed",1),master_seed=config["master_seed"],
                    n=g.n,degree_target=spec.get("degree",np.nan),
                    cluster_size=spec.get("cluster_size",32),mixing=spec.get("mixing",np.nan),design=design,p=probability,
                    rho=rho,gamma=gamma,replicate=rep,assignment_seed=str(ass_seed),
                    noise_seed=str(noise_seed),prediction_seed=str(prediction_seed),
                    assignment_units=g.n if design=="bernoulli" else int(g.clusters.max()+1),
                    treated=int(z.sum()), exposure_min=float(s.min()),exposure_max=float(s.max()),
                    exposure_sd=float(s.std()),exposure_q05=float(np.quantile(s,.05)),
                    exposure_q95=float(np.quantile(s,.95)),threshold_active=int(np.sum(s>=.75)),tail_active=int(np.sum(s>.85)),
                    near_zero=int(np.sum(s<=.1)),near_one=int(np.sum(s>=.9)),
                    expected_full_treated=float(probabilities[0].sum()),
                    expected_full_control=float(probabilities[1].sum()),
                    min_full_probability=float(min(probabilities[0].min(),probabilities[1].min())))
        for mechanism in config["mechanisms"]:
            mean=outcome_mean(g,z,mechanism,gamma=gamma)
            truth=true_gate(g,mechanism,gamma=gamma)
            y=mean+eps
            test_mean=outcome_mean(g,z_test,mechanism,gamma=gamma)
            y_test=test_mean+eps_test
            for model in models:
                fit=fitted[model]
                vals=regression(g,z,y,mean,truth,b,model,prepared=fit)
                beta=fit[2]@y
                prediction=prediction_features[model]@beta
                if model=="naive" and (z.sum()==0 or z.sum()==g.n):
                    vals.update(estimate=np.nan,error=np.nan,valid=False,cover_hc3=np.nan,cover_oracle=np.nan,
                                failure_reason="empty_arm")
                else:
                    vals["failure_reason"]="" if vals["valid"] else "nonestimable_contrast"
                vals["prediction_mse"]=float(np.mean((prediction-y_test)**2))
                vals["prediction_mean_mse"]=float(np.mean((prediction-test_mean)**2))
                if model=="naive" and not vals["valid"]:
                    vals["prediction_mse"]=np.nan
                    vals["prediction_mean_mse"]=np.nan
                rows.append(dict(**common,mechanism=mechanism,truth=truth,model=model,**vals))
            ht=full_exposure_estimates(g,z,y,probabilities)
            for name in ("ht","hajek"):
                estimate=ht[name]
                rows.append(dict(**common,mechanism=mechanism,truth=truth,model=name,
                                 estimate=estimate,error=estimate-truth,valid=bool(np.isfinite(estimate)),
                                 full_treated=ht["full_treated"],full_control=ht["full_control"]))
        if (rep+1)%max(1,config["replicates"]//4)==0:
            print(f"PROGRESS {cell_id} {rep+1}/{config['replicates']} wall={time.perf_counter()-start:.2f}s",flush=True)
    current_hashes={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                    for name in SOURCE_HASHES}
    if current_hashes!=SOURCE_HASHES:
        raise RuntimeError("Simulation source changed during execution; refusing mixed-source checkpoint")
    frame=pd.DataFrame(rows)
    tmp=file.with_suffix(".tmp.parquet")
    frame.to_parquet(tmp,index=False)
    os.replace(tmp,file)
    meta=dict(cell_id=cell_id,graph=summary,rows=len(rows),replicates=config["replicates"],
              source_sha256=SOURCE_HASHES,
              config_sha256=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
              wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu_start,
              peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    file.with_suffix(".json").write_text(json.dumps(meta,indent=2))
    print("Completed "+json.dumps(meta),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("config")
    args=parser.parse_args()
    config=json.loads(Path(args.config).read_text())
    output=Path(config["output"])
    output.mkdir(parents=True,exist_ok=True)
    frozen=output/"config.json"
    if frozen.exists() and json.loads(frozen.read_text())!=config:
        raise ValueError("Refusing to mix different configurations in one output directory")
    frozen.write_text(json.dumps(config,indent=2,sort_keys=True))
    completed=0
    for spec in config["graphs"]:
        for design in config.get("designs",["bernoulli","cluster"]):
            for p in config.get("probabilities",[.5]):
                for rho in config.get("rhos",[0.]):
                    for gamma in config.get("gammas",[1.]):
                        run_cell(config,spec,design,p,rho,gamma,output)
                        completed+=1
                        if completed%10==0:
                            print(f"HUTIAN_WAKE: {completed} cells checkpointed in {output}",flush=True)
    print(f"HUTIAN_WAKE: simulation complete {output}",flush=True)

if __name__=="__main__":
    main()
