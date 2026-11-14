"""Claim diagnostics from executed production checkpoints; no model fitting.

Complements gatebench.summarize without changing the frozen simulator. Outputs
retain all scenarios, estimator failures and oracle labels. Normal/delta MC
intervals describe finite-return simulation performance, not causal intervals.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t
from gatebench.summarize import KEYS, mean_se, wilson

SCRIPT_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

IDENTITY = [k for k in KEYS if k != 'truth']
FAMILY = [k for k in IDENTITY if k not in ['graph', 'graph_seed']]


def moment(row, name, values):
    values = np.asarray(values, dtype=float)
    count = int(np.isfinite(values).sum())
    value, se = mean_se(values)
    row.update({name: value, name+'_mcse': se, name+'_n': count,
                name+'_lo': value-1.96*se, name+'_hi': value+1.96*se})


def rate(row, name, values):
    value, lo, hi = wilson(values)
    row.update({name: value, name+'_lo': lo, name+'_hi': hi,
                name+'_n': int(np.isfinite(values).sum())})


def family_average(frame, keys, metrics):
    """Equal graph weights, t interval over independent graph draws (n=1: NaN)."""
    rows = []
    for key, g in frame.groupby(keys, dropna=False, sort=True):
        if len(g) != g.graph.nunique():
            raise ValueError('Duplicate graph/scenario in supplementary family summary')
        row = dict(zip(keys, key)); row['graphs'] = len(g)
        for metric in metrics:
            if metric not in g:
                continue
            value, se = mean_se(g[metric]); n = int(np.isfinite(g[metric]).sum())
            critical = t.ppf(.975, n-1) if n > 1 else np.nan
            row.update({metric+'_graph_mean': value, metric+'_graph_se': se,
                        metric+'_graphs_defined': n, metric+'_graph_lo': value-critical*se,
                        metric+'_graph_hi': value+critical*se})
        rows.append(row)
    return pd.DataFrame(rows)


def diagnostics(frame):
    rows = []
    for key, g in frame.groupby(IDENTITY, dropna=False, sort=True):
        row = dict(zip(IDENTITY, key)); row['replicates'] = len(g)
        row['truth'] = g.truth.iloc[0]
        error = g.error.to_numpy(float)
        finite = np.isfinite(error)
        row['defined_fraction'] = float(finite.mean())
        row['error_sd'] = float(np.std(error[finite], ddof=1)) if finite.sum() > 1 else np.nan
        rate(row, 'estimable_fraction', g.valid.to_numpy(float))
        for name in ['exposure_sd', 'expected_full_treated', 'expected_full_control',
                     'full_treated', 'full_control', 'prediction_mean_mse', 'prediction_mse',
                     'hc3_se', 'oracle_se', 'weight_norm2', 'oracle_variance',
                     'conditional_mse', 'conditional_bias', 'estimability_error']:
            moment(row, name, g[name])
        b = g.conditional_bias.to_numpy(float)
        v = g.oracle_variance.to_numpy(float)
        moment(row, 'assignment_bias_squared', b*b)
        moment(row, 'mse_identity_residual', error*error-g.conditional_mse.to_numpy(float))
        moment(row, 'bias_identity_residual', error-b)
        for name in ['cover_hc3', 'cover_oracle']:
            rate(row, name, g[name].to_numpy(float))
        row['oracle_to_iid_variance_ratio'] = np.nan
        good = np.isfinite(v) & np.isfinite(g.weight_norm2) & (g.weight_norm2 > 0)
        if good.any():
            # Mean of per-assignment ratios; distinct from ratio of means.
            row['oracle_to_iid_variance_ratio'] = float(np.mean(v[good]/g.weight_norm2.to_numpy()[good]))
        for name, values in [('tail_absent_fraction', g.tail_active == 0),
                             ('threshold_absent_fraction', g.threshold_active == 0),
                             ('both_exposure_arms_fraction', (g.full_treated > 0) & (g.full_control > 0))]:
            if name == 'both_exposure_arms_fraction' and g.model.iloc[0] not in ['ht', 'hajek']:
                continue
            rate(row, name, values.to_numpy(float))
        rows.append(row)
    return rows


def prediction_pairs(frame):
    keys = [k for k in IDENTITY if k != 'model']
    rows = []
    for key, g in frame.groupby(keys, dropna=False, sort=True):
        groups = {name: part.set_index('pairing_id') for name, part in g.groupby('model')}
        reference = groups['linear']
        for model, part in groups.items():
            if model in ['linear', 'ht', 'hajek']:
                continue
            row = dict(zip(keys, key)); row.update(model=model, reference='linear', total_pairs=len(part))
            a, b = part.align(reference, join='inner', axis=0)
            finite = np.isfinite(a.error) & np.isfinite(b.error)
            row['defined_pairs'] = int(finite.sum())
            row['estimable_pairs'] = int((finite & a.valid & b.valid).sum())
            ea = a.loc[finite, 'error'].to_numpy(float); eb = b.loc[finite, 'error'].to_numpy(float)
            moment(row, 'delta_mse', ea*ea-eb*eb)
            for name in ['prediction_mean_mse', 'prediction_mse']:
                # Use same finite-GATE paired rows; preserve each metric's denominator.
                moment(row, 'delta_'+name, a.loc[finite, name]-b.loc[finite, name])
            rows.append(row)
    return rows


def coupling(frame):
    keys = [k for k in IDENTITY if k not in ['model', 'mechanism']]
    rows = []
    for key, g in frame.groupby(keys, dropna=False, sort=True):
        for model, part in g.groupby('model'):
            linear = part[part.mechanism == 'linear'].set_index('pairing_id')
            tail = part[part.mechanism == 'hidden_tail'].set_index('pairing_id')
            linear, tail = linear.align(tail, join='inner', axis=0)
            row = dict(zip(keys, key)); row.update(model=model, replicates=len(linear))
            equal = linear.tail_active == 0
            rate(row, 'identical_data_fraction', equal.to_numpy(float))
            finite = np.isfinite(linear.estimate) & np.isfinite(tail.estimate)
            chosen = equal & finite
            row['finite_identical_data_replicates'] = int(chosen.sum())
            differences = tail.loc[chosen, 'estimate']-linear.loc[chosen, 'estimate']
            row['max_estimate_difference_on_identical_data'] = float(np.abs(differences).max()) if chosen.any() else np.nan
            if chosen.any():
                assert row['max_estimate_difference_on_identical_data'] < 1e-8
            delta = tail.truth.to_numpy(float)-linear.truth.to_numpy(float)
            row['target_gap'] = float(delta[0])
            row['empirical_two_risk_bound'] = delta[0]**2/4*equal.mean()
            # Conditional finite pairs for partial algorithms are explicitly separate.
            row['defined_pair_fraction'] = float(finite.mean())
            moment(row, 'linear_squared_error', linear.loc[finite, 'error']**2)
            moment(row, 'tail_squared_error', tail.loc[finite, 'error']**2)
            rows.append(row)
    return rows


def independent_contrasts(summary):
    """No replicate pairing across designs/panels. MCSEs add in quadrature."""
    rows = []
    base = [k for k in IDENTITY if k not in ['design', 'rho']]+['panel']
    tasks = []
    for key, g in summary.groupby(base+['rho'], dropna=False):
        indexed = g.set_index('design')
        if {'bernoulli', 'cluster'} <= set(indexed.index):
            tasks.append((dict(zip(base+['rho'], key)), indexed.loc['cluster'], indexed.loc['bernoulli'], 'cluster_minus_node'))
    noise_keys = [k for k in IDENTITY if k != 'rho']
    for key, g in summary[summary.panel.isin(['core', 'noise'])].groupby(noise_keys, dropna=False):
        indexed = g.set_index('rho')
        if {0., 1.} <= set(indexed.index):
            tasks.append((dict(zip(noise_keys, key)), indexed.loc[1.], indexed.loc[0.], 'rho1_minus_rho0'))
    for row, a, b, contrast in tasks:
        row.update(contrast=contrast, master_a=int(a.master_seed), master_b=int(b.master_seed),
                   defined_fraction_a=a.defined_fraction, defined_fraction_b=b.defined_fraction,
                   valid_fraction_a=a.valid_fraction, valid_fraction_b=b.valid_fraction)
        for metric, se_name in [('bias', 'bias_mcse'), ('mse', 'mse_mcse'), ('rmse', 'rmse_mcse'),
                                ('prediction_mse_mean', 'prediction_mse_mcse'),
                                ('prediction_mean_mse_mean', 'prediction_mean_mse_mcse'),
                                ('oracle_variance_mean', 'oracle_variance_mcse')]:
            value = a[metric]-b[metric]
            se = np.sqrt(a[se_name]**2+b[se_name]**2)
            row.update({'delta_'+metric: value, 'delta_'+metric+'_mcse': se,
                        'delta_'+metric+'_lo': value-1.96*se, 'delta_'+metric+'_hi': value+1.96*se})
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', default='.')
    p.add_argument('--partial', action='store_true', help='Checkpoint audit only; not full study evidence')
    a = p.parse_args(); root = Path(a.root).resolve()
    code = root/'code' if (root/'code/configs').exists() else root
    out = root/'results'/('checkpoint_diagnostics' if a.partial else 'diagnostics')
    out.mkdir(exist_ok=True, parents=True)
    results = {'diagnostics_by_graph': [], 'prediction_gate_pairs_by_graph': [], 'support_coupling_by_graph': []}
    inventory = {}; records = []; totals = 0; exact = []
    masters = {}; exact_inputs = []
    for stage in ['core', 'noise', 'imbalance']:
        config = json.loads((code/f'configs/production_{stage}.json').read_text())
        masters[stage] = config['master_seed']
        folder = root/config['output']
        files = sorted(f for f in folder.glob('*.parquet') if not f.name.endswith('.tmp.parquet') and f.with_suffix('.json').exists())
        expected = len(config['graphs'])*len(config['designs'])*len(config['probabilities'])*len(config['rhos'])*len(config['gammas'])
        if not a.partial:
            assert len(files) == expected, (stage, len(files), expected)
        for file in files:
            frame = pd.read_parquet(file); totals += len(frame)
            meta = json.loads(file.with_suffix('.json').read_text())
            info = meta['graph']; graph = frame.graph.iloc[0]
            if graph in inventory:
                assert inventory[graph] == info
            inventory[graph] = info
            for name, function in [('diagnostics_by_graph', diagnostics), ('prediction_gate_pairs_by_graph', prediction_pairs),
                                   ('support_coupling_by_graph', coupling)]:
                rows = function(frame)
                for row in rows:
                    row.update(panel=stage, master_seed=config['master_seed'])
                results[name].extend(rows)
            records.append(dict(path=str(file.relative_to(root)), sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
        for file in sorted((folder/'exact_ht').glob('*.json')):
            exact_inputs.append(dict(path=str(file.relative_to(root)), sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
            for row in json.loads(file.read_text()):
                exact.append(dict(panel=stage, **row))
        print(f'HUTIAN_WAKE: supplementary diagnostics stage {stage} cells={len(files)}', flush=True)
    for name, rows in results.items():
        data = pd.DataFrame(rows); data.to_csv(out/(name+'.csv'), index=False)
        extra = ['reference'] if name.startswith('prediction') else []
        keys = [k for k in FAMILY if k in data]+['panel']+extra
        metrics = {'diagnostics_by_graph': ['error_sd', 'defined_fraction', 'estimable_fraction', 'prediction_mean_mse',
                        'prediction_mse', 'oracle_variance', 'assignment_bias_squared', 'mse_identity_residual', 'hc3_se',
                        'oracle_se', 'cover_hc3', 'cover_oracle', 'tail_absent_fraction', 'threshold_absent_fraction',
                        'oracle_to_iid_variance_ratio'],
                   'prediction_gate_pairs_by_graph': ['delta_mse', 'delta_prediction_mse', 'delta_prediction_mean_mse'],
                   'support_coupling_by_graph': ['identical_data_fraction', 'linear_squared_error', 'tail_squared_error',
                        'defined_pair_fraction', 'empirical_two_risk_bound']}[name]
        family_average(data, keys, metrics).to_csv(out/(name.replace('_by_graph', '_by_family')+'.csv'), index=False)
    pd.DataFrame([dict(graph=key, **value) for key, value in inventory.items()]).to_csv(out/'graph_inventory.csv', index=False)
    pd.DataFrame(exact).to_csv(out/'exact_ht_risk.csv', index=False)
    if not a.partial:
        summary = pd.read_csv(root/'results/summary/performance_by_graph.csv')
        summary['panel'] = np.select([summary.rho == 1., summary.p != .5], ['noise', 'imbalance'], default='core')
        summary['master_seed'] = summary.panel.map(masters)
        contrasts = independent_contrasts(summary)
        contrasts.to_csv(out/'independent_contrasts_by_graph.csv', index=False)
        keys = [k for k in FAMILY if k not in ['design', 'rho']]+['contrast']
        # Keep design for noise contrasts and rho for design contrasts; fill in
        # constants without merging the independent panels with each other.
        for key in ['design', 'rho', 'panel']:
            if key in contrasts: keys.append(key)
        family_average(contrasts, keys, [c for c in contrasts if c.startswith('delta_') and not c.endswith(('_mcse', '_lo', '_hi'))]).to_csv(out/'independent_contrasts_by_family.csv', index=False)
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != SCRIPT_HASH:
        raise RuntimeError('Analysis source changed during execution')
    manifest = dict(status='partial' if a.partial else 'complete', rows=totals, cells=len(records),
                    script_sha256=SCRIPT_HASH, inputs=records, exact_ht_inputs=exact_inputs)
    (out/'diagnostics_manifest.json').write_text(json.dumps(manifest, indent=2))
    print('HUTIAN_WAKE: supplementary claim diagnostics complete', flush=True)


if __name__ == '__main__':
    main()
