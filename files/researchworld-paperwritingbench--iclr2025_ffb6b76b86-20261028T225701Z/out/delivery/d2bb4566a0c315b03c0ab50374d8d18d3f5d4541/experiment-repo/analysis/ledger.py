"""Transcribe the tables of experimental_log.md (INSTRUCTIONS.md, [EXPERIMENTAL LOGS]) and derive
the quantities the paper's claims rest on. Writes results/*.csv and results/claims_check.md.
Source numbers are copied verbatim; nothing is re-measured here."""
import csv, math, json, os
OUT = os.path.join(os.path.dirname(__file__), "..", "results")

# Table 1 (CodeLlama-7b, HumanEval Random Span), pass rate %
T1 = {
 "Token-level":            dict(PSM_greedy=64.9, PSM_at10=84.0, SPM_greedy=45.0, SPM_at10=66.5),
 "Token-level + Healing":  dict(PSM_greedy=None, PSM_at10=None, SPM_greedy=62.7, SPM_at10=83.8),
 "Token-level + Alignment":dict(PSM_greedy=None, PSM_at10=None, SPM_greedy=63.0, SPM_at10=82.9),
 "Byte-level":             dict(PSM_greedy=65.7, PSM_at10=84.1, SPM_greedy=63.9, SPM_at10=84.3),
}
# Table 2: model -> bench -> (token, byte)
T2 = {
 "Llama2-7B":      dict(MMLU=(45.4,45.7), PIQA=(78.1,78.2), NQ=(25.0,23.4), TriviaQA=(58.4,58.1), GSM8K=(15.1,12.5)),
 "Yi-1.5-6B":      dict(MMLU=(63.4,63.4), PIQA=(78.5,78.5), NQ=(22.8,22.7), TriviaQA=(53.7,53.4), GSM8K=(61.3,61.5)),
 "Mistral-7B-v0.3":dict(MMLU=(62.1,62.1), PIQA=(80.1,80.3), NQ=(28.5,28.8), TriviaQA=(63.6,63.5), GSM8K=(39.0,39.0)),
}
T2_VOTE = dict(MMLU=62.1, PIQA=80.1)
T2_ENS  = dict(MMLU=65.4, PIQA=80.7, NQ=30.0, TriviaQA=64.2, GSM8K=55.8)
# Table 3
T3 = {
 "CodeLlama2-7b": dict(HumanEval=(32.3,28.7), MBPP=(40.6,42.4)),
 "CodeLlama2-13b":dict(HumanEval=(35.8,33.5), MBPP=(47.6,47.4)),
 "Yi-Coder-1.5B": dict(HumanEval=(38.4,36.5), MBPP=(52.8,53.6)),
}
T3_ENS = dict(HumanEval=42.1, MBPP=53.6)
# Table 4
T4 = {1:(65.7,63.9), 2:(66.8,65.9), 4:(67.7,66.8)}

# Benchmark sizes are NOT in the log: external, from the benchmarks' public definitions; used only for
# rough binomial standard errors (planning estimate, flagged as such in every output).
N_EXT = dict(HumanEval=164, MBPP=500, MMLU=14042, PIQA=1838, NQ=3610, TriviaQA=17944, GSM8K=1319, HE_RandomSpan=1640)
def se(p, n): return 100*math.sqrt((p/100)*(1-p/100)/n)

def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)

# --- tidy ledger of all log numbers
rows = []
for m, d in T1.items():
    for k, v in d.items(): rows.append(["T1", "CodeLlama-7b", "HE_RandomSpan", m, k, v])
for m, d in T2.items():
    for b, (t, y) in d.items():
        rows += [["T2", m, b, "token", "acc", t], ["T2", m, b, "byte", "acc", y]]
for b, v in T2_VOTE.items(): rows.append(["T2", "Voting(top-2)", b, "byte", "acc", v])
for b, v in T2_ENS.items(): rows.append(["T2", "Top-2 Ensemble", b, "byte", "acc", v])
for m, d in T3.items():
    for b, (t, y) in d.items():
        rows += [["T3", m, b, "token", "pass@1", t], ["T3", m, b, "byte", "pass@1", y]]
