"""Baseline candidate: a one-layer transformer trained on modular binary operations.

Interface ``python_rpc_v1:handle``: ``handle(request) -> response`` with finite JSON values.
All model, optimizer, data and RNG state lives in this process and is rebuilt by ``reset``.
The evaluator owns the data split, the checkpoint plan, the controls and every metric; the
candidate never receives validation labels, and nothing reported by the candidate is trusted.

Integer arrays cross the wire as inline objects
    {"dtype": "int16", "shape": [...], "encoding": "base64-le", "data": "<base64 of little-endian int16>"}

Operations (every request is a dict with an "op" key; unknown keys are ignored):

``reset``  {"op": "reset", "seed": int>=0, "modulus": int (prime p), "operation": "add",
            "d_model": int (multiple of n_heads), "n_heads": int, "learning_rate": float,
            "betas": [float, float], "weight_decay": float, "full_batch": true,
            "max_steps": int}
    Rebuilds all state. ``seed`` only initializes randomness. The workload fields are chosen by
    the evaluator and must be honored: width, optimizer hyperparameters (AdamW, decoupled weight
    decay), full-batch updates and the total step budget. The family is a single-layer
    transformer with at most 1e6 parameters. Response: exactly {"ok": true}.

``load_train``  {"op": "load_train", "rows": int16 array of shape [n, 3] holding (a, b, label)}
    Training rows only. Called once after reset. Response: exactly {"ok": true}.

``train``  {"op": "train", "steps": int>=0}
    Advance ``steps`` full-batch optimizer steps (0 is legal and must leave the model
    untouched). The cumulative step count may not exceed ``max_steps``. Response: exactly
    {"ok": true}.

``predict``  {"op": "predict", "pairs": int16 array of shape [m, 2] holding (a, b)}
    Inputs only; no labels. Response: exactly
    {"ok": true, "predictions": int16 array of shape [m] with values in [0, p-1]} giving the
    argmax class for each queried pair, in query order. The extra keys are forbidden.

Any malformed request raises an exception (the evaluator counts the episode as failed).
Extra response keys, wrong shapes or out-of-range predictions are scored as a failed episode.
"""

import base64
import math
import os

import numpy as np
import torch
import torch.nn as nn

_THREADS = max(1, min(8, len(os.sched_getaffinity(0))))
torch.set_num_threads(_THREADS)

_STATE = {}
_INIT_SCALE = 0.5
# Width-aware (muP-like) output scaling: logits are multiplied by (REF_WIDTH / d) ** OUT_EXP.
# OUT_EXP = 0 reproduces the standard parametrization (with UNEMBED_INIT = 1 it is program_0).
# Both knobs are plain constants; offline selection was not possible in this stage (no code
# execution allowed), so the defaults are a moderate, conservative choice: a mild width-aware
# multiplier (<= 2x for d >= 32) and a 0.5x unembed init shrink (total 0.25x of the default).
REF_WIDTH = 128
OUT_EXP = 0.5
UNEMBED_INIT = 0.5


