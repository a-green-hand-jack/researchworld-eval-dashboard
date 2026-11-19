"""Resource-job entrypoint: sequential independent extension tasks, fail fast."""
import subprocess,sys
commands=[
 [sys.executable,'-u','analysis/benchmark.py','--output','results/weighted.jsonl','--reps','100','--start','1000','--dimensions','3','10','--calibration','99','499','--scenarios','homogeneous','heterogeneous','--ntest','5000','--nvolume','8192','--methods','clr_weighted'],
 [sys.executable,'-u','analysis/sensitivity.py','--mode','rank','--output','results/rank_checks.csv'],
 [sys.executable,'-u','analysis/sensitivity.py','--mode','boundary','--output','results/boundary.jsonl'],
]
for command in commands:
    subprocess.run(command,check=True)
print('HUTIAN_WAKE: all weighted/rank/boundary extension tasks complete',flush=True)
