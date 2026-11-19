"""Baseline candidate: naive best-search-score reporter with a Wilson 90% interval.

Interface (python_rpc_v1:handle): ``handle(request) -> response`` over finite JSON values.
The evaluator calls ``reset`` once per episode, then ``report`` many times (independent
replications).  Keep candidate state in memory only; there is no shared filesystem, no
network, and no GPU.  numpy and scipy are installed; the CPU budget is at most 4 threads
and each call must finish in well under 10 seconds (a timed-out call forfeits the episode).
Aggregate candidate time is also capped: plan for an average of at most about 2.7 s per
call (search: 2052 s over 760 calls; final: 5400 s over 2000 calls); exhausting the
aggregate cap turns later calls into worst-case timeouts.

World being scored (the evaluator does not tell you which one a request comes from):
a system searched K prompt/pipeline configurations on N benchmark questions, a searcher
selected one configuration, and you report the accuracy that configuration would have on
FRESH questions from the same source.  Requests come from synthetic latent-difficulty
worlds and from cached real MMLU-Pro outcomes of a small LLM under 24 prompt
configurations, searched either exhaustively or by successive halving.  Some requests come
from worlds where all configurations are equally good, or where every outcome is 0; they
are not labelled.  Configuration indices are relabelled at random in every request, so
an index carries no information across requests.

``{"op": "reset", "seed": <int>}``
    Seeds candidate randomness only (the seed never selects the workload).  Exactly one
    reset precedes each episode of consecutive ``report`` calls.  Response: exactly
    ``{"ok": true}`` (no other keys).

``{"op": "report", ...}``  fields:
    n_questions (int N >= 1)      number of benchmark questions in the search sample.
    n_configs (int K >= 2)        number of searched configurations.
    level (float)                 nominal two-sided interval level, always 0.90.
    searcher (str)                "exhaustive": every config is evaluated on all N
                                  questions (log has N*K entries, question-major order);
                                  "halving": successive halving, a sparse log in which
                                  each round evaluates the surviving configs on new
                                  questions and keeps the best half, the selected
                                  config is the last survivor.
    selected_config (int)         index in [0, K) chosen by the searcher (highest mean
                                  search accuracy among survivors; ties -> lowest index).
    log (dict)                    parallel arrays in evaluation order, each encoded as
                                  {"dtype": str, "shape": [M], "encoding":
                                  "base64-little-endian-c-order", "data": base64 str}:
                                    question_idx  uint16, in [0, N)
                                    config_idx    uint8,  in [0, K)
                                    outcome       uint8,  1 = answered correctly, else 0
    subject_code (same encoding)  uint8 array of shape [N]: anonymized question category
                                  (all zeros for synthetic worlds).
    Response: exactly the keys ``estimate``, ``lower``, ``upper`` (finite int/float, not
    bool) with 0 <= lower <= estimate <= upper <= 1.  Any other key set, non-finite
    value, or ordering violation makes that replication invalid (it then receives the
    worst-case score and the episode continues).

Scoring (evaluator-private): interval score at level 0.90,
IS = (upper - lower) + 20 * max(lower - y, 0) + 20 * max(y - upper, 0), where y is the true
accuracy of the selected config on fresh questions; lower IS is better.  Failed or
timed-out replications count as IS = 20.
"""
import base64
import math

_Z90 = 1.6448536269514722
_STATE = {"seed": None}


def _decode(field):
    return base64.b64decode(field["data"])  # bytes; uint8 arrays iterate as ints


def _wilson(p, n, z=_Z90):
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(max(p * (1.0 - p) / n + z * z / (4.0 * n * n), 0.0)) / denom
    return max(0.0, min(center - half, p)), min(1.0, max(center + half, p))


def handle(request):
    op = request.get("op")
    if op == "reset":
        _STATE["seed"] = int(request["seed"])
        return {"ok": True}
    if op != "report":
        raise ValueError("unknown op")
    k = int(request["selected_config"])
    config = _decode(request["log"]["config_idx"])  # uint8: one byte per entry
    outcome = _decode(request["log"]["outcome"])
    hits = n = 0
    for c, o in zip(config, outcome):
        if c == k:
            n += 1
            hits += o
    p = hits / n if n else 0.0
    lo, hi = _wilson(p, n) if n else (0.0, 1.0)
    return {"estimate": p, "lower": lo, "upper": hi}