for b, v in T3_ENS.items(): rows.append(["T3", "Top-2 Ensemble", b, "byte", "pass@1", v])
for k, (p, s) in T4.items():
    rows += [["T4", "CodeLlama-7b", "HE_FIM", f"beam{k}", "PSM", p], ["T4", "CodeLlama-7b", "HE_FIM", f"beam{k}", "SPM", s]]
w("log_numbers.csv", ["table","model","benchmark","method","metric","value"], rows)

# --- byte - token differences per model/benchmark
drows = []
for tab, T, ben in (("T2", T2, None), ("T3", T3, None)):
    for m, d in T.items():
        for b, (t, y) in d.items():
            n = N_EXT[b]
            s = math.hypot(se(t, n), se(y, n))  # unpaired => conservative upper bound for paired diff
            drows.append([tab, m, b, t, y, round(y-t,1), round(100*(y-t)/t,1), round(s,2)])
w("byte_minus_token.csv", ["table","model","benchmark","token","byte","diff_pts","diff_rel_pct","unpaired_se_pts(ext_n)"], drows)

# --- ensemble vs best member (token-level best, byte-level best)
erows = []
def ens(tab, T, E, ben_list):
    for b in ben_list:
        bt = max((d[b][0], m) for m, d in T.items()); by = max((d[b][1], m) for m, d in T.items())
        # top-2 byte members, by byte accuracy
        top2 = sorted(((d[b][1], m) for m, d in T.items()), reverse=True)[:2]
        gap = top2[0][0]-top2[1][0]
        erows.append([tab, b, E[b], by[0], by[1], round(E[b]-by[0],1), bt[0], bt[1], round(E[b]-bt[0],1),
                      "+".join(m for _, m in top2), round(gap,1)])
ens("T2", T2, T2_ENS, ["MMLU","PIQA","NQ","TriviaQA","GSM8K"])
ens("T3", T3, T3_ENS, ["HumanEval","MBPP"])
w("ensemble_vs_best.csv", ["table","benchmark","ensemble","best_byte","best_byte_model","ens-best_byte","best_token","best_token_model","ens-best_token","top2_by_byte","top2_gap_pts"], erows)

# --- FIM
f = []
for mode in ("PSM","SPM"):
    for k in ("greedy","at10"):
        t = T1["Token-level"][f"{mode}_{k}"]; y = T1["Byte-level"][f"{mode}_{k}"]
        f.append([mode, k, t, y, round(y-t,1), round(100*(y-t)/t,1), round(math.hypot(se(t,1640),se(y,1640)),2)])
w("fim_byte_vs_token.csv", ["mode","metric","token","byte","diff_pts","diff_rel_pct","unpaired_se_pts(n=1640 ext)"], f)
a = [[k, p, s, round(p-T4[1][0],1), round(s-T4[1][1],1)] for k,(p,s) in T4.items()]
w("beam_ablation.csv", ["beam","PSM","SPM","PSM_gain_vs_beam1","SPM_gain_vs_beam1"], a)

# --- claims check
L = []
def chk(claim, val, verdict): L.append(f"| {claim} | {val} | {verdict} |")
chk('"18% improvement in SPM FIM vs standard token baseline"',
    f"greedy 63.9 vs 45.0: +18.9 pts (+{100*18.9/45:.1f}% relative); @10 84.3 vs 66.5: +17.8 pts (+{100*17.8/66.5:.1f}% rel.)",
    "Supported as ~18-19 ABSOLUTE points; a 'relative' reading would be wrong (42% rel. greedy). State as points.")
chk('"SPM greedy recovered to 63.9, comparable to PSM"', "PSM byte 65.7 vs SPM byte 63.9: gap 1.8 pts (token: 19.9 pts)", "Supported; gap shrinks 19.9 -> 1.8 pts, not zero.")
chk('"Byte-level consistently outperforms healing/alignment"', "SPM greedy +1.2 / +0.9 pts; SPM@10 +0.5 / +1.4 pts",
    "Direction holds in all 4 cells, but margins are 0.5-1.4 pts; with n=1640 (external) unpaired SE ~1.2 pts => NOT individually distinguishable without paired test. Say 'slightly higher', not 'significantly'.")
