"""Solver verification table (solver_check): re-runs the brute-force / LP / enumeration checks in tests/ and writes OUT.csv (rule, instance class, n_instances, n_agree, max_size).
usage: run_checks.py OUT.csv [n_bruteforce=200]   (python3 -m tests.* modules are run as subprocesses and their summary lines parsed)"""
import sys, os, re, ast, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
out = sys.argv[1]; n = sys.argv[2] if len(sys.argv) > 2 else "200"
rows = []
def sh(args): return subprocess.run([sys.executable, "-m"] + args, capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).stdout
txt = sh(["tests.test_bruteforce", n])
for line in txt.splitlines():
    m = re.match(r"(checked|rank-rule check) (\d+) mismatches (\d+) (\{.*\})", line)
    if m:
        cls = "brute force over all integer plans (N<=7, m<=5; depth and breadth; gamma 1 and 2; own and restricted rivals)" if m.group(1) == "checked" else \
              "brute force over all tie-aware level plans (N<=7, m<=4; depth and breadth; gamma 1 and 2)"
        for rule, (tot, ok) in ast.literal_eval(m.group(4)).items():
            rows.append(dict(rule=rule, instance_class=cls, n_instances=tot, n_agree=ok, max_size="N=7, m=5" if m.group(1) == "checked" else "N=7, m=4"))
txt = sh(["tests.test_mean"])
m = re.search(r"mean-family checks (\d+) mismatches (\d+)", txt)
if m: rows.append(dict(rule="mean,zmean", instance_class="scipy linprog (depth), subset enumeration (breadth), SLSQP for gamma=2 (N<=8, m<=7)", n_instances=int(m.group(1)), n_agree=int(m.group(1)) - int(m.group(2)), max_size="N=8, m=7"))
txt = sh(["tests.test_frontier"])
m = re.search(r"frontier checks (\d+) mismatches (\d+)", txt)
if m: rows.append(dict(rule="all (frontier)", instance_class="breadth-constrained solver vs subset enumeration (N<=7, m<=5, all k)", n_instances=int(m.group(1)), n_agree=int(m.group(1)) - int(m.group(2)), max_size="N=7, m=5"))
pd.DataFrame(rows).to_csv(out, index=False); print(pd.DataFrame(rows).to_string())
