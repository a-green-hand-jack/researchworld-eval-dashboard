"""Compare closed-form predictions (code/docs/THEORY.md) with simulation.
 P2: empirical SD of ols_f error per graph draw vs theory_sd (Bernoulli, linear-in-f truth, homogeneous gamma).
 P1: mean error of ols_f@pop per graph draw vs pop_bias_ols_f (Bernoulli, g in pow/sat/thresh/lin).
Usage: theory_check.py E1_size E2_degree ...   -> results/theory_check_{var,bias}.csv"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np, pandas as pd
from netgate.sim import setup_graph, theory_sd
from netgate.theory import pop_bias_ols_f, pop_plim_linear

R = os.path.join(os.path.dirname(__file__), "..", "..", "results")
var_rows, bias_rows = [], []
for e in sys.argv[1:]:
    df = pd.read_parquet(os.path.join(R, "raw", f"{e}.parquet"))
    specs = {s["tag"]: {k: v for k, v in s.items() if k != "tag"} for s in json.load(open(os.path.join(R, "raw", f"{e}.specs.json")))}
    df["err"] = df.est - df.gate
    for tag, spec in specs.items():
        if spec["design"]["kind"] != "bernoulli" or spec.get("graph_err", 0) > 0:
            continue
        oc, p = spec["outcome"], spec["design"]["p"]
        for g in range(spec["G"]):
            net, out, gate, *_ = setup_graph(spec, g)
            sub = df[(df.tag == tag) & (df.g == g)]
            if oc["kind"] == "lin_frac" and oc.get("het", 0) == 0:
                x = sub[sub.est_name == "ols_f"].err
                if len(x) > 20:
                    var_rows.append(dict(exp=e, tag=tag, g=g, n=net.n, dH=1 / np.mean(1 / net.deg), p=p, sigma_c=oc.get("sigma_c", 1.0),
                                         emp_sd=x.std(), emp_bias=x.mean(), th_sd=theory_sd(net, out.base, out.sigma_e, p), reps=len(x)))
            x = sub[sub.est_name == "ols_f@pop"].err
            if len(x) > 5:
                if oc["kind"] in ("pow", "sat", "thresh") or (oc["kind"] == "lin_frac" and oc.get("het", 0) == 0):
                    b, _ = pop_bias_ols_f(net.deg, out.exposure_g, p); form = "P1"
                else:
                    pl, gt = pop_plim_linear(net, out); b = pl - gt; form = "P3"
                bias_rows.append(dict(exp=e, tag=tag, g=g, n=net.n, p=p, kind=oc["kind"], het=oc.get("het", 0), formula=form,
                                      emp_pop_bias=x.mean(), th_pop_bias=b, reps=len(x)))
v = pd.DataFrame(var_rows); b = pd.DataFrame(bias_rows)
if len(v):
    v["ratio"] = v.emp_sd / v.th_sd
    v.to_csv(os.path.join(R, "theory_check_var.csv"), index=False)
    print("P2 variance: n=%d graph draws; ratio emp/theory: median %.3f, IQR %.3f-%.3f; log-log corr %.4f" % (
        len(v), v.ratio.median(), v.ratio.quantile(.25), v.ratio.quantile(.75), np.corrcoef(np.log(v.emp_sd), np.log(v.th_sd))[0, 1]))
if len(b):
    b.to_csv(os.path.join(R, "theory_check_bias.csv"), index=False)
    print("P1 bias: n=%d graph draws; max |emp-theory| = %.4f; corr %.5f" % (len(b), (b.emp_pop_bias - b.th_pop_bias).abs().max(), np.corrcoef(b.emp_pop_bias, b.th_pop_bias)[0, 1]))
