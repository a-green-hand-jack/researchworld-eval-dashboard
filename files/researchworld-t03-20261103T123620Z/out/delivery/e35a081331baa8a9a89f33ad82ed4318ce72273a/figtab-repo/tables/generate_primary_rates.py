"""Present all 18 lowest-budget conditions and their supplied intervals/costs."""
import argparse
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'figures'))
from generate_main import load_evidence, DATASET_NAMES, MODEL_NAMES, truth
from rendering import file_record
sys.path.insert(0, str(ROOT/'tables'))
from generate_main_tables import emit_table


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results', type=Path, default=ROOT/'results')
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--analysis-revision', required=True)
    a = p.parse_args()
    config, manifest, paths, metrics = load_evidence(a.results.resolve(), a.config.resolve())
    revision = a.analysis_revision
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Use the verified full analysis revision')
    rows, rowmap = [], []
    for d in config['datasets']:
        for m in config['models']:
            for e in config['estimators']:
                def get(metric, high=False):
                    b = max(config['budgets'][d]) if high else min(config['budgets'][d])
                    f = metrics[metric]
                    return f[(f.dataset==d)&(f.model==m)&(f.estimator==e)&(f.budget==b)].iloc[0]
                q, work, cpu, high = [get(x) for x in ['joint_success_0p2', 'prediction_rows', 'cpu_seconds']] + [get('joint_success_0p2', True)]
                if high.estimate != 1 or truth(high.certifies_mean_ge_0p95):
                    raise ValueError('High-budget description requires revision')
                mark = r'\dagger' if truth(q.boundary_adjusted) else ''
                rate = f'${q.estimate:.3f}\\ [{q.ci_low:.3f},{q.ci_high:.3f}]{mark}$'
                rows.append([DATASET_NAMES[d], MODEL_NAMES[m], e.title(), str(int(q.budget)),
                             f'{work.estimate:,.0f}', f'{1000*cpu.estimate:.2f}', rate])
                rowmap.append(dict(dataset=d, model=m, estimator=e,
                    file='results/aggregate_metrics.csv',
                    input_csv_lines=[int(x.input_csv_line) for x in [q,work,cpu,high]],
                    metrics=['joint_success_0p2 (lowest)', 'prediction_rows (lowest)',
                             'cpu_seconds (lowest)', 'joint_success_0p2 (highest; caption)'],
                    interval=q.interval, n_instances=int(q.n_instances), n_repeats=int(q.n_repeats),
                    formatting='rate/CI .3f; work nearest row; CPU seconds times 1000 rounded .2f'))
    command='python3 tables/generate_primary_rates.py --results results --config '+str(a.config.resolve().relative_to(ROOT))+' --analysis-revision '+revision
    provenance=dict(schema_version=1, analysis_revision=revision, source_signature=manifest['signature'],
        inputs=[file_record(x, ROOT) for x in [*paths.values(), a.config.resolve()]],
        generator=file_record(Path(__file__), ROOT), supporting_code=[file_record(ROOT/x, ROOT) for x in
            ['figures/generate_main.py', 'figures/rendering.py', 'tables/generate_main_tables.py']])
    caption=('All lowest-requested-budget conditions. Adequacy means L1/max(exact-reference L1,0.01) '
        '$\\leq0.20$ and signed top-3 overlap $\\geq2/3$ for the fixed B32 empirical interventional '
        'probability game over raw-feature groups. Rates average 60 input clusters with 30 independent '
        'runs each; brackets are supplied pointwise 95\\% instance-cluster percentile intervals. '
        '$\\dagger$ marks an observed all-success panel with the supplied two-sided Hoeffding '
        'boundary interval instead. Actual rows and process CPU milliseconds are means per call; '
        'requested budget labels do not equate realized work. At every highest budget (German 2048, '
        'ACS 512, Diabetes 128), observed primary rates are 1 with displayed interval [0.825,1]; '
        'none certifies population adequacy $\\geq0.95$. Intervals condition on fixed models/split/background.')
    emit_table('primary_rates', caption,
        ['Dataset','Model','Method','Budget','Rows','CPU ms','Rate [95\\% interval]'],
        rows,rowmap,provenance,command)


if __name__=='__main__':
    main()
