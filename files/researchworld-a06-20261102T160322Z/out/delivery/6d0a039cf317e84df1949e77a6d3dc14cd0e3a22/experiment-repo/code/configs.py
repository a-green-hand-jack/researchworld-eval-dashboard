"""Prompt/pipeline configuration family (24 base prompts) for MMLU-Pro. Deterministic."""
import itertools, numpy as np, pandas as pd
LET = "ABCDEFGHIJ"
DATA = "/hutian/data/mmlu_pro/data/"
INSTR = {
 "terse":   "Answer the following multiple-choice question with a single letter.",
 "expert":  "You are an expert in {cat}. Select the correct option for the question below and reply with its letter only.",
 "careful": "Read the question carefully, consider every option, then give only the letter of the best answer.",
 "exam":    "The following is a multiple-choice exam question about {cat}. Choose the correct answer.",
}
CUE = {"is": "The answer is ", "paren": "The answer is ("}
SHOTS = {"0shot": None, "3shotA": 101, "3shotB": 202}   # value = demo sampling seed
BASE = [f"{i}|{c}|{s}" for i in INSTR for c in CUE for s in SHOTS]   # 24 names

def load_test():
    return pd.read_parquet(DATA + "test-00000-of-00001.parquet")
def load_val():
    return pd.read_parquet(DATA + "validation-00000-of-00001.parquet")

def pool_indices(n_pool, seed=0):
    """Fixed random pool of test rows (positional indices), in random order."""
    return np.random.RandomState(seed).permutation(12032)[:n_pool]

def fmt_q(q, opts):
    return f"Question: {q}\n" + "\n".join(f"{LET[i]}. {o}" for i, o in enumerate(opts))

def demos(val, cat, seed, k=3):
    v = val[val.category == cat]
    idx = np.random.RandomState(seed).permutation(len(v))[:k]  # hash%1==0: deterministic
    return [v.iloc[i] for i in idx]

def prefix_suffix(name, row, val, cat_text):
    ins, cue, sh = name.split("|")
    head = INSTR[ins].format(cat=cat_text) + "\n\n"
    if SHOTS[sh] is not None:
        for d in demos(val, row.category, SHOTS[sh]):
            head += fmt_q(d.question, list(d.options)) + f"\n{CUE[cue]}{LET[d.answer_index]}" + (")" if cue == "paren" else "") + "\n\n"
    prefix = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n" + head
    suffix = fmt_q(row.question, list(row.options)) + "<|im_end|>\n<|im_start|>assistant\n" + CUE[cue]
    return prefix, suffix
