"""Local open-weight LLM scoring of many suffix-variant prompt configs with a shared question KV cache.

Prompt = chat_template(user = "Question: ...\nA. ...\n...J. ...\n" + SUFFIX_INSTR) + assistant cue.
Question tokens are encoded once per question; each config only re-encodes its (short) suffix.
Prediction = argmax of the 10 option-letter logits.

Usage: python local_run.py MODEL N NSHARDS SHARD [KCFG]
Writes cache/local_<MODEL>_s<SHARD>.npz  (correct [K,n], logp [K,n,10], pool positions)
"""
import os, sys, time, json, random
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, pandas as pd, torch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = BASE + "/data/mmlu-pro/data"
LET = "ABCDEFGHIJ"

SUF_INSTR = [
    "",
    "Choose the correct answer.",
    "You are an expert. Answer the multiple-choice question above.",
    "Read the question carefully and select the single best option.",
    "You are a university professor grading an exam. Select the right option.",
    "This is a hard exam question with ten options and exactly one correct answer.",
    "Be careful: several options look plausible, but only one is fully correct.",
    "Do not overthink. Trust your first well-informed judgment.",
    "Eliminate the clearly wrong options, then pick the best remaining one.",
    "Respond with only the letter of the correct option.",
]
CUES = ["Answer:", "The answer is (", "Correct option:", "Final answer: ("]


def local_configs(K, seed=0):
    rng = random.Random(seed)
    grid = [(i, c) for i in range(len(SUF_INSTR)) for c in range(len(CUES))]
    rng.shuffle(grid)
    grid = [g for g in grid if g != (0, 0)]
    sel = [(0, 0)] + grid[: K - 1]
    return [dict(id=k, ins=i, cue=c) for k, (i, c) in enumerate(sel)]


def pool_indices(N, seed=0):
    return np.random.RandomState(seed).permutation(12032)[:N]


def question_text(row):
    opts = "\n".join(f"{LET[i]}. {o}" for i, o in enumerate(row["options"]))
    return "Question: " + row["question"].strip() + "\n" + opts + "\n"


def letter_ids(tok, cue):
    base = tok(cue, add_special_tokens=False)["input_ids"]
    ids = []
    for L in LET:
        sp = "" if cue.endswith("(") else " "
        full = tok(cue + sp + L, add_special_tokens=False)["input_ids"]
        assert full[: len(base)] == base, (cue, L)
        ids.append(full[-1])
    return ids


def main():
    model_name, N, nsh, sh = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    K = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    bs = int(os.environ.get("BS", 8))
    torch.set_num_threads(1)
    from transformers import AutoTokenizer, AutoModelForCausalLM, DynamicCache
    tok = AutoTokenizer.from_pretrained(f"{BASE}/data/{model_name}")
    model = AutoModelForCausalLM.from_pretrained(f"{BASE}/data/{model_name}", dtype=torch.float32).eval()
    test = pd.read_parquet(f"{DATA}/test-00000-of-00001.parquet")
    pool = pool_indices(N)
    my = np.arange(N)[sh::nsh]
    cfgs = local_configs(K)
    # suffix token ids (per config): instruction (in user turn) + end-of-user + assistant cue
    # We split the chat string at the question boundary so the question prefix is shared.
    dummy = tok.apply_chat_template([{"role": "user", "content": "XXQXX"}], tokenize=False, add_generation_prompt=True)
    pre, post = dummy.split("XXQXX")
    pre_ids = tok(pre, add_special_tokens=False)["input_ids"]
    suff, lids = [], []
    for c in cfgs:
        s = (SUF_INSTR[c["ins"]] if SUF_INSTR[c["ins"]] else "").rstrip() + post + CUES[c["cue"]]
        s = ("\n" if False else "") + s
        suff.append(torch.tensor(tok(s, add_special_tokens=False)["input_ids"]))
        lids.append(torch.tensor(letter_ids(tok, CUES[c["cue"]])))
    qtext = [question_text(test.iloc[int(pool[j])]) for j in my]
    qenc = [pre_ids + tok(t.rstrip("\n") if False else t, add_special_tokens=False)["input_ids"][-1500:] for t in qtext]
    order = np.argsort([len(e) for e in qenc])
    gold = np.array([test.iloc[int(pool[j])]["answer_index"] for j in my])
    correct = np.zeros((K, len(my)), np.int8); logp = np.zeros((K, len(my), 10), np.float16)
    pad = tok.pad_token_id or 0
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, len(order), bs):
            b = order[s: s + bs]; B = len(b); Lq = max(len(qenc[i]) for i in b)
            ids = torch.full((B, Lq), pad); att = torch.zeros((B, Lq), dtype=torch.long)
            for r, i in enumerate(b):
                ids[r, Lq - len(qenc[i]):] = torch.tensor(qenc[i]); att[r, Lq - len(qenc[i]):] = 1
            pos = (att.cumsum(1) - 1).clamp(min=0)
            cache = DynamicCache()
            model(input_ids=ids, attention_mask=att, position_ids=pos, past_key_values=cache, use_cache=True, logits_to_keep=1)
            nreal = att.sum(1, keepdim=True)
            for k in range(K):
                S = suff[k].shape[0]
                sid = suff[k].unsqueeze(0).expand(B, S)
                a2 = torch.cat([att, torch.ones((B, S), dtype=torch.long)], 1)
                p2 = nreal + torch.arange(S).unsqueeze(0)
                out = model(input_ids=sid, attention_mask=a2, position_ids=p2, past_key_values=cache, use_cache=True, logits_to_keep=1).logits[:, -1, :]
                cache.crop(-S)
                lg = out[:, lids[k]].float()
                lp = torch.log_softmax(lg, -1)
                pr = lg.argmax(-1).numpy()
                correct[k, b] = (pr == gold[b]); logp[k, b] = lp.numpy().astype(np.float16)
            if (s // bs) % 5 == 0:
                print(f"shard {sh}: {s + B}/{len(my)} q, {time.time() - t0:.0f}s, acc cfg0 so far {correct[0, order[:s + B]].mean():.3f}", flush=True)
    out = f"{BASE}/cache/local_{model_name}_s{sh}.npz"
    np.savez(out, correct=correct, logp=logp, qpos=my, cfgs=json.dumps(cfgs))
    print("saved", out, time.time() - t0)


if __name__ == "__main__":
    main()
