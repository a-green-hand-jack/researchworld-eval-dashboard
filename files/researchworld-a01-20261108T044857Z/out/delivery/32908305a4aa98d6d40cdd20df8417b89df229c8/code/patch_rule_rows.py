"""Replace the rows of one rule in a result CSV by the rows of a rerun of that rule only.
Usage: python3 code/patch_rule_rows.py OLD.csv NEW.csv RULE [--out OUT.csv]
Valid because draws/targets do not depend on the rule list (run_core.py / run_robust.py: one random stream per draw, not per rule);
the rule column of the rerun must cover the same keys (checked: same number of rows as the old rule rows)."""
import sys, pandas as pd
old, new, rule = sys.argv[1:4]; out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else old
o = pd.read_csv(old); nw = pd.read_csv(new)
assert (nw.rule == rule).all() and len(nw) > 0, "rerun file must contain only the rule"
assert (o.rule == rule).sum() == len(nw), f"row count differs: old {(o.rule == rule).sum()} new {len(nw)}"
res = pd.concat([o[o.rule != rule], nw], ignore_index=True)
res.to_csv(out, index=False); print(f"{out}: {len(nw)} {rule} rows replaced")
