import json, sys
m = sys.argv[1]
d = json.load(open(f"results/real_{m}.json"))
print("true acc", [round(x, 3) for x in sorted(d["true_acc"])])
for r in sorted(d["rows"], key=lambda r: (r["opt"], r["n"], r["K"])):
    if r["n"] in (100, 400):
        print(r["opt"], "K", r["K"], "n", r["n"], "R", r["R"], "naive %.4f+-%.4f pred_gauss %s pred_null %s | boot %.4f cv %.4f eb %.4f s50 %.4f s20 %.4f | cov naive %.2f split50 %.2f boot %.2f eb %.2f maxt %.2f | regret %.4f" % (
            r["naive"]["bias"], r["naive"]["bias_se"], "%.4f" % r["pred_gauss"] if "pred_gauss" in r else "-", "%.4f" % r["pred_null"] if "pred_null" in r else "-",
            r["boot_opt"]["bias"], r["cv"]["bias"], r["eb"]["bias"], r["split50"]["bias"], r["split20"]["bias"],
            r["naive"]["cov"], r["split50"]["cov"], r["boot_opt"]["cov"], r["eb"]["cov"], r["maxt"]["cov"], r["oracle_mean"] - r["truth_mean"]))
e = json.load(open(f"results/dec_{m}.json"))
print("== claims"); [print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}) for r in e["claims"] if r["n"] in (200, 800)]
print("== systems"); [print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}) for r in e["systems"] if r["n"] in (100, 400)]
print("== shift"); [print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}) for r in e["shift"] if r["n"] == 100]
