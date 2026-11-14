"""Apply the documented post-scoring numerical-rank repair to frozen outputs.

This calls the frozen scorer with the canonical metric implementation. It
neither refits nor changes predictions, selections, truth or score-error units.
"""
import datetime,hashlib,importlib.util,json,pathlib,shutil
from rank_metrics import metrics
root=pathlib.Path(__file__).resolve().parents[1];out=root/'results/study'
original_names=['metrics.parquet','metrics.csv','summary.csv','paired_contrasts.csv','robustness_contrasts.csv','macro_repeats.csv','paired_macro_repeats.csv','scoring_provenance.json']
archive=out/'original_raw_ties';manifest={}
if (out/'metrics.parquet').exists() and not archive.exists():
 archive.mkdir()
 for name in original_names:
  path=out/name
  if path.exists():
   manifest[name]=hashlib.sha256(path.read_bytes()).hexdigest();shutil.copy2(path,archive/name)
 (archive/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
spec=importlib.util.spec_from_file_location('frozen_scorer',root/'scripts/score_study.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.metrics=metrics;module.score()
provenance=json.loads((out/'scoring_provenance.json').read_text())
provenance['rank_correction']={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rank_decimal_places':12,
 'trigger':'95 primary cells violated common-constant rank invariance due to binary floating-point tie fragmentation; raw1pp boundary subtraction also needs canonicalization',
 'scope':'Round truth/predictions to12 decimal places for rank/tie computations and round true pair gaps to12 decimals for1pp bin membership; all score errors use unrounded predictions/truth',
 'amendment':'notes/postscore_amendments/2026-11-05_rank_numerics.json',
 'generator_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__),root/'diagnostics/rank_metrics.py']},
 'original_metrics_archive':'results/study/original_raw_ties','primary_predictor_freeze_unchanged':True}
(out/'scoring_provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
print('HUTIAN_WAKE: numerical rank correction complete; original metrics archived and predictions unchanged',flush=True)
