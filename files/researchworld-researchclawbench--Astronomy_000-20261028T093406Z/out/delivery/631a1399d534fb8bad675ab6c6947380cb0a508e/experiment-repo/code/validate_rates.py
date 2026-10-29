"""Validation of the growth rates: (i) Leaver continued fraction vs the benchmark of Witek et al. 2012
(paper_003 Table II: alpha=0.42, a*=0.99, l=m=1, n=0 -> M*omega = 0.4088 + 1.504e-7 i), (ii) Leaver vs
Detweiler on a few (alpha, a*) points. Writes outputs/rate_validation.csv and outputs/literature_windows.json."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sr, leaver
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
rows = [("alpha", "a_star", "l=m", "Gamma_Leaver_rg", "Gamma_Detweiler_rg", "ratio", "Re_omega_rg")]
for l, al, a in [(1, 0.42, 0.99), (1, 0.05, 0.9), (1, 0.10, 0.9), (1, 0.20, 0.9), (1, 0.30, 0.9), (1, 0.05, 0.99),
                 (2, 0.20, 0.9), (2, 0.40, 0.9), (2, 0.30, 0.9)]:
    try:
        w = leaver.growth_rate(al, a, l, l)
        gd = float(sr.gamma_detweiler(al, a, l))
        rows.append((al, a, l, float(w.imag), gd, float(w.imag) / gd, float(w.real)))
    except Exception as e:
        rows.append((al, a, l, "fail", "", "", repr(e)[:40]))
with open(os.path.join(OUT, "rate_validation.csv"), "w") as f:
    for r in rows:
        f.write(",".join(str(x) for x in r) + "\n")
lit = {
    "Witek2012_TableII": {"alpha": 0.42, "a_star": 0.99, "Im_omega_rg": 1.504e-7, "source": "related_work/paper_003, Table II"},
    "Stott2018_excluded_mu_eV": {"stellar_BHs": [7e-14, 2e-11], "SMBHs": [7e-20, 1e-16],
        "note": "union over many BHs (Fig. 2 left of paper_001); tau_Salpeter=4.5e7 yr; not a single-source window"},
}
json.dump(lit, open(os.path.join(OUT, "literature_windows.json"), "w"), indent=1)
print(open(os.path.join(OUT, "rate_validation.csv")).read())
