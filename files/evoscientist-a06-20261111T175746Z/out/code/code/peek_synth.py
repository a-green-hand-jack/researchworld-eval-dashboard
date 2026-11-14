import json
d = json.load(open("results/synth.json"))["rows"]
print(len(d))
print("== scaleK (bias naive, pred_null, hoeff) ==")
for r in d:
    if r["kind"] == "scaleK" and r["n"] == 400:
        print(r["rho_target"], r["K"], r["n"], "naive %.4f pred %.4f hoef %.4f rho_hat %.2f  cov %.2f" % (r["naive"]["bias"], r["pred_null"], r["pred_hoeffding"], r["rho_hat"], r["naive"]["cov"]))
print("== gap ==")
for r in d:
    if r["kind"] == "gap":
        print(r["regime"], "naive %.4f boot %.4f cv %.4f eb %.4f split50 %.4f | regret %.4f mu_range %.4f" % (r["naive"]["bias"], r["boot_opt"]["bias"], r["cv"]["bias"], r["eb"]["bias"], r["split50"]["bias"], r["oracle_mean"] - r["truth_mean"], r["mu_range"]))
print("== regimes ==")
for r in d:
    if r["kind"] == "regimes":
        print(r["regime"], r["opt"], r["K"], r["n"], " ".join("%s b%.4f c%.2f" % (m, r[m]["bias"], r[m].get("cov", float("nan"))) for m in ["naive", "boot_opt", "cv", "eb", "split50"]), "maxt cov %.2f lower1 %.2f naive_lower1 %.2f" % (r["maxt"]["cov"], r["maxt_lower1"]["cov"], r["naive_lower1"]["cov"]))
