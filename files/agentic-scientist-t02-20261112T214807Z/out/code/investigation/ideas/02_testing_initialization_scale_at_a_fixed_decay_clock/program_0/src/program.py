"""Trusted CPU grokking experiment controller: finite JSON handle(request).

Exact keys, no extra response fields, no optional response keys, no tensors or
state transfer. Complete JSON+envelope+LF <16KiB and strictly <64MiB.

reset request: {"op":"reset", "seed":integer>=0}; boolean is not integer.
Return exactly {"ok":true}. Accept arbitrary seeds, clear all episode state.
Seeds initialize randomness only: NEVER select settings or workload by seed.

plan request (all fields required): op="plan", modulus=97 (integer),
operation="addition", width in [32,128,256] (integer),
architecture="two_embeddings_sum_gelu_linear_v1", updates (positive integer),
checkpoints (strictly ascending integer array, first0, last updates),
train_fraction=0.6, precision="float32". Workload comes from these fields,
not seed identity. Exactly one plan follows each reset.
Response exactly {"learning_rate":number in [0.0001,0.01],
"weight_decay":number in [0.1,2], "init_multiplier":number in [0.5,2]}.
All numbers finite, not boolean. Return SAME common configuration for every
width, workload and arbitrary seed, including after source freeze.

Actual trusted training uses two97-by-width embeddings, sum+bias, GELU,
width-by97 projection+bias, full-batch cross-entropy/AdamW. Four matched arms:
chosen configuration, fixed reference, zero decay, matched initial norm.
No architecture, objective, curriculum or adaptive-feedback control provided.
Candidate receives no examples, labels, curves, scores, baseline outputs or
paths. Candidate-reported state/counters/flags are not scientific evidence.
Search eligibility is complete valid execution, not hypothesis agreement;
final claim assessment and required research paper are separate obligations.
Default behavior is deterministic/lightweight and uses only standard Python.
Candidate intervention: use learning rate 0.003 with weight decay 1.0 and
initialization multiplier 1.0, fixed for every permitted request. This speeds
the nominal AdamW multiplicative-decay clock relative to the starter, but also
changes gradient dynamics. The interface does not expose the proposed decay
grid or trajectories, so this controller alone cannot test clock collapse.
"""

LEARNING_RATE = 0.003
WEIGHT_DECAY = 1.0
INIT_MULTIPLIER = 1.0

_ready = False
_planned = False


def handle(request):
    global _ready, _planned
    if type(request) is not dict:
        raise ValueError("request must be a dictionary")
    if request.get("op") == "reset":
        if (set(request) != {"op", "seed"} or type(request["seed"]) is not int
                or request["seed"] < 0):
            raise ValueError("invalid reset")
        _ready, _planned = True, False
        return {"ok": True}
    if request.get("op") == "plan":
        expected = {"op", "modulus", "operation", "width", "architecture", "updates",
                    "checkpoints", "train_fraction", "precision"}
        if not _ready or _planned or set(request) != expected:
            raise ValueError("plan requires exactly one reset")
        if (request["modulus"] != 97 or request["operation"] != "addition"
                or type(request["width"]) is not int or request["width"] not in (32, 128, 256)
                or request["architecture"] != "two_embeddings_sum_gelu_linear_v1"
                or type(request["updates"]) is not int or request["updates"] < 1
                or request["precision"] != "float32" or request["train_fraction"] != .6):
            raise ValueError("invalid public workload")
        checkpoints = request["checkpoints"]
        if (type(checkpoints) is not list or not checkpoints or checkpoints[0] != 0
                or checkpoints[-1] != request["updates"]
                or any(type(step) is not int for step in checkpoints)
                or checkpoints != sorted(set(checkpoints))):
            raise ValueError("invalid checkpoint schedule")
        _planned = True
        return {"learning_rate": LEARNING_RATE, "weight_decay": WEIGHT_DECAY,
                "init_multiplier": INIT_MULTIPLIER}
    raise ValueError("unsupported operation")
