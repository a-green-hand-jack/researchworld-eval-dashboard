"""Migrate existing measured outputs after the infeasible-target denominator correction.

No optimizer, subset, random draw, cost, or timing is recomputed. Requested
baseline groups are identified by their stored nonnull baseline measurements.
The co-first incumbent guarantees at least one such row per requested group.
"""
import pandas as pd
from analysis import ROOT

def main():
    for path in list((ROOT/'results').glob('attacks_*.csv'))+list((ROOT/'results').glob('pilot*.csv')):
        frame=pd.read_csv(path)
        keys=['dataset','rule','ceiling','alpha','strict']
        requested=frame.groupby(keys).random_expected_censored_k.transform(lambda s:s.notna().any())
        frame['random_requested']=requested
        frame['random_baseline_method']='not_requested'
        frame.loc[requested & frame.k.notna(),'random_baseline_method']='exact_subsets'
        frame.loc[frame.random_reps.gt(0),'random_baseline_method']='mc_permutations'
        infeasible=requested & frame.status.eq('infeasible')
        frame.loc[infeasible,'random_expected_censored_k']=frame.loc[infeasible,'n_tasks']+1
        frame.loc[infeasible,'random_baseline_method']='exact_infeasible'
        # No optimum exists on infeasible rows, so success AT an optimum is undefined.
        assert frame.loc[infeasible,'random_success_at_k'].isna().all()
        assert frame.loc[requested,'random_expected_censored_k'].notna().all()
        frame.to_csv(path,index=False,float_format='%.12g')
        print(f'{path.name}: {int(infeasible.sum())} exact censored rows',flush=True)
if __name__=='__main__':main()
