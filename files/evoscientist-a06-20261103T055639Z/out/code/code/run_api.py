"""Evaluate all 36 prompt configs on the question universe with an API model; cache raw replies (jsonl).
Usage: python code/run_api.py MODEL NQ [threads] [config_subset_csv]
Resumable: skips (cfg,qid) pairs already in the cache file.
"""
import sys, json, os, time, threading, warnings
import concurrent.futures as cf
import anthropic
sys.path.insert(0, "code")
from configs import *
warnings.filterwarnings("ignore")

model = sys.argv[1]; nq = int(sys.argv[2]); nthr = int(sys.argv[3]) if len(sys.argv) > 3 else 16
cfg_ids = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else list(range(len(CONFIGS)))
out = f"cache/api_{model}.jsonl"
U = universe(nq)
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l); done.add((r["c"], r["q"]))
client = anthropic.Anthropic(max_retries=3, timeout=60)
lock = threading.Lock(); fh = open(out, "a")
jobs = [(c, q) for q in range(nq) for c in cfg_ids if (c, q) not in done]
print("jobs", len(jobs), flush=True)
cnt = [0, 0]; t0 = time.time()


def work(job):
    c, q = job
    row = U.iloc[q]
    p = build_prompt(CONFIGS[c], row)
    for attempt in range(6):
        try:
            x = client.messages.create(model=model, max_tokens=12, messages=[{"role": "user", "content": p}],
                                       extra_body={"temperature": 0})
            txt = x.content[0].text if x.content and hasattr(x.content[0], "text") else ""
            if x.usage.output_tokens == 0 and x.usage.input_tokens == 0:  # gateway notice, not a model reply
                raise RuntimeError("notice:" + txt[:40])
            rec = {"c": c, "q": q, "t": txt, "it": x.usage.input_tokens, "ot": x.usage.output_tokens}
            break
        except Exception as e:
            err = str(e)[:80]
            time.sleep(2 + 3 * attempt)
    else:
        rec = {"c": c, "q": q, "t": None, "err": err}
    with lock:
        if rec["t"] is not None:
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            cnt[0] += 1
        else:
            cnt[1] += 1
        if (cnt[0] + cnt[1]) % 500 == 0:
            print(f"{cnt[0]} ok {cnt[1]} fail, {time.time()-t0:.0f}s", flush=True)


with cf.ThreadPoolExecutor(nthr) as ex:
    list(ex.map(work, jobs))
print("finished", cnt, time.time() - t0)