class _Net(nn.Module):
    def __init__(self, p, d, heads):
        super().__init__()
        self.heads = heads
        self.embed = nn.Embedding(p + 1, d)  # token p is the "=" separator
        self.pos = nn.Parameter(torch.randn(3, d) * 0.02)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.proj = nn.Linear(d, d, bias=False)
        self.fc1 = nn.Linear(d, 4 * d)
        self.fc2 = nn.Linear(4 * d, d)
        self.unembed = nn.Linear(d, p, bias=False)
        nn.init.normal_(self.embed.weight, std=1.0 / math.sqrt(d))
        # Omnigrok-style smaller initial weight norm: less lazy-regime memorization, so the
        # weight-decay-driven transition to the generalizing circuit starts from a smaller norm.
        with torch.no_grad():
            for lin in (self.qkv, self.proj, self.fc1, self.fc2, self.unembed):
                lin.weight.mul_(_INIT_SCALE)
            self.unembed.weight.mul_(UNEMBED_INIT)
        self.out_mult = (REF_WIDTH / d) ** OUT_EXP

    def forward(self, x):
        z = self.embed(x) + self.pos
        b, t, d = z.shape
        # Only the last ("=") position feeds the loss/readout, and attention is non-causal, so
        # queries, residual stream, and MLP are computed for that position only. This is exactly
        # equivalent to running all positions (same outputs and gradients), ~3x cheaper.
        w = self.qkv.weight
        q = (z[:, -1:] @ w[:d].T).view(b, 1, self.heads, d // self.heads).transpose(1, 2)
        k = (z @ w[d:2 * d].T).view(b, t, self.heads, d // self.heads).transpose(1, 2)
        v = (z @ w[2 * d:].T).view(b, t, self.heads, d // self.heads).transpose(1, 2)
        a = nn.functional.scaled_dot_product_attention(q, k, v).transpose(1, 2).reshape(b, d)
        h = z[:, -1] + self.proj(a)
        h = h + self.fc2(torch.relu(self.fc1(h)))
        return self.unembed(h) * self.out_mult


def _decode(obj, ndim, last):
    if (type(obj) is not dict or set(obj) != {"dtype", "shape", "encoding", "data"}
            or obj["dtype"] != "int16" or obj["encoding"] != "base64-le"):
        raise ValueError("bad array envelope")
    shape = obj["shape"]
    if (type(shape) is not list or len(shape) != ndim
            or any(type(n) is not int or n < 0 for n in shape)
            or (ndim == 2 and shape[1] != last)):
        raise ValueError("bad array shape")
    raw = base64.b64decode(obj["data"], validate=True)
    arr = np.frombuffer(raw, dtype="<i2")
    if arr.size != int(np.prod(shape)):
        raise ValueError("bad array length")
    return arr.reshape(shape).astype(np.int64)


def _encode(arr):
    arr = np.ascontiguousarray(arr, dtype="<i2")
    return {"dtype": "int16", "shape": list(arr.shape), "encoding": "base64-le",
            "data": base64.b64encode(arr.tobytes()).decode("ascii")}


def _reset(req):
    p, d, heads = req["modulus"], req["d_model"], req["n_heads"]
    if req["operation"] != "add" or type(p) is not int or p < 2:
        raise ValueError("unsupported task")
    if type(d) is not int or type(heads) is not int or d % heads != 0:
        raise ValueError("bad width")
    seed = req["seed"]
    if type(seed) is not int or seed < 0:
        raise ValueError("bad seed")
    torch.manual_seed(seed)
    np.random.seed(seed % (2 ** 32))
    model = _Net(p, d, heads)
    opt = torch.optim.AdamW(model.parameters(), lr=float(req["learning_rate"]),
                            betas=tuple(float(b) for b in req["betas"]),
                            weight_decay=float(req["weight_decay"]))
    _STATE.clear()
    _STATE.update(p=p, model=model, opt=opt, x=None, y=None, steps=0,
                  max_steps=int(req["max_steps"]), full_batch=bool(req["full_batch"]))
    return {"ok": True}


def _load_train(req):
    p = _STATE["p"]
    rows = _decode(req["rows"], 2, 3)
    if rows.shape[0] == 0 or rows.min() < 0 or rows.max() >= p:
        raise ValueError("bad rows")
    x = np.stack([rows[:, 0], rows[:, 1], np.full(rows.shape[0], p)], axis=1)
    _STATE["x"] = torch.from_numpy(x)
    _STATE["y"] = torch.from_numpy(rows[:, 2].copy())
    return {"ok": True}


def _train(req):
    steps = req["steps"]
    if type(steps) is not int or steps < 0 or _STATE["steps"] + steps > _STATE["max_steps"]:
        raise ValueError("bad step count")
    if steps and _STATE["x"] is None:
        raise ValueError("no training rows loaded")
    model, opt = _STATE["model"], _STATE["opt"]
    model.train()
    for _ in range(steps):
        loss = nn.functional.cross_entropy(model(_STATE["x"]), _STATE["y"])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    _STATE["steps"] += steps
    return {"ok": True}


def _predict(req):
    p = _STATE["p"]
    pairs = _decode(req["pairs"], 2, 2)
    if pairs.size and (pairs.min() < 0 or pairs.max() >= p):
        raise ValueError("bad pairs")
    x = torch.from_numpy(np.concatenate([pairs, np.full((pairs.shape[0], 1), p)], axis=1))
    model = _STATE["model"]
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, x.shape[0], 4096):
            out.append(model(x[i:i + 4096]).argmax(-1).numpy())
    preds = np.concatenate(out) if out else np.zeros(0, dtype=np.int64)
    return {"ok": True, "predictions": _encode(preds)}


_OPS = {"reset": _reset, "load_train": _load_train, "train": _train, "predict": _predict}


def handle(request):
    if type(request) is not dict or request.get("op") not in _OPS:
        raise ValueError("unknown op")
    return _OPS[request["op"]](request)
