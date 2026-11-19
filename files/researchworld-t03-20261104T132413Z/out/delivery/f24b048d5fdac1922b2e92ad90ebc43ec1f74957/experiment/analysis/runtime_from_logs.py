"""Wall-clock seconds per stage and cell, from the run logs.

usage: python3 analysis/runtime_from_logs.py [log_dir] [out_dir]
Each log line is '<stage> <index> <seconds since process start>'; a stage's duration is the last time stamp of the stage minus the last
time stamp of the previous line of the process (the time stamp restarts at 0 when a cell is resumed in a new process, so durations
are summed over processes).  Wall-clock on a shared, oversubscribed host, single thread per job; CPU time is only metered per job
(see REPRODUCE.md section 4).  Writes tables/runtime_cells.csv.
"""
import collections, glob, os, sys
import pandas as pd

logs = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "logs")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
rows = []
for f in sorted(glob.glob(f"{logs}/*.log")):
    cell = os.path.basename(f)[:-4]
    dur = collections.defaultdict(float); cur_last = 0.0
    for ln in open(f):
        t = ln.split()
        if len(t) == 3 and t[1].isdigit() and t[0] != "done":
            try:
                ts = float(t[2])
            except ValueError:
                continue
            dur[t[0]] += ts - cur_last if ts >= cur_last else ts      # a smaller stamp means the cell was resumed in a new process
            cur_last = ts
    tot = sum(dur.values())
    rows.append(dict(cell=cell, **{f"{s}_s": round(dur.get(s, 0.0), 1) for s in ("ref", "kernel", "perm", "retrain", "bg")}, total_s=round(tot, 1), total_h=round(tot / 3600, 2)))
pd.DataFrame(rows).to_csv(f"{out}/runtime_cells.csv", index=False)
print(len(rows), "logs")
