"""Prompt-configuration space (factorial) and question universe for MMLU-Pro experiments.

Config = (instruction I in 0..3, format F in 0..2, demo-set D in 0..5) -> 72 configs (all 2-shot).
Demonstrations come from the MMLU-Pro *validation* split (disjoint from the test-split universe).
"""
import itertools, re
import numpy as np, pandas as pd

L = "ABCDEFGHIJ"
TEST = "data/mmlu_pro/data/test-00000-of-00001.parquet"
VAL = "data/mmlu_pro/data/validation-00000-of-00001.parquet"
UNIVERSE_SEED = 12345

INSTR = [
    "Answer the following multiple-choice question. Reply with only the letter of the correct option.",
    "You are an expert in {subject}. Answer the multiple-choice question below. Respond with just the letter of the best option.",
    "Pick the single best option. Output just its letter.",
    "Read the question carefully and consider every option before deciding. Then output only the letter of the best answer, nothing else.",
]
N_I, N_F, N_D = 4, 3, 6
CONFIGS = list(itertools.product(range(N_I), range(N_F), range(N_D)))  # 72


def fmt_q(row_q, row_opts, F):
    if F == 0:
        return "Question: " + row_q + "\n" + "\n".join(f"{L[i]}. {o}" for i, o in enumerate(row_opts)) + "\nAnswer:"
    if F == 1:
        return "Q: " + row_q + "\n" + "\n".join(f"({L[i]}) {o}" for i, o in enumerate(row_opts)) + "\nThe correct option is ("
    return "### Question\n" + row_q + "\n\n### Options\n" + "\n".join(f"{L[i]}) {o}" for i, o in enumerate(row_opts)) + "\n\n### Answer\n"


def fmt_demo_answer(a, F):
    if F == 0:
        return f" {a}"
    if F == 1:
        return f"{a})"
    return f"{a}"


_demo_cache = {}


def demo_sets():
    if _demo_cache:
        return _demo_cache["d"]
    v = pd.read_parquet(VAL)
    v["len"] = v.question.str.len() + v.options.map(lambda o: sum(len(x) for x in o))
    v = v[v.len < 450].reset_index(drop=True)
    rng = np.random.RandomState(7)
    idx = rng.permutation(len(v))
    sets = {}
    for d in range(N_D):
        r2 = np.random.RandomState(100 + d)
        sets[d] = [v.iloc[i] for i in r2.choice(len(v), 2, replace=False)]
    _demo_cache["d"] = sets
    return sets


def build_prompt(cfg, row):
    """Return the user-message string for config cfg on a question row (with .question,.options,.category)."""
    I, F, D = cfg
    head = INSTR[I].format(subject=row.category)
    parts = [head, ""]
    for d in demo_sets()[D]:
        parts.append(fmt_q(d.question, d.options, F) + fmt_demo_answer(d.answer, F))
        parts.append("")
    parts.append(fmt_q(row.question, row.options, F))
    return "\n".join(parts)


def universe(n=1000):
    """Fixed random subset of the MMLU-Pro test split (the finite 'population' of questions)."""
    t = pd.read_parquet(TEST)
    rng = np.random.RandomState(UNIVERSE_SEED)
    idx = rng.permutation(len(t))[:n]
    return t.iloc[idx].reset_index(drop=True)


_pat = re.compile(r"^[\s\*\(\[]*(?:answer\s*[:\-]?\s*)?(?:the\s+(?:correct\s+)?(?:answer|option)\s+is\s*)?[\s\*\(\[]*([A-J])(?![A-Za-z0-9'])", re.I)


def parse_letter(text):
    """Strict-ish: the reply must START with a letter A-J (optionally in brackets/bold/'Answer:').
    Anything else counts as a format failure (-1) and is scored wrong; this is part of what prompt search can exploit."""
    m = _pat.match(text or "")
    if not m:
        return -1
    ch = m.group(1)
    if ch.islower():  # avoid 'a ...' / 'i ...' being read as letters
        return -1
    return L.index(ch)
