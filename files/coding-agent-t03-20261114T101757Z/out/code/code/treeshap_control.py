"""Control: deterministic TreeSHAP (interventional) vs exact enumeration for tree models.

TreeSHAP has no sampling, so repeated runs are identical by construction. Comparing it
with our enumeration (exact.py) on the same background/output checks that the exact
reference is correct, and documents that the run-to-run variance seen for KernelSHAP is
algorithmic (sampling), not a property of the model's attributions.
Output: printed summary and results/control_treeshap.txt
"""
import numpy as np
import shap

from common import RES_DIR, get_model, output_fn, split
from exact import exact_shapley

lines = []
for ds in ["acs", "pima"]:
    s = split(ds)
    bg = s["background"][:100]
    for mn, output in [("LGBM", "margin"), ("RF", "prob")]:
        m = get_model(ds, mn, 0)
        f = output_fn(m, mn, output)
        phi_ex, gap = exact_shapley(f, s["X_inst"], bg)
        tm = "raw" if output == "margin" else "probability"
        te = shap.TreeExplainer(m, data=bg, feature_perturbation="interventional",
                                model_output=tm)
        phi_tree = te.shap_values(s["X_inst"], check_additivity=False)
        if isinstance(phi_tree, list):  # older shap returns [class0, class1]
            phi_tree = phi_tree[1]
        phi_tree2 = te.shap_values(s["X_inst"], check_additivity=False)
        diff = np.abs(phi_tree - phi_ex).max()
        rep = np.abs(phi_tree - phi_tree2).max()
        msg = (f"{ds} {mn} output={output}: TreeSHAP vs exact max|diff|={diff:.2e}; "
               f"TreeSHAP repeat max|diff|={rep:.1e}; exact additivity gap={gap:.1e}")
        print(msg, flush=True)
        lines.append(msg)

with open(f"{RES_DIR}/control_treeshap.txt", "w") as fh:
    fh.write("\n".join(lines) + "\n")
