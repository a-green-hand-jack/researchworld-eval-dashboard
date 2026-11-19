"""Trace complete measured results into a structured analysis claim ledger.

This supplies evidence to report/presentation owners; it neither selects their
claims nor makes equal-cost, population-certification or clinical-use claims.
"""
import argparse, hashlib, json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
KEYS = ['dataset', 'model', 'estimator', 'budget', 'background_size']


def records(frame):
    # pandas renders missing optional interval fields as JSON null, not NaN.
    return json.loads(frame.to_json(orient='records', double_precision=15))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='results')
    a = p.parse_args()
    root = ROOT / a.input
    cfg = json.loads((ROOT / 'configs/main.json').read_text())
    manifest = json.loads((root / 'aggregation_manifest.json').read_text())
    audit = json.loads((root / 'panel_audit.json').read_text())
    expected_refs = len(cfg['datasets']) * len(cfg['models']) * cfg['n_instances']
    expected_runs = expected_refs * len(cfg['estimators']) * 3 * cfg['n_repeats']
    for label, obj in [('aggregation', manifest), ('independent panel audit', audit)]:
        if obj['status'] != 'complete' or obj['n_runs'] != expected_runs or obj['n_reference_inputs'] != expected_refs:
            raise ValueError(f'{label} is incomplete; no claim handoff written')
    if manifest['signature'] != audit['signature']:
        raise ValueError('audit/aggregate identity mismatch')
    if audit['recorded_failed_attempts'] or audit['warning_messages']:
        raise ValueError('failures/warnings require explicit analyst disposition before handoff')
    names = ['aggregate_metrics.csv', 'paired_contrasts.csv', 'aggregate_repeatability.csv',
             'stratified_metrics.csv', 'assessability_counts.csv', 'floor_sensitivity.csv',
             'averaged_run_metrics.csv', 'job_costs.csv', 'model_diagnostics.csv',
             'reference_diagnostics.csv', 'instance_success.csv']
    tables = {name: pd.read_csv(root / name) for name in names}
    agg = tables['aggregate_metrics.csv']
    expected_conditions = {
        (d, m, e, b, cfg['background_size'])
        for d in cfg['datasets'] for m in cfg['models']
        for e in cfg['estimators'] for b in cfg['budgets'][d]
    }
    primary = agg[agg.metric == 'joint_success_0p2'].copy()
    if set(map(tuple, primary[KEYS].to_numpy())) != expected_conditions or len(primary) != len(expected_conditions):
        raise ValueError('missing/duplicate primary condition')
    if not ((primary.n_instances == cfg['n_instances']) & (primary.n_repeats == cfg['n_repeats'])).all():
        raise ValueError('unexpected primary denominator')
    rows = []
    for key, g in agg.groupby(KEYS):
        base = dict(zip(KEYS, key))
        metrics = g.set_index('metric')
        summary = {}
        for metric in ['joint_success_0p2', 'nl1_error', 'absolute_l1_error', 'signed_topk_overlap',
                       'top1_match', 'prediction_rows', 'cpu_seconds', 'wall_seconds']:
            summary[metric] = records(metrics.loc[[metric]].reset_index())[0]
        rows.append(dict(condition=base, metrics=summary))
    # Compare finite means descriptively; these do not gain a new interval from
    # arbitrary pairing of independently seeded runs or from pooling model cells.
    means = tables['averaged_run_metrics.csv']
    averaged = []
    for key, g in means.groupby(KEYS):
        if len(g) != cfg['n_instances'] or not (g.n_averaged == cfg['n_repeats']).all():
            raise ValueError('mean-of-runs denominator mismatch')
        averaged.append(dict(zip(KEYS, key), n_instances=len(g), n_averaged=cfg['n_repeats'],
                             observed_averaged_vector_success=float(g.joint_success_0p2.mean()),
                             mean_averaged_vector_nl1=float(g.nl1_error.mean()),
                             mean_total_prediction_rows=float(g.total_prediction_rows.mean()),
                             inference='descriptive observed mean; use saved per-instance vectors for further inference'))
    references = tables['reference_diagnostics.csv']
    costs = tables['job_costs.csv']
    ref_cpu = float(references.cpu_seconds.sum())
    total_cpu = float(costs.process_total_cpu_seconds.sum())
    # Whole-job CPU contains references, stochastic calls and setup/import/write
    # overhead. This difference is explicitly a residual, not a fit-time estimate.
    stochastic_cpu = agg[agg.metric == 'cpu_seconds'].estimate.sum() * cfg['n_instances'] * cfg['n_repeats']
    budget_pairs = tables['paired_contrasts.csv']
    same_estimator = budget_pairs[budget_pairs.estimator_a == budget_pairs.estimator_b]
    data = dict(
        status='complete_main_evidence', signature=manifest['signature'],
        provenance={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                    for name in names + ['aggregation_manifest.json', 'panel_audit.json', 'run_metrics.parquet']},
        denominators=dict(model_cells=manifest['n_model_cells'], exact_references=expected_refs,
                          stochastic_calls=expected_runs, independent_instances_per_condition=cfg['n_instances'],
                          repeats_per_instance=cfg['n_repeats']),
        primary_event='L1(phi-reference)/max(L1(reference),.01)<=.20 AND signed top3 overlap>=2/3',
        one_run_conditions=rows,
        budget_contrasts=records(same_estimator),
        nominal_budget_estimator_contrasts=records(budget_pairs[budget_pairs.estimator_a != budget_pairs.estimator_b]),
        repeatability=records(tables['aggregate_repeatability.csv']),
        reference_defined_strata=records(tables['stratified_metrics.csv']),
        all_instance_denominators_and_ambiguity=records(tables['assessability_counts.csv']),
        floor_sensitivity=records(tables['floor_sensitivity.csv']),
        threshold_and_selection_sensitivity=records(agg[agg.metric.str.contains('success_')]),
        averaged_vectors=averaged,
        measured_main_cost=dict(whole_jobs_cpu_seconds=total_cpu, exact_reference_cpu_seconds=ref_cpu,
                                stochastic_cpu_seconds=float(stochastic_cpu),
                                other_job_cpu_residual_seconds=float(total_cpu-ref_cpu-stochastic_cpu),
                                peak_process_rss_kib=int(costs.peak_process_rss_kib.max()),
                                parallel_wall_policy='cell wall times overlap; their sum is not elapsed study wall time'),
        supported_claim_types=[
            'conditional observed one-run accuracy/signed selection for every named cell with displayed pointwise intervals',
            'paired-instance budget contrasts and nominal-budget estimator contrasts with measured cost differences exposed',
            'two-run repeatability versus reference accuracy on the same reference scale',
            'reference-defined conditions, tolerance/floor/tie sensitivities and separately charged mean-of-30 vectors'],
        unsupported_claims=[
            'population >=.95 reliability unless the conservative guard itself passes; n=60 cannot pass it',
            'exactly equal-work/time estimator superiority from matching nominal budget labels',
            'every input is individually reliable based on a panel mean or 30 all-success trials',
            'background-population, retraining, causal, clinical, fairness, safety or neural-model generalization',
            'multiple-comparison-adjusted discoveries or novelty against withheld material'],
        inference='pointwise instance-cluster intervals conditional on fixed fitted model/split/background; finite-boundary guards retained',
        scope='main estimator-only arm; changed-background evidence is separately audited and labeled')
    (root / 'claim_ledger.json').write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    print(f'Claim ledger: {len(primary)} conditions, {expected_runs} calls, {expected_refs} exact targets', flush=True)


if __name__ == '__main__':
    main()
