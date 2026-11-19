"""Composition of the (fine-tune, base) pairs behind the empirical caps, and the caps from the restricted subset.
Writes results/pairs_composition.csv (counts per class), results/emp_caps_restricted.csv (emp95/emp99/pooled quantiles, all pairs vs restricted pairs),
results/base_model_metadata.csv (how reliable the user-entered `Base Model` entry is). Classes come only from the leaderboard's `Type`/`Merged` columns and the model name
(regex in mti.data.gain_pairs); no hand labels. Usage: python3 src/emp_pairs_composition.py"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
R = pathlib.Path(__file__).resolve().parents[1] / "results"
SHORT = {"🔶": "fine-tuned on domain-specific datasets", "💬": "chat models (RLHF, DPO, IFT)", "🟢": "pretrained", "🟩": "continuously pretrained", "🤝": "base merges and moerges", "❓": "other"}
cls = lambda t: next((v for k, v in SHORT.items() if str(t).startswith(k)), str(t))
p, g = dt.gain_pairs("all"); pr, gr = dt.gain_pairs("restricted")
name_chat = p.fullname.str.contains(r"instruct|chat|[-_]it\b|dpo|rlhf|orpo|simpo", case=False, regex=True)
p = p.assign(cls=p.Type.map(cls), name_chat=name_chat, in_restricted=p.fullname.isin(pr.fullname))
rows = [dict(grouping="Type of the fine-tune", cls=c, n_pairs=int(n), share=n / len(p)) for c, n in p.cls.value_counts().items()]
d = pd.read_csv(dt.PROC / "ollb6.csv"); d = d[~d.Flagged]; idx = d.set_index("fullname")
bt = idx.loc[p["Base Model"], "Type"].map(cls).values
rows += [dict(grouping="Type of the base model", cls=c, n_pairs=int(n), share=n / len(p)) for c, n in pd.Series(bt).value_counts().items()]
rows += [dict(grouping="criteria", cls="Merged flag set", n_pairs=int(p.Merged.sum()), share=p.Merged.mean()),
         dict(grouping="criteria", cls="name matches instruct|chat|-it|dpo|rlhf|orpo|simpo", n_pairs=int(name_chat.sum()), share=name_chat.mean()),
         dict(grouping="criteria", cls="name matches but Type not 'chat'", n_pairs=int((name_chat & ~p.Type.str.contains("chat")).sum()), share=float((name_chat & ~p.Type.str.contains("chat")).mean())),
         dict(grouping="criteria", cls="Type 'chat' but name does not match", n_pairs=int((~name_chat & p.Type.str.contains("chat")).sum()), share=float((~name_chat & p.Type.str.contains("chat")).mean())),
         dict(grouping="restricted subset", cls="neither chat Type, merge, nor chat-like name (kept)", n_pairs=len(pr), share=len(pr) / len(p)),
         dict(grouping="distinct base models", cls="all pairs", n_pairs=int(p["Base Model"].nunique()), share=np.nan),
         dict(grouping="distinct base models", cls="restricted pairs", n_pairs=int(pr["Base Model"].nunique()), share=np.nan)]
pd.DataFrame(rows).to_csv(R / "pairs_composition.csv", index=False)
q = []
for sub, gg, n in (("all", g, len(p)), ("restricted", gr, len(pr))):
    for qq in (95, 99):
        pt = np.percentile(gg, qq, axis=0)
        for j, t in enumerate(dt.OLLB_TASKS): q.append(dict(subset=sub, n_pairs=n, quantile=qq, task=t, cap_gain=float(pt[j])))
        q.append(dict(subset=sub, n_pairs=n, quantile=qq, task="pooled scalar", cap_gain=float(np.percentile(gg, qq))))
        q.append(dict(subset=sub, n_pairs=n, quantile=qq, task="MMLU-PRO (transferred to every HELM subject)", cap_gain=float(pt[dt.OLLB_TASKS.index("MMLU-PRO")])))
pd.DataFrame(q).to_csv(R / "emp_caps_restricted.csv", index=False)
# reliability of the user-entered Base Model field (4496 unflagged models)
bm = d["Base Model"]
meta = [("unflagged models", len(d)), ("Base Model empty", int(bm.isna().sum())),
        ("Base Model equals own name", int((bm == d.fullname).sum())),
        ("Base Model is another unflagged leaderboard model (used as pair)", int(((bm != d.fullname) & bm.isin(idx.index)).sum())),
        ("Base Model not on the (unflagged) leaderboard", int((~bm.isin(idx.index)).sum())),
        ("... of which 'Removed' / '(Merge)' / starts with '[' placeholder strings", int((~bm.isin(idx.index) & bm.astype(str).str.contains(r"Removed|\(Merge\)|^\[", regex=True)).sum()))]
# disagreement of the pair gains with the type claim: a "pair" whose fine-tune scores lower than its base on all six tasks
neg = int((g < 0).all(axis=1).sum()); meta.append(("pairs whose fine-tune scores below its base on all six tasks (suspect base entry)", neg))
meta.append(("pairs with mean gain over six tasks < -5 points", int((g.mean(axis=1) < -5).sum())))
pd.DataFrame(meta, columns=["item", "count"]).to_csv(R / "base_model_metadata.csv", index=False)
print(pd.DataFrame(rows).to_string()); print(pd.DataFrame(q).pivot_table(index="task", columns=["subset", "quantile"], values="cap_gain").round(2).to_string()); print(pd.DataFrame(meta).to_string())

# C8 under the restricted-pair caps: share of targets (ranks 2-30 on OLLB, 11-30 and 2-30 on HELM) for which first is infeasible under the shipped (all 540 pairs) and restricted caps.
# Grids: results/{ollb,helm}_emp_restricted.csv from run_extra2.sh (run_core.py, caps emp95,emp99,emp95r,emp99r, rules mean,median,min, targets top30).
out = []
for ds in ("ollb", "helm"):
    f = R / f"{ds}_emp_restricted.csv"
    if not f.exists(): continue
    e = pd.read_csv(f); e = e[e.rank_mean >= 2]
    for lo, hi in ((2, 30), (11, 30)):
        s = e[(e.rank_mean >= lo) & (e.rank_mean <= hi)]
        for (cap, rule), g in s.groupby(["cap", "rule"]):
            out.append(dict(dataset=ds, ranks=f"{lo}-{hi}", cap=cap, pairs="restricted" if cap.endswith("r") else "all 540", quantile=int(cap[3:5]), rule=rule, n_targets=len(g),
                            share_infeasible=float((g.status == "infeasible").mean()), n_censored=int((g.status == "censored").sum())))
if out:
    o = pd.DataFrame(out); o.to_csv(R / "summary" / "c8_restricted_pairs.csv", index=False)
    print(o.pivot_table(index=["dataset", "ranks", "rule"], columns=["quantile", "pairs"], values="share_infeasible").round(3).to_string())
