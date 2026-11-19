"""Download latest results_*.json per model from open-llm-leaderboard/results @ aa81ecc (pinned).
usage: python3 -I fetch_olmb_results.py OUTDIR"""
import sys, json, os, re, urllib.request, urllib.parse, concurrent.futures as cf, time
out = sys.argv[1]
SHA = "aa81ecc38fdc5708254b833923368970efdf5ef5"
meta = json.load(urllib.request.urlopen(f"https://huggingface.co/api/datasets/open-llm-leaderboard/results/revision/{SHA}"))
files = [s["rfilename"] for s in meta["siblings"] if s["rfilename"].endswith(".json") and "/results_" in s["rfilename"]]
print("result files", len(files))
by = {}
for f in files:
    model, name = f.rsplit("/", 1)
    ts = name[len("results_"):-5]
    if model not in by or ts > by[model][0]: by[model] = (ts, f)
print("models", len(by))
json.dump({m: v[1] for m, v in by.items()}, open(os.path.join(out, "_selected_files.json"), "w"), indent=0)
def get(item):
    m, (ts, f) = item
    dst = os.path.join(out, f.replace("/", "__"))
    if os.path.exists(dst) and os.path.getsize(dst) > 0: return 0
    url = f"https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/{SHA}/" + urllib.parse.quote(f)
    for k in range(4):
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
            open(dst, "wb").write(data); return 0
        except Exception as e:
            time.sleep(1 + k)
    return 1
t = time.time(); fails = 0
with cf.ThreadPoolExecutor(16) as ex:
    for i, r in enumerate(ex.map(get, by.items())):
        fails += r
        if i % 500 == 0: print(i, fails, round(time.time() - t), flush=True)
print("done fails", fails)
