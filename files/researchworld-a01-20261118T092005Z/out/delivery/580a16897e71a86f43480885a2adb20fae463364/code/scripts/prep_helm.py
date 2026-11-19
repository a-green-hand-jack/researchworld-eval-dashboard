"""Build the HELM MMLU score matrix (models x 57 subjects) from the v1.13.0 groups/json tables.
usage: prep_helm.py HELM_DIR OUT_DIR"""
import sys, json, glob, os
import pandas as pd
src, out = sys.argv[1], sys.argv[2]
rows = {}
n_eval = {}
for f in sorted(glob.glob(os.path.join(src, "groups/json/mmlu_mmlu_subject:*.json"))):
    d = json.load(open(f)); subj = d["name"].split(":", 1)[1]
    hdr = [h["value"] for h in d["header"]]
    iem, ine = hdr.index("EM"), hdr.index("# eval")
    for r in d["rows"]:
        model = r[0]["value"]; em = r[iem].get("value"); ne = r[ine].get("value")
        if em is None: continue
        rows.setdefault(model, {})[subj] = em
        n_eval.setdefault(subj, set()).add(ne)
S = pd.DataFrame(rows).T.sort_index()
print("raw matrix", S.shape, "missing cells", int(S.isna().sum().sum()))
assert all(len(v) == 1 for v in n_eval.values()), "n_eval differs across models within a subject"
n = pd.Series({k: int(next(iter(v))) for k, v in n_eval.items()}).sort_index()
S = S[n.index]
S.to_csv(os.path.join(out, "helm_mmlu_em.csv")); n.to_csv(os.path.join(out, "helm_mmlu_neval.csv"), header=["n_eval"])
print(S.shape, "n_eval total", n.sum())
