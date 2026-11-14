"""Sum wall-clock seconds of LLM scoring from the logs (used for the compute statement in the paper)."""
import re, glob
tot = {}
for f in sorted(glob.glob("results/score_*.log")):
    s = open(f, errors="ignore").read()
    t = [int(x) for x in re.findall(r"time=(\d+)s", s)]
    tot[f] = (len(t), sum(t) / 3600)
    print(f, "configs", len(t), "wall-hours %.2f" % (sum(t) / 3600))
print("total wall-hours (LLM scoring, 4 threads each, shared 40-core CPU):", round(sum(v[1] for v in tot.values()), 2))
