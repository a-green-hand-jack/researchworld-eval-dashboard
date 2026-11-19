"""Scores MMLU-Pro questions under a prompt configuration by reading next-token logits over answer letters."""
import copy, time, sys
torch_threads = 4
import numpy as np, pandas as pd, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
LETTERS = "ABCDEFGHIJ"

torch.set_num_threads(4)

class Scorer:
    def __init__(self, path, dtype=torch.float32):
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=dtype).eval()
        # token ids for " A".." J" and "A".."J"
        self.ids = [[self.tok.encode(l, add_special_tokens=False)[0] for l in LETTERS],
                    [self.tok.encode(" " + l, add_special_tokens=False)[0] for l in LETTERS]]

    @torch.no_grad()
    def prefix_cache(self, prefix):
        enc = self.tok(prefix, return_tensors="pt", add_special_tokens=False)
        out = self.model(**enc, use_cache=True)
        return out.past_key_values, enc.input_ids.shape[1]

    @torch.no_grad()
    def score(self, prefix, suffixes, nopts, bs=16):
        """Return array (len(suffixes), 10) of log-probs over letters (masked beyond nopts), prefix is shared."""
        pkv, plen = self.prefix_cache(prefix)
        res = np.full((len(suffixes), 10), -np.inf, dtype=np.float32)
        order = np.argsort([len(s) for s in suffixes])
        for b in range(0, len(order), bs):
            idx = order[b:b + bs]
            enc = self.tok([suffixes[i] for i in idx], return_tensors="pt", padding=True, padding_side="right", add_special_tokens=False)
            B, L = enc.input_ids.shape
            cache = copy.deepcopy(pkv)
            cache.batch_repeat_interleave(B)
            am = torch.cat([torch.ones(B, plen, dtype=torch.long), enc.attention_mask], 1)
            pos = (plen + torch.arange(L)).unsqueeze(0).expand(B, -1)
            h = self.model.model(input_ids=enc.input_ids, attention_mask=am, past_key_values=cache, position_ids=pos, use_cache=True).last_hidden_state
            last = enc.attention_mask.sum(1) - 1
            lg = self.model.lm_head(h[torch.arange(B), last]).float()   # lm_head only at the answer position
            lp = torch.log_softmax(lg, -1)
            for r, i in enumerate(idx):
                n = nopts[i]
                v = torch.logsumexp(torch.stack([lp[r, self.ids[0][:n]], lp[r, self.ids[1][:n]]]), 0)
                res[i, :n] = v.numpy()
        return res
