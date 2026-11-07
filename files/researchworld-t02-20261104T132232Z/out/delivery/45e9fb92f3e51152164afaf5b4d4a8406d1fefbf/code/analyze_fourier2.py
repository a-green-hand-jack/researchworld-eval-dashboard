"""Selection-free sparsity timing (E12b): python3 analyze_fourier2.py OUT_PREFIX DIR:LABEL [...]
From the snapshots of fourier.py (steps <= 1000, then every 150), per run:
  emb_pr, logit_pr   participation ratio 1/sum(q^2) of the power spectrum of the token embedding (28.1 for a random embedding, 5 for a
                     5-frequency solution with equal power) and of the 2-D DFT of the logits over (a, b) (p-1)^2 components; no frequency
                     is chosen and no later snapshot is used for the value at a step;
  t_half_*           first snapshot at which log PR has covered half of the way from its first to its last snapshot value (the run's own scale);
  t_abs_*            first snapshot with emb_pr <= 15 (half the random-embedding value) / logit_pr <= 330 (a tenth of the random-logit value, 3300);
  position           (t_event - t_fit99)/(t_gen99 - t_fit99): 0 at the fit, 1 at the generalisation, < 0 before the fit, > 1 after t_gen.
and the same for the key-frequency measure of E12 (t_sp_half, restricted loss < 1.0), recomputed on the same runs for comparison.
Output OUT_PREFIX_runs.csv, OUT_PREFIX_summary.csv (median, min, max over seeds; n)."""
import glob, json, sys
import numpy as np, pandas as pd

def first(st, cond):
    i = np.flatnonzero(cond); return float(st[i[0]]) if len(i) else np.nan

def half_time(st, v):
    lv = np.log(v); h = lv[0] + 0.5 * (lv[-1] - lv[0]); return first(st, lv <= h) if lv[-1] < lv[0] else np.nan

rows = []
for spec in sys.argv[2:]:
    d, label = spec.rsplit(":", 1)
    for f in sorted(glob.glob(d + "/*.json")):
        r = json.load(open(f)); R = pd.DataFrame(r["rows"]); s = r["summary"]; st = R.step.values; c = r["config"]
        tf, tg = s["t_fit99"], s["t_gen99"]
        ev = {"t_half_emb": half_time(st, R.emb_pr.values), "t_half_logit": half_time(st, R.logit_pr.values),
              "t_abs_emb": first(st, R.emb_pr.values <= 15), "t_abs_logit": first(st, R.logit_pr.values <= 330),
              "t_sp_half": first(st, R.s_top5.values >= R.s_top5.iloc[0] + 0.5 * (R.s_top5.iloc[-1] - R.s_top5.iloc[0])),
              "t_rs_1": first(st, R.loss_restricted.values < 1.0)}
        row = {"label": label, "width": c["width"], "seed": c["seed"], "t_fit99": tf, "t_gen99": tg,
               "emb_pr_first": R.emb_pr.iloc[0], "emb_pr_last": R.emb_pr.iloc[-1], "logit_pr_first": R.logit_pr.iloc[0], "logit_pr_last": R.logit_pr.iloc[-1], **ev}
        for nm in ("emb_pr", "logit_pr"):
            row[nm + "_at_fit"] = float(np.interp(tf, st, R[nm])) if tf is not None else np.nan
            row[nm + "_at_gen"] = float(np.interp(tg, st, R[nm])) if tg is not None else np.nan
        for k, v in ev.items():
            row["pos_" + k[2:]] = (v - tf) / (tg - tf) if (tf is not None and tg is not None and tg > tf) else np.nan
        rows.append(row)
D = pd.DataFrame(rows).sort_values(["label", "width", "seed"]); D.to_csv(sys.argv[1] + "_runs.csv", index=False)
g = D.groupby(["label", "width"]); S = g.median(numeric_only=True).drop(columns="seed")
S = S.join(g[[c for c in D.columns if c.startswith("pos_")]].min().add_suffix("_min")).join(g[[c for c in D.columns if c.startswith("pos_")]].max().add_suffix("_max"))
S["n"] = g.size(); S.to_csv(sys.argv[1] + "_summary.csv")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(S[["n", "t_fit99", "t_gen99", "emb_pr_first", "emb_pr_at_fit", "emb_pr_at_gen", "emb_pr_last", "logit_pr_first", "logit_pr_at_fit", "logit_pr_at_gen", "logit_pr_last"]].round(1))
print(S[["n", "pos_half_emb", "pos_half_logit", "pos_abs_emb", "pos_abs_logit", "pos_sp_half", "pos_rs_1"]].round(2))
