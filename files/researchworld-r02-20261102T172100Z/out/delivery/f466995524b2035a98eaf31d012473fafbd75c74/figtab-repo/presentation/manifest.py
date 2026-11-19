"""Record artifact-to-code/data provenance after rendering and inspection."""
import argparse,hashlib,json
from pathlib import Path

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--output-root',type=Path,default=Path('.'));p.add_argument('--source-root',type=Path,required=True);p.add_argument('--source-commit',required=True);a=p.parse_args();root=a.output_root
 descriptions={
  'joint_coverage':'RQ1: iid whole-composition coverage; K=3/10, ncal=499, homogeneous/heterogeneous, alpha=.1.',
  'group_shift_coverage':'RQ2/RQ4: iid observed-group coverage and marginal coverage after controlled .2-to-.8 mixture shift; K=3/10, heterogeneous, ncal=499.',
  'simplex_area':'RQ3: iid common Euclidean K=3 area with paired geometry contrasts; ncal=499, both noise mechanisms.',
  'replication_variability':'RQ2: ECDF of finite-test joint coverage, K=3 heterogeneous iid, ncal=99/499, global/scaled/group Aitchison.',
  'oracle_shift':'RQ4: shifted marginal/group1 coverage and K=3 common area; heterogeneous, ncal=499; exact oracle ratios.',
  'prior_score_area':'RQ3: TV/forward-KL paired K3 area differences against raw L2, maximum and Aitchison; ncal=499, both mechanisms and environments.',
  'paired_method_estimates':'All supplied paired method contrasts across cells; pointwise replication intervals.',
  'area_precision':'Supplied K3 candidate-resolution diagnostics, including unresolved ordering flags.',
  'pullback_equivalence':'Exact event identity giving original-response inverse-image coverage from measured transformed coverage; no new simulation or area estimate.',
  'boundary_targets':'RQ4: transformed response / original-target inverse-image coverage versus direct positive-domain original-response diagnostic, K=3/10, ncal=499, paired epsilon grid.'}
 main_inputs=['main_summary/summary.csv','main_summary/paired_contrasts.csv','main_summary/replications.csv','main_summary/summary_manifest.json']
 extra_inputs=['main_summary/summary.csv','main_summary/paired_contrasts.csv','main_summary/diagnostics.csv','main_summary/shift_contrasts.csv','boundary_summary/summary.csv','boundary_summary/epsilon_contrasts.csv','boundary_summary/zero_prevalence.csv','boundary_summary/pullback_equivalence.csv','main_summary/area_precision.csv','rank_checks.csv']
 result={'source_repository':'world/experiment-repo','source_commit':a.source_commit,'methods':'Seven core methods, matched-seed known-ratio oracle, TV and forward KL. All 160 main cells have 100 independent replications; K10 area is unmeasured.','generators':{},'inputs':{},'artifacts':[]}
 for code in ['presentation/render.py','presentation/supplement.py','presentation/manifest.py']:
  result['generators'][code]=digest(root/code)
 for item in sorted(set(main_inputs+extra_inputs)):result['inputs']['results/'+item]=digest(a.source_root/item)
 for directory in ['figures','tables']:
  for f in sorted((root/directory).iterdir()):
   if not f.is_file(): continue
   stem=f.stem.removesuffix('_caption')
   main_asset=(stem in ['joint_coverage','group_shift_coverage','simplex_area','replication_variability','main_summary','all_estimates','provenance'] or stem.startswith('k'))
   result['artifacts'].append({'path':str(f.relative_to(root)),'sha256':digest(f),'generator':'presentation/render.py' if main_asset else 'presentation/supplement.py','input_paths':['results/'+s for s in (main_inputs if main_asset else extra_inputs)],'purpose':descriptions.get(stem,'Numeric cell estimates, supplied paired contrasts/diagnostics, caption or provenance; keys and denominators retained.')})
 (root/'presentation'/'artifact_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
