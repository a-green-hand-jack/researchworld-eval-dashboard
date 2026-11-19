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
  subset, makes the interior least-squares weights equal. This implementation
  stratifies that distribution, pairs complements when the design has enough
  rows, and covers each size stratum without replacement before recycling.
  Samples are dependent within a run, with the same kernel marginals.
  Empty/full endpoints
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

from math import comb

import numpy as np

_seed = 0
_active = None


def _stratified_sizes(feature_count, count, generator):
    """Sample unordered complement strata with kernel-proportional marginals."""
    if count == 0:
        return np.empty(0, dtype=np.int64)
    sizes = np.arange(1, feature_count // 2 + 1, dtype=np.int64)
    weights = 1.0 / (sizes * (feature_count - sizes))
    weights *= np.where(2 * sizes == feature_count, 1.0, 2.0)
    cumulative = np.cumsum(weights / weights.sum())
    cumulative[-1] = 1.0
    positions = (np.arange(count) + generator.random(count)) / count
    selected = sizes[np.searchsorted(cumulative, positions, side="right")]
    generator.shuffle(selected)
    return selected


def _draw_mask(feature_count, size, generator, visited):
    """Draw a uniformly oriented pair, without replacement within each cycle."""
    full_mask = (1 << feature_count) - 1
    capacity = comb(feature_count, size)
    if 2 * size == feature_count:
        capacity //= 2
    seen = visited.setdefault(size, set())
    if len(seen) == capacity:
        seen.clear()
    while True:
        columns = generator.choice(feature_count, size=size, replace=False)
        encoded = sum(1 << int(column_index) for column_index in columns)
        if 2 * size == feature_count:
            encoded = min(encoded, full_mask ^ encoded)
        if encoded not in seen:
            seen.add(encoded)
            break
    if generator.integers(2):
        encoded = full_mask ^ encoded
    return np.asarray(
        [(encoded >> column_index) & 1 for column_index in range(feature_count)],
        dtype=np.int64,
    )


def _coalition_design(feature_count, budget, generator):
    """Spend exactly budget rows, retaining rank headroom before pairing."""
    masks = np.zeros((budget, feature_count), dtype=np.int64)
    masks[1] = 1
    interior_count = budget - 2
    pair_count = min(
        interior_count // 2,
        max(0, interior_count - 2 * (feature_count - 1)),
    )
    single_count = interior_count - 2 * pair_count
    pair_sizes = _stratified_sizes(feature_count, pair_count, generator)
    single_sizes = _stratified_sizes(feature_count, single_count, generator)
    visited = {}
    row_index = 2
    for size in pair_sizes:
        mask = _draw_mask(feature_count, int(size), generator, visited)
        masks[row_index] = mask
        masks[row_index + 1] = 1 - mask
        row_index += 2
    for size in single_sizes:
        masks[row_index] = _draw_mask(feature_count, int(size), generator, visited)
        row_index += 1
    generator.shuffle(masks[2:])
    return masks


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
        masks = _coalition_design(features, budget, generator)
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
