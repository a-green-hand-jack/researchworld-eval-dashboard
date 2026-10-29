"""Derived quantities and claim checks for the numbers in experimental_log.md.

Inputs: data/table*.csv, transcribed verbatim from
/initial-state/inputs/0/INSTRUCTIONS.md (section [EXPERIMENTAL LOGS], Tables 1-4).
Output: derived.json (all derived numbers; pp = absolute percentage points).
"""
import json, pathlib
import pandas as pd

D = pathlib.Path(__file__).parent / "data"
t1 = pd.read_csv(D / "table1_fim.csv", index_col=0)
t2 = pd.read_csv(D / "table2_general.csv", index_col=0)
t3 = pd.read_csv(D / "table3_code.csv", index_col=0)
t4 = pd.read_csv(D / "table4_beam.csv", index_col=0)
r = lambda x: round(float(x), 2)
out = {}

# Table 1: FIM
tok, byte = t1.loc["token"], t1.loc["byte"]
out["fim"] = {
    "byte_minus_token_pp": {c: r(byte[c] - tok[c]) for c in t1.columns},
    "byte_over_token_relative_pct": {c: r(100 * (byte[c] / tok[c] - 1)) for c in t1.columns},
    "token_psm_to_spm_drop_pp": {"greedy": r(tok.psm_greedy - tok.spm_greedy), "at10": r(tok.psm_at10 - tok.spm_at10)},
    "byte_psm_to_spm_drop_pp": {"greedy": r(byte.psm_greedy - byte.spm_greedy), "at10": r(byte.psm_at10 - byte.spm_at10)},
    "spm_gap_recovered_vs_psm_token_pct": r(100 * (byte.spm_greedy - tok.spm_greedy) / (tok.psm_greedy - tok.spm_greedy)),
    "byte_minus_healing_pp": {c: r(byte[c] - t1.loc["token_healing", c]) for c in ["spm_greedy", "spm_at10"]},
    "byte_minus_alignment_pp": {c: r(byte[c] - t1.loc["token_alignment", c]) for c in ["spm_greedy", "spm_at10"]},
}

# Table 2/3: byte minus token per model and benchmark; ensemble vs best member
def per_model(t, benches, members):
    res = {}
    for b in benches:
        d = {m: r(t.loc[m, f"{b}_byte"] - t.loc[m, f"{b}_token"]) for m in members}
        best_tok = t.loc[members, f"{b}_token"].astype(float)
        best_byte = t.loc[members, f"{b}_byte"].astype(float)
        ens = t.loc["Top-2 Ensemble", f"{b}_byte"]
        res[b] = {
            "byte_minus_token_pp": d,
            "best_single_token": [best_tok.idxmax(), r(best_tok.max())],
            "best_single_byte": [best_byte.idxmax(), r(best_byte.max())],
            "top2_by_byte": list(best_byte.sort_values(ascending=False).index[:2]),
            "ensemble": r(ens),
            "ensemble_minus_best_token_pp": r(ens - best_tok.max()),
            "ensemble_minus_best_byte_pp": r(ens - best_byte.max()),
        }
    return res
gm = ["Llama2-7B", "Yi-1.5-6B", "Mistral-7B-v0.3"]
out["general"] = per_model(t2, ["mmlu", "piqa", "nq", "triviaqa", "gsm8k"], gm)
for b in ["mmlu", "piqa"]:
    v = t2.loc["Voting (top-2)", f"{b}_byte"]
    out["general"][b]["voting"] = r(v)
    out["general"][b]["ensemble_minus_voting_pp"] = r(t2.loc["Top-2 Ensemble", f"{b}_byte"] - v)
cm = ["CodeLlama2-7b", "CodeLlama2-13b", "Yi-Coder-1.5B"]
out["code"] = per_model(t3, ["humaneval", "mbpp"], cm)
out["gsm8k_yi_minus_mistral_pp"] = {"token": r(t2.loc["Yi-1.5-6B", "gsm8k_token"] - t2.loc["Mistral-7B-v0.3", "gsm8k_token"]),
                                    "byte": r(t2.loc["Yi-1.5-6B", "gsm8k_byte"] - t2.loc["Mistral-7B-v0.3", "gsm8k_byte"])}
# sign counts of byte - token over all (model, benchmark) cells
cells = [v for sec in ("general", "code") for b in out[sec].values() for v in b["byte_minus_token_pp"].values()]
out["byte_vs_token_sign_counts"] = {"n": len(cells), "better": sum(c > 0 for c in cells),
                                    "equal": sum(c == 0 for c in cells), "worse": sum(c < 0 for c in cells),
                                    "min_pp": min(cells), "max_pp": max(cells)}
# Table 4: beam
out["beam"] = {m: {"w2_minus_w1_pp": r(t4.loc[2, m] - t4.loc[1, m]), "w4_minus_w1_pp": r(t4.loc[4, m] - t4.loc[1, m]),
                   "w4_over_w1_relative_pct": r(100 * (t4.loc[4, m] / t4.loc[1, m] - 1))} for m in t4.columns}
out["beam"]["w1_equals_table1_byte_greedy"] = bool(t4.loc[1, "psm"] == byte.psm_greedy and t4.loc[1, "spm"] == byte.spm_greedy)

(pathlib.Path(__file__).parent / "derived.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
