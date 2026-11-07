"""Candidate-owned prompt-bank and honest-report partition policy (CPU, stdlib).

Interface: python_rpc_v1:handle. Every request/response is finite inline JSON.
Keep this entrypoint self-contained or use installed packages: native smoke copies
only the entrypoint into its filesystem sandbox, not neighboring helper modules.
No filesystem exchange, model inference, labels, audit examples, outcome matrices,
baseline outputs, scoring feedback, or host paths are supplied to this process.
Arbitrary nonnegative integer seeds initialize randomness, never workload identity.

Operations (additional request and response fields are forbidden):
  reset: {"op":"reset", "seed": int in [0, 2**63-1]} -> {"ok": true}.
    Initializes a fresh episode's RNG. Exactly one reset per independent episode.
  update: {"op":"update", "arms": int in [1,16], "confidence":0.95,
           "slots":[{"key":str, "stratum":str}, ...]}.
    Exactly one update after reset. Slots are distinct unlabelled content hashes
    (or synthetic slot hashes); length n is a multiple of four. Settings arrive
    through these fields, not through seeds. The same API serves all workloads.
    Returns exactly {"prompts":list[str], "selection":list[str],
                     "report":list[str], "weights":list[number],
                     "tie_order":list[int]}.
    prompts: exactly 16 distinct instruction/format variants, each 1..4096 UTF-8
    bytes, with DEFAULT_PROMPT at index 0. Bank must be identical for every reset,
    seed, episode and workload; only its first `arms` prompts are executed. No
    example-specific rules, answer keys, benchmark lookups, hashes, URLs or IDs.
    Control characters except tab/newline are forbidden. Selection/report are
    nonempty disjoint exhaustive lists of supplied keys, without repetitions.
    Selection size is between n/4 and 3n/4 inclusive. Weights have report length,
    and each equals 1/len(report) within absolute tolerance 1e-12. tie_order is a
    permutation of range(arms), defining highest-score tie priority. No tensor or
    binary values are transferred; there is no state-transfer operation.

The evaluator uses the actual returned partition and prompt texts. It selects the
maximum-accuracy prompt on selection rows, then reports its uniform mean and 95%
Wilson interval on report rows. It privately generates genuine model responses,
owns targets, and compares against fresh audit accuracy (synthetic known truth).
No in-episode feedback/adaptivity is required. Invalid parsed model responses and
context overflow count as incorrect, never disappear. Baselines: fixed, random,
full-sample winner/reuse, same-winner selector reuse, and honest half-split.
Matched constant, copy-arm, contaminated copy-report, effective nonidentity input
permutation and terminal reset/replay controls are evaluator-owned, not self-reports.

Score: 1 - mean report MSE. Equal weights: synthetic/real families, n/K cases,
seeds, four synthetic regimes and their replicates. Replay is a control, not an
extra scored replicate. Missing episodes/controls retain MSE=1, accuracy=coverage=0,
bias=optimism=width=reversal=failure=1. Search and final correct separately require
complete valid experiments/controls and deterministic replay, NOT superiority,
significance or a positive finding. Publication additionally requires a supported
paper and reproducibility code; search eligibility does not certify these claims.
Methods may change this policy, not the estimator or hidden evaluation objectives.
All complete JSON messages must stay below 8 MiB operationally and 64 MiB on wire.
"""
import random

DEFAULT_PROMPT = 'Answer the multiple-choice question. Return only the correct option letter A through J.'
_random = None
_updated = False

def prompt_bank():
    variants = [
        'Choose the best answer. Output only its capital letter.',
        'Solve the question carefully, then give only the option letter.',
        'Identify the correct option. Respond with a single capital letter.',
        'Consider each option and select the best one. Print the letter only.',
        'Your answer must consist solely of the correct choice letter.',
        'Read the question and choices. Return the correct letter, no explanation.',
        'Select one answer from the provided options. Give only its letter.',
        'Please answer this multiple-choice question using one capital letter.',
        'Determine which option is most accurate. Output the letter only.',
        'Choose the single best option; omit all text except its capital letter.',
        'Evaluate the alternatives. Give the correct answer as its option letter.',
        'Respond to this question with the letter of the best available answer.',
        'Find the right answer among the listed choices. Return only its letter.',
        'Pick the most appropriate answer and output its capital letter alone.',
        'Answer accurately. Use only the capital letter identifying your choice.',
    ]
    return [DEFAULT_PROMPT] + variants

def handle(request):
    global _random, _updated
    if type(request) is not dict:
        raise ValueError('request must be an object')
    if request.get('op') == 'reset':
        if set(request) != {'op', 'seed'} or type(request['seed']) is not int or not 0 <= request['seed'] < 2**63:
            raise ValueError('invalid reset')
        _random = random.Random(request['seed'])
        _updated = False
        return {'ok': True}
    if request.get('op') != 'update' or set(request) != {'op', 'arms', 'slots', 'confidence'} or _random is None or _updated:
        raise ValueError('expected one update after reset')
    arms = request['arms']
    slots = request['slots']
    if type(arms) is not int or not 1 <= arms <= 16 or request['confidence'] != .95 or type(slots) is not list or len(slots) < 4 or len(slots) % 4:
        raise ValueError('invalid workload')
    keys = [slot['key'] for slot in slots]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate slots')
    selection_size = len(slots) // 4
    grouped_keys = {}
    for slot in slots:
        grouped_keys.setdefault(slot['stratum'], []).append(slot['key'])
    strata = sorted(grouped_keys)
    _random.shuffle(strata)
    offset = _random.randrange(4)
    cumulative = 0
    selection = []
    report = []
    for stratum in strata:
        group_keys = sorted(grouped_keys[stratum])
        group_size = len(group_keys)
        quota = (cumulative + group_size + offset) // 4 - (cumulative + offset) // 4
        cumulative += group_size
        _random.shuffle(group_keys)
        selection.extend(group_keys[:quota])
        report.extend(group_keys[quota:])
    assert len(selection) == selection_size
    assert 4 * len(report) == 3 * len(slots)
    assert selection and report
    assert set(selection).isdisjoint(report)
    assert set(selection) | set(report) == set(keys)
    prompts = prompt_bank()
    assert len(prompts) == 16 and len(set(prompts)) == 16
    assert prompts[0] == DEFAULT_PROMPT
    tie_order = list(range(arms))
    _updated = True
    return {'prompts': prompts, 'selection': selection, 'report': report, 'weights': [1.0 / len(report)] * len(report), 'tie_order': tie_order}