chk('"Unexpected PSM greedy gain 65.7 vs 64.9"', "+0.8 pts; PSM@10 +0.1", "Within noise (SE ~1.7 pts unpaired); report as 'on par/slightly higher'.")
chk('"Ensemble improves HumanEval by up to 3.7%"', "42.1 - 38.4 (best member, Yi-Coder token) = 3.7 pts; vs best byte member 36.5: +5.6 pts",
    "Supported as 3.7 ABSOLUTE pts vs best TOKEN-level member; vs best byte-level member it is +5.6. HumanEval n=164 => 3.7 pts = 6 problems, SE ~3.8 pts: suggestive only. Log says ensemble of Yi-Coder + CodeLlama2-13b.")
chk('"Ensemble generally outperforms members (MMLU, PIQA, TriviaQA)"',
    "MMLU 65.4 vs 63.4 (+2.0); PIQA 80.7 vs 80.3 byte / 80.1 token (+0.4/+0.6); TriviaQA 64.2 vs 63.5 byte / 63.6 token (+0.7/+0.6); NQ 30.0 vs 28.8 byte (+1.2)",
    "Supported in direction. MMLU gain is the only one clearly > noise; PIQA/TriviaQA gains <= 0.7 pts are within SE (~1 pt PIQA, ~0.4 TriviaQA).")
chk('"MBPP ensemble"', "ensemble 53.6 = best byte member Yi-Coder 53.6 (+0.8 vs its token 52.8)", "NO gain over best byte-level member; do not claim MBPP ensemble improvement.")
chk('"Divergence limitation GSM8K (Yi outperforms Mistral by 20%)"', "Yi 61.5 vs Mistral 39.0 byte (22.5 pts; 22.3 token); ensemble 55.8 < 61.5 (-5.7 pts)",
    "Gap is ~22 pts (log says 20%); ensemble worse than best member: report as negative result. NB: top-2 by byte accuracy on GSM8K = Yi + Mistral; Llama2 (12.5) excluded.")
chk('Byte vs token on single models (Table 2)', "Within +-0.3 pts on 13 of 15 cells; exceptions Llama2-7B NQ -1.6 and GSM8K -2.6",
    "Byte conversion is approximately lossless on benchmarks except Llama2-7B NQ/GSM8K; report those honestly.")
chk('Byte vs token on code (Table 3)', "HumanEval@1: -3.6 (CL-7b), -2.3 (CL-13b), -1.9 (Yi-Coder); MBPP: +1.8, -0.2, +0.8",
    "NEGATIVE: byte-level lowers HumanEval@1 for all 3 models (mean -2.6 pts) -- not mentioned in the log's qualitative notes. Must be reported; plausible but untested explanation: not given in log, so label as hypothesis.")
chk('"Beam width up to ~2.9% improvement; peak 67.7 PSM"', "PSM 65.7->67.7 (+2.0); SPM 63.9->66.8 (+2.9)", "Supported: +2.9 is the SPM gain (points), +2.0 PSM; monotone in beam width. Table 4 is HumanEval (random span) pass rate, greedy-type single metric; beam cost not logged.")
chk('Table 1 vs Table 4 consistency', "beam 1: PSM 65.7 / SPM 63.9 = Table 1 byte greedy", "Consistent.")
chk('Naming', "Log uses 'CodeLlama-7b' (Table 1), 'CodeLlama2-7b' / 'CodeLlama2-13b' (Table 3, setup)", "Ambiguous; use as in log per table or treat as CodeLlama-7b/13b -- flag to paper-repo; do not invent versions.")
chk('Statistics', "single run, no seeds/CI/paired tests in log", "All gaps <~2 pts on small benchmarks should be described descriptively; no significance claims.")
hdr = ("# Claims check against experimental log\n\nGenerated by `analysis/ledger.py`. Source: `[EXPERIMENTAL LOGS]` in `/initial-state/inputs/0/INSTRUCTIONS.md`.\n"
       "Benchmark sizes used for the rough SEs are NOT from the log (external public sizes: "+json.dumps(N_EXT)+"); they are planning estimates, "
       "unpaired binomial SEs, indicative only.\n\n| Claim in log | Numbers | Verdict / how to word it |\n|---|---|---|\n")
open(os.path.join(OUT, "claims_check.md"), "w").write(hdr + "\n".join(L) + "\n")
