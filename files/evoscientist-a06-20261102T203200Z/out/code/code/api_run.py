"""Evaluate K prompt configurations x N MMLU-Pro questions with an API LLM (direct-answer, max_tokens=8).
Resumable: results appended to cache/api_<model>.jsonl as {"c": cfg_id, "q": question_idx, "r": raw_text}.
Usage: python api_run.py MODEL K N CONC
"""
import anthropic, time, sys, os, json, random, re, threading
import numpy as np, pandas as pd, concurrent.futures as cf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = BASE + "/data/mmlu-pro/data"
L = "ABCDEFGHIJ"

INSTRS = [
    "",
    "The following is a multiple choice question. Choose the correct answer.",
    "You are an expert. Answer the following multiple-choice question.",
    "Read the question carefully and select the single best option.",
    "You are a university professor grading an exam. Select the right option.",
    "This is a hard exam question with ten options and exactly one correct answer.",
    "Be careful: several options look plausible, but only one is fully correct.",
    "Do not overthink. Trust your first well-informed judgment.",
]
FMTS = ["{L}.", "({L})", "{L})"]
ENDS = [  # final line telling the model how to answer
    "Respond with only the letter of the correct option.",
    "Answer with the option letter only.",
    "Output just the letter (A-J) and nothing else.",
    "The answer is: (give only the letter)",
]
HEADERS = ["Question:", "Q:", ""]
SHOTS = [0, 1, 3, 5]


def load():
    test = pd.read_parquet(f"{DATA}/test-00000-of-00001.parquet")
    val = pd.read_parquet(f"{DATA}/validation-00000-of-00001.parquet")
    return test, val


def sample_configs(K, seed=0):
    rng = random.Random(seed)
    cfgs = [dict(ins=0, fmt=0, end=0, hdr=0, shots=0, dseed=0)]  # config 0 = plain untuned default
    seen = {tuple(cfgs[0].values())}
    while len(cfgs) < K:
        sh = rng.choice(SHOTS)
        c = dict(ins=rng.randrange(len(INSTRS)), fmt=rng.randrange(3), end=rng.randrange(len(ENDS)),
                 hdr=rng.randrange(3), shots=sh, dseed=rng.randrange(8) if sh else 0)
        if tuple(c.values()) in seen: continue
        seen.add(tuple(c.values())); cfgs.append(c)
    for i, c in enumerate(cfgs): c["id"] = i
    return cfgs


def fmt_q(row, cfg):
    h = HEADERS[cfg["hdr"]]
    opts = "\n".join(f"{FMTS[cfg['fmt']].format(L=L[i])} {o}" for i, o in enumerate(row["options"]))
    return (h + " " if h else "") + row["question"].strip() + "\n" + opts


def build_prompt(cfg, row, val):
    parts = []
    if INSTRS[cfg["ins"]]: parts.append(INSTRS[cfg["ins"]])
    if cfg["shots"]:
        rng = np.random.RandomState(500 + cfg["dseed"])
        idx = rng.choice(len(val), cfg["shots"], replace=False)
        for i in idx:
            r = val.iloc[int(i)]
            parts.append(fmt_q(r, cfg) + "\nAnswer: " + r["answer"])
        parts.append(fmt_q(row, cfg) + "\nAnswer:")
        parts.append(ENDS[cfg["end"]])
    else:
        parts.append(fmt_q(row, cfg))
        parts.append(ENDS[cfg["end"]])
    return "\n\n".join(parts)


def pool_indices(N, seed=0):
    rng = np.random.RandomState(seed)
    return rng.permutation(12032)[:N]


def parse(txt):
    m = re.match(r"\s*\(?\**([A-J])\b", txt)
    return m.group(1) if m else None


if __name__ == "__main__":
    model, K, N, conc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    test, val = load()
    pool = pool_indices(N)
    cfgs = sample_configs(K)
    os.makedirs(BASE + "/cache", exist_ok=True)
    path = f"{BASE}/cache/api_{model}.jsonl"
    json.dump(dict(configs=cfgs, pool=pool.tolist(), model=model), open(f"{BASE}/cache/api_{model}_meta.json", "w"))
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                d = json.loads(line)
                if d.get("r") is not None: done.add((d["c"], d["q"]))
            except Exception: pass
    # order: interleave configs so partial runs still cover all configs on a prefix of questions
    jobs = [(c["id"], j) for j in range(N) for c in cfgs if (c["id"], j) not in done]
    print(f"{len(done)} done, {len(jobs)} to run", flush=True)
    client = anthropic.Anthropic(max_retries=0)
    lock = threading.Lock(); f = open(path, "a"); cnt = [0]; t0 = time.time()

    def work(job):
        cid, j = job
        row = test.iloc[int(pool[j])]
        prompt = build_prompt(cfgs[cid], row, val)
        for att in range(8):
            try:
                m = client.messages.create(model=model, max_tokens=8, messages=[{"role": "user", "content": prompt}])
                txt = "".join(b.text for b in m.content if getattr(b, "type", "") == "text")
                with lock:
                    f.write(json.dumps(dict(c=cid, q=j, r=txt)) + "\n"); cnt[0] += 1
                    if cnt[0] % 500 == 0:
                        f.flush(); print(cnt[0], round(time.time() - t0), "s", flush=True)
                return
            except Exception as e:
                time.sleep(min(30, 2 ** att + random.random()))
        with lock: print("FAILED", job, flush=True)

    with cf.ThreadPoolExecutor(conc) as ex: list(ex.map(work, jobs))
    f.flush(); print("done", time.time() - t0)
