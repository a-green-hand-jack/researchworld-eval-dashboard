"""Profile the pinned MTEB results checkout: long table of (model, revision, task, split, subset, main_score).
Usage: python3 profile_mteb.py <results_dir> <out.parquet>"""
import json, os, sys
import pandas as pd
root, out = sys.argv[1], sys.argv[2]
import pyarrow as pa, pyarrow.parquet as pq
rows = []
writer=None
def flush():
    global rows, writer
    if not rows: return
    t=pa.Table.from_pandas(pd.DataFrame(rows, columns=COLS).astype({'mteb_version':'string','main_score':'float64'}), schema=SCHEMA, preserve_index=False)
    if writer is None: writer=pq.ParquetWriter(out, t.schema)
    writer.write_table(t); rows=[]
SCHEMA=pa.schema([('model',pa.string()),('rev',pa.string()),('task',pa.string()),('mteb_version',pa.string()),('split',pa.string()),('subset',pa.string()),('main_score',pa.float64())])
COLS=['model','rev','task','mteb_version','split','subset','main_score']
for m in sorted(os.listdir(root)):
    flush()
    mp = os.path.join(root, m)
    if not os.path.isdir(mp):
        continue
    for rev in os.listdir(mp):
        rp = os.path.join(mp, rev)
        if not os.path.isdir(rp):
            continue
        for fn in os.listdir(rp):
            if not fn.endswith('.json') or fn == 'model_meta.json':
                continue
            try:
                d = json.load(open(os.path.join(rp, fn)))
            except Exception:
                continue
            for split, lst in (d.get('scores') or {}).items():
                for e in lst:
                    rows.append((m, rev, d.get('task_name', fn[:-5]), d.get('mteb_version'), split,
                                 e.get('hf_subset'), e.get('main_score')))
flush(); writer.close(); df = pd.read_parquet(out)
print(df.shape, df.model.nunique(), df.task.nunique())
