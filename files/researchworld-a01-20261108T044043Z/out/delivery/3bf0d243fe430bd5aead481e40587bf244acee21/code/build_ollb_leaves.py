"""Build the OLLB model x leaf-task matrix for the top-N models (completeness gate for the leaf-task run).
Input: the files of code/fetch_ollb_leaves.py.  Rule for models with several result files: among the files whose six task-level raw
metrics equal the `Raw` columns of the processed leaderboard table (|diff| < 1e-6), take the latest file name; a model with no
matching file or with a missing leaf is *not covered* (no imputation).  Leaf scores: raw accuracy normalised as the leaderboard does
(subtract the random baseline 1/num_choices, rescale, clip at 0; MATH/IFEval floor 0), on the 0..100 scale.
Usage: python3 code/build_ollb_leaves.py RAWDIR OUT_CSV OUT_REPORT_JSON"""
import sys, json, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti.data import load, OLLB_TASKS

raw_dir, out_csv, out_rep = map(pathlib.Path, sys.argv[1:4])
BBH = {"boolean_expressions": 2, "causal_judgement": 2, "date_understanding": 6, "disambiguation_qa": 3, "formal_fallacies": 2,
       "geometric_shapes": 11, "hyperbaton": 2, "logical_deduction_five_objects": 5, "logical_deduction_seven_objects": 7,
       "logical_deduction_three_objects": 3, "movie_recommendation": 6, "navigate": 2, "object_counting": None, "penguins_in_a_table": 5,
       "reasoning_about_colored_objects": None, "ruin_names": 6, "salient_translation_error_detection": 6, "snarks": 2,
       "sports_understanding": 2, "temporal_sequences": 4, "tracking_shuffled_objects_five_objects": 5,
       "tracking_shuffled_objects_seven_objects": 7, "tracking_shuffled_objects_three_objects": 3, "web_of_lies": 2}
# number of answer options not fixed by the config of the probe file are read from its doc_to_choice length (set below)
LEAF = {}   # name -> (result key, metric, floor)
for k, n in BBH.items(): LEAF["bbh_" + k] = (f"leaderboard_bbh_{k}", "acc_norm,none", n)
for k in ("diamond", "extended", "main"): LEAF["gpqa_" + k] = (f"leaderboard_gpqa_{k}", "acc_norm,none", 4)
for k in ("algebra", "counting_and_prob", "geometry", "intermediate_algebra", "num_theory", "prealgebra", "precalculus"):
    LEAF["math_" + k] = (f"leaderboard_math_{k}_hard", "exact_match,none", 0)
for k, n in (("murder_mysteries", 2), ("object_placements", 5), ("team_allocation", 3)):
    LEAF["musr_" + k] = (f"leaderboard_musr_{k}", "acc_norm,none", n)
LEAF["mmlu_pro"] = ("leaderboard_mmlu_pro", "acc,none", 10)
LEAF["ifeval"] = ("leaderboard_ifeval", None, 0)
# the two BBH tasks whose option count differs from the letter list length are filled from the config of the probe file
extra = json.load(open(pathlib.Path(sys.argv[0]).resolve().parent.parent / "data/processed/ollb_leaf_choices.json"))
for k in ("object_counting", "reasoning_about_colored_objects"): LEAF["bbh_" + k] = (f"leaderboard_bbh_{k}", "acc_norm,none", extra[k])
# how the leaderboard's `Raw` column of each task is formed from a result file: IFEval = mean of the two strict accuracies, BBH and
# MUSR = unweighted mean of the leaf accuracies (not lm-eval's sample-weighted aggregate), MATH / GPQA / MMLU-PRO = the aggregate
TASK_RAW = {"IFEval": None, "BBH": "leafmean:bbh_", "MATH Lvl 5": ("leaderboard_math_hard", "exact_match,none"),
            "GPQA": ("leaderboard_gpqa", "acc_norm,none"), "MUSR": "leafmean:musr_", "MMLU-PRO": ("leaderboard_mmlu_pro", "acc,none")}

def val(r, key, metric):
    if key == "leaderboard_ifeval":
        v = r.get(key)
        return None if v is None else (v["prompt_level_strict_acc,none"] + v["inst_level_strict_acc,none"]) / 2
    v = r.get(key, {}).get(metric)
    return v if isinstance(v, (int, float)) else None

def norm(raw, n):
    if raw is None: return np.nan
    f = 0.0 if not n else 1.0 / n
    return 100.0 * max(raw - f, 0.0) / (1 - f)

X, names, _, meta = load("ollb")
meta = meta.set_index("fullname")
order = np.argsort(-X.mean(axis=1), kind="stable")[:500]
rank_names = [names[i] for i in order]
files = {}
for line in open(raw_dir / "leaves.jsonl"):
    r = json.loads(line); files.setdefault(r["model"], []).append(r)
rows, rep, why = [], {"n_models": len(rank_names)}, {}
for rk, m in enumerate(rank_names, 1):
    fs = sorted(files.get(m, []), key=lambda r: r["file"]); status = "no_file"; chosen = None
    if fs:
        status = "no_matching_file"
        for r in fs[::-1]:                      # latest first
            ok = True
            for t, spec in TASK_RAW.items():
                if spec is None: got = val(r["results"], "leaderboard_ifeval", None)
                elif isinstance(spec, str):
                    lv = [val(r["results"], LEAF[k][0], LEAF[k][1]) for k in LEAF if k.startswith(spec[9:])]
                    got = None if any(v is None for v in lv) else float(np.mean(lv))
                else: got = val(r["results"], *spec)
                ref = meta.loc[m, t + " Raw"]
                if got is None or abs(got - ref) > 1e-6: ok = False; break
            if ok: chosen = r; break
    if chosen is not None:
        raws = {k: val(chosen["results"], key, met) for k, (key, met, n) in LEAF.items()}
        if any(v is None for v in raws.values()): status = "missing_leaf"; chosen = None
        else: status = "ok"
    why[m] = status
    if chosen is not None:
        row = {"model": m, "rank_mean6": rk, "file": chosen["file"], "n_files": len(fs)}
        row.update({k: norm(raws[k], LEAF[k][2]) for k in LEAF}); rows.append(row)
d = pd.DataFrame(rows)
cnt = pd.Series(why).value_counts().to_dict(); rep["status_counts"] = cnt
rep["covered"] = int(len(d)); rep["missing_fraction"] = 1 - len(d) / len(rank_names)
rep["n_leaves"] = len(LEAF)
rep["models_with_several_files"] = int(sum(len(files.get(m, [])) > 1 for m in rank_names))
# task-level check: mean of the normalised leaves against the processed normalised task score
chk = {}
for t, pre in (("BBH", "bbh_"), ("GPQA", "gpqa_"), ("MUSR", "musr_"), ("MMLU-PRO", "mmlu_pro")):
    cols = [c for c in LEAF if c.startswith(pre)]
    rec = d[cols].mean(axis=1).values; ref = meta.loc[d.model, t].values
    chk[t] = {"max_abs_diff": float(np.max(np.abs(rec - ref))), "median_abs_diff": float(np.median(np.abs(rec - ref)))} if len(d) else None
rep["task_level_check_vs_contents"] = chk
d.to_csv(out_csv, index=False); json.dump(rep, open(out_rep, "w"), indent=1); print(json.dumps(rep, indent=1))
