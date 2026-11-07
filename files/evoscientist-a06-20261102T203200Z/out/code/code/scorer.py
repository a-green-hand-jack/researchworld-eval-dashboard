"""Prompt-configuration space for MMLU-Pro and a fast logit-based scorer (CPU).

A configuration = (instruction, option-label format, answer cue, chat-template flag,
question header, few-shot demo set).  Scoring: one forward pass per (config, question);
prediction = argmax over the 10 option-letter logits at the answer position.
"""
import itertools, json, random, time, sys, os
import numpy as np, pandas as pd, torch

LETTERS = "ABCDEFGHIJ"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = BASE + "/data/mmlu-pro/data"

INSTRS = [
    "",
    "The following is a multiple choice question. Choose the correct answer.",
    "You are an expert. Answer the following multiple-choice question.",
    "Read the question carefully and select the single best option.",
    "Answer the question below by giving the letter of the correct option.",
    "This is a hard exam question with ten options and exactly one correct answer. Pick it.",
    "You are a university professor grading an exam. Select the right option.",
    "Think about which option is most accurate, then output only its letter.",
]
FMTS = ["{L}.", "({L})", "{L})"]
CUES = ["Answer:", "The answer is (", "Correct option:"]
HEADERS = ["Question:", "Q:", ""]
SHOTS = [0, 1, 2, 3]


def load_data():
    test = pd.read_parquet(f"{DATA}/test-00000-of-00001.parquet")
    val = pd.read_parquet(f"{DATA}/validation-00000-of-00001.parquet")
    return test, val


def fmt_q(row, fmt, header, with_answer=None, cue=None):
    opts = "\n".join(f"{fmt.format(L=LETTERS[i])} {o}" for i, o in enumerate(row["options"]))
    s = (header + " " if header else "") + row["question"].strip() + "\n" + opts + "\n"
    return s


def sample_configs(K, seed=0):
    rng = random.Random(seed)
    grid = []
    for ins in range(len(INSTRS)):
        for f in range(len(FMTS)):
            for c in range(len(CUES)):
                for ch in (0, 1):
                    for h in range(len(HEADERS)):
                        for sh in SHOTS:
                            for ds in (range(6) if sh > 0 else [0]):
                                grid.append(dict(ins=ins, fmt=f, cue=c, chat=ch, hdr=h, shots=sh, dseed=ds))
    rng.shuffle(grid)
    # stratify a bit by shots to keep cost balanced: 25% zero-shot, 75% few-shot (1-3)
    out = []
    zs = [g for g in grid if g["shots"] == 0][: int(K * 0.3)]
    fs = [g for g in grid if g["shots"] > 0][: K - len(zs)]
    out = zs + fs
    rng.shuffle(out)
    for i, g in enumerate(out):
        g["id"] = i
    return out


def build_prompt(cfg, row, val, tok):
    fmt, cue, hdr = FMTS[cfg["fmt"]], CUES[cfg["cue"]], HEADERS[cfg["hdr"]]
    parts = []
    if INSTRS[cfg["ins"]]:
        parts.append(INSTRS[cfg["ins"]] + "\n\n")
    if cfg["shots"] > 0:
        rng = np.random.RandomState(1000 + cfg["dseed"] * 7 + cfg["shots"])
        idx = rng.choice(len(val), cfg["shots"], replace=False)
        for i in idx:
            r = val.iloc[int(i)]
            parts.append(fmt_q(r, fmt, hdr) + cue + (" " if not cue.endswith("(") else "") + r["answer"] + (")" if cue.endswith("(") else "") + "\n\n")
    body = "".join(parts) + fmt_q(row, fmt, hdr)
    if cfg["chat"]:
        msgs = [{"role": "user", "content": body.rstrip()}]
        pre = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        return pre + cue
    return body + cue


def letter_ids(tok, cue):
    ids = []
    base = tok(cue, add_special_tokens=False)["input_ids"]
    for L in LETTERS:
        sp = "" if cue.endswith("(") else " "
        full = tok(cue + sp + L, add_special_tokens=False)["input_ids"]
        assert full[: len(base)] == base, (cue, L)
        ids.append(full[-1])
    return ids


@torch.no_grad()
def score_config(model, tok, cfg, test_rows, val, bs=8, maxlen=1400):
    """returns (correct[0/1] array, pred array, margin array) over test_rows (DataFrame)."""
    cue = CUES[cfg["cue"]]
    lids = torch.tensor(letter_ids(tok, cue))
    prompts = [build_prompt(cfg, test_rows.iloc[i], val, tok) for i in range(len(test_rows))]
    enc = [tok(p, add_special_tokens=False)["input_ids"][-maxlen:] for p in prompts]
    order = np.argsort([len(e) for e in enc])
    preds = np.zeros(len(enc), dtype=np.int64)
    logp = np.zeros((len(enc), 10), dtype=np.float32)
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0
    for s in range(0, len(order), bs):
        b = order[s : s + bs]
        L = max(len(enc[i]) for i in b)
        ids = torch.full((len(b), L), pad); att = torch.zeros((len(b), L), dtype=torch.long)
        for j, i in enumerate(b):  # left pad
            ids[j, L - len(enc[i]):] = torch.tensor(enc[i]); att[j, L - len(enc[i]):] = 1
        out = model(input_ids=ids, attention_mask=att, logits_to_keep=1).logits[:, -1, :]
        lg = out[:, lids].float()
        logp[b] = torch.log_softmax(lg, -1).numpy()
        preds[b] = lg.argmax(-1).numpy()
    gold = test_rows["answer_index"].values
    return (preds == gold).astype(np.int8), preds.astype(np.int8), logp


def load_model(name, dtype=torch.bfloat16):
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tok = AutoTokenizer.from_pretrained(f"{BASE}/data/{name}")
    model = AutoModelForCausalLM.from_pretrained(f"{BASE}/data/{name}", dtype=dtype)
    model.eval()
    return model, tok


if __name__ == "__main__":
    torch.set_num_threads(int(os.environ.get("NT", 40)))
    name = sys.argv[1]; dt = {"bf16": torch.bfloat16, "fp32": torch.float32}[sys.argv[2]]
    test, val = load_data()
    model, tok = load_model(name, dt)
    cfgs = sample_configs(96)
    rows = test.iloc[:64]
    for cfg in cfgs[:3]:
        t = time.time()
        c, p, _ = score_config(model, tok, cfg, rows, val)
        print(cfg, "acc", c.mean(), "sec/64q", round(time.time() - t, 1), flush=True)
