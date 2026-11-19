import json, sys, os
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(H, '..', 'results', 'summary.json')))
print(open(os.path.join(H, '..', 'paper', 'tables', 'tab_e1.tex')).read())
for k, v in S.get('e4_table', {}).items(): print(k, v['tv'], v['tt'], v['cens'])
print(S.get('e4_equal_product_ratio_max_over_min'))
print(S.get('probe_spearman_real_vs_random'), S.get('probe_median_ratio_random_over_real'), S.get('probe_n_pairs'))
print({k: v for k, v in S.items() if k.startswith('probe_slope')})
for k, v in S.get('capacity_threshold', {}).items(): print(k, v)
