"""Configuration pool: instruction (6) x demonstration set (0-shot or one of 4 random 3-shot sets) x layout (plain / reversed options)."""
import numpy as np
LETTERS = list("ABCDEFGHIJ")
INSTR = [
 "Answer the following multiple choice question by selecting the single best option.",
 "You are an expert. Read the question carefully and choose the correct answer.",
 "The following is a multiple choice question with ten options. Reply with the letter of the correct option.",
 "Think about which option is most accurate, then give only its letter.",
 "Choose the answer that is correct. Be precise.",
 "Solve the problem below. Exactly one option is right.",
]
def make_configs(n_val=70, seed=12345):
    rng = np.random.default_rng(seed)
    demo_sets = [[]] + [sorted(rng.choice(n_val, 3, replace=False).tolist()) for _ in range(4)]
    cfgs = []
    for i in range(len(INSTR)):
        for d, ds in enumerate(demo_sets):
            for lay in ("plain", "reversed"):
                cfgs.append(dict(instr=i, demo_id=d, demos=ds, layout=lay))
    return cfgs
def _order(cfg, n):
    return list(range(n)) if cfg["layout"] == "plain" else list(range(n - 1, -1, -1))
def build_prefix(cfg, val):
    s = INSTR[cfg["instr"]] + "\n\n"
    for r in cfg.get("demos", []):
        s += format_question(cfg, val.iloc[r], with_answer=True)
    return s
def format_question(cfg, row, with_answer=False):
    opts = list(row["options"]); order = _order(cfg, len(opts))
    s = f"Question: {row['question']}\nOptions:\n"
    for L, k in zip(LETTERS, order): s += f"{L}. {opts[k]}\n"
    s += "Answer:"
    if with_answer: s += f" {LETTERS[order.index(int(row['answer_index']))]}\n\n"
    return s
def displayed_to_original(cfg, n):
    """order[j] = original option index shown at displayed letter j"""
    return _order(cfg, n)
