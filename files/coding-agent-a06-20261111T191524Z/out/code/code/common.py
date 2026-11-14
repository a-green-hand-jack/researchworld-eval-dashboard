"""Shared definitions: pool construction, configuration grid, prompt building."""
import numpy as np, pandas as pd

ROOT = "/work"
LETTERS = "ABCDEFGHIJ"
MAX_Q_TOKENS = 200       # keep questions whose (question+options) text is <= 200 Qwen tokens (cost control)
POOL_SEED = 12345

INSTRUCTIONS = [
    None,  # I0: no system message (chat-template default system prompt)
    "You are a helpful assistant.",
    "Answer the following multiple-choice question. Respond with the letter of the correct option.",
    "You are a world-class expert across all academic disciplines. Choose the single best answer.",
    "Read the question carefully, eliminate options that are clearly wrong, and select the most likely correct answer.",
    "The following are multiple choice questions from a difficult university-level exam. Be precise.",
    "Be careful: many questions look easy but contain subtle traps. Think about what the question is really asking before choosing.",
    "Reply with only the letter of the best option.",
]
N_DEMO_SETS = 5          # demo set 0 = zero-shot; sets 1..4 = 3 random validation questions each
DEMO_K = 3

def format_q(question, options):
    return question + "\n\nOptions:\n" + "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(options))

def user_text(question, options):
    return format_q(question, options) + "\n\nAnswer with the letter of the correct option."

def load_data():
    t = pd.read_parquet(f"{ROOT}/data/mmlu-pro/data/test-00000-of-00001.parquet")
    v = pd.read_parquet(f"{ROOT}/data/mmlu-pro/data/validation-00000-of-00001.parquet")
    return t, v

def config_list():
    """K = 8 instructions x 5 demo sets = 40 configurations; id = demo*8+instr."""
    return [(i, d) for d in range(N_DEMO_SETS) for i in range(len(INSTRUCTIONS))]

def demo_sets(v):
    rng = np.random.RandomState(777)
    sets = [[]]
    for _ in range(N_DEMO_SETS - 1):
        sets.append(list(rng.choice(len(v), DEMO_K, replace=False)))
    return sets

def build_pool(tok, n_pool):
    """Random sample (seeded) of n_pool questions among those with <= MAX_Q_TOKENS tokens; fixed order."""
    t, _ = load_data()
    txt = [format_q(q, op) for q, op in zip(t.question, t.options)]
    n = np.array([len(x) for x in tok(txt).input_ids])
    elig = np.where(n <= MAX_Q_TOKENS)[0]
    rng = np.random.RandomState(POOL_SEED)
    idx = rng.permutation(elig)[:n_pool]
    return t.iloc[idx].reset_index(drop=True)
