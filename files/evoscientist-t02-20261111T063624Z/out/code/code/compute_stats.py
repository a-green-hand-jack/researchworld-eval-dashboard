"""Count runs and summed per-run wall-clock seconds (measured on a shared CPU slice, ~4-5 effective cores for up to ~12 concurrent procs)."""
import glob, json, os
H = os.path.dirname(os.path.abspath(__file__))
tot_r = tot_s = 0
for f in sorted(glob.glob(os.path.join(H, "..", "results", "*.jsonl"))):
    seen, n, s = set(), 0, 0.0
    for l in open(f):
        r = json.loads(l)
        if r["key"] in seen:
            continue
        seen.add(r["key"]); n += 1; s += r["secs"]
    print(f"{os.path.basename(f):28s} runs={n:4d}  summed_run_wallclock_h={s/3600:6.2f}")
    tot_r += n; tot_s += s
print("TOTAL runs", tot_r, "summed wallclock h", round(tot_s / 3600, 1))
