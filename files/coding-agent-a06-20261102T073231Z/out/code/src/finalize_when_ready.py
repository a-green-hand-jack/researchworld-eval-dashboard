"""Run the downstream pipeline when the frozen response matrix is complete."""
import json, os, pathlib, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    while True:
        p=ROOT/'data/responses.jsonl'
        n=sum(1 for _ in p.open()) if p.exists() else 0
        if n==2048*24:break
        if n>2048*24:raise RuntimeError('Unexpected extra responses')
        time.sleep(30)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1')
    with (ROOT/'logs/finalize.log').open('w') as log:
        pid=(ROOT/'logs/server.pid').read_text().strip()
        for args in [[sys.executable,'src/capture_compute.py','--pid',pid],
                     [sys.executable,'src/analyze.py','--mode','all'],
                     [sys.executable,'src/render.py'],['bash','src/build_paper.sh']]:
            start=time.time();subprocess.run(args,cwd=ROOT,env=env,stdout=log,stderr=log,check=True)
            print(json.dumps(dict(command=args,elapsed_seconds=time.time()-start)),file=log,flush=True)
    (ROOT/'logs/pipeline_complete.json').write_text(json.dumps(dict(completed_unix=time.time())))
if __name__=='__main__':main()
