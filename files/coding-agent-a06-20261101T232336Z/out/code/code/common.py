"""Shared helpers: MMLU-Pro loading, population sampling, prompt-config space."""
import numpy as np, pandas as pd, itertools, json, os
DATA = "/work/data/mmlu-pro/data"
LETTERS = "ABCDEFGHIJ"

def load_test():
    return pd.read_parquet(f"{DATA}/test-00000-of-00001.parquet")
def load_val():
    return pd.read_parquet(f"{DATA}/validation-00000-of-00001.parquet")

def population_ids(N, seed=0):
    """Fixed random subset (without replacement) of N test items = our 'population' P."""
    df = load_test()
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(len(df), size=N, replace=False))
    return idx

INSTRUCTIONS = [
    "The following is a multiple choice question. Choose the correct answer.",
    "Answer the question by selecting the letter of the correct option. Respond with only the letter.",
    "Think carefully about each option, then give the single best answer.",
    "Solve the following problem. Exactly one of the options is correct.",
    "You are a knowledgeable expert. Read the question and pick the most accurate option.",
    "Pick the right option.",
]
# (option template, cue appended after the question). The letter placeholders are {L}, text {T}.
FORMATS = [
    ("{L}. {T}", "Answer:"),
    ("({L}) {T}", "The answer is ("),
    ("{L}) {T}", "Correct option:"),
    ("[{L}] {T}", "Answer: ["),
]
N_DEMO_SETS = 6  # 0: none, 1-3: k=3, 4-5: k=6

def demo_sets(val, seed=123):
    rng = np.random.default_rng(seed)
    out = [[]]
    for k in (3, 3, 3, 6, 6):
        out.append(list(rng.choice(len(val), size=k, replace=False)))
    return out

def fmt_question(row, fmt, with_answer=None):
    ot, cue = FORMATS[fmt]
    opts = list(row["options"])
    body = "Question: " + row["question"].strip() + "\nOptions:\n" + "\n".join(ot.format(L=LETTERS[i], T=str(o).strip()) for i, o in enumerate(opts)) + "\n"
    if with_answer is None:
        return body, cue
    return body + cue + (" " if not cue.endswith(("(", "[")) else "") + LETTERS[with_answer] + ("" if not cue.endswith(("(", "[")) else {"(": ")", "[": "]"}[cue[-1]])

def config_list():
    return [dict(instr=i, fmt=f, demo=d) for i, f, d in itertools.product(range(len(INSTRUCTIONS)), range(len(FORMATS)), range(N_DEMO_SETS))]

def build_prefix(cfg, val, dsets):
    """Text shared by all items for this config (chat template applied by the scorer)."""
    s = INSTRUCTIONS[cfg["instr"]] + "\n\n"
    for j in dsets[cfg["demo"]]:
        r = val.iloc[int(j)]
        s += fmt_question(r, cfg["fmt"], with_answer=int(r["answer_index"])) + "\n\n"
    return s
