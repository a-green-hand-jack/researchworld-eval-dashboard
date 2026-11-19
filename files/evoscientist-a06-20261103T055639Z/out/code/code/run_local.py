"""Local open-weight model (CPU): score all prompt configs by next-token logits restricted to letters A-J.
Usage: python code/run_local.py MODEL_ID NQ [threads] [batch]
Resumable; writes cache/local_<name>.npy-like jsonl lines {c,q,pred,lp}.
Chat template applied to the same user prompt as the API runs; the assistant turn is primed empty, and the
argmax over the 10 letter tokens is taken (no format failures are possible here).
"""
import sys, json, os, time
import numpy as np, torch
sys.path.insert(0, "code")
from configs import *
from transformers import AutoTokenizer, AutoModelForCausalLM

mid = sys.argv[1]; nq = int(sys.argv[2]); nthr = int(sys.argv[3]) if len(sys.argv) > 3 else 20
bs = int(sys.argv[4]) if len(sys.argv) > 4 else 8
torch.set_num_threads(nthr)
name = mid.split("/")[-1]
out = f"cache/local_{name}.jsonl"
tok = AutoTokenizer.from_pretrained(mid); tok.padding_side = "left"
model = AutoModelForCausalLM.from_pretrained(mid, torch_dtype=torch.float32).eval()
letter_ids = [tok.encode(l, add_special_tokens=False)[0] for l in L]
letter_ids_sp = [tok.encode(" " + l, add_special_tokens=False)[0] for l in L]
U = universe(nq)
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l); done.add((r["c"], r["q"]))
jobs = [(c, q) for q in range(nq) for c in range(len(CONFIGS)) if (c, q) not in done]
print("jobs", len(jobs), flush=True)
# sort chunks by q so that batches share length roughly
fh = open(out, "a"); t0 = time.time(); n = 0
for i in range(0, len(jobs), bs):
    B = jobs[i:i + bs]
    texts = [tok.apply_chat_template([{"role": "user", "content": build_prompt(CONFIGS[c], U.iloc[q])}],
                                     tokenize=False, add_generation_prompt=True) for c, q in B]
    enc = tok(texts, return_tensors="pt", padding=True)
    with torch.no_grad():
        lg = model(**enc).logits[:, -1, :].float()
    lp = torch.log_softmax(lg, -1)
    s = torch.logsumexp(torch.stack([lp[:, letter_ids], lp[:, letter_ids_sp]], 0), 0)  # (B,10)
    for (c, q), row in zip(B, s):
        fh.write(json.dumps({"c": c, "q": q, "pred": int(row.argmax()), "lp": [round(float(x), 3) for x in row]}) + "\n")
    fh.flush(); n += len(B)
    if (i // bs) % 25 == 0:
        print(f"{n}/{len(jobs)} {time.time()-t0:.0f}s", flush=True)
