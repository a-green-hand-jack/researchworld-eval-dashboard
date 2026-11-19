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

from itertools import combinations

import numpy as np

_seed = 0
_active = None


def _kernel_size_schedule(feature_count, count, generator):
    sizes = np.arange(1, feature_count)
    kernel_mass = 1.0 / (sizes * (feature_count - sizes))
    kernel_mass /= kernel_mass.sum()
    cumulative_mass = np.cumsum(kernel_mass)
    cumulative_mass[-1] = 1.0
    quantiles = (np.arange(count) + generator.random(count)) / count
    size_schedule = sizes[np.searchsorted(cumulative_mass, quantiles, side="right")]
    generator.shuffle(size_schedule)
    return size_schedule


def _interaction_alias_masks(feature_count, budget, generator):
    size_schedule = _kernel_size_schedule(feature_count, budget - 2, generator)
    best_key = None
    best_masks = None
    for candidate_index in range(8):
        candidate_masks = np.zeros((budget, feature_count), dtype=np.int64)
        candidate_masks[1] = 1
        for row_index, size in enumerate(size_schedule, start=2):
            columns = generator.choice(feature_count, size=int(size), replace=False)
            candidate_masks[row_index, columns] = 1
        interior_masks = candidate_masks[2:].astype(np.float64)
        centered_masks = interior_masks - interior_masks.mean(axis=1, keepdims=True)
        singular_values = np.linalg.svd(centered_masks, compute_uv=False)
        tolerance = 1e-10 * max(float(singular_values[0]), 1.0)
        contrast_rank = int(np.count_nonzero(singular_values > tolerance))
        contrast_inverse = np.linalg.pinv(centered_masks, rcond=1e-10)
        interaction_alias = 0.0
        for degree in range(2, min(3, feature_count) + 1):
            interaction_columns = np.asarray(list(combinations(range(feature_count), degree)), dtype=np.int64)
            interaction_masks = interior_masks[:, interaction_columns]
            interaction_residuals = interaction_masks.prod(axis=2) - interaction_masks.mean(axis=2)
            alias = contrast_inverse @ interaction_residuals
            interaction_alias += degree * float(np.sum(alias * alias)) / len(interaction_columns)
        candidate_key = (contrast_rank, -interaction_alias)
        if best_key is None or candidate_key > best_key:
            best_key = candidate_key
            best_masks = candidate_masks.copy()
    return best_masks


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
        masks = _interaction_alias_masks(features, budget, generator)
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
