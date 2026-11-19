"""Regenerate every figure and table from a results/ directory: python3 figures/make_all.py --results results [--out .]
Writes figures/*.pdf, tables/*.tex and the MANIFEST.json files (sha256 of the input files of every output)."""
import argparse
import os
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument("--results", required=True)
p.add_argument("--out", default=".", help="directory containing figures/ and tables/")
a = p.parse_args()
a.results = os.path.abspath(a.results)
a.out = os.path.abspath(a.out)
here = os.path.dirname(os.path.abspath(__file__))
tdir = os.path.join(here, "..", "tables")
jobs = [("fig1_leaderboards.py", []), ("fig2_survival.py", []), ("fig2_survival.py", ["--perturbation", "flip"]),
        ("fig2_survival.py", ["--layout", "grid"]), ("fig2_survival.py", ["--layout", "grid", "--perturbation", "flip"]), ("fig3_budgets.py", []),
        ("fig4_budget_vs_z.py", []), ("fig5_matched.py", []), ("fig6_controls.py", []), ("fig7_noise.py", []), ("fig8_window.py", [])]
jobs = [(os.path.join(here, s), x, os.path.join(a.out, "figures")) for s, x in jobs]
jobs += [(os.path.join(tdir, s), [], os.path.join(a.out, "tables")) for s in
         ["table0_headline.py", "table1_datasets.py", "table2_regression.py", "table3_method_validity.py", "table3b_exhaustive.py", "table4_ablations.py", "table5_additions.py", "table6_published.py", "table7_estimator.py", "table8_oos.py", "table9_restarts.py"]]
for script, extra, out in jobs:
    os.makedirs(out, exist_ok=True)
    subprocess.run([sys.executable, script, "--results", a.results, "--out", out, *extra], check=True, cwd=here)
