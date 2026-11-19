"""Score every (prompt config, question) pair with a local LLM and cache the letter log-scores.

Usage: python code/score.py --model Qwen2.5-0.5B-Instruct --K 32 --N 2000 [--quant int8] [--threads 4]
Output: results/raw/<tag>/cfg{k}.npy  (N x 10 float32 letter log-probs, -inf for absent options)
        results/raw/<tag>/meta.json   (pool question ids, answers, config list)
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, torch
sys.path.insert(0, os.path.dirname(__file__))
import prompts
from transformers import AutoTokenizer, AutoModelForCausalLM

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--K", type=int, default=32)
ap.add_argument("--N", type=int, default=2000); ap.add_argument("--quant", default="int8")
ap.add_argument("--threads", type=int, default=4); ap.add_argument("--bs", type=int, default=16)
ap.add_argument("--maxtok", type=int, default=300, help="pool keeps questions whose zero-shot prompt <= maxtok tokens")
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--check", type=int, default=0)
ap.add_argument("--skip", type=int, default=0); ap.add_argument("--suffix", default="")
a = ap.parse_args()
torch.set_num_threads(a.threads)
tag = f"{a.model}_{a.quant}{a.suffix}"
out = f"results/raw/{tag}"; os.makedirs(out, exist_ok=True)
tok = AutoTokenizer.from_pretrained(f"data/models/{a.model}"); tok.padding_side = "left"

test = pd.read_parquet("data/mmlu_pro/data/test-00000-of-00001.parquet")
val = pd.read_parquet("data/mmlu_pro/data/validation-00000-of-00001.parquet")
# ---- pool: random questions with short-enough zero-shot prompts (fixed seed, model-independent) ----
base_cfg = dict(system=0, instr=1, opt=0, cue=0, ndemo=0, demo_ids=[])
rng = np.random.RandomState(a.seed)
perm = rng.permutation(len(test))
pool_idx = []; n_qual = 0
for i in perm:
    r = test.iloc[i].to_dict()
    n = len(tok(prompts.build_prompt(base_cfg, r, [], tok)).input_ids)
    if n <= a.maxtok:
        n_qual += 1
        if n_qual > a.skip: pool_idx.append(int(i))   # --skip: ignore the first `skip` qualifying questions (used to build a disjoint 'fresh' pool)
    if len(pool_idx) == a.N: break
pool = test.iloc[pool_idx].reset_index(drop=True)
# demo pool = the 25 shortest validation questions (so 1-shot configs stay cheap)
vlen = [len(tok(v["question"] + " ".join(v["options"])).input_ids) for v in val.to_dict("records")]
demo_pool = list(np.argsort(vlen)[:25])
cfgs = prompts.sample_configs(a.K, seed=a.seed, n_demo_pool=25)
for c in cfgs: c["demo_ids"] = [int(demo_pool[j]) for j in c["demo_ids"]]
meta = dict(model=a.model, quant=a.quant, N=a.N, K=a.K, seed=a.seed, maxtok=a.maxtok,
            question_id=[int(x) for x in pool.question_id], answer_index=[int(x) for x in pool.answer_index],
            category=list(pool.category), n_opts=[len(o) for o in pool.options], configs=cfgs)
json.dump(meta, open(f"{out}/meta.json", "w"))

m = AutoModelForCausalLM.from_pretrained(f"data/models/{a.model}", dtype=torch.float32).eval()
if a.quant == "int8":
    m = torch.ao.quantization.quantize_dynamic(m, {torch.nn.Linear}, dtype=torch.qint8)
ids_plain = [tok.encode(L, add_special_tokens=False)[0] for L in prompts.LETTERS]
ids_space = [tok.encode(" " + L, add_special_tokens=False)[0] for L in prompts.LETTERS]
recs = pool.to_dict("records")
nopt = np.array(meta["n_opts"])
mask = np.arange(10)[None, :] < nopt[:, None]

def run_cfg(cfg, qs):
    demos = [dict(val.iloc[j].to_dict()) for j in cfg["demo_ids"]]
    texts = [prompts.build_prompt(cfg, r, demos, tok) for r in qs]
    lens = np.array([len(tok(t).input_ids) for t in texts]); order = np.argsort(lens)
    res = np.full((len(qs), 10), -np.inf, dtype=np.float32)
    with torch.no_grad():
        for i in range(0, len(texts), a.bs):
            idx = order[i:i + a.bs]
            enc = tok([texts[j] for j in idx], return_tensors="pt", padding=True)
            lg = torch.log_softmax(m(**enc, logits_to_keep=1).logits[:, -1, :].float(), -1)
            s = torch.logaddexp(lg[:, ids_plain], lg[:, ids_space]).numpy()
            for b, j in enumerate(idx):
                res[j, :len(qs[j]["options"])] = s[b, :len(qs[j]["options"])]
    return res, lens.mean()

if a.check:
    qs = recs[:a.check]; t0 = time.time()
    for k in range(3):
        res, ml = run_cfg(cfgs[k], qs)
        acc = (res.argmax(1) == np.array(meta["answer_index"][:a.check])).mean()
        print(tag, "cfg", k, cfgs[k], "acc", acc, "meanlen", ml, f"{(time.time()-t0):.1f}s", flush=True)
    sys.exit()
for k, cfg in enumerate(cfgs):
    f = f"{out}/cfg{k}.npy"
    if os.path.exists(f): continue
    t0 = time.time(); res, ml = run_cfg(cfg, recs)
    np.save(f + ".tmp.npy", res); os.replace(f + ".tmp.npy", f)
    acc = (res.argmax(1) == np.array(meta["answer_index"])).mean()
    print(f"[{tag}] cfg {k}/{len(cfgs)} acc={acc:.4f} meanlen={ml:.0f} time={time.time()-t0:.0f}s", flush=True)
