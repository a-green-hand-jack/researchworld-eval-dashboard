"""Numbers transcribed from the experimental log (/initial-state/inputs/0/INSTRUCTIONS.md, section 2).
Order: (test acc, remaining acc, forget acc, MIA score), all in %. Single runs; the log reports no seeds."""

# CIFAR-10, forget-size ablation: size -> (Retrained, Unlearned(-))
FORGET = {
    5:  ((73, 74, 73, 49.4), (73, 74, 73, 49.4)),
    10: ((72, 74, 72, 50.0), (70, 71, 68, 51.4)),
    15: ((73, 75, 73, 50.0), (59, 60, 59, 55.8)),
}
# CIFAR-10, perturbation-count ablation (one shared Retrained row)
PERT_RETRAINED = (72, 74, 72, 50.0)
PERT = {250: (57, 58, 57, 56.2), 500: (70, 71, 68, 51.4), 1000: (72, 74, 71, 49.0)}
# CIFAR-10, L2 lambda ablation (one shared Retrained row)
LAM_RETRAINED = (72, 74, 72, 50.0)
LAM = {0: (70, 71, 68, 51.4), 0.0005: (71, 72, 71, 49.8), 0.001: (72, 73, 72, 50.9)}
# CIFAR-100, ResNet-18 mixed linear network: size -> (Retrained, Unlearned(+), Unlearned(-))
MIXED = {
    20: ((62.2, 65.7, 62.6, 50.0), (60.1, 63.4, 59.3, 50.4), (60.0, 70.0, 63.2, 50.8)),
    15: ((63.1, 68.9, 63.3, 50.2), (61.9, 67.9, 62.2, 50.7), (61.4, 70.1, 62.2, 51.7)),
    10: ((63.7, 72.0, 63.9, 50.0), (63.3, 72.5, 64.9, 51.0), (62.8, 70.1, 61.2, 52.3)),
}
# CIFAR-10, linear classifier, 10% forget, source-free baselines
BASE = [
    ("Retrained",     (72, 74, 72, 50.0)),
    ("NegGrad",       (51.9, 53.2, 51.2, 48.0)),
    ("Random Labels", (20.6, 21.6, 21.4, 47.0)),
    ("JiT",           (52.1, 53.1, 51.1, 49.1)),
    ("Adversarial",   (51.5, 52.7, 51.0, 50.0)),
    ("Unlearned($-$)", (70, 71, 68, 51.4)),
]

def gap(a, b):
    """Absolute gap per metric in percentage points (rounded to the log's 0.1 resolution)."""
    return tuple(round(abs(x - y), 1) for x, y in zip(a, b))
