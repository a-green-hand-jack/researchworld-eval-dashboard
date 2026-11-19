"""Measured matrix-specific cost quote; no confirmatory outcomes are consumed."""
import argparse
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
args = parser.parse_args()
root = args.root
bench = {p.parent.name:json.loads(p.read_text()) for p in (root/'results/gate-benchmarks').rglob('summary.json')}
old = {json.loads(p.read_text())['config']['width']:json.loads(p.read_text())
       for p in (root/'results/pilot').glob('pilot_relu_w*_wd1/summary.json')}
rates = {w:s['cpu_s']/s['config']['steps'] for w,s in old.items()}
for width in [64,256]:
    s = bench[f'gate_w{width}']; rates[width]=s['cpu_s']/s['config']['steps']
recipe_bench = dict(decay='gate_decay_w512',frozen='gate_frozen_w512',
    **{'lr-low':'gate_lr-low_w512','lr-high':'gate_lr-high_w512',
       'orbit':'gate_orbit_w512','multiply':'gate_multiply_w512'})
registered = json.loads((root/'configs/confirmatory.json').read_text())['runs']
# For lower unbenchmarked widths, preserve full-model baseline rate and apply
# only upward recipe ratios. Frozen feature savings are used only where measured.
# Main width512 also uses the highest measured full-model width512 rate, covering
# instrumentation and recipe differences rather than extrapolating a faster old code.
full512 = max(s['cpu_s']/s['config']['steps'] for name,s in bench.items()
              if s['config']['width']==512 and not s['config'].get('frozen_hidden'))
base512 = rates[512]
rates[512] = max(base512,full512)
family = {}
run_quotes = []
for run in registered:
    rate = rates[run['width']]
    method = 'measured width baseline; conservative maximum for full width512'
    if run['family'] in recipe_bench:
        s = bench[recipe_bench[run['family']]]
        measured_recipe_rate = s['cpu_s']/s['config']['steps']
        if run['width']==512:
            rate = max(measured_recipe_rate,rate) if run['family']!='frozen' else measured_recipe_rate
            method = 'measured recipe width512, conservatively floored by full-model maximum except frozen'
        else:
            rate *= max(1,measured_recipe_rate/base512)
            method = 'measured lower-width baseline times nondecreasing recipe-over-reference ratio'
    quote = rate*run['steps']
    family[run['family']] = family.get(run['family'],0)+quote
    run_quotes.append(dict(name=run['name'],projected_cpu_s=quote,method=method))
job_wrappers = [json.loads(p.read_text()) for p in (root/'results/gate-benchmarks').glob('*end-to-end.json')]
startup = 0.0
# Wrapper CPU minus four run CPU totals gives measured one-interpreter startup/loop overhead.
for index in [1,2]:
    wrapper = json.loads((root/f'results/gate-benchmarks/job{index}-end-to-end.json').read_text())
    total = sum(json.loads(p.read_text())['cpu_s'] for p in (root/f'results/gate-benchmarks/job{index}').glob('*/summary.json'))
    startup = max(startup,wrapper['child_cpu_s']-total)
production_startup_quote = 4*startup
training_total = sum(family.values())
with_reserve = 1.5*(training_total+production_startup_quote)
# Archive estimate uses logical bytes (counts hard-link aliases separately, as Git does).
max_run_bytes = 0
max_line = 0
for directory in [p.parent for p in (root/'results/gate-benchmarks').rglob('summary.json')]:
    size = sum(p.stat().st_size for p in directory.iterdir() if p.is_file())
    max_run_bytes = max(max_run_bytes,size)
    max_line = max(max_line,max(len(line)+1 for line in (directory/'curve.jsonl').read_text().splitlines()))
# Benchmarks have 21 rows; production has603. Use largest measured row plus25% margin.
per_run_archive_bound = max_run_bytes+int((603-21)*max_line*1.25)
archive_all = 204*per_run_archive_bound
quote = dict(type='planning projection from measured nonconfirmatory benchmarks, not completed-study compute',
    completed_benchmark_runs=len(bench),baseline_cpu_s_per_update=rates,
    recipe_benchmark_paths={k:f'results/gate-benchmarks/{"job1" if k in ["frozen","multiply","lr-high"] else "job2"}/{v}/summary.json' for k,v in recipe_bench.items()},
    family_projected_cpu_hours={k:v/3600 for k,v in family.items()},
    all204_training_cpu_hours=training_total/3600,
    startup_cpu_s_per_interpreter_upper_measured=startup,
    all204_with_startup_and_50percent_reserve_cpu_hours=with_reserve/3600,
    planning_cap_cpu_hours=44,headroom_to_cap_cpu_hours=44-with_reserve/3600,
    uniform_largest_cell_with50percent_cpu_hours=204*max(q['projected_cpu_s'] for q in run_quotes)*1.5/3600,
    maximum_measured_process_rss_kib=max(s['process_peak_rss_kib'] for s in bench.values()),
    max_measured_run_logical_bytes=max_run_bytes,max_measured_curve_line_bytes=max_line,
    conservative_all204_logical_archive_bytes=archive_all,
    archive_with50percent_failed_attempt_reserve_bytes=int(archive_all*1.5),
    storage_limit_reference_bytes=1000000000,run_quotes=run_quotes,
    caveats=['Rates and changed-recipe ratios are planning extrapolations, not strict worst-case guarantees.',
             'Two one-thread jobs were measured concurrently; no guaranteed linear speedup is assumed.',
             '204-run weighted projection fits cap; crude maximum-price-every-run bound can exceed44h.',
             'CPU budget and scientific horizon remain registered; reserve is not permission to omit controls.'])
(root/'results/gate-benchmarks/resource-quote.json').write_text(json.dumps(quote,indent=2)+'\n')
start = datetime.fromtimestamp(1793709550.373,timezone.utc)
deadline = start+timedelta(days=7)
ledger = dict(overall_research_started_utc=start.isoformat(),source='first experiment activation timestamp',
    protocol_preparation_started_utc=datetime.fromtimestamp(1793712218.206,timezone.utc).isoformat(),
    production_launched_utc=None,production_status='not launched: relevant feasibility/context gates pending',
    absolute_one_week_deadline_utc=deadline.isoformat(),
    experimental_completion_deadline_utc=(deadline-timedelta(hours=96)).isoformat(),
    writing_figures_analysis_deadline_utc=(deadline-timedelta(hours=48)).isoformat(),
    final_review_reproduction_reserve_hours=48,analysis_writing_reserve_hours=48,
    projected_serial_compute_with_reserve_hours=with_reserve/3600,
    no_deadline_restart=True,job_refs=['job-ec82c12fb1','job-7ec903f3c5','job-90501e0219','job-9f529629f1','job-423cd843d2'])
ledger_path = root/'reproduction/deadline_ledger.json'
if not ledger_path.exists():
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({k:v for k,v in quote.items() if k not in ['run_quotes','recipe_benchmark_paths','caveats']},indent=2))
