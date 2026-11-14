"""Dump task type / languages / domains for MTEB tasks using the mteb package (separate venv; metadata only)."""
import sys, mteb, pandas as pd
rows = []
for t in mteb.get_tasks():
    m = t.metadata
    rows.append(dict(task=m.name, type=m.type, langs=";".join(sorted(set(l.split("-")[0] for l in m.eval_langs if isinstance(l,str)))) if not isinstance(m.eval_langs, dict) else ";".join(sorted(set(l.split("-")[0] for v in m.eval_langs.values() for l in v))),
                     domains=";".join(m.domains or []), main_score=m.main_score))
pd.DataFrame(rows).to_csv(sys.argv[1], index=False)
print(len(rows))
