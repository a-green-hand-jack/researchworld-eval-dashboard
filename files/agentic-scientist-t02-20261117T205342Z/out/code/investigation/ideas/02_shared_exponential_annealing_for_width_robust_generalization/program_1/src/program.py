"""Deterministic shared learning-rate controller for evaluator-owned neural training.

Entrypoint: handle(request) -> response, finite JSON objects only. Exactly the
documented keys are accepted and returned; additional response keys are forbidden.
There are no tensors, paths, state transfers, binary data, or implicit RPC calls.
State is reset for every episode and remains in candidate-owned memory only.

reset: {"op":"reset","seed":integer >=0} -> {"ok":true}. Seeds initialize
randomness only, never workload or plane identity. Accept arbitrary valid seeds.
Clears all state. This is always the first request of an episode.

recipe: {"op":"recipe","steps":positive integer,"block_steps":positive
integer dividing steps,"min_lr":0.0001,"max_lr":0.01} ->
{"initial_lr":number in [0.0001,0.01],"decay_rate":number in [0.01,1]}.
Called once after reset. The SAME numeric recipe must apply across every seed,
width, operation and decay arm; reset seeds must not select recipes. Public
workload fields have identical meanings in all planes and smoke. The evaluator
owns a 194-input, width-[16,64,256] ReLU MLP with 97 logits, AdamW, CE, full-batch
training and all data. Candidate controls only this bounded learning-rate family.

schedule: {"op":"schedule","step":integer in [0,steps),"steps":positive
integer,"block_steps":positive integer} -> {"lr":finite number}. After recipe,
called in increasing steps 0,block_steps,...,steps-block_steps. Return exactly
max(0.0001,min(0.01,initial_lr*decay_rate**(step/steps))) within absolute 1e-12.
Each rate governs one evaluator-owned block of optimizer updates. Workload must
match recipe; no observations, scores, targets, outcomes or feedback enter RPC.
At production workload steps=20000,block_steps=500, 42 calls per episode: reset,
recipe,40 schedule. Smoke reduces steps and block_steps only. No replay. Search
eligibility tests complete, genuine training and controls, NOT a favorable size
trend or a performance margin. Null and negative scientific results are valid.

Search ranks the mean accuracy of the last five heldout checkpoints, averaged
equally across seeds, widths, decays and operations. An episode failure scores 0
in the original denominator. Evaluation never trusts candidate internal flags.
All messages including JSON framing must be below 16 KiB here (and 64 MiB wire).
Implementations cannot supply code, weights, labels or artifact paths to training.
"""

import math

_state = None


def handle(request):
    global _state
    if type(request) is not dict:
        raise ValueError("request must be an object")
    operation = request.get("op")
    if operation == "reset":
        if set(request) != {"op", "seed"} or type(request["seed"]) is not int or request["seed"] < 0:
            raise ValueError("invalid reset")
        _state = {}
        return {"ok": True}
    if _state is None:
        raise ValueError("reset required")
    if operation == "recipe":
        if set(request) != {"op", "steps", "block_steps", "min_lr", "max_lr"}:
            raise ValueError("invalid recipe fields")
        steps, block_steps = request["steps"], request["block_steps"]
        if type(steps) is not int or type(block_steps) is not int or block_steps <= 0 or steps <= 0 or steps % block_steps:
            raise ValueError("invalid workload")
        if request["min_lr"] != 0.0001 or request["max_lr"] != 0.01 or _state:
            raise ValueError("invalid recipe state")
        _state = {"steps": steps, "block_steps": block_steps, "next_step": 0,
                  "initial_lr": 0.01, "decay_rate": 0.1}
        return {"initial_lr": _state["initial_lr"], "decay_rate": _state["decay_rate"]}
    if operation == "schedule":
        if set(request) != {"op", "step", "steps", "block_steps"} or not _state:
            raise ValueError("invalid schedule fields")
        if any(type(request[key]) is not int or request[key] != _state[key if key != "step" else "next_step"]
               for key in ("step", "steps", "block_steps")) or request["step"] >= _state["steps"]:
            raise ValueError("invalid schedule state")
        rate = max(0.0001, min(0.01, _state["initial_lr"] * _state["decay_rate"] ** (request["step"] / request["steps"])))
        if not math.isfinite(rate):
            raise ValueError("invalid rate")
        _state["next_step"] += _state["block_steps"]
        return {"lr": rate}
    raise ValueError("unknown operation")
