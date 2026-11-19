"""Finite-budget interventional Kernel SHAP, CPU/NumPy, handle-only API.

All requests/responses are finite JSON objects. Extra response keys are forbidden.
Seeds are arbitrary nonnegative integers and initialize randomness, never workload.
Every episode starts with reset; subsequent independent explanations use start.

reset: {"op":"reset","seed":int} -> {"ok":true}. Erases all state.
start: {"op":"start", "features":int in [2,20], "budget":int in [32,256],
        "stream":nonnegative int, "input":list[features],
        "background":list[1..32][features], "output":"positive_probability",
        "value_function":"interventional_grouped"}
  Original columns are the players; numeric/string category values are opaque.
  The evaluator masks complete original columns before training-fitted encoding.
  Returns {"masks":list[budget][features]} of integer 0/1 values, first empty,
  second full. All interior masks must be nonempty/nonfull. One live explanation;
  start may discard prior state after a failure. No paths or model labels exist.
observe: {"op":"observe","values":list[budget] of finite probabilities}
  Supplies the background-averaged black-box model values in mask order.
  Returns {"phi":list[features] of finite numbers, abs(value)<=1e6} on the
  probability scale. Strings and booleans are not attribution numbers.
  Consumes the live explanation. Solve a Shapley-kernel sampled constrained
  regression: sampling a size proportional to 1/(size*(d-size)), then a uniform
  subset, makes the interior least-squares weights equal. Empty/full endpoints
  impose exact efficiency (lstsq rcond=1e-10). Regression auditing uses
  rtol=1e-6, atol=1e-7. The evaluator checks masks, budgets, the regression,
  synthetic exact controls and reset replay, not candidate internal claims.

Budgets include endpoints, duplicates and all model evaluations. No optimization
or metric feedback is delivered. Independent repetitions have distinct stream
IDs; same reset/stream/settings must replay deterministically. No training,
state export, file exchange, or large-value transport is needed: all bounded
messages fit below 64 MiB including JSON/envelope/framing. Larger shapes are
invalid, not requests to load files. Each run has exactly start + observe RPCs.
Search ranks evidence completion, not a favorable reliability conclusion. The
paper still needs real results, uncertainty, references, official conference
template/checklist and all reproduction code; this starter is not a paper.
"""

import numpy as np

_seed = 0
_active = None


def handle(request):
    global _seed, _active
    operation = request["op"]
    if operation == "reset":
        if type(request["seed"]) is not int or request["seed"] < 0:
            raise ValueError("invalid seed")
        _seed = request["seed"]
        _active = None
        return {"ok": True}
    if operation == "start":
        features = request["features"]
        budget = request["budget"]
        if not 2 <= features <= 20 or not 32 <= budget <= 256:
            raise ValueError("unsupported shape")
        generator = np.random.default_rng(np.random.SeedSequence([_seed, request["stream"]]))
        sizes = np.arange(1, features)
        probabilities = 1.0 / (sizes * (features - sizes))
        probabilities /= probabilities.sum()
        masks = np.zeros((budget, features), dtype=np.int64)
        masks[1] = 1
        for index in range(2, budget):
            size = int(generator.choice(sizes, p=probabilities))
            masks[index, generator.choice(features, size=size, replace=False)] = 1
        _active = masks
        return {"masks": masks.tolist()}
    if operation == "observe":
        if _active is None:
            raise ValueError("no active explanation")
        masks = _active
        values = np.asarray(request["values"], dtype=np.float64)
        total = values[1] - values[0]
        design = masks[2:, :-1] - masks[2:, -1:]
        target = values[2:] - values[0] - masks[2:, -1] * total
        partial = np.linalg.lstsq(design, target, rcond=1e-10)[0]
        attribution = np.append(partial, total - partial.sum())
        _active = None
        return {"phi": attribution.tolist()}
    raise ValueError("unknown operation")
