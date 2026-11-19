"""Hyper-parameter selection on 4 DEV benchmarks (arc_challenge, musr, commonsense, med_qa), dev seed offset 1e7.
These benchmarks are excluded from the headline test aggregates. Grid: latent dim x prior-covariance scale."""
import subprocess, itertools, sys
DEV = "arc_challenge,musr,commonsense,med_qa"
for d, s in itertools.product([1, 2, 3, 5], [1, 10, 100]):
    out = f"results/dev/d{d}_s{s}"
    cmd = ["python3", "code/run_experiments.py", "--out", out, "--reps", "5", "--dim", str(d), "--scale", str(s),
           "--benchmarks", DEV, "--scen", "random,top,bottom", "--seed-offset", "10000000", "--procs", "36"]
    print(" ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout[-300:], r.stderr[-500:], flush=True)
