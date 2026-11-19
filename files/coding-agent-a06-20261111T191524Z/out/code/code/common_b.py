"""World B: heterogeneous configuration space (format fragility, label-biased demonstrations, demo count)."""
import numpy as np
from common import LETTERS, load_data, build_pool, format_q

FORMATS = ['chat_paren', 'raw', 'chat_plain_opts', 'chat_bare', 'chat_opts_first']
DEMOS = ['zero', 'rand3', 'allA3', 'rand8']
INSTR = [None, "You are a world-class expert across all academic disciplines. Choose the single best answer."]
DEFAULT_SYS = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."

def config_list_b():
    """id = (f*len(DEMOS)+d)*2+i ; 5 x 4 x 2 = 40 configurations"""
    return [(f, d, i) for f in range(len(FORMATS)) for d in range(len(DEMOS)) for i in range(2)]

def demo_indices(v):
    rng = np.random.RandomState(4242)
    rand3 = list(rng.choice(len(v), 3, replace=False)); rand8 = list(rng.choice(len(v), 8, replace=False))
    a_idx = [j for j in range(len(v)) if v.iloc[j].answer == 'A']
    allA = a_idx[:3]
    assert len(allA) == 3
    return dict(zero=[], rand3=rand3, allA3=allA, rand8=rand8)

def opts_block(options, style):
    if style == 'paren': return "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(options))
    return "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(options))

def q_block(fmt, question, options):
    """question as shown to the model (user-turn content or raw-text block), excluding assistant prefix"""
    f = FORMATS[fmt]
    if f == 'chat_paren': return question + "\n\nOptions:\n" + opts_block(options, 'dot') + "\n\nAnswer with the letter of the correct option."
    if f == 'raw': return "Question: " + question + "\nOptions:\n" + opts_block(options, 'dot') + "\nAnswer:"
    if f == 'chat_plain_opts': return question + "\n\n" + opts_block(options, 'paren') + "\n\nAnswer with the letter of the correct option."
    if f == 'chat_bare': return question + "\n\n" + opts_block(options, 'dot')
    if f == 'chat_opts_first': return "Options:\n" + opts_block(options, 'dot') + "\n\nQuestion: " + question + "\n\nAnswer with the letter of the correct option."

def asst_prefix(fmt):
    f = FORMATS[fmt]
    return "Answer:" if f == 'chat_plain_opts' else "The answer is ("

def letter_style(fmt):  # True if letter tokens carry a leading space
    return FORMATS[fmt] in ('raw', 'chat_plain_opts')

def build_prompt(cfg, v, dsets):
    """returns prefix_text (cacheable) and a function question->suffix_text"""
    f, d, i = cfg; name = DEMOS[d]; demos = dsets[name]
    chat = FORMATS[f] != 'raw'
    if chat:
        sysmsg = INSTR[i] if INSTR[i] is not None else DEFAULT_SYS
        pre = f"<|im_start|>system\n{sysmsg}<|im_end|>\n"
        for j in demos:
            r = v.iloc[j]
            pre += f"<|im_start|>user\n{q_block(f, r.question, r.options)}<|im_end|>\n<|im_start|>assistant\n{asst_prefix(f)}{' ' if letter_style(f) else ''}{r.answer}{'' if letter_style(f) else ')'}<|im_end|>\n"
        suf = lambda r: f"<|im_start|>user\n{q_block(f, r.question, r.options)}<|im_end|>\n<|im_start|>assistant\n{asst_prefix(f)}"
    else:
        head = (INSTR[i] + "\n\n") if INSTR[i] is not None else ""
        pre = head
        for j in demos:
            r = v.iloc[j]; pre += q_block(f, r.question, r.options) + f" {r.answer}\n\n"
        suf = lambda r: q_block(f, r.question, r.options)
    return pre, suf
