"""Extract number of test instances per MMLU subject from HELM runs.json (stat num_instances)."""
import json, sys, collections
runs = json.load(open(sys.argv[1]))
n = collections.defaultdict(set)
for r in runs:
    subj = r['run_spec']['scenario_spec']['args']['subject']
    for s in r['stats']:
        if s['name']['name'] == 'num_instances' and 'perturbation' not in s['name']:
            n[subj].add(int(s['sum']))
json.dump({k: sorted(v) for k, v in n.items()}, open(sys.argv[2], 'w'), indent=1)
print(len(n), {k: v for k, v in n.items() if len(v) > 1}, sum(max(v) for v in n.values()))
