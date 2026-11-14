import json, os, numpy as np
H = os.path.dirname(os.path.abspath(__file__))
for name in ("e12_tf128_long", "e5_tf"):
    for l in open(os.path.join(H, "..", "results", name + ".jsonl")):
        r = json.loads(l)
        if r["cfg"]["width"] not in (64, 128):
            continue
        cv = np.array(r["curve"])
        va = cv[:, 3]
        i = int(np.argmax(va))
        print(name, "w", r["cfg"]["width"], "seed", r["cfg"]["seed"], "t_val", r["t_val"], "max val acc %.4f at step %d" % (va[i], cv[i, 0]),
              "final val acc %.4f" % va[-1], "val acc @20k/40k/60k/80k:",
              [round(float(va[np.searchsorted(cv[:, 0], s)]), 3) for s in (20000, 40000, 60000, 80000) if s <= cv[-1, 0]])
