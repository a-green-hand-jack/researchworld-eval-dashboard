"""Shapes, dtypes, value sets, model-list alignment for the pinned benchpred data. usage: check_data.py <outdir>"""
import sys, os, urllib.request, joblib, numpy as np
C = "55faff496947789f94e6b5908c77cbc3e84f81ad"
B = f"https://raw.githubusercontent.com/socialfoundations/benchmark-prediction/{C}/data/"
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
def get(p):
    f = os.path.join(out, p.replace("/", "__"))
    if not os.path.exists(f): urllib.request.urlretrieve(B + p, f)
    return f
oll = open(get("openllm_model_list.txt")).read().split("\n")
helm = open(get("helm_model_list.txt")).read().split("\n")
print("openllm list lines (incl. empty):", len(oll), "non-empty:", len([x for x in oll if x]), "unique:", len(set(oll)))
print("helm list lines (incl. empty):", len(helm), "non-empty:", len([x for x in helm if x]), "unique:", len(set(helm)))
for n in "arc_challenge bbh gpqa ifeval mmlu_pro musr openllm_math".split():
    a = joblib.load(get(f"scores/{n}.jbl")); m = None
    try: m = joblib.load(get(f"scores/{n}_models.jbl"))
    except Exception as e: m = f"ERR {type(e).__name__}"
    ml = len(m) if not isinstance(m, str) else m
    a = np.asarray(a, float)
    print(n, a.shape, "binary:", set(np.unique(a)) <= {0., 1.}, "mean=%.3f" % a.mean(), "models_file:", ml,
          "const-rows:", int(((a.min(1) == a.max(1))).sum()), "dup-items:", a.shape[1] - len({c.tobytes() for c in a.T}),
          "model-acc range: %.3f-%.3f" % (a.mean(1).min(), a.mean(1).max()))
for n in "commonsense gsm legalbench math med_qa mmlu".split():
    a = np.asarray(joblib.load(get(f"scores/{n}.jbl")), float)
    print("helm", n, a.shape, "binary:", set(np.unique(a)) <= {0., 1.}, "mean=%.3f" % a.mean(),
          "const-rows:", int(((a.min(1) == a.max(1))).sum()), "dup-items:", a.shape[1] - len({c.tobytes() for c in a.T}),
          "model-acc range: %.3f-%.3f" % (a.mean(1).min(), a.mean(1).max()))
