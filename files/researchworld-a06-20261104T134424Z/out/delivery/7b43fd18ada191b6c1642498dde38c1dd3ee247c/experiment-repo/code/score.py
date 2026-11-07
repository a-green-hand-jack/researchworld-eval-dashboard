"""Score MMLU-Pro questions under prompt configurations with a causal LM (option-letter logits).
Each (config, question) -> logits over letters A..J, from ONE forward pass of the question suffix
on top of a cached prefix (instruction + demonstrations). Deterministic; outputs cached as npy."""
import sys, json, time, copy, argparse, numpy as np, pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from configs import build_prefix, format_question, displayed_to_original, LETTERS

def load_data(root):
    test = pd.read_parquet(f"{root}/data/test-00000-of-00001.parquet")
    val = pd.read_parquet(f"{root}/data/validation-00000-of-00001.parquet")
    return test, val

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model"); ap.add_argument("--data"); ap.add_argument("--qidx")  # npy of test row positions
    ap.add_argument("--configs")  # json list of config dicts
    ap.add_argument("--cfg_range", default=None); ap.add_argument("--out"); ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--maxtok", type=int, default=700)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float32).eval()
    test, val = load_data(a.data)
    qidx = np.load(a.qidx); cfgs = json.load(open(a.configs))
    lo, hi = (0, len(cfgs)) if a.cfg_range is None else map(int, a.cfg_range.split(":"))
    letter_ids = [tok.encode(" " + L, add_special_tokens=False)[-1] for L in LETTERS]
    letter_ids2 = [tok.encode(L, add_special_tokens=False)[-1] for L in LETTERS]
    out = np.full((hi - lo, len(qidx), 10), np.nan, dtype=np.float32)
    t0 = time.time()
    import os
    if os.path.exists(a.out): out[:] = np.load(a.out)   # resume
    for ci in range(lo, hi):
        if not np.isnan(out[ci - lo]).all(): continue
        cfg = cfgs[ci]
        prefix = build_prefix(cfg, val)
        pids = tok(prefix, return_tensors="pt").input_ids
        with torch.no_grad():
            pout = model(pids, use_cache=True)
        cache = pout.past_key_values; plen = pids.shape[1]
        for j, qi in enumerate(qidx):
            row = test.iloc[int(qi)]
            sfx = format_question(cfg, row)
            ids = tok(sfx, return_tensors="pt", add_special_tokens=False).input_ids[:, -a.maxtok:]
            with torch.no_grad():
                lg = model(ids, past_key_values=cache, use_cache=True).logits[0, -1].float()
            cache.crop(-(cache.get_seq_length() - plen))
            lp = torch.log_softmax(lg, -1)
            lpl = torch.logaddexp(lp[letter_ids], lp[letter_ids2]).numpy()
            n_opt = len(row["options"]); order = displayed_to_original(cfg, n_opt)
            v = np.full(10, -np.inf, dtype=np.float32)   # log-probs by ORIGINAL option index, -inf for absent options
            for jj, k in enumerate(order): v[k] = lpl[jj]
            out[ci - lo, j] = v
            if j % 200 == 199:
                print(f"cfg {ci} q {j+1}/{len(qidx)} elapsed {time.time()-t0:.0f}s", flush=True)
        np.save(a.out, out)
    print("done", time.time() - t0, flush=True)
main()
