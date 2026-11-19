import json, sys, collections
name = sys.argv[1]
keys = sys.argv[2].split(",") if len(sys.argv) > 2 else ["width"]
rows = [json.loads(l) for l in open(f"/work/results/{name}.jsonl")]
g = collections.defaultdict(list)
for r in rows:
    g[tuple(r["cfg"][k] for k in keys)].append(r)
for k in sorted(g):
    rs = g[k]
    print(k, "np=%d" % rs[0]["n_params"],
          "tt=", [r["t_train"] for r in rs], "tv=", [r["t_val"] for r in rs],
          "secs=%d" % (sum(r["secs"] for r in rs) / len(rs)))
