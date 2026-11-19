#!/usr/bin/env python3
"""Reproducible fixed-game SHAP analysis only; never imports/runs experiment.py.

Default: require all 27 main cells before any all-dataset result. An explicit
--partial exact selects complete 3-seed exact-game model cells. Sensitivity cells
are validated independently (six expected); absence never silently disappears.
All CIs describe instance sampling conditional on fixed seeds/games. No German
true-accuracy inference and no unconditional ACS certification are performed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

DATASETS = ('pima', 'acs', 'german')
MODELS = ('lr', 'rf', 'mlp')
SEEDS = (11, 23, 47)
BUDGETS = (1, 4, 16, 64)
DIMS = dict(pima=8, acs=10, german=20)
METHODS = dict(antithetic='phi', iid_oneway='nonantithetic', kernel='kernel')
GAPS = ('<.002', '.002-.01', '>=.01')
BOOT_REPS = 2000
BOOT_SEED = 20261104
WARNINGS = [
    'Exploratory/descriptive instance-cluster percentile bootstrap intervals, not finite-sample certificates; 2000 replicates.',
    'Seeds 11,23,47 are fixed, not sampled model-training replicates; LR seeds are not independent fitted-model evidence.',
    'Repeated explanations and repetition pairs are not independent instance observations.',
    'Boundary bootstrap intervals may collapse at 0 or 1; narrow/collapsed intervals do not certify reliability.',
    'ACS random-person scanning with household deduplication induces unequal household selection; sampling justification is absent. ACS intervals and Hoeffding values are descriptive, not unconditional certificates or survey-weighted population inference.',
    'German uses an approximate two-pool reference, not ground truth; all German match/error metrics concern reference agreement only, never true accuracy or certification.',
    'Reference-gap strata are descriptive, oracle-dependent, and conditional on the empirical game; not deployable selectors.',
    'B16 changes the background and hence the estimand; compare each estimate to its own recomputed target.',
    'Kernel control is plain constrained least squares without L1 feature selection. At budgets covering the cube it enumerates the full exact game, rather than sampling; cost is capped at 2**d background-averaged rows.',
    'Cached actual rows and timings include reference construction and all estimators, and cannot be assigned to individual methods or interpreted as deployment timings.',
    'Cell/seed/gap percentile intervals are marginal descriptive intervals. Effect comparisons additionally receive simultaneous max-deviation bootstrap bands across the reported exact-game contrast family; these bands remain descriptive and may degenerate at boundaries.',
]


def clean(obj):
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    if isinstance(obj, np.generic):
        return clean(obj.item())
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def write_json(path, obj):
    path.write_text(json.dumps(clean(obj), indent=2, allow_nan=False) + '\n')


def latex_table(df):
    # Avoid pandas Styler/Jinja2: no extra dependency or network installation.
    escape = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
              '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    def fmt(value):
        if value is None or (isinstance(value, (float, np.floating)) and not np.isfinite(value)):
            return '--'
        text = f'{value:.8g}' if isinstance(value, (float, np.floating)) else str(value)
        return ''.join(escape.get(char, char) for char in text)
    if not len(df.columns):
        return '% No eligible data.\n'
    lines = ['% Requires booktabs. Machine-readable full precision: matching CSV.',
             r'\begin{tabular}{' + 'l' * len(df.columns) + '}', r'\toprule',
             ' & '.join(fmt(c) for c in df.columns) + r' \\', r'\midrule']
    lines.extend(' & '.join(fmt(v) for v in row) + r' \\' for row in df.itertuples(index=False, name=None))
    return '\n'.join(lines + [r'\bottomrule', r'\end{tabular}', ''])


def save_table(out, name, rows):
    df = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    df.to_csv(out / f'{name}.csv', index=False, float_format='%.12g')
    (out / f'{name}.tex').write_text(latex_table(df))
    return df


def selection(phi):
    # Stable sorting enforces lower raw-feature index first on exact ties.
    ix = np.argsort(-np.abs(phi), axis=-1, kind='stable')[..., :3]
    z = np.zeros(phi.shape, dtype=bool)
    np.put_along_axis(z, ix, True, axis=-1)
    return z


def mean_valid(a, axis=None):
    a = np.asarray(a, dtype=float)
    count = np.isfinite(a).sum(axis=axis)
    total = np.where(np.isfinite(a), a, 0).sum(axis=axis)
    return np.divide(total, count, out=np.full(np.shape(total), np.nan), where=count > 0)


def interval(point, boot):
    valid = np.asarray(boot)[np.isfinite(boot)]
    if not len(valid):
        return (float(point), np.nan, np.nan)
    lo, hi = np.quantile(valid, [.025, .975])
    return (float(point), float(lo), float(hi))


def cluster_stat(values, indices):
    return mean_valid(values), mean_valid(np.asarray(values)[indices], axis=1)


def validate_cell(root, ds, model, seed, sensitivity=False):
    name = f'{ds}_{model}_{seed}' + ('_b16' if sensitivity else '')
    path = root / f'{name}.npz'
    report = dict(cell=name, sensitivity=sensitivity, status='missing', errors=[])
    if not path.exists() or not path.with_suffix('.json').exists():
        report['errors'] = ['missing completed NPZ and/or companion JSON']
        return report, None
    try:
        meta = json.loads(path.with_suffix('.json').read_text())
        with np.load(path, allow_pickle=False) as z:
            arrays = {k: z[k].copy() for k in z.files}
        n, d, bg = (10 if sensitivity else 30), DIMS[ds], (16 if sensitivity else 8)
        expected_meta = dict(dataset=ds, model=model, seed=seed, n=n, repetitions=20, background=bg,
                             reference_type='exact_enumeration' if d <= 10 else 'two_independent_permutation_pools')
        for k, value in expected_meta.items():
            if meta.get(k) != value:
                raise ValueError(f'metadata {k}: {meta.get(k)!r}, expected {value!r}')
        shapes = dict(phi=(n, 20, 4, d), reference=(n, d),
                      reference_pools=(n, d) if d <= 10 else (n, 2, d),
                      instances=(n,), budgets=(4,), efficiency=(n,),
                      nonantithetic=(n, 20, 4, d) if d <= 10 else (0,),
                      kernel=(n, 20, 4, d) if d <= 10 else (0,))
        for k, shape in shapes.items():
            if k not in arrays or arrays[k].shape != shape:
                raise ValueError(f'{k} shape {arrays.get(k, np.array([])).shape}, expected {shape}')
            if not np.isfinite(arrays[k]).all():
                raise ValueError(f'nonfinite values in {k}')
        if not np.array_equal(arrays['budgets'], BUDGETS):
            raise ValueError('wrong budget vector')
        if arrays['instances'].dtype.kind not in 'iu' or len(np.unique(arrays['instances'])) != n:
            raise ValueError('instances must be unique integer row IDs')
        data_meta = json.loads((root / f'data_{ds}.json').read_text())
        if data_meta['d'] != d or not np.array_equal(arrays['instances'], data_meta['instances'][:n]):
            raise ValueError('dimension or fixed instance IDs differ from data manifest')
        if len(data_meta['background']) < bg or len(set(data_meta['background'][:bg])) != bg:
            raise ValueError('background manifest incomplete')
        if not set(data_meta['background'][:bg]).issubset(data_meta['train']):
            raise ValueError('background not train-only')
        if not set(arrays['instances']).issubset(data_meta['test']):
            raise ValueError('instance not in test split')
        if ds == 'acs' and len(set(data_meta['test_cluster_ids'][:n])) != n:
            raise ValueError('ACS duplicate household clusters')
        if len(meta['counters']) != n:
            raise ValueError('wrong counter count')
        if d <= 10 and not np.allclose(arrays['reference_pools'], arrays['reference'], atol=1e-13, rtol=0):
            raise ValueError('exact reference pool differs from reference')
        if d > 10:
            if meta.get('reference_cycles_per_pool') != 512:
                raise ValueError('German reference pools must each have 512 cycles')
            if not np.allclose(arrays['reference_pools'].mean(axis=1), arrays['reference'], atol=1e-13, rtol=0):
                raise ValueError('German reference is not the two-pool mean')
        for p in BUDGETS:
            if meta['logical_model_rows_per_run'].get(str(p)) != bg * (2 + 2 * p * (d - 1)):
                raise ValueError('incorrect logical row budget')
        for c in meta['counters']:
            if c['actual_rows'] != bg * c['cached_coalitions'] or c['actual_rows'] < 0:
                raise ValueError('actual rows inconsistent with cached coalitions')
            if d <= 10 and c['cached_coalitions'] != 2**d:
                raise ValueError('exact cube incomplete')
        for k in ('cpu_seconds', 'wall_seconds', 'train_seconds'):
            if not np.isfinite(meta[k]) or meta[k] < 0:
                raise ValueError(f'invalid timing {k}')
        if not all(np.isfinite(v) for v in meta['metrics'].values()):
            raise ValueError('nonfinite model evaluation metric')
        for method, key in METHODS.items():
            if arrays[key].size:
                resid = np.max(np.abs(arrays[key].sum(axis=-1) - arrays['reference'].sum(axis=-1)[:, None, None]))
                if resid > 1e-8:
                    raise ValueError(f'{method} efficiency residual {resid}')
        report.update(status='valid', shape=list(arrays['phi'].shape), background=bg,
                      npz_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      json_sha256=hashlib.sha256(path.with_suffix('.json').read_bytes()).hexdigest())
        return report, dict(name=name, dataset=ds, model=model, seed=seed, sensitivity=sensitivity,
                            arrays=arrays, metadata=meta, data_metadata=data_meta)
    except (OSError, KeyError, ValueError, TypeError, EOFError, zipfile.BadZipFile) as exc:
        report.update(status='invalid', errors=[str(exc)])
        return report, None


def run_metrics(phi, ref):
    """Per-instance, per-budget statistics, averaging only runs inside this game."""
    z, target = selection(phi), selection(ref)[:, None, None, :]
    l1 = np.abs(phi - ref[:, None, None, :]).sum(axis=-1)
    material = np.abs(ref) >= .01
    sign_num = ((np.sign(phi) == np.sign(ref[:, None, None, :])) & material[:, None, None, :]).sum(axis=-1)
    sign_den = material.sum(axis=-1)[:, None, None]
    signs = np.divide(sign_num, sign_den, out=np.full(sign_num.shape, np.nan), where=sign_den > 0)
    r = phi.shape[1]
    a, b = np.triu_indices(r, 1)
    freq = z.mean(axis=1)
    q = freq.mean(axis=-1)
    variance = r / (r - 1) * freq * (1 - freq)
    stability = 1 - mean_valid(variance, axis=-1) / (q * (1 - q))
    return dict(
        top3_match=np.all(z == target, axis=-1).mean(axis=1),
        reference_top3_overlap=(z & target).sum(axis=-1).mean(axis=1) / 3,
        absolute_l1=l1.mean(axis=1),
        normalized_l1=(l1 / np.maximum(np.abs(ref).sum(axis=-1), .01)[:, None, None]).mean(axis=1),
        material_sign_agreement=mean_valid(signs, axis=1),
        pairwise_top3_match=np.all(z[:, a] == z[:, b], axis=-1).mean(axis=1),
        pairwise_mean_overlap=(z[:, a] & z[:, b]).sum(axis=-1).mean(axis=1) / 3,
        nogueira_stability=stability,
        efficiency_residual=np.abs(phi.sum(axis=-1) - ref.sum(axis=-1)[:, None, None]).mean(axis=1),
        low_signal_fraction=np.repeat((np.abs(ref).sum(axis=-1) < .01)[:, None], 4, axis=1).astype(float),
        material_feature_coverage=np.repeat(material.any(axis=-1)[:, None], 4, axis=1).astype(float),
    )


def metric_summary(metrics, indices):
    row = {}
    for metric, values in metrics.items():
        point, boot = cluster_stat(values, indices)
        estimate, lo, hi = interval(point, boot)
        row.update({metric: estimate, metric + '_lo': lo, metric + '_hi': hi,
                    metric + '_n_instances': int(np.isfinite(values).sum())})
    return row


def gap_ids(ref):
    ordered = np.sort(np.abs(ref), axis=-1)[..., ::-1]
    return np.digitize(ordered[..., 2] - ordered[..., 3], [.002, .01], right=False)


def conditional_stat(values, mask, indices):
    # Equal game weights over fixed seeds, then ratio over resampled instances.
    valid = mask & np.isfinite(values)
    num = np.where(valid, values, 0).sum(axis=0)
    den = valid.sum(axis=0)
    point = num.sum() / den.sum() if den.sum() else np.nan
    bn, bd = num[indices].sum(axis=1), den[indices].sum(axis=1)
    boot = np.divide(bn, bd, out=np.full(len(indices), np.nan), where=bd > 0)
    return point, boot, int(den.sum()), int((den > 0).sum())


def resource_tables(out, cells):
    records, logical = [], []
    for c in cells:
        meta = c['metadata']
        ctr = meta['counters']
        records.append(dict(cell=c['name'], dataset=c['dataset'], model=c['model'], seed=c['seed'],
                            sensitivity=c['sensitivity'], n=meta['n'], background=meta['background'],
                            cpu_seconds=meta['cpu_seconds'], wall_seconds=meta['wall_seconds'],
                            train_wall_seconds=meta['train_seconds'],
                            prediction_wall_seconds=sum(x['prediction_seconds'] for x in ctr),
                            actual_model_rows=sum(x['actual_rows'] for x in ctr),
                            cached_coalitions=sum(x['cached_coalitions'] for x in ctr),
                            efficiency_max=float(c['arrays']['efficiency'].max()),
                            warnings=json.dumps(meta['warnings']), **meta['metrics']))
        for p in BUDGETS:
            d, bg = DIMS[c['dataset']], meta['background']
            for method in (METHODS if d <= 10 else ('antithetic',)):
                rows = bg * (min(2 + 2*p*(d-1), 2**d) if method == 'kernel' else (2 + 2*p*(d-1)))
                logical.append(dict(cell=c['name'], dataset=c['dataset'], model=c['model'], seed=c['seed'],
                                    sensitivity=c['sensitivity'], method=method, budget=p,
                                    logical_model_rows_per_run=rows,
                                    full_enumeration=method == 'kernel' and 2+2*p*(d-1) >= 2**d))
    df = save_table(out, 'resources', records)
    save_table(out, 'logical_costs', logical)
    sums = []
    if not df.empty:
        for sensitivity, sub in df.groupby('sensitivity', sort=False):
            sums.append(dict(sensitivity=bool(sensitivity), completed_cells=len(sub),
                             **{k: float(sub[k].sum()) for k in ('cpu_seconds', 'wall_seconds', 'train_wall_seconds',
                                 'prediction_wall_seconds', 'actual_model_rows', 'cached_coalitions')},
                             warning_cells=sub.loc[sub.warnings != '[]', 'cell'].tolist()))
    return sums


def paper_tables(out, cells, macro):
    """Compact LaTeX views; full numerical columns remain in the raw CSV/TeX."""
    def compact(df, label):
        result = pd.DataFrame(index=df.index)
        if 'dataset' in df:
            result['Game'] = df.dataset + '/' + df.model.str.upper()
        result['Method'] = df.method.map({'antithetic':'Anti.', 'iid_oneway':'IID', 'kernel':'Kernel'})
        result['P'] = df.budget
        for key, title in [('top3_match', 'Top3 [95% CI]'), ('pairwise_top3_match', 'Pair match [95% CI]')]:
            result[title] = [f'{p:.3f} [{lo:.3f}, {hi:.3f}]' for p, lo, hi in zip(df[key], df[key+'_lo'], df[key+'_hi'])]
        for key, title in [('absolute_l1', 'L1'), ('normalized_l1', 'Norm L1'), ('nogueira_stability', 'Stability')]:
            result[title] = [f'{value:.4g}' for value in df[key]]
        return ('% ' + label + '\n' + r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}' + '\n'
                + latex_table(result) + '\n' + r'\endgroup' + '\n')
    (out/'cell_summary_raw.tex').write_text(latex_table(cells))
    sections = []
    for ds in DATASETS:
        sub = cells[cells.dataset == ds]
        if sub.empty:
            continue
        text = compact(sub, ds + (' APPROX reference agreement ONLY' if ds == 'german' else ' exact targets'))
        (out/f'cell_summary_{ds}.tex').write_text(text)
        sections.append(text)
    (out/'cell_summary.tex').write_text('\n\n'.join(sections))
    if not macro.empty:
        (out/'exact_macro_raw.tex').write_text(latex_table(macro))
        (out/'exact_macro.tex').write_text(compact(macro, 'Six exact dataset-model cells, fixed-seed averages; descriptive CIs'))


def analyze(cells, indices, out):
    groups = {}
    individual = []
    seed_rows, cell_rows, cluster_rows, gap_rows, pool_rows = [], [], [], [], []
    pool_clusters = []
    for c in cells:
        if c['sensitivity']:
            continue
        ds, model, seed = c['dataset'], c['model'], c['seed']
        a, ref = c['arrays'], c['arrays']['reference']
        for method, key in METHODS.items():
            if not a[key].size:
                continue
            metrics = run_metrics(a[key], ref)
            groups.setdefault((ds, model, method), []).append((seed, metrics, ref))
            for bi, budget in enumerate(BUDGETS):
                label = 'exact_target' if ds != 'german' else 'APPROX_reference_ONLY'
                row = dict(dataset=ds, model=model, seed=seed, method=method, budget=budget, target=label)
                row.update(metric_summary({k: v[:, bi] for k, v in metrics.items()}, indices[ds]))
                seed_rows.append(row)
        if ds == 'german':
            pools = a['reference_pools']
            agree = np.all(selection(pools[:, 0]) == selection(pools[:, 1]), axis=-1).astype(float)
            difference = np.abs(pools[:, 0] - pools[:, 1]).sum(axis=-1)
            pool_clusters.append((model, seed, agree, difference))
            for metric, vec in [('reference_pool_top3_agreement', agree), ('pool_difference_l1', difference)]:
                point, boot = cluster_stat(vec, indices[ds])
                est, lo, hi = interval(point, boot)
                pool_rows.append(dict(dataset=ds, model=model, seed=str(seed), metric=metric,
                                      mean=est, lo=lo, hi=hi, target='APPROX_reference_ONLY'))
    aggregate = {}
    boot_top = {}
    for (ds, model, method), items in groups.items():
        items.sort(key=lambda item: item[0])
        if [x[0] for x in items] != list(SEEDS):
            raise ValueError(f'incomplete fixed seed set for {ds}/{model}/{method}')
        stack = {k: np.stack([m[k] for _, m, _ in items]) for k in items[0][1]}
        avg = {k: mean_valid(v, axis=0) for k, v in stack.items()}
        aggregate[(ds, model, method)] = avg
        for bi, budget in enumerate(BUDGETS):
            row = dict(dataset=ds, model=model, method=method, budget=budget,
                       target='exact_target' if ds != 'german' else 'APPROX_reference_ONLY',
                       n_instances=30, fixed_seeds='11,23,47', runs_per_seed_instance=20)
            row.update(metric_summary({k: v[:, bi] for k, v in avg.items()}, indices[ds]))
            if ds != 'german' and method == 'antithetic':
                row['bootstrap_095_relation_descriptive_only'] = ('interval_at_or_above_095_NOT_certificate'
                    if row['top3_match_lo'] >= .95 else ('interval_below_095' if row['top3_match_hi'] < .95 else 'interval_overlaps_095'))
                row['hoeffding_24_lower_illustration'] = max(0., row['top3_match'] - math.sqrt(math.log(24/.05)/(2*30)))
                row['certification_status'] = 'inconclusive_sample_size_only; ACS assumptions unverified' if ds == 'acs' else 'inconclusive_sample_size_only'
            cell_rows.append(row)
            boot_top[(ds, model, method, budget)] = cluster_stat(avg['top3_match'][:, bi], indices[ds])[1]
            for i, instance_id in enumerate(next(c['arrays']['instances'] for c in cells if c['dataset'] == ds and not c['sensitivity'])):
                cluster_rows.append(dict(dataset=ds, model=model, method=method, budget=budget,
                                         instance_id=int(instance_id), **{k: float(v[i, bi]) for k, v in avg.items()}))
        if ds != 'german':
            bins = np.stack([gap_ids(ref) for _, _, ref in items])
            for gi, gap in enumerate(GAPS):
                for bi, budget in enumerate(BUDGETS):
                    point, boot, games, clusters = conditional_stat(stack['top3_match'][..., bi], bins == gi, indices[ds])
                    est, lo, hi = interval(point, boot)
                    gap_rows.append(dict(dataset=ds, model=model, method=method, budget=budget,
                                         gap_bin=gap, top3_match=est, top3_match_lo=lo, top3_match_hi=hi,
                                         n_seed_instance_games=games, n_instance_clusters=clusters,
                                         empty_bootstrap_replicates=int((~np.isfinite(boot)).sum()),
                                         interpretation='descriptive_oracle_dependent'))
    for model in MODELS:
        g = [r for r in pool_clusters if r[0] == model]
        if len(g) == 3:
            for metric, pos in [('reference_pool_top3_agreement', 2), ('pool_difference_l1', 3)]:
                vec = np.stack([r[pos] for r in g]).mean(axis=0)
                point, boot = cluster_stat(vec, indices['german'])
                est, lo, hi = interval(point, boot)
                pool_rows.append(dict(dataset='german', model=model, seed='fixed_seed_average', metric=metric,
                                      mean=est, lo=lo, hi=hi, target='APPROX_reference_ONLY'))
    save_table(out, 'per_seed', seed_rows)
    cell_df = save_table(out, 'cell_summary', cell_rows)
    save_table(out, 'instance_clusters', cluster_rows)
    save_table(out, 'gap_summary', gap_rows)
    save_table(out, 'reference_pool_summary', pool_rows)

    # Equal-weight macro over 2 datasets x 3 models, never over their raw rows.
    exact_complete = all((ds, model, method) in aggregate for ds in ('pima', 'acs') for model in MODELS for method in METHODS)
    macro_rows, macro_boot = [], {}
    if exact_complete:
        for method in METHODS:
            for bi, budget in enumerate(BUDGETS):
                row = dict(method=method, budget=budget, n_dataset_model_cells=6, n_instances_per_dataset=30,
                           target='exact_target_macro_six_cells')
                for metric in aggregate[('pima', 'lr', method)]:
                    points, boots = [], []
                    for ds in ('pima', 'acs'):
                        for model in MODELS:
                            point, boot = cluster_stat(aggregate[(ds, model, method)][metric][:, bi], indices[ds])
                            points.append(point); boots.append(boot)
                    est, lo, hi = interval(mean_valid(points), mean_valid(boots, axis=0))
                    row.update({metric: est, metric+'_lo': lo, metric+'_hi': hi})
                macro_rows.append(row)
                macro_boot[(method, budget)] = np.mean([boot_top[(ds, m, method, budget)] for ds in ('pima', 'acs') for m in MODELS], axis=0)
    macro_df = save_table(out, 'exact_macro', macro_rows)

    # All prespecified method/budget contrasts form one simultaneous family.
    contrasts, contrast_boot = [], []
    for ds in ('pima', 'acs'):
        for model in MODELS:
            if (ds, model, 'antithetic') not in aggregate:
                continue
            for budget in BUDGETS:
                for control in ('iid_oneway', 'kernel'):
                    left = cell_df.query('dataset == @ds and model == @model and method == "antithetic" and budget == @budget').iloc[0]
                    right = cell_df.query('dataset == @ds and model == @model and method == @control and budget == @budget').iloc[0]
                    contrasts.append(dict(dataset=ds, model=model, budget=budget, contrast=f'antithetic_minus_{control}',
                                          top3_match_difference=left.top3_match-right.top3_match))
                    contrast_boot.append(boot_top[(ds, model, 'antithetic', budget)] - boot_top[(ds, model, control, budget)])
            lo = cell_df.query('dataset == @ds and model == @model and method == "antithetic" and budget == 1').iloc[0]
            hi = cell_df.query('dataset == @ds and model == @model and method == "antithetic" and budget == 64').iloc[0]
            contrasts.append(dict(dataset=ds, model=model, budget=64, contrast='antithetic_P64_minus_P1', top3_match_difference=hi.top3_match-lo.top3_match))
            contrast_boot.append(boot_top[(ds, model, 'antithetic', 64)] - boot_top[(ds, model, 'antithetic', 1)])
    if exact_complete:
        for budget in BUDGETS:
            for control in ('iid_oneway', 'kernel'):
                left = macro_df.query('method == "antithetic" and budget == @budget').iloc[0]
                right = macro_df.query('method == @control and budget == @budget').iloc[0]
                contrasts.append(dict(dataset='exact_macro', model='all_six_cells', budget=budget, contrast=f'antithetic_minus_{control}', top3_match_difference=left.top3_match-right.top3_match))
                contrast_boot.append(macro_boot[('antithetic', budget)] - macro_boot[(control, budget)])
        lo = macro_df.query('method == "antithetic" and budget == 1').iloc[0]
        hi = macro_df.query('method == "antithetic" and budget == 64').iloc[0]
        contrasts.append(dict(dataset='exact_macro', model='all_six_cells', budget=64, contrast='antithetic_P64_minus_P1', top3_match_difference=hi.top3_match-lo.top3_match))
        contrast_boot.append(macro_boot[('antithetic', 64)]-macro_boot[('antithetic', 1)])
    if contrasts:
        cb = np.stack(contrast_boot, axis=1)
        points = np.array([r['top3_match_difference'] for r in contrasts])
        radius = float(np.quantile(np.max(np.abs(cb-points), axis=1), .95))
        for j, row in enumerate(contrasts):
            _, lo, hi = interval(points[j], cb[:, j])
            row.update(paired_bootstrap_lo=lo, paired_bootstrap_hi=hi,
                       simultaneous_max_deviation_lo=max(-1., points[j]-radius),
                       simultaneous_max_deviation_hi=min(1., points[j]+radius),
                       family_size=len(contrasts), correction='95% joint max-centered-absolute-deviation paired bootstrap; exploratory')
        np.savez_compressed(out/'contrast_bootstrap.npz', samples=cb, estimates=points)
    save_table(out, 'paired_comparisons', contrasts)
    paper_tables(out, cell_df, macro_df)
    return cell_df, macro_df, pd.DataFrame(gap_rows), pd.DataFrame(pool_rows), contrasts


def sensitivity(cells, out):
    lookup = {c['name']: c for c in cells}
    rows = []
    # First-ten-only sensitivity uses an independent deterministic stream,
    # shared across all B8/B16 methods and models within each dataset.
    sens_indices = {ds: np.random.default_rng(np.random.SeedSequence([BOOT_SEED, 16, di])).integers(0, 10, (BOOT_REPS, 10))
                    for di, ds in enumerate(DATASETS[:2])}
    for ds in DATASETS[:2]:
        for model in MODELS:
            name = f'{ds}_{model}_11'
            if name not in lookup or name+'_b16' not in lookup:
                continue
            base, changed = lookup[name], lookup[name+'_b16']
            a, b = base['arrays'], changed['arrays']
            if not np.array_equal(a['instances'][:10], b['instances']):
                raise ValueError('B16 not first ten prespecified B8 instances')
            for key in ('model_parameters', 'metrics'):
                if base['metadata'][key] != changed['metadata'][key]:
                    raise ValueError(f'B8/B16 fitted-model {key} differs; background is not the only change')
            idx = sens_indices[ds]
            targets_changed = (~np.all(selection(a['reference'][:10]) == selection(b['reference']), axis=-1)).astype(float)
            delta = np.abs(a['reference'][:10]-b['reference']).sum(axis=-1)
            for method, key in METHODS.items():
                am = run_metrics(a[key][:10], a['reference'][:10])
                bm = run_metrics(b[key], b['reference'])
                for bi, budget in enumerate(BUDGETS):
                    row = dict(dataset=ds, model=model, seed=11, method=method, budget=budget, n_instances=10,
                               interpretation='different_estimands_each_compared_to_own_recomputed_target')
                    vecs = dict(reference_top3_change=targets_changed, reference_absolute_l1_change=delta,
                                b8_top3_match=am['top3_match'][:, bi], b16_top3_match=bm['top3_match'][:, bi],
                                b16_minus_b8_own_target_match=bm['top3_match'][:, bi]-am['top3_match'][:, bi],
                                b8_absolute_l1=am['absolute_l1'][:, bi], b16_absolute_l1=bm['absolute_l1'][:, bi])
                    for metric in ('normalized_l1', 'material_sign_agreement', 'pairwise_top3_match',
                                   'nogueira_stability', 'reference_top3_overlap', 'pairwise_mean_overlap'):
                        vecs['b8_'+metric] = am[metric][:, bi]
                        vecs['b16_'+metric] = bm[metric][:, bi]
                    row.update(metric_summary(vecs, idx))
                    row['reference_top3_change_count'] = int(targets_changed.sum())
                    rows.append(row)
    save_table(out, 'background_sensitivity', rows)
    return rows, sens_indices


def definitions():
    return dict(
        top3_match='Unordered set equality of three largest absolute attributions vs target; stable index tie-break; runs then fixed seeds averaged within instance.',
        pairwise_top3_match='Fraction of the 190 unordered within-game repetition pairs with equal top-3 subsets; average fixed seeds within instance; do not count pairs as samples.',
        reference_top3_overlap='Mean |estimated top3 intersect reference top3|/3.',
        pairwise_mean_overlap='Mean pairwise within-game |top3_r intersect top3_s|/3.',
        absolute_l1='sum_j |estimate_j-reference_j| in probability units; mean over runs.',
        normalized_l1='Absolute L1 / max(sum_j |reference_j|,0.01), computed per game before averaging.',
        material_sign_agreement='Fraction of reference features with |phi_j|>=0.01 whose sign is recovered; undefined when none; equal available-seed average within instance and equal valid-instance mean; coverage and valid n reported.',
        nogueira_stability='1 - mean_j [R/(R-1)*p_j*(1-p_j)] / [q*(1-q)], R=20, top3 selection frequency p_j and q=3/d. Never clipped; computed per fixed game, then averaged.',
        efficiency_residual='Mean absolute sum(estimate)-sum(reference); stored max antithetic residual also in resources table.',
        reference_pool_top3_agreement='German independent 512-cycle pools: top3 equality, not true-reference accuracy.',
        pool_difference_l1='German sum_j |poolA_j-poolB_j|, probability units.',
        gap_bin='Reference absolute rank3-minus-rank4 gap: <.002, [.002,.01), >=.01. Per seed-instance game; average selected games using cluster-bootstrap ratios.',
        uncertainty='2000 paired instance-cluster bootstrap replicates; same indices within dataset across all methods/models/budgets/fixed seeds. Independent dataset streams. Percentile 2.5/97.5 intervals; undefined bootstrap ratios omitted and counted.',
        exact_macro='Equal mean over six dataset-model cells (pima/acs x lr/rf/mlp); each seed/run mean within instance; bootstrap instances independently across datasets, shared across models within dataset.',
        multiple_comparisons='All exact antithetic-minus-controls and P64-minus-P1 contrasts, including macro contrasts, use one 95% max-centered-absolute-deviation paired-bootstrap simultaneous band. Marginal intervals also reported; no unadjusted significance/certification claims.',
        hoeffding='max(0,mean-sqrt(log(24/.05)/(2*n))), one-sided Bonferroni sample-size illustration over 24 exact antithetic dataset/model/budget cells. ACS sampling assumptions unverified; not an unconditional certificate.',
        costs='Permutation/iid logical rows per run B*(2+2P*(d-1)); kernel rows capped at B*2**d on full enumeration. Actual cached rows/timings aggregate shared game reference and estimator work. train_seconds/prediction_seconds are wall timings despite names.')


def write_report(out, overview, macro, pools, sensitivity_rows, comparisons):
    lines = ['# SHAP study analysis', '', f'**Status:** {overview["status"]}. {overview["scope"]}.',
             f'Main artifacts: {overview["main_valid"]}/27 valid (n=30, R=20, P=1,4,16,64). B16: {overview["sensitivity_valid"]}/6 valid (n=10, seed=11).',
             '', '## Exact-game macro top-3 match', '',
             'Equal-weight average over Pima/ACS x LR/RF/MLP; fixed seeds/runs averaged within instance. Intervals are exploratory/descriptive, not certification.',
             '', '| Method | P | Match | 95% paired cluster CI |', '|---|---:|---:|---:|']
    for row in macro.itertuples():
        lines.append(f'| {row.method} | {row.budget} | {row.top3_match:.6f} | [{row.top3_match_lo:.6f}, {row.top3_match_hi:.6f}] |')
    lines += ['', '## Effect sizes and multiplicity', '']
    for row in comparisons:
        if row['dataset'] == 'exact_macro' and row['contrast'] == 'antithetic_P64_minus_P1':
            lines += [f"P64-minus-P1 top-3 match difference: {100*row['top3_match_difference']:.3f} percentage points; paired 95% CI [{100*row['paired_bootstrap_lo']:.3f}, {100*row['paired_bootstrap_hi']:.3f}]; simultaneous {row['family_size']}-contrast exploratory bootstrap band [{100*row['simultaneous_max_deviation_lo']:.3f}, {100*row['simultaneous_max_deviation_hi']:.3f}]."]
    lines += ['All exact method comparisons and budget-gain contrasts are in paired_comparisons.csv/tex. No uncorrected significance tests or universal reliability declarations are made.',
              '', '## German: approximate reference diagnostics only', '']
    if pools.empty:
        lines += ['German omitted in explicit exact-only partial mode.']
    else:
        for row in pools[pools.seed == 'fixed_seed_average'].itertuples():
            lines.append(f'- {row.model} {row.metric}: {row.mean:.6g} [{row.lo:.6g}, {row.hi:.6g}].')
        lines += ['Pool agreement is convergence evidence, not accuracy against true Shapley values; no formal reference coverage or certification is inferred.']
    lines += ['', '## Background sensitivity (different estimands)', '']
    for row in sensitivity_rows:
        if row['method'] == 'antithetic' and row['budget'] == 64:
            lines.append(f"- {row['dataset']}/{row['model']}: reference top-3 changes in {row['reference_top3_change_count']}/10 fixed instances; own-target B8 vs B16 top-3 match {row['b8_top3_match']:.3f} vs {row['b16_top3_match']:.3f}. Full paired intervals and metrics: background_sensitivity.csv/tex.")
    illustration = overview['hoeffding_illustration']
    lines += ['', '## Sample-size illustration, not ACS certification',
              f"Bonferroni one-sided Hoeffding over 24 exact antithetic cells: lower=max(0,mean-{illustration['penalty']:.6f}). At perfection n=30 reaches at most {illustration['maximum_lower_bound_at_perfection']:.6f}; n>={illustration['minimum_n_to_reach_095_at_perfection']} would be needed for a .95 lower bound at observed perfection under justified sampling assumptions. ACS household PPS-style selection is not justified by the current design.",
              '', '## Resources', '']
    for row in overview['resources']:
        lines.append(f"- {'B16 sensitivity' if row['sensitivity'] else 'Main'}: {row['completed_cells']} artifacts; summed CPU {row['cpu_seconds']:.6f} s; actual shared cached model rows {row['actual_model_rows']:.0f}; summed cell wall {row['wall_seconds']:.6f} s (not elapsed parallel makespan).")
    lines += ['Per-cell held-out AUC, log loss, accuracy, fit warnings and resource counters: resources.csv/tex. Logical per-run uncached row costs: logical_costs.csv/tex. Actual timings/rows include the shared references and all methods, not per-explanation deployment cost.',
              '', '## Metric definitions', '']
    lines += [f'- **{key}:** {value}' for key, value in overview['definitions'].items()]
    lines += ['', '## Caveats', ''] + ['- '+w for w in overview['warnings']]
    lines += ['', '## Reproduce / use outputs', '', '```sh',
              overview['command'],
              f'python {out}/plot.py --out {out}',
              f'python {Path(__file__).resolve()} --self-test', '```',
              '- summary.json: numerical results, validation state, definitions, warnings and resource totals.',
              '- cell_summary.csv: full numerical summaries and CIs; cell_summary.tex: compact per-dataset tables. Separate cell_summary_pima/acs/german.tex may be included individually. Booktabs is required.',
              '- exact_macro.csv/tex, per_seed.csv/tex, gap_summary.csv/tex, reference_pool_summary.csv/tex, paired_comparisons.csv/tex, background_sensitivity.csv/tex: corresponding raw numbers and LaTeX. *_raw.tex retains full-column views where compact views are provided.',
              '- budget_accuracy.png, repeatability_accuracy.png, gap_budget.png (+PDF): measured figures. Each matching directory has plot.py, inputs.csv, plot.png/pdf, figure-spec.md and audit.md.',
              '- analysis_inputs.npz: complete source arrays plus every deterministic bootstrap index array. input_metadata.json and validation.json retain metadata and input SHA256 hashes.',
              '- instance_clusters.csv/tex: seed/run-averaged paired cluster observations. contrast_bootstrap.npz: joint contrast replicates in paired_comparisons.csv row order.',
              '- The copied analyze.py can be run with explicit --results and --out paths; original source is /work/analyze.py. --partial exact is opt-in and never labelled a final all-dataset analysis.',
              '', '## Recommended next experiments (not run here)',
              '1. Prespecify a justified equal-probability household or design-weighted ACS audit before making population-level claims; increase independent instance clusters if certification is the goal.',
              '2. Increase independent German reference-pool budgets and examine remaining top-3 disagreements, retaining all cases and approximate-reference labels.', '']
    (out/'README.md').write_text('\n'.join(lines))


def self_test():
    ref = np.array([[4., 3., 2., 1., 0.]])
    phi = np.repeat(np.repeat(ref[:, None, None, :], 20, axis=1), 4, axis=2)
    m = run_metrics(phi, ref)
    assert np.all(m['top3_match'] == 1) and np.allclose(m['nogueira_stability'], 1)
    assert np.all(m['absolute_l1'] == 0) and np.all(m['pairwise_mean_overlap'] == 1)
    # Two opposite top3 sets in d=6 have Nogueira=-1 at R=2, not zero.
    alt = np.array([[[[3., 2., 1., 0., 0., 0.]], [[0., 0., 0., 3., 2., 1.]]]])
    assert np.allclose(run_metrics(alt, alt[:, 0, 0])['nogueira_stability'], -1)
    tie = selection(np.zeros((1, 8)))
    assert np.array_equal(np.flatnonzero(tie), [0, 1, 2])
    assert gap_ids(np.array([[.04, .03, .02, .02, 0.]]))[0] == 0
    idx = np.array([[0, 0], [1, 1]])
    assert np.array_equal(cluster_stat(np.array([0., 1.]), idx)[1], [0, 1])
    assert mean_valid([np.nan, 1]) == 1
    assert np.isnan(mean_valid([np.nan]))
    print('Analysis self-tests passed (synthetic unit tests only; never used in study outputs).')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--results', type=Path, default=Path(__file__).resolve().parent/'results')
    ap.add_argument('--out', type=Path, default=Path(__file__).resolve().parent/'analysis')
    ap.add_argument('--partial', choices=['exact'], help='Explicit exact-only subset, never final all-dataset analysis')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    validation, loaded = [], []
    for ds in DATASETS:
        for model in MODELS:
            for seed in SEEDS:
                row, cell = validate_cell(args.results, ds, model, seed)
                validation.append(row)
                if cell is not None:
                    loaded.append(cell)
    for ds in DATASETS[:2]:
        for model in MODELS:
            row, cell = validate_cell(args.results, ds, model, 11, True)
            validation.append(row)
            if cell is not None:
                loaded.append(cell)
    main_valid = [r for r in validation if not r['sensitivity'] and r['status'] == 'valid']
    sens_valid = [r for r in validation if r['sensitivity'] and r['status'] == 'valid']
    all_main = len(main_valid) == 27
    write_json(out/'validation.json', validation)
    pending = [r['cell'] for r in validation if r['status'] != 'valid']
    overview = dict(status='pending_main_cells', main_valid=len(main_valid), main_required=27,
                    sensitivity_valid=len(sens_valid), sensitivity_required=6, pending=pending,
                    command=f'python {Path(__file__).resolve()} --results {args.results.resolve()} --out {out}',
                    warnings=WARNINGS, definitions=definitions(),
                    validation=str(out/'validation.json'))
    if not all_main and args.partial is None:
        # Never leave a stale complete/partial summary presented as this run.
        if (out/'summary.json').exists():
            shutil.copy2(out/'summary.json', out/'previous_summary.json')
            overview['previous_analysis_outputs_not_refreshed'] = True
        write_json(out/'pending.json', overview)
        write_json(out/'summary.json', overview)
        print(json.dumps(clean(overview | {'warnings': 'See summary/pending JSON'}), indent=2))
        return 2
    selected = loaded
    if args.partial:
        complete = {(ds, model) for ds in DATASETS[:2] for model in MODELS
                    if sum(c['dataset'] == ds and c['model'] == model and not c['sensitivity'] for c in loaded) == 3}
        selected = [c for c in loaded if (c['dataset'], c['model']) in complete]
        if not complete:
            write_json(out/'summary.json', overview)
            print('No complete exact model cell (all 3 fixed seeds) available.')
            return 2
    from importlib.metadata import version
    write_json(out/'versions.json', {'python': sys.version, **{package: version(package)
               for package in ('numpy', 'pandas', 'matplotlib', 'pillow')}})
    # Shared resampling indices: fixed seed sequences make independent dataset
    # streams reproducible even if a previous run selected fewer datasets.
    indices = {ds: np.random.default_rng(np.random.SeedSequence([BOOT_SEED, di])).integers(0, 30, (BOOT_REPS, 30))
               for di, ds in enumerate(DATASETS)}
    cell_df, macro, gaps, pools, comparisons = analyze(selected, indices, out)
    sens, sens_indices = sensitivity(selected, out)
    costs = resource_tables(out, selected)
    raw = {f'{c["name"]}__{k}': v for c in selected for k, v in c['arrays'].items()}
    raw.update({f'bootstrap__{ds}': idx for ds, idx in indices.items()})
    raw.update({f'bootstrap_sensitivity__{ds}': idx for ds, idx in sens_indices.items()})
    np.savez_compressed(out/'analysis_inputs.npz', **raw)
    write_json(out/'input_metadata.json', {c['name']: {'run': c['metadata'], 'data': c['data_metadata']} for c in selected})
    shutil.copy2(Path(__file__), out/'analyze.py') if Path(__file__).resolve() != (out/'analyze.py').resolve() else None
    threshold_n = math.ceil(math.log(24/.05)/(2*(1-.95)**2))
    overview.update(status='partial_exact' if args.partial else ('complete' if len(sens_valid) == 6 else 'main_complete_sensitivity_pending'),
                    scope='EXACT-ONLY PARTIAL; not all-dataset final analysis' if args.partial else '27 validated main cells',
                    analyzed_main_cells=sum(not c['sensitivity'] for c in selected),
                    analyzed_sensitivity_cells=sum(c['sensitivity'] for c in selected),
                    bootstrap=dict(replicates=BOOT_REPS, seed=BOOT_SEED, resampling='paired instance clusters; independent datasets'),
                    exact_macro=macro.to_dict(orient='records'),
                    antithetic_cells=cell_df[cell_df.method == 'antithetic'].to_dict(orient='records'),
                    reference_pool_summary=pools.to_dict(orient='records'),
                    resources=costs,
                    hoeffding_illustration=dict(family_size=24, alpha=.05, n=30,
                        penalty=math.sqrt(math.log(24/.05)/(2*30)), maximum_lower_bound_at_perfection=1-math.sqrt(math.log(24/.05)/(2*30)),
                        minimum_n_to_reach_095_at_perfection=threshold_n,
                        conclusion='inconclusive at n=30; ACS assumptions unverified; not an unconditional certificate'),
                    paired_comparison_family_size=len(comparisons),
                    boundary_cells=cell_df.loc[(cell_df.top3_match_lo == cell_df.top3_match_hi), ['dataset','model','method','budget','top3_match']].to_dict(orient='records'),
                    outputs=sorted(p.name for p in out.iterdir() if p.is_file()),
                    analysis_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write_json(out/'summary.json', overview)
    from importlib.util import spec_from_file_location, module_from_spec
    plot_path = Path(__file__).resolve().parent/'analysis'/'plot.py'
    # Saved analyze.py can replay in its directory too.
    if not plot_path.exists():
        plot_path = Path(__file__).resolve().parent/'plot.py'
    if plot_path.exists():
        spec = spec_from_file_location('study_plots', plot_path)
        plotting = module_from_spec(spec); spec.loader.exec_module(plotting)
        plotting.render_all(out, partial=bool(args.partial))
        overview['outputs'] = sorted(p.name for p in out.iterdir() if p.is_file())
        write_json(out/'summary.json', overview)
    else:
        overview['warnings'].append('Plot replay script not found: expected analysis/plot.py next to source.')
        write_json(out/'summary.json', overview)
    write_report(out, overview, macro, pools, sens, comparisons)
    overview['outputs'] = sorted(p.name for p in out.iterdir() if p.is_file())
    write_json(out/'summary.json', overview)
    print(f'Status: {overview["status"]}; main validated {len(main_valid)}/27; sensitivity {len(sens_valid)}/6.')
    print(f'Outputs: {out}; pending cells: {pending}')
    if not macro.empty:
        print(macro[['method', 'budget', 'top3_match', 'top3_match_lo', 'top3_match_hi']].to_string(index=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
