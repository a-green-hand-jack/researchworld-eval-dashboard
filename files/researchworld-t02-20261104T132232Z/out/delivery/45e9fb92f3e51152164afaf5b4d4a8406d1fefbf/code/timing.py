"""CPU time per training step (single thread, process time, not wall time) for each model/width/depth at p=59, f=0.5.
python3 timing.py OUT.csv [steps]   Runs grok.run for `steps` (default 300) steps with the normal evaluation schedule (eval_every 50) and divides
process_time by steps; the first 20 steps are a warm-up in a separate run. Used for the 'dedicated CPU' estimates in REPRODUCE.md."""
import csv, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grok
steps = int(sys.argv[2]) if len(sys.argv) > 2 else 300
rows = []
for model, depth, widths in [("mlp", 1, [16, 32, 64, 128, 256]), ("tfm", 1, [16, 32, 64, 128, 256]), ("mlp", 2, [16, 128]), ("tfm", 2, [16, 64])]:
    for w in widths:
        cfg = {**grok.DEFAULT, "model": model, "depth": depth, "width": w, "train_frac": 0.5, "p": 59, "seed": 0, "max_steps": steps, "eval_every": 50, "stop_val": 2.0}
        grok.run({**cfg, "max_steps": 20}); t0 = time.process_time(); w0 = time.time(); grok.run(cfg)
        rows.append(dict(model=model, depth=depth, width=w, cpu_ms_per_step=1000 * (time.process_time() - t0) / steps, wall_ms_per_step=1000 * (time.time() - w0) / steps))
        print(rows[-1], flush=True)
with open(sys.argv[1], "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
