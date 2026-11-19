"""Summary of the Fourier-sparsity runs (E12): python3 analyze_fourier.py OUT_PREFIX DIR:LABEL [...]
Per run, from the snapshots of fourier.py: t_fit99 / t_gen99 (the run's own first-crossing times), and
  t_sp_half   first snapshot at which s_top5 has covered half of the way from its first to its last snapshot value;
  t_sp_50     first snapshot with s_top5 >= 0.5 (chance for a random embedding is about 5/29 = 0.17);
  t_rs_1      first snapshot with loss_restricted < 1.0 (chance level ln 59 = 4.08);
  t_rs_close  first snapshot with loss_restricted <= 1.5 * loss_all and loss_all < 2 (the key-frequency components carry the logit loss, with 5 frequencies fixed post hoc at the last snapshot);
and the position of each event inside the delay, (t_event - t_fit)/(t_gen - t_fit) (< 0 before the fit, 1 at t_gen).
Per (label, width): medians over seeds. Output: OUT_PREFIX_runs.csv, OUT_PREFIX_summary.csv."""
import glob, json, sys
import numpy as np, pandas as pd


def first(steps, cond):
    i = np.flatnonzero(cond)
    return float(steps[i[0]]) if len(i) else np.nan


rows = []
for spec in sys.argv[2:]:
    d, label = spec.rsplit(":", 1)
    for f in sorted(glob.glob(d + "/*.json")):
        r = json.load(open(f)); R = pd.DataFrame(r["rows"]); s = r["summary"]; st = R.step.values
        half = R.s_top5.iloc[0] + 0.5 * (R.s_top5.iloc[-1] - R.s_top5.iloc[0])
        ev = {"t_sp_half": first(st, R.s_top5.values >= half), "t_sp_50": first(st, R.s_top5.values >= 0.5),
              "t_rs_1": first(st, R.loss_restricted.values < 1.0), "t_rs_close": first(st, (R.loss_restricted.values <= 1.5 * R.loss_all.values) & (R.loss_all.values < 2.0))}
        c = r["config"]; tf, tg = s["t_fit99"], s["t_gen99"]
        row = {"label": label, "width": c["width"], "seed": c["seed"], "t_fit99": tf, "t_gen99": tg, "s_top5_first": R.s_top5.iloc[0],
               "s_top5_last": R.s_top5.iloc[-1], "loss_all_last": R.loss_all.iloc[-1], "loss_restr_last": R.loss_restricted.iloc[-1], **ev,
               "s_top5_at_fit": float(np.interp(tf, st, R.s_top5)) if tf is not None else np.nan,
               "restr_at_fit": float(np.interp(tf, st, R.loss_restricted)) if tf is not None else np.nan}
        for k, v in ev.items():
            row["pos_" + k[2:]] = (v - tf) / (tg - tf) if (tf is not None and tg is not None and tg > tf) else np.nan
        rows.append(row)
D = pd.DataFrame(rows).sort_values(["label", "width", "seed"]); D.to_csv(sys.argv[1] + "_runs.csv", index=False)
S = D.groupby(["label", "width"]).median(numeric_only=True).drop(columns="seed"); S["n"] = D.groupby(["label", "width"]).size()
S.to_csv(sys.argv[1] + "_summary.csv")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(S[["n", "t_fit99", "t_gen99", "t_sp_half", "t_sp_50", "t_rs_1", "t_rs_close", "pos_sp_half", "pos_sp_50", "pos_rs_1", "pos_rs_close", "s_top5_at_fit", "s_top5_last", "restr_at_fit"]].round(2))
