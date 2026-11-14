#!/usr/bin/env python3
"""Reproducible fixed-game SHAP analysis only; never imports/runs experiment.py.

Default validation targets 27 n30 main cells; precision expansion must pass
--expected-n 120 --sensitivity-results /work/results and an explicit new --out.
Full-source validation and measured original-prefix audit precede positional
slicing and slice-sized cluster rebootstrap. Original analysis/analysis30 outputs
are protected. --partial exact remains an explicit, never-final subset option.
B16 sensitivity is always original first10, even in the held-out additional90
report. All CIs condition on fixed seeds/games; no German true-accuracy inference
or unconditional ACS population certification is performed.
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


def validate_cell(root, ds, model, seed, sensitivity=False, expected_n=30):
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
        n, d, bg = (10 if sensitivity else expected_n), DIMS[ds], (16 if sensitivity else 8)
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


INSTANCE_ARRAYS = ('phi', 'reference', 'reference_pools', 'instances', 'efficiency', 'nonantithetic', 'kernel')
FROZEN_META = ('dataset', 'model', 'seed', 'repetitions', 'background', 'reference_cycles_per_pool',
               'reference_type', 'model_parameters', 'metrics', 'logical_model_rows_per_run', 'warnings')


def bootstrap_indices(n, start=0):
    # Preserve original n30 stream; expansion/slice streams are explicitly distinct.
    return {ds: np.random.default_rng(np.random.SeedSequence(
                [BOOT_SEED, di] if (n, start) == (30, 0) else [BOOT_SEED, di, start, n]
            )).integers(0, n, (BOOT_REPS, n)) for di, ds in enumerate(DATASETS)}


def slice_cell(cell, start, stop):
    if cell['sensitivity']:
        return cell
    sliced = dict(cell)
    sliced['arrays'] = {k: (v[start:stop].copy() if k in INSTANCE_ARRAYS and v.size else v.copy())
                        for k, v in cell['arrays'].items()}
    sliced['source_metadata'] = cell['metadata']
    sliced['metadata'] = dict(cell['metadata'], n=stop-start,
                              counters=cell['metadata']['counters'][start:stop])
    sliced['slice'] = dict(start=start, stop=stop, n=stop-start)
    return sliced


def prefix_audit(cells, original_root, out):
    """Measured exact equality, not tolerance-only agreement; missing cells stay pending."""
    rows, cell_rows = [], []
    for cell in cells:
        if cell['sensitivity']:
            continue
        ds, model, seed = cell['dataset'], cell['model'], cell['seed']
        report, original = validate_cell(original_root, ds, model, seed, expected_n=30)
        checks = []
        if original is None:
            cell_rows.append(dict(cell=cell['name'], status='invalid_original', errors=report['errors']))
            continue
        old, new = original['arrays'], cell['arrays']
        checks.append(set(old) == set(new))
        for key in sorted(set(old) | set(new)):
            a, b = old.get(key), new.get(key)
            if a is None or b is None:
                equal, maxdiff, shape = False, None, None
            else:
                compared = b[:30] if key in INSTANCE_ARRAYS and b.size else b
                equal = np.array_equal(a, compared)
                shape = list(compared.shape)
                maxdiff = float(np.max(np.abs(a.astype(float)-compared.astype(float)))) if a.size and a.shape == compared.shape else (0. if not a.size and equal else None)
            checks.append(equal)
            rows.append(dict(cell=cell['name'], array=key, original_shape=None if a is None else list(a.shape),
                             expanded_prefix_shape=shape, exact_equal=bool(equal), max_absolute_difference=maxdiff))
        frozen = {k: original['metadata'].get(k) == cell['metadata'].get(k) for k in FROZEN_META}
        om, nm = original['data_metadata'], cell['data_metadata']
        manifest = {k: (nm.get(k, [])[:30] == v if k in ('instances', 'test_cluster_ids') else nm.get(k) == v)
                    for k, v in om.items()}
        counter_equal = all({k: v for k, v in x.items() if k != 'prediction_seconds'} ==
                            {k: v for k, v in y.items() if k != 'prediction_seconds'}
                            for x, y in zip(original['metadata']['counters'], cell['metadata']['counters'][:30]))
        passed = all(checks) and all(frozen.values()) and all(manifest.values()) and counter_equal
        cell_rows.append(dict(cell=cell['name'], status='equal' if passed else 'mismatch',
                              all_npz_arrays_exact_equal=all(checks), frozen_metadata_equal=frozen,
                              data_manifest_equal=manifest, prefix_cache_counts_equal=counter_equal,
                              original_npz_sha256=report['npz_sha256'],
                              expanded_npz_sha256=hashlib.sha256((cell['source_root']/(cell['name']+'.npz')).read_bytes()).hexdigest()))
    save_table(out, 'original_prefix_npz_audit', rows)
    audit = dict(status='passed' if len(cell_rows) == 27 and all(c['status'] == 'equal' for c in cell_rows)
                 else ('pending' if all(c['status'] == 'equal' for c in cell_rows) else 'failed'),
                 audited_cells=len(cell_rows), required_cells=27, equal_cells=sum(c['status'] == 'equal' for c in cell_rows),
                 original_root=str(original_root.resolve()), compared_prefix_n=30,
                 equality='np.array_equal, every NPZ array; no tolerance substitutions',
                 timing_exclusion='Runtime and prediction seconds may change; deterministic cache row/coalition counts must match.',
                 cells=cell_rows)
    write_json(out/'original_prefix_audit.json', audit)
    return audit


def compact_ci(df, key, digits=3):
    return [f'{p:.{digits}f} [{lo:.{digits}f}, {hi:.{digits}f}]' if np.isfinite(p) else '--'
            for p, lo, hi in zip(df[key], df[key+'_lo'], df[key+'_hi'])]


def precision_tables(out, cell_df, macro, gaps, pools, sensitivity_rows, full_cells, start, stop):
    """Small manuscript views plus matching CSVs; full diagnostics remain unchanged."""
    anti = cell_df[cell_df.method == 'antithetic'].copy()
    view = anti[['dataset', 'model', 'budget', 'target', 'n_instances']].copy()
    for metric, title in [('top3_match', 'Top3 [95% CI]'), ('pairwise_top3_match', 'Pair match [95% CI]'),
                          ('absolute_l1', 'L1 [95% CI]'), ('normalized_l1', 'Norm L1 [95% CI]'),
                          ('nogueira_stability', 'Stability [95% CI]')]:
        view[title] = compact_ci(anti, metric)
    save_table(out, 'paper_antithetic_metrics_long', view)
    wide = []
    for (ds, model), group in anti.groupby(['dataset', 'model'], sort=False):
        row = dict(Game=ds.upper() + (' (approx.)' if ds == 'german' else '') + '/' + model.upper())
        for budget in BUDGETS:
            sub = group[group.budget == budget]
            row[f'P={budget}'] = compact_ci(sub, 'top3_match')[0]
        wide.append(row)
    save_table(out, 'paper_antithetic_9cells', wide)
    (out/'paper_antithetic_9cells.tex').write_text(
        '% Top-3 subset agreement [marginal descriptive 95% instance-cluster CI]. German: approximate reference only.\n'
        + r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}' + '\n'
        + latex_table(pd.DataFrame(wide)) + r'\endgroup' + '\n')
    if not macro.empty:
        view = macro[['method', 'budget', 'n_instances_per_dataset']].copy()
        for key in ('top3_match', 'pairwise_top3_match', 'absolute_l1', 'nogueira_stability'):
            view[key+' [95% CI]'] = compact_ci(macro, key)
        view['regime'] = ['full_cube_control' if m == 'kernel' and b == 64 else 'sampled' for m,b in zip(view.method, view.budget)]
        save_table(out, 'paper_exact_macro_metrics_long', view)
        wide = []
        for method, group in macro.groupby('method', sort=False):
            row = {'Method': method}
            for budget in BUDGETS:
                row[f'P={budget}'] = compact_ci(group[group.budget == budget], 'top3_match')[0]
            wide.append(row)
        save_table(out, 'paper_exact_macro_controls', wide)
    if not pools.empty:
        records = []
        view = pools[pools.seed == 'fixed_seed_average']
        for model in MODELS:
            group = view[view.model == model]
            row = {'Model': model.upper()}
            for metric, title in [('reference_pool_top3_agreement', 'Pool top3 agreement [95% CI]'),
                                  ('pool_difference_l1', 'Pool L1 difference [95% CI]')]:
                sub = group[group.metric == metric]
                if not sub.empty:
                    r = next(sub.itertuples())
                    row[title] = f'{r.mean:.4f} [{r.lo:.4f}, {r.hi:.4f}]'
            records.append(row)
        save_table(out, 'paper_german_reference_pools', records)
    if not gaps.empty:
        view = gaps[gaps.method == 'antithetic']
        wide = []
        for (ds, model, gap), group in view.groupby(['dataset','model','gap_bin'], sort=False):
            first = group.iloc[0]
            row = {'Game': ds.upper()+'/'+model.upper(), 'Gap': gap,
                   'Games/clusters': f'{first.n_seed_instance_games}/{first.n_instance_clusters}'}
            for budget in BUDGETS:
                row[f'P={budget}'] = compact_ci(group[group.budget == budget], 'top3_match')[0]
            wide.append(row)
        save_table(out, 'paper_gaps_per_budget', wide)
    if sensitivity_rows:
        view = pd.DataFrame(sensitivity_rows).query('method == "antithetic"').copy()
        for key in ('b8_top3_match','b16_top3_match','b16_minus_b8_own_target_match','reference_top3_change'):
            view[key+' [95% CI]'] = compact_ci(view, key)
        compact = pd.DataFrame({'Game': view.dataset.str.upper()+'/'+view.model.str.upper(), 'P': view.budget,
                                'Target changes /10': view.reference_top3_change_count,
                                'B8 match [95% CI]': compact_ci(view, 'b8_top3_match'),
                                'B16 match [95% CI]': compact_ci(view, 'b16_top3_match'),
                                'B16-B8 [95% CI]': compact_ci(view, 'b16_minus_b8_own_target_match')})
        save_table(out, 'paper_sensitivity_first10', compact)
    models, splits, seen = [], [], set()
    for c in full_cells:
        if c['sensitivity']:
            continue
        m, d = c['metadata'], c['data_metadata']
        models.append(dict(dataset=c['dataset'], model=c['model'], seed=c['seed'], **m['metrics'],
                           fit_warnings=json.dumps(m['warnings']), evaluation='fixed full test split, not attribution slice'))
        if c['dataset'] not in seen:
            seen.add(c['dataset'])
            splits.append(dict(dataset=c['dataset'], total_n=d['n'], train_n=len(d['train']),
                               validation_n=len(d['validation']), test_n=len(d['test']), raw_features=d['d'],
                               encoded_features=d['encoded_d'], background_n=8, sensitivity_background_n=16 if c['dataset'] != 'german' else 0,
                               audit_source_n=m['n'], analyzed_n=stop-start, start_instance=start, stop_instance=stop,
                               positive_fraction=d['positive_fraction'], duplicate_raw_rows=d['duplicate_raw_rows'],
                               missing_entries=d['missing_entries'], household_disjoint=d['household_disjoint']))
    model_df = save_table(out, 'model_performance', models)
    split_df = save_table(out, 'data_splits', splits)
    if not split_df.empty:
        view = split_df[['dataset','total_n','train_n','validation_n','test_n']].copy()
        view['Raw/encoded d'] = [f'{a}/{b}' for a,b in zip(split_df.raw_features, split_df.encoded_features)]
        view['Positive %'] = [f'{100*p:.2f}' for p in split_df.positive_fraction]
        save_table(out, 'paper_data_splits', view)
    if not model_df.empty:
        view = model_df[['dataset','model','seed']].copy()
        for k in ('auc','log_loss','accuracy'):
            view[k] = [f'{v:.4f}' for v in model_df[k]]
        view['fit_warnings'] = model_df.fit_warnings
        save_table(out, 'paper_model_performance', view)
    notes = {'paper_antithetic_9cells': 'Top3 subset agreement; German approximate reference ONLY.',
             'paper_exact_macro_controls': 'Six exact dataset/model cells; Kernel P64 fully enumerates both cubes (not sampled).',
             'paper_german_reference_pools': 'German independent 512-cycle pools, fixed-seed average; convergence evidence, NOT true accuracy.',
             'paper_gaps_per_budget': 'Antithetic oracle rank3-rank4 reference-gap strata; games/clusters counts; undefined strata marked --.',
             'paper_sensitivity_first10': 'Seed11 original first10 ONLY; each B8/B16 estimate compared with its own target; not heldout90.',
             'paper_model_performance': 'Frozen model performance on entire fixed test split; no prediction-level CI available.',
             'paper_data_splits': 'Frozen splits; ACS household-disjoint but audit inclusion is unequal-probability, not survey-weighted.'}
    for name, note in notes.items():
        path = out/(name+'.tex')
        if path.exists():
            text = path.read_text()
            if name != 'paper_antithetic_9cells':
                text = r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}' + '\n' + text + r'\endgroup' + '\n'
            path.write_text(f'% Main slice n={stop-start}; positional range [{start},{stop}); marginal descriptive 95% cluster CIs, not certificates.\n% {note}\n'+text)


def campaign_resources(original_root, full_cells):
    records = []
    for label, meta in [('original30_and_B16', json.loads(p.read_text()))
                        for p in sorted(original_root.glob('*.json')) if p.stem.split('_')[-1] in ('11','23','47','b16')]:
        records.append(dict(campaign=label, cpu_seconds=meta['cpu_seconds'], wall_seconds=meta['wall_seconds'],
                            actual_model_rows=sum(x['actual_rows'] for x in meta['counters'])))
    records += [dict(campaign='expanded120_including_prefix_replay', cpu_seconds=c['metadata']['cpu_seconds'],
                     wall_seconds=c['metadata']['wall_seconds'],
                     actual_model_rows=sum(x['actual_rows'] for x in c['metadata']['counters']))
                for c in full_cells if not c['sensitivity']]
    totals = []
    for campaign in dict.fromkeys(r['campaign'] for r in records):
        group = [r for r in records if r['campaign'] == campaign]
        totals.append(dict(campaign=campaign, cells=len(group), **{k: sum(r[k] for r in group)
                           for k in ('cpu_seconds','wall_seconds','actual_model_rows')}))
    cpu = sum(r['cpu_seconds'] for r in totals)
    return dict(campaigns=totals, total_cpu_seconds=cpu, total_cpu_hours=cpu/3600,
                planned_cpu_budget_hours=24, cpu_budget_fraction=cpu/(24*3600),
                accounting='Each original main/B16 and expanded main run counted once. Prefix replay is real consumed compute; n90 is a subset, never a new run. Summed wall is not parallel elapsed makespan. Failed/incomplete runs and orchestration overhead unavailable.')


def cohort_headlines(full_cells, out):
    """Report all three cohorts from validated full arrays, with slice-rebooted CIs."""
    main = [c for c in full_cells if not c['sensitivity']]
    n_source = main[0]['metadata']['n']
    scopes = [('exploratory_first30', 0, 30), ('heldout_next90', 30, 120), ('combined120_main', 0, 120)] if n_source == 120 else [('exploratory_first30', 0, n_source)]
    rows = []
    cached = {(ds, model): np.mean([run_metrics(c['arrays']['phi'], c['arrays']['reference'])['top3_match']
               for c in main if c['dataset'] == ds and c['model'] == model], axis=0)
              for ds in DATASETS for model in MODELS
              if sum(c['dataset'] == ds and c['model'] == model for c in main) == 3}
    for stage, lo, hi in scopes:
        n = hi-lo
        idx = bootstrap_indices(n, lo)
        for bi, budget in enumerate(BUDGETS):
            estimates, boots = [], []
            for (ds, model), vec in cached.items():
                est, boot = cluster_stat(vec[lo:hi, bi], idx[ds])
                point, low, high = interval(est, boot)
                rows.append(dict(stage=stage, dataset=ds, model=model, budget=budget, n=n,
                                 top3_match=point, top3_match_lo=low, top3_match_hi=high,
                                 target='APPROX_reference_ONLY' if ds == 'german' else 'exact_target'))
                if ds != 'german':
                    estimates.append(est); boots.append(boot)
            if len(estimates) == 6:
                point, low, high = interval(np.mean(estimates), np.mean(boots, axis=0))
                rows.append(dict(stage=stage, dataset='exact_macro', model='six_cells', budget=budget, n=n,
                                 top3_match=point, top3_match_lo=low, top3_match_hi=high, target='exact_target_macro'))
    df = save_table(out, 'expansion_cohort_headlines', rows)
    return df.to_dict(orient='records')


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
        source_meta = c.get('source_metadata', meta)
        ctr = meta['counters']
        records.append(dict(cell=c['name'], dataset=c['dataset'], model=c['model'], seed=c['seed'],
                            sensitivity=c['sensitivity'], n=meta['n'], source_n=source_meta['n'], background=meta['background'],
                            timing_scope='full source run, NOT allocated to slice/method',
                            cpu_seconds=source_meta['cpu_seconds'], wall_seconds=source_meta['wall_seconds'],
                            train_wall_seconds=source_meta['train_seconds'],
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
                             timing_scope='full source runs (shared references/all estimators); do not add across overlapping cohort analyses',
                             counter_scope='selected instance slice; per-instance shared prediction wall, rows and coalitions',
                             source_n_per_cell=sorted(sub.source_n.unique().tolist()), analyzed_n_per_cell=sorted(sub.n.unique().tolist()),
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
                       n_instances=len(indices[ds][0]), fixed_seeds='11,23,47', runs_per_seed_instance=20)
            row.update(metric_summary({k: v[:, bi] for k, v in avg.items()}, indices[ds]))
            if ds != 'german' and method == 'antithetic':
                row['bootstrap_095_relation_descriptive_only'] = ('interval_at_or_above_095_NOT_certificate'
                    if row['top3_match_lo'] >= .95 else ('interval_below_095' if row['top3_match_hi'] < .95 else 'interval_overlaps_095'))
                row['hoeffding_24_lower_illustration'] = max(0., row['top3_match'] - math.sqrt(math.log(24/.05)/(2*len(indices[ds][0]))))
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
                                         n_total_instance_clusters=len(indices[ds][0]), analysis_stage='slice_specific',
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
                row = dict(method=method, budget=budget, n_dataset_model_cells=6, n_instances_per_dataset=len(indices['pima'][0]),
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
             f'Main artifacts: {overview["main_valid"]}/27 valid at source n={overview["expected_source_n"]}; analyzed n={overview["n_instances"]}, positional slice [{overview["start_instance"]},{overview["stop_instance"]}) (R=20, P=1,4,16,64). B16: {overview["sensitivity_valid"]}/6 valid (first10, seed=11; not additional90).',
             '', '## Study chronology', overview['study_design'],
             f'Analysis stage: **{overview["analysis_stage"]}**. Original n30 outputs remain unchanged under /work/analysis and archived under /work/analysis30.',
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
              f"Bonferroni one-sided Hoeffding over 24 exact antithetic cells: lower=max(0,mean-{illustration['penalty']:.6f}). At perfection n={overview['n_instances']} reaches at most {illustration['maximum_lower_bound_at_perfection']:.6f}; n>={illustration['minimum_n_to_reach_095_at_perfection']} would be needed for a .95 lower bound at observed perfection under justified sampling assumptions. ACS household PPS-style selection is not justified by the current design.",
              '', '## Resources', '']
    for row in overview['resources']:
        lines.append(f"- {'B16 sensitivity' if row['sensitivity'] else 'Main'}: {row['completed_cells']} artifacts; summed CPU {row['cpu_seconds']:.6f} s; actual shared cached model rows {row['actual_model_rows']:.0f}; summed cell wall {row['wall_seconds']:.6f} s (not elapsed parallel makespan).")
    lines += ['Per-cell held-out AUC, log loss, accuracy, fit warnings and resource counters: resources.csv/tex. Logical per-run uncached row costs: logical_costs.csv/tex. Actual timings/rows include the shared references and all methods, not per-explanation deployment cost.']
    if overview.get('campaign_resources'):
        resource = overview['campaign_resources']
        lines += [f"Measured successful original30+B16+expanded120 campaigns total {resource['total_cpu_seconds']:.3f} CPU seconds ({resource['total_cpu_hours']:.4f} CPU hours; {100*resource['cpu_budget_fraction']:.3f}% of 24 CPU-hours). Prefix replay is counted as consumed compute; additional90 analysis consumes no new experiment run. Failed runs/overhead are not available."]
    lines += ['', '## Original-prefix/frozen-game audit', '']
    audit = overview.get('original_prefix_audit')
    if audit:
        lines.append(f"Measured prefix status **{audit['status']}**: {audit['equal_cells']}/27 cells exactly equal across every NPZ array; model parameters, test metrics, manifests and deterministic counters checked. original_prefix_npz_audit.csv and original_prefix_audit.json retain per-array max differences and input hashes. Timings excluded from equality.")
    else:
        lines.append('No expanded-prefix audit requested for this source n.')
    lines += ['', '## Exploratory first30 / held-out additional90 / combined120', '',
              'CIs reboot instance clusters at each actual cohort n. Do not pool overlapping cohorts as independent studies.',
              '| Cohort | n | P | Exact macro antithetic match | Descriptive 95% CI |', '|---|---:|---:|---:|---:|']
    for row in overview.get('expansion_cohort_headlines', []):
        if row['dataset'] == 'exact_macro':
            lines.append(f"| {row['stage']} | {row['n']} | {row['budget']} | {row['top3_match']:.6f} | [{row['top3_match_lo']:.6f}, {row['top3_match_hi']:.6f}] |")
    lines += ['', 'Compact manuscript tables: paper_antithetic_9cells, paper_exact_macro_controls, paper_german_reference_pools, paper_model_performance, data_splits, paper_gaps_per_budget, paper_sensitivity_first10 (.csv/.tex). Model test metrics are fixed-test observations; prediction-level CIs cannot be recovered from aggregate artifacts.',
              '', 'Resource scope: CPU, total wall and training wall are measured FULL source-run totals, not attributable slice costs. Rows, coalitions and prediction wall are summed over selected instance counters. n90 and n120 resource tables overlap: do not add them. No imputed per-method cost or proportional CPU allocation.',
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
    ap.add_argument('--expected-n', type=int, default=30, help='Require full source n before slicing (precision expansion: 120)')
    ap.add_argument('--start-instance', type=int, default=0, help='Inclusive positional slice start, after full validation')
    ap.add_argument('--stop-instance', type=int, help='Exclusive slice stop (default: expected-n)')
    ap.add_argument('--sensitivity-results', type=Path, help='Original results with B16 first10 and n30 prefix audit baseline')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    stop = args.expected_n if args.stop_instance is None else args.stop_instance
    if not 0 <= args.start_instance < stop <= args.expected_n:
        ap.error('Require 0 <= start-instance < stop-instance <= expected-n')
    if args.expected_n == 120 and args.sensitivity_results is None:
        ap.error('n120 requires --sensitivity-results pointing to retained original n30 results for prefix audit')
    if args.self_test:
        self_test()
        return 0
    out = args.out.resolve()
    protected = (Path('/work/analysis').resolve(), Path('/work/analysis30').resolve())
    if out in protected:
        ap.error('Retained n30 analysis directories are immutable; choose --out analysis120/analysis90 or a new directory')
    out.mkdir(parents=True, exist_ok=True)
    validation, loaded = [], []
    for ds in DATASETS:
        for model in MODELS:
            for seed in SEEDS:
                row, cell = validate_cell(args.results, ds, model, seed, expected_n=args.expected_n)
                row['source_root'] = str(args.results.resolve())
                validation.append(row)
                if cell is not None:
                    cell['source_root'] = args.results.resolve()
                    loaded.append(cell)
    sens_root = args.sensitivity_results or args.results
    for ds in DATASETS[:2]:
        for model in MODELS:
            row, cell = validate_cell(sens_root, ds, model, 11, True)
            row['source_root'] = str(sens_root.resolve())
            validation.append(row)
            if cell is not None:
                cell['source_root'] = sens_root.resolve()
                loaded.append(cell)
    main_valid = [r for r in validation if not r['sensitivity'] and r['status'] == 'valid']
    sens_valid = [r for r in validation if r['sensitivity'] and r['status'] == 'valid']
    all_main = len(main_valid) == 27
    write_json(out/'validation.json', validation)
    pending = [r['cell'] for r in validation if r['status'] != 'valid']
    n = stop - args.start_instance
    stage = ('combined120_main' if (args.expected_n, args.start_instance, stop) == (120, 0, 120) else
             'heldout_next90' if (args.expected_n, args.start_instance, stop) == (120, 30, 120) else
             'exploratory_first30' if (args.start_instance, stop) == (0, 30) else 'explicit_instance_slice')
    study_design = ('Original n30 is exploratory. The uniform additional90 expansion was prespecified AFTER outcome inspection of n30, '
                    'before expanded outcomes; no cell/model/budget/metric dropped. Combined120 is the main expanded study, '
                    'not an originally preregistered n120 study. Additional90 are held-out precision validation under the fixed ordering; '
                    'not a new independently preregistered confirmatory experiment. B16 remains first10 seed11 only.')
    audit = prefix_audit(loaded, sens_root, out) if args.expected_n == 120 else None
    overview = dict(status='pending_main_cells', main_valid=len(main_valid), main_required=27,
                    expected_source_n=args.expected_n, n_instances=n, start_instance=args.start_instance, stop_instance=stop,
                    analysis_stage=stage, study_design=study_design, original_prefix_audit=audit,
                    sensitivity_scope='prespecified first10 seed11, original results, independent of main slice; not next90 sensitivity',
                    sensitivity_valid=len(sens_valid), sensitivity_required=6, pending=pending,
                    command=f'python {Path(__file__).resolve()} --results {args.results.resolve()} --out {out} --expected-n {args.expected_n} --start-instance {args.start_instance} --stop-instance {stop} --sensitivity-results {sens_root.resolve()}',
                    warnings=list(WARNINGS) + [study_design], definitions=definitions(),
                    validation=str(out/'validation.json'))
    if audit is not None and audit['status'] == 'failed':
        overview['status'] = 'blocked_prefix_audit_failed'
        write_json(out/'summary.json', overview)
        print('Prefix or frozen-model/split equality failed; analysis blocked. See original_prefix_audit.json.')
        return 3
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
    full_selected = selected
    selected = [slice_cell(c, args.start_instance, stop) for c in full_selected]
    indices = bootstrap_indices(n, args.start_instance)
    cell_df, macro, gaps, pools, comparisons = analyze(selected, indices, out)
    # Sensitivity must ALWAYS use unsliced B8 first10, including next90-only reports.
    sens, sens_indices = sensitivity(full_selected, out)
    costs = resource_tables(out, selected)
    precision_tables(out, cell_df, macro, gaps, pools, sens, full_selected, args.start_instance, stop)
    cohort_results = cohort_headlines(full_selected, out)
    raw = {f'{c["name"]}__{k}': v for c in selected for k, v in c['arrays'].items()}
    raw.update({f'full_source__{c["name"]}__{k}': v for c in full_selected if not c['sensitivity']
                for k, v in c['arrays'].items()})
    raw.update({f'bootstrap__{ds}': idx for ds, idx in indices.items()})
    raw.update({f'bootstrap_sensitivity__{ds}': idx for ds, idx in sens_indices.items()})
    np.savez_compressed(out/'analysis_inputs.npz', **raw)
    write_json(out/'input_metadata.json', {c['name']: {'run': c['metadata'], 'source_run': c.get('source_metadata', c['metadata']),
               'slice': c.get('slice'), 'source_root': str(c['source_root']), 'data': c['data_metadata']} for c in selected})
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
                    resources=costs, expansion_cohort_headlines=cohort_results,
                    campaign_resources=campaign_resources(sens_root, full_selected) if args.expected_n == 120 else None,
                    quantitative_headlines=dict(exact_macro_antithetic=macro.loc[macro.method == 'antithetic',
                        ['budget','top3_match','top3_match_lo','top3_match_hi']].to_dict(orient='records') if not macro.empty else [],
                        macro_budget_gain=[r for r in comparisons if r['dataset'] == 'exact_macro' and r['contrast'] == 'antithetic_P64_minus_P1'],
                        resources=costs, original_prefix_equal_cells=None if audit is None else audit['equal_cells']),
                    hoeffding_illustration=dict(family_size=24, alpha=.05, n=n,
                        penalty=math.sqrt(math.log(24/.05)/(2*n)), maximum_lower_bound_at_perfection=1-math.sqrt(math.log(24/.05)/(2*n)),
                        minimum_n_to_reach_095_at_perfection=threshold_n,
                        conclusion=f'inconclusive at n={n}; ACS assumptions unverified; not an unconditional certificate'),
                    paired_comparison_family_size=len(comparisons),
                    boundary_cells=cell_df.loc[(cell_df.top3_match_lo == cell_df.top3_match_hi), ['dataset','model','method','budget','top3_match']].to_dict(orient='records'),
                    outputs=sorted(p.name for p in out.iterdir() if p.is_file()),
                    analysis_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write_json(out/'summary.json', overview)
    from importlib.util import spec_from_file_location, module_from_spec
    plot_path = Path(__file__).resolve().parent/'plot_precision.py'
    # Saved analyze.py can replay in its directory too; never rewrite n30 plots.
    if not plot_path.exists():
        plot_path = Path(__file__).resolve().parent/'plot.py'
    if plot_path.exists():
        if plot_path.resolve() != (out/'plot.py').resolve():
            shutil.copy2(plot_path, out/'plot.py')
        spec_path = Path(__file__).resolve().parent/'analysis30'/'figure-spec.md'
        if spec_path.exists():
            (out/'figure-spec.md').write_text(spec_path.read_text() + f'\n- analyzed_n: {n}; positional slice [{args.start_instance},{stop}); stage: {stage}.\n')
        spec = spec_from_file_location('study_plots', plot_path)
        plotting = module_from_spec(spec); spec.loader.exec_module(plotting)
        plotting.render_all(out, partial=bool(args.partial))
        overview['outputs'] = sorted(p.name for p in out.iterdir() if p.is_file())
        write_json(out/'summary.json', overview)
    else:
        overview['warnings'].append('Plot replay script not found: expected plot_precision.py beside source or plot.py beside saved analyzer.')
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
