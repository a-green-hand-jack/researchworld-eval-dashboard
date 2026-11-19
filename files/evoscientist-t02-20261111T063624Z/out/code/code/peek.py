import json, sys
rs = [json.loads(l) for l in open(f"/work/results/{sys.argv[1]}.jsonl")]
r = rs[int(sys.argv[2]) if len(sys.argv) > 2 else 0]
print({k: v for k, v in r.items() if k != "curve"})
print(r["curve"][-4:] if "curve" in r else None)
