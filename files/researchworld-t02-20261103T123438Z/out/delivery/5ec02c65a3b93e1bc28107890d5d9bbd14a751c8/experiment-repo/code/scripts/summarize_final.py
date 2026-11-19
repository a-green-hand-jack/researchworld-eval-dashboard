"""Select final owner handoff inputs without estimating new scientific statistics."""
import hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

root=Path(__file__).resolve().parents[2]
load=lambda path:json.loads((root/path).read_text())
paths=['configs/confirmatory.json','results/registered-audit.json','results/confirmatory-analysis/analysis.json','results/confirmatory-analysis/runs.json','results/confirmatory-analysis/cells.json','results/confirmatory-analysis/cells-first8.json','results/confirmatory-analysis/predictions.json','results/sensitivity/sensitivity.json']
registry=load(paths[0])['runs']; audit=load(paths[1]); cells=load(paths[4]);pred=load(paths[6]);sens=load(paths[7]);runs=load(paths[3])
assert len(registry)==len(runs)==204 and len(cells)==23 and audit['completed_audited']==204 and audit['status']=='PASS'
assert all(c['complete'] for c in pred['scope_width_contrasts'])
variants=[]
for variant in sens['variants']:
    assert variant['complete']
    base='results/sensitivity/'+variant['name']
    for leaf in ['cells.json','predictions.json']:paths.append(base+'/'+leaf)
    vp=load(base+'/predictions.json');vc=load(base+'/cells.json')
    variants.append(dict(name=variant['name'],P1=vp['P1']['interpretation'],P2=vp['P2']['interpretation'],P3=vp['P3']['interpretation'],scope_width_contrasts=vp['scope_width_contrasts'],cells=[{k:c[k] for k in ['family','width','n','train_events','valid_events','delayed_events','terminal_valid_events']} for c in vc]))
out=dict(kind='Selection of complete owner-computed scientific results; no new inference',generated_utc=datetime.now(timezone.utc).isoformat(),registered_runs=204,registered_cells=23,all_primary_predictions={k:pred[k] for k in ['P1','P2','P3']},cells=cells,cells_first8=load(paths[5]),scope_width_contrasts=pred['scope_width_contrasts'],decay_contrasts=pred['decay_contrasts'],sensitivity_variants=variants,cpu_accounting_incomplete_runs=[r['path'] for r in runs if r['cpu_accounting_incomplete']],float64_prediction_disagreements=[r['name'] for r in audit['split_diagnostics'] if r['numerical_precision']['total_prediction_differences']],sources=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths],generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits=['All secondary intervals are pointwise, not multiplicity adjusted.','Restricted clocks do not estimate eventual events.','P3 mechanism remains unresolved because fit gate fails.','CPU100 measures unequal actual progress with no interpolation; missing account remains unavailable.','Scope comparisons do not identify a universal width law, isolated rate effect or unique mechanism.'])
(root/'results/final-study-summary.json').write_text(json.dumps(out,indent=2)+'\n')
print('Selected204 runs,23 cells,13 variants and all registered paired contrasts;no new statistics')
