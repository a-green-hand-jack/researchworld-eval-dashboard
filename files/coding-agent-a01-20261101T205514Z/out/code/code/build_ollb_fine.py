"""Build the 39-subtask Open LLM Leaderboard (v2) matrix from the compact results file.
Subtasks: 24 BBH + 3 GPQA + 7 MATH-hard (Lvl 5) + 3 MuSR + MMLU-Pro + IFEval.
IFEval score = mean(prompt_level_strict_acc, inst_level_strict_acc) as in the official aggregation.
Outputs data/processed/ollb_fine.csv (raw accuracies, models x subtasks) and ollb_fine_n.json."""
import json, sys
import numpy as np, pandas as pd
src, out_csv, out_n = sys.argv[1:4]
rows = [json.loads(l) for l in open(src)]
data, nn = {}, {}
for r in rows:
    res = r['results']
    ks = [k for k in res if k.startswith('leaderboard_') and k not in
          ('leaderboard_bbh', 'leaderboard_gpqa', 'leaderboard_math_hard', 'leaderboard_musr')]
    d = {}
    for k in ks:
        v = res[k]
        if k == 'leaderboard_ifeval':
            d[k] = 0.5 * (v['prompt_level_strict_acc,none'] + v['inst_level_strict_acc,none'])
        elif 'acc_norm,none' in v: d[k] = v['acc_norm,none']
        elif 'exact_match,none' in v: d[k] = v['exact_match,none']
        elif 'acc,none' in v: d[k] = v['acc,none']
    if len(d) == 39:
        data[r['model']] = d
        for k in d: nn[k] = r['n_samples'].get(k)
df = pd.DataFrame(data).T.sort_index()
df.index.name = 'model'
df.to_csv(out_csv)
json.dump(nn, open(out_n, 'w'), indent=1)
print(df.shape, 'models dropped (missing subtasks):', len(rows) - len(df))
