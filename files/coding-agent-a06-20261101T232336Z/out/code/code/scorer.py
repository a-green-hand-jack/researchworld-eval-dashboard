"""llama.cpp scorer: next-token distribution over option letters with shared-prefix KV reuse."""
import numpy as np, time, sys
from llama_cpp import Llama
from common import *

class Scorer:
    def __init__(self, path, n_threads=8, n_ctx=4096):
        self.llm = Llama(model_path=path, n_ctx=n_ctx, n_threads=n_threads, n_threads_batch=n_threads, n_batch=512, verbose=False, logits_all=False)
        self.tok = lambda s, special=False: self.llm.tokenize(s.encode(), add_bos=False, special=special)
        self.letter_ids = []
        for L in LETTERS:
            ids = set()
            for v in (L, " " + L):
                t = self.llm.tokenize(v.encode(), add_bos=False)
                if len(t) == 1: ids.add(t[0])
            self.letter_ids.append(sorted(ids))
        self.prefix_key = None; self.prefix_toks = []
    def set_prefix(self, text):
        # chat wrapper: system + user header, then prefix text; per-item part appended after.
        head = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n" + text
        toks = self.tok(head, special=True)
        self.llm.reset(); self.llm._ctx.kv_cache_clear()
        self.llm.eval(toks)
        self.prefix_toks = toks
    def score(self, q, cue, nopt):
        """q = formatted question body, cue = assistant-turn answer cue; returns log-probs over first nopt letters."""
        toks = self.tok(q + "<|im_end|>\n<|im_start|>assistant\n" + cue, special=True)
        P = len(self.prefix_toks)
        self.llm._ctx.kv_cache_seq_rm(0, P, -1)
        self.llm.n_tokens = P
        self.llm.eval(toks)
        lg = np.array(np.ctypeslib.as_array(self.llm._ctx.get_logits(), shape=(self.llm._n_vocab,)), dtype=np.float64)
        lg = lg - np.logaddexp.reduce(lg)
        out = np.array([np.logaddexp.reduce(lg[self.letter_ids[i]]) for i in range(nopt)])
        return out
