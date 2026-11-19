"""Per-subject test-set sizes of HELM MMLU v1.13.0 (external-review request #6.4a).
Usage: python3 src/helm_subject_sizes.py HELM_DIR OUT_CSV      (HELM_DIR from src/fetch_helm.py; reads groups/json/mmlu_mmlu_subject:*.json)
One row per subject: `# eval` (items) across the models of the release (min == max checked), the binomial standard error of a subject
accuracy at accuracy 0.5 and 0.8, and the size of one item in score points (100/n). A last row set summarises min / median / max over the 57 subjects.
"""
import json, sys, pathlib
import numpy as np, pandas as pd
rows = []
for f in sorted((pathlib.Path(sys.argv[1]) / "groups" / "json").glob("mmlu_mmlu_subject:*.json")):
    subj = f.name[len("mmlu_mmlu_subject:"):-5]; t = json.load(open(f)); hdr = [h["value"] for h in t["header"]]; ine = hdr.index("# eval")
    ne = [r[ine].get("value") for r in t["rows"] if r[ine].get("value") is not None]
    n = int(max(ne)); rows.append(dict(subject=subj, n_items=n, n_items_min_over_models=int(min(ne)), n_models_with_count=len(ne),
                                         item_points=100 / n, se_points_at_p50=100 * np.sqrt(.25 / n), se_points_at_p80=100 * np.sqrt(.16 / n)))
D = pd.DataFrame(rows); D.to_csv(sys.argv[2], index=False)
print(len(D), "subjects; total items", D.n_items.sum(), "; items per subject min/median/max", D.n_items.min(), D.n_items.median(), D.n_items.max())
print("subjects with 100 items:", int((D.n_items == 100).sum()), "; counts differ across models in", int((D.n_items != D.n_items_min_over_models).sum()), "subjects")
print("SE at p=.5 (points): min/median/max", D.se_points_at_p50.min().round(2), D.se_points_at_p50.median().round(2), D.se_points_at_p50.max().round(2))
