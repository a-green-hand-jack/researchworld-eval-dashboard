"""Prompt-program search space for MMLU-Pro multiple-choice scoring.

A configuration is a dict with discrete components; `build_prompt` renders it to a chat prompt.
Scoring = argmax over option-letter logits at the first answer position (no free generation),
so one forward pass per (config, question)."""
import itertools, random
import numpy as np

LETTERS = "ABCDEFGHIJ"
SYSTEMS = [
    None,
    "You are a helpful assistant.",
    "You are a knowledgeable expert who answers multiple-choice questions accurately.",
    "You are a careful test-taker. Pick the single best option.",
]
INSTR = [  # placed before the question
    "",
    "Answer the following multiple-choice question.\n\n",
    "The following is a multiple-choice question about {subject}. Choose the correct option.\n\n",
    "Read the question and select the one best answer from the options.\n\n",
    "Think about which option is most accurate, then give only its letter.\n\n",
]
OPT_FMT = ["{L}. {t}", "({L}) {t}", "{L}) {t}", "{L}: {t}"]
CUE = [  # appended at the end of the user turn / start of assistant turn
    ("Answer:", ""),
    ("Respond with only the letter of the correct option.", "The answer is ("),
    ("Which option is correct?", "Answer:"),
    ("", "The correct option is"),
]
N_DEMOS = [0, 0, 0, 1]  # 1-shot in ~25% of configs (demo from the 70-question validation split)

def space():
    return dict(system=len(SYSTEMS), instr=len(INSTR), opt=len(OPT_FMT), cue=len(CUE), ndemo=len(N_DEMOS))

def sample_configs(K, seed=0, n_demo_pool=70):
    rng = random.Random(seed)
    allc = list(itertools.product(range(len(SYSTEMS)), range(len(INSTR)), range(len(OPT_FMT)),
                                  range(len(CUE)), range(len(N_DEMOS))))
    # dedupe on N_DEMOS value duplicates is harmless; sample without replacement
    rng.shuffle(allc)
    cfgs = []
    for i, (s, ins, o, c, nd) in enumerate(allc[:K]):
        k = N_DEMOS[nd]
        demo_ids = rng.sample(range(n_demo_pool), k) if k else []
        cfgs.append(dict(id=i, system=s, instr=ins, opt=o, cue=c, ndemo=k, demo_ids=demo_ids))
    return cfgs

def fmt_q(q, opts, optfmt, instr, cue_user):
    body = INSTR[instr].format(subject=q.get("category", "this subject"))
    body += "Question: " + q["question"].strip() + "\nOptions:\n"
    body += "\n".join(OPT_FMT[optfmt].format(L=LETTERS[i], t=o) for i, o in enumerate(opts))
    if cue_user:
        body += "\n" + cue_user
    return body

def build_prompt(cfg, q, demos, tok):
    """q: dict with question, options, category. demos: list of (q, answer_letter) dicts."""
    cue_user, cue_asst = CUE[cfg["cue"]]
    msgs = []
    if SYSTEMS[cfg["system"]]:
        msgs.append({"role": "system", "content": SYSTEMS[cfg["system"]]})
    for d in demos:
        msgs.append({"role": "user", "content": fmt_q(d, list(d["options"]), cfg["opt"], cfg["instr"], cue_user)})
        msgs.append({"role": "assistant", "content": cue_asst + d["answer"]})
    msgs.append({"role": "user", "content": fmt_q(q, list(q["options"]), cfg["opt"], cfg["instr"], cue_user)})
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    return text + cue_asst
