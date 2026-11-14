"""All ad-hoc numbers quoted in the paper prose (printed and saved to paper/gen/extra_stats.json)."""
import json, pickle, numpy as np, pandas as pd
from scipy.stats import spearmanr
src = open("analyze_figs.py").read().split('if __name__')[0]
exec(src)   # re-uses loaders / boot_pooled / curve from analyze_figs
out = {}
sub = inst[(inst.d >= 16) & (inst.est == "kernel")]
cellsets = [(ds, k) for ds in ["acsemployment", "german"] for k in KIND]
def pooled(metric, m):
    return [round(float(x), 4) for x in boot_pooled([sub[(sub.ds == ds) & (sub.kind == k) & (sub.m == m)][metric].values for ds, k in cellsets])]
for metric in ["t_top1", "t_topk", "rel90", "t_rel", "stab3", "r2r_topk", "r2r_rbo"]:
    out[f"pooled_{metric}"] = {m: pooled(metric, m) for m in [64, 128, 256, 512, 1024, 2048, 4096, 8192]}
need = []
for key, g in sub.groupby(["ds", "kind", "inst"]):
    ok = g[g.rel90 == 1]; need.append(ok.m.min() if len(ok) else np.inf)
need = np.array(need)
out["need"] = dict(n=len(need), q50_90_95=np.percentile(need[np.isfinite(need)], [50, 90, 95]).tolist(),
                   frac_gt2048=float(np.mean(need > 2048)), frac_never=float(np.mean(~np.isfinite(need))))
x = sub[sub.m == 2048]
out["m2048"] = dict(frac_gap_lt_002=float((x.gap3 < 0.02).mean()), n_fail=int((x.rel90 == 0).sum()), n=len(x),
                    fail_with_gap_lt_002=int(((x.rel90 == 0) & (x.gap3 < 0.02)).sum()),
                    reliable_by_model=x.groupby("kind").rel90.mean().round(3).to_dict())
q = inst[(inst.est == "kernel") & (inst.m == 512) & (inst.d >= 16)]
out["spearman_rho_sd_m512"] = dict(all=float(spearmanr(q.rho, q.sd_rel)[0]), **{ds: float(spearmanr(q[q.ds == ds].rho, q[q.ds == ds].sd_rel)[0]) for ds in ["acsemployment", "german"]})
out["se_over_sd_median"] = sub.groupby(["d", "m"]).se_over_sd.median().round(3).unstack(0).to_dict()
# collapse first bin
k = inst[inst.est == "kernel"].copy(); k["zb"] = pd.cut(k.oz3, [0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 6, 1e9])
g = k.groupby("zb", observed=True).agg(z=("oz3", "median"), p=("t_topk", "mean"), n=("t_topk", "size"))
out["collapse"] = {str(i): [round(float(r.z), 3), round(float(r.p), 3), int(r.n)] for i, r in g.iterrows()}
rl = pd.read_parquet(f"{S}/run_level.parquet"); rl = rl[(rl.est == "kernel") & rl.ds.isin(["acsemployment", "german"])]
rl["z3"] = rl.z3.replace([np.inf], 1e6).fillna(0)
out["uncert_correct_z_lt_1"] = {m: float(rl[(rl.m == m) & (rl.z3 < 1)].ok3.mean()) for m in (128, 512, 2048)}
D = pickle.load(open("/work/results/highd/highd.pkl", "rb"))
out["highd_top10_share_sq"] = [float(np.mean([np.sort(r["phi"] ** 2)[::-1][:10].sum() / (r["phi"] ** 2).sum() for r in D["res"]])),
                               float(np.min([np.sort(r["phi"] ** 2)[::-1][:10].sum() / (r["phi"] ** 2).sum() for r in D["res"]]))]
b = pd.read_parquet("/work/results/summary_rep1/inst_level.parquet")
for nm, xx in [("main", inst), ("rep", b[b.m >= 64])]:
    qq = xx[(xx.est == "kernel") & (xx.m == 128) & (xx.ds == "gmsc")]
    out[f"gmsc_{nm}"] = qq.groupby("kind").agg(frac_gap_lt_002=("gap3", lambda g: float((g < 0.02).mean())), sd_rel_median=("sd_rel", "median")).round(3).to_dict()
sd = inst[(inst.est == "kernel") & (inst.d == 20)].groupby("m").sd_rel.median().round(4)
out["sd_rel_d20_median"] = sd.to_dict()
out["auc_range_retrain"] = {f"{r['ds']}_{r['kind']}": [min(a for a in [r['auc']]) ] for r in []}
res = pickle.load(open("/work/results/retrain/retrain.pkl", "rb"))
out["retrain_auc_span_max"] = max(max(r["auc"] for r in res if r["ds"] == ds and r["kind"] == kd) - min(r["auc"] for r in res if r["ds"] == ds and r["kind"] == kd) for ds in ["pima", "gmsc", "acsincome"] for kd in KIND)
json.dump(out, open(f"{GEN}/extra_stats.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
