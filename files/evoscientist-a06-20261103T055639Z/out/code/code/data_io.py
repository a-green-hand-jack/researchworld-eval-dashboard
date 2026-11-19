"""Load cached API replies into per-question 0/1 score matrices M[q, c].
Two scoring rules (both computed from the SAME cached raw replies, so no extra LLM calls):
  strict  : reply must start with the answer letter (format-sensitive; format failures count wrong)
  lenient : first standalone capital letter A-J anywhere in the (<=12 token) reply
"""
import json, re, sys, os
import numpy as np
sys.path.insert(0, "code")
from configs import *

_len = re.compile(r"(?<![A-Za-z0-9])([A-J])(?![A-Za-z0-9])")


def parse_lenient(t):
    m = _len.search(t or "")
    return L.index(m.group(1)) if m else -1


def load(model, nq=None, parser="strict"):
    path = f"cache/api_{model}.jsonl"
    U = universe(3000)
    C = len(CONFIGS)
    pred = -np.ones((len(U), C), dtype=np.int8); have = np.zeros((len(U), C), bool)
    f = parse_letter if parser == "strict" else parse_lenient
    for l in open(path):
        r = json.loads(l)
        pred[r["q"], r["c"]] = f(r["t"]); have[r["q"], r["c"]] = True
    ok = have.all(1)
    Q = int(np.argmin(ok)) if not ok.all() else len(ok)  # contiguous complete prefix
    if nq: Q = min(Q, nq)
    gold = U.answer_index.values[:Q]
    M = (pred[:Q] == gold[:, None]).astype(np.float32)
    return M, dict(Q=Q, fail=float((pred[:Q] == -1).mean()), cats=U.category.values[:Q])


if __name__ == "__main__":
    for m in ["claude-opus-4-5", "claude-sonnet-4-6"]:
        for p in ["strict", "lenient"]:
            M, info = load(m, parser=p)
            mu = M.mean(0)
            print(m, p, "Q", info["Q"], "fail %.3f" % info["fail"], "cfg acc min/med/max %.3f %.3f %.3f" % (mu.min(), np.median(mu), mu.max()))
