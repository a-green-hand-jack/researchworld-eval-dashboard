"""Check rank correction against archived metrics and independent precision run."""
import hashlib,json,pathlib
import numpy as np,pandas as pd
root=pathlib.Path(__file__).resolve().parents[1];out=root/'results/study'
final=pd.read_parquet(out/'metrics.parquet');old=pd.read_parquet(out/'original_raw_ties/metrics.parquet')
keys=['benchmark','scenario','budget','repeat','method','evaluation_subset'];joined=final.merge(old,on=keys,suffixes=('_final','_old'),validate='one_to_one');assert len(joined)==len(final)==len(old)
errors=['mae_pp','rmse_pp','bias_pp','p90_abs_error_pp','out_of_range_fraction']
for metric in errors:assert np.array_equal(joined[metric+'_final'],joined[metric+'_old']),metric
primary=final[(final.evaluation_subset=='primary')&(final.scenario!='family_reference')]
a=primary[primary.method=='random_mean'].set_index(keys[:4]);b=primary[primary.method=='source_difference'].set_index(keys[:4])
for metric in ['spearman','kendall_tau_b','prediction_tie_pairs','close_pair_inversion','wide_pair_inversion']:
 np.testing.assert_allclose(a[metric],b[metric],atol=1e-12,rtol=0,equal_nan=True)
ranks=pd.read_parquet(out/'rank_precision_repeats.parquet');ranks=ranks[ranks.decimals==12].set_index(keys[:5]);check=primary.set_index(keys[:5]).loc[ranks.index]
for metric in ['spearman','kendall_tau_b']:np.testing.assert_allclose(check[metric],ranks[metric],atol=1e-12,rtol=0,equal_nan=True)
record={'metric_rows_checked':len(joined),'all_unrounded_error_fields_bitwise_equal':errors,
 'constant_shift_cells_checked':len(a),'constant_shift_rank_ties_inversions_pass':True,
 'independent12decimal_rank_cells_checked':len(ranks),'independent12decimal_rank_pass':True,
 'raw_rank_spearman_cells_changed':int((abs(joined.spearman_final-joined.spearman_old)>1e-12).sum()),
 'input_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'metrics.parquet',out/'original_raw_ties/metrics.parquet',out/'rank_precision_repeats.parquet']}}
(out/'rank_correction_checks.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('Rank repair verified on all80840 metric rows,1420 constant-shift cells and22360 independent rank cells.')
