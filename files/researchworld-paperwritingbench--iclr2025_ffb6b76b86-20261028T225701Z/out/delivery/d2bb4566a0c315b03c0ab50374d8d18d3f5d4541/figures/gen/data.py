"""Numbers transcribed verbatim from the experimental log (Tables 1-4 of the log).
None = reported N/A / not run in the log."""

# Table 1: CodeLlama-7b, HumanEval Random Span infilling, pass rates
T1_COLS = ["PSM greedy", "PSM @10", "SPM greedy", "SPM @10"]
T1 = [
    ("Token-level", [64.9, 84.0, 45.0, 66.5]),
    ("\\quad + healing", [None, None, 62.7, 83.8]),
    ("\\quad + alignment", [None, None, 63.0, 82.9]),
    ("Byte-level (ours)", [65.7, 84.1, 63.9, 84.3]),
]

# Table 2: general LMs. benchmark -> (token, byte)
T2_BENCH = ["MMLU", "PIQA", "NQ", "TriviaQA", "GSM8K"]
T2 = {
    "Llama2-7B": {"MMLU": (45.4, 45.7), "PIQA": (78.1, 78.2), "NQ": (25.0, 23.4), "TriviaQA": (58.4, 58.1), "GSM8K": (15.1, 12.5)},
    "Yi-1.5-6B": {"MMLU": (63.4, 63.4), "PIQA": (78.5, 78.5), "NQ": (22.8, 22.7), "TriviaQA": (53.7, 53.4), "GSM8K": (61.3, 61.5)},
    "Mistral-7B-v0.3": {"MMLU": (62.1, 62.1), "PIQA": (80.1, 80.3), "NQ": (28.5, 28.8), "TriviaQA": (63.6, 63.5), "GSM8K": (39.0, 39.0)},
}
T2_VOTE = {"MMLU": 62.1, "PIQA": 80.1, "NQ": None, "TriviaQA": None, "GSM8K": None}
T2_ENS = {"MMLU": 65.4, "PIQA": 80.7, "NQ": 30.0, "TriviaQA": 64.2, "GSM8K": 55.8}

# Table 3: code LMs, pass@1. benchmark -> (token, byte)
T3_BENCH = ["HumanEval", "MBPP"]
T3 = {
    "CodeLlama-7b": {"HumanEval": (32.3, 28.7), "MBPP": (40.6, 42.4)},
    "CodeLlama-13b": {"HumanEval": (35.8, 33.5), "MBPP": (47.6, 47.4)},
    "Yi-Coder-1.5B": {"HumanEval": (38.4, 36.5), "MBPP": (52.8, 53.6)},
}
T3_ENS = {"HumanEval": 42.1, "MBPP": 53.6}

# Table 4: beam width ablation (byte-level, FIM pass rate on HumanEval)
T4 = [(1, 65.7, 63.9), (2, 66.8, 65.9), (4, 67.7, 66.8)]
