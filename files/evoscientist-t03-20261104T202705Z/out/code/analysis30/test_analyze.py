#!/usr/bin/env python3
"""Analysis-only regression tests; no estimator/explanation experiments."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import numpy as np
import pandas as pd

SOURCE = Path(__file__).resolve().parents[1]/'analyze.py'
spec = importlib.util.spec_from_file_location('analysis_under_test', SOURCE)
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
RESULTS = SOURCE.parent/'results'
OUT = Path(__file__).resolve().parent


def test():
    checks = []
    a.self_test(); checks.append('metric unit tests and negative unclipped Nogueira')
    for ds in a.DATASETS:
        for model in a.MODELS:
            for seed in a.SEEDS:
                report, cell = a.validate_cell(RESULTS, ds, model, seed)
                assert report['status'] == 'valid', report
    checks.append('all 27 artifacts pass shapes, metadata, budgets, IDs, efficiency and costs')
    df = pd.read_csv(OUT/'cell_summary.csv')
    macro = pd.read_csv(OUT/'exact_macro.csv')
    clusters = pd.read_csv(OUT/'instance_clusters.csv')
    with np.load(OUT/'analysis_inputs.npz', allow_pickle=False) as raw:
        all_raw = {k: raw[k] for k in raw.files}
    # Independent sort/set implementation, plus direct count-of-identical-sets
    # pairwise calculation (not repetition-pair pseudoreplication).
    for ds in ('pima', 'acs'):
        for model in a.MODELS:
            vectors = []
            for seed in a.SEEDS:
                prefix = f'{ds}_{model}_{seed}__'
                phi, ref = all_raw[prefix+'phi'], all_raw[prefix+'reference']
                means, pairs = np.zeros((30,4)), np.zeros((30,4))
                for i in range(30):
                    target = frozenset(sorted(range(ref.shape[-1]), key=lambda j: (-abs(ref[i,j]),j))[:3])
                    for bi in range(4):
                        subsets = [frozenset(sorted(range(ref.shape[-1]),key=lambda j: (-abs(v[j]),j))[:3]) for v in phi[i,:,bi]]
                        means[i,bi] = sum(s == target for s in subsets)/20
                        counts = {s: subsets.count(s) for s in set(subsets)}
                        pairs[i,bi] = sum(c*(c-1)/2 for c in counts.values())/190
                vectors.append(means)
                for bi,b in enumerate(a.BUDGETS):
                    row = pd.read_csv(OUT/'per_seed.csv').query('dataset==@ds and model==@model and seed==@seed and method=="antithetic" and budget==@b').iloc[0]
                    assert np.isclose(row.top3_match, means[:,bi].mean())
                    assert np.isclose(row.pairwise_top3_match, pairs[:,bi].mean())
            vec = np.stack(vectors).mean(axis=0)
            for bi,b in enumerate(a.BUDGETS):
                row = df.query('dataset==@ds and model==@model and method=="antithetic" and budget==@b').iloc[0]
                idx = all_raw[f'bootstrap__{ds}']
                boot = vec[idx,bi].mean(axis=1)
                assert np.isclose(row.top3_match,vec[:,bi].mean())
                assert np.allclose([row.top3_match_lo,row.top3_match_hi],np.quantile(boot,[.025,.975]))
    checks.append('independent top3 and pairwise-count implementation agrees with seed/cell results and paired CIs')
    for method in a.METHODS:
        for b in a.BUDGETS:
            per_ds = []
            for ds in ('pima','acs'):
                sub = clusters.query('dataset==@ds and method==@method and budget==@b')
                means = sub.pivot(index='instance_id',columns='model',values='top3_match')
                # Restore original instance order, not numerical row-ID order.
                ids = all_raw[f'{ds}_lr_11__instances']
                instance_mean = means.loc[ids].mean(axis=1).to_numpy()
                per_ds.append(instance_mean[all_raw[f'bootstrap__{ds}']].mean(axis=1))
            expected = np.mean(per_ds,axis=0)
            row = macro.query('method==@method and budget==@b').iloc[0]
            assert np.allclose([row.top3_match_lo,row.top3_match_hi],np.quantile(expected,[.025,.975]))
    assert not np.array_equal(all_raw['bootstrap__pima'],all_raw['bootstrap__acs'])
    checks.append('macro CIs verified from independent-dataset resamples with within-dataset cross-model pairing')
    # Input completeness: all arrays, not just averaged top-k or truncated runs.
    for report in json.loads((OUT/'validation.json').read_text()):
        with np.load(RESULTS/(report['cell']+'.npz'),allow_pickle=False) as z:
            for key in z.files:
                assert np.array_equal(z[key],all_raw[report['cell']+'__'+key])
    checks.append('analysis_inputs.npz retains every array of all 33 completed main/sensitivity artifacts')
    with tempfile.TemporaryDirectory(prefix='shap_analysis_tests_') as temporary:
        tmp = Path(temporary); fixture = tmp/'results'; fixture.mkdir()
        for path in RESULTS.iterdir():
            if path.suffix in ('.json','.npz'):
                (fixture/path.name).symlink_to(path)
        (fixture/'german_rf_47.npz').unlink()  # temporary symlink only
        proc = subprocess.run([sys.executable,str(SOURCE),'--results',str(fixture),'--out',str(tmp/'pending')],capture_output=True,text=True)
        assert proc.returncode == 2, proc.stderr
        summary = json.loads((tmp/'pending'/'summary.json').read_text())
        assert summary['main_valid'] == 26 and summary['status']=='pending_main_cells'
        assert not (tmp/'pending'/'cell_summary.csv').exists()
        # Ensure stale summary is not presented as a valid final rerun.
        a.write_json(tmp/'pending'/'summary.json',{'status':'complete'})
        proc = subprocess.run([sys.executable,str(SOURCE),'--results',str(fixture),'--out',str(tmp/'pending')],capture_output=True,text=True)
        assert proc.returncode == 2
        assert json.loads((tmp/'pending'/'summary.json').read_text())['status']=='pending_main_cells'
        # Simulate a pilot-sized cell using a copy, never touching original data.
        (fixture/'pima_lr_11.npz').unlink()
        with np.load(RESULTS/'pima_lr_11.npz',allow_pickle=False) as z:
            truncated = {k:z[k] for k in z.files}
        truncated['phi']=truncated['phi'][:2,:3]
        np.savez_compressed(fixture/'pima_lr_11.npz',**truncated)
        report,_ = a.validate_cell(fixture,'pima','lr',11)
        assert report['status']=='invalid' and 'shape' in report['errors'][0]
    checks.append('missing-cell gate, stale-summary guard and pilot-dimension rejection verified without touching inputs')
    assert all(row['target']=='APPROX_reference_ONLY' for row in json.loads((OUT/'summary.json').read_text())['reference_pool_summary'])
    checks.append('German diagnostics carry APPROX reference-only labels')
    a.write_json(OUT/'analysis_tests.json',{'status':'passed','checks':checks})
    print('\n'.join(checks))


if __name__=='__main__':
    test()
