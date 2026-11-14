"""Search-plane summaries of the three scored reporter variants, derived from their recorded per-seed episodes.
Search plane: seeds 101-104, cases P1-P4 (primary; 0.4 synthetic / 0.6 real), controls N1, N2, Z1.
# @evidence[[paper_data.json#all_programs]]
"""
import json, numpy as np
d = json.load(open('paper_data.json'))
names = {"c01_eb_irt_posterior_interval_attempt_01": "eb_irt",
         "c02_param_bootstrap_pivot_calibration_attempt_01": "param_bootstrap_pivot",
         "c03_eb_irt_config_subject_interaction_attempt_01": "config_subject_interaction"}
out = {}
for p in d['all_programs']:
    eps = p['evaluation_evidence']['episodes']
    def cv(key, case): return np.mean([e['solution'][case][key] for e in eps])
    def plane(key):
        syn = np.mean([cv(key, c) for c in ("P1", "P2")]); real = np.mean([cv(key, c) for c in ("P3", "P4")])
        return 0.4 * syn + 0.6 * real
    r = {"score_recorded": p['combined_score'], "n_seeds": len(eps), "seeds": [e['seed'] for e in eps],
         "interval_score": plane("cand_IS"), "coverage": plane("coverage"), "width": plane("width"), "signed_bias": plane("bias"),
         "naive_IS": plane("naive_IS"), "bonferroni_IS": plane("bonferroni_IS"), "resample_IS": plane("resample_IS"),
         "naive_bias": plane("naive_bias"),
         "null_control_coverage": float(np.mean([cv("coverage", c) for c in ("N1", "N2")])),
         "null_control_abs_bias": float(np.mean([abs(cv("bias", c)) for c in ("N1", "N2")])),
         "z1_width": cv("width", "Z1"),
         "per_case": {c: {"IS": cv("cand_IS", c), "coverage": cv("coverage", c), "width": cv("width", c), "bias": cv("bias", c)}
                      for c in eps[0]['solution']},
         "per_seed_scores": [e['score'] for e in eps]}
    out[names[p['attempt_id']]] = r
json.dump(out, open('analysis/search_variants.json', 'w'), indent=1)
for k, r in out.items():
    print(k, round(-r['interval_score'], 6), round(r['score_recorded'], 6), {m: round(r[m], 4) for m in ('coverage', 'width', 'signed_bias', 'naive_IS', 'bonferroni_IS', 'resample_IS', 'null_control_coverage', 'null_control_abs_bias')})
