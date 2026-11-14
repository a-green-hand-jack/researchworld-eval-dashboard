import sys, time
sys.path.insert(0, "code")
import run_experiments as R
t = time.time()
for b in ["math", "ifeval"]:
    for sc in ["random", "top"]:
        print(R.run_task((b, sc, 0, 1, "results/smoke2", 5, [10, 50, 200], 1.0, 2, 100.0)), flush=True)
