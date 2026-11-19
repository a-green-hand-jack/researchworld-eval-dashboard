import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from events import sustained_event,summarize_curve,bootstrap_mean,wilson_interval
rows = [dict(step=100*i,train_acc=t,valid_acc=v) for i,(t,v) in enumerate([
    (.1,.1),(1.,.96),(1.,.2),(1.,.96),(1.,.97),(1.,1.),(1.,.1)])]
e = summarize_curve(rows)
assert e['train_event']['step'] == 100
assert e['valid_event']['step'] == 300
assert e['valid_event']['confirmed_step'] == 500
assert e['valid_event']['terminal_above'] is False
assert e['event_delay'] == 200
assert e['restricted_waiting_time'] == 200
truncated = summarize_curve(rows[:4])
assert truncated['valid_event']['observed'] is False
assert truncated['valid_event']['step'] is None
assert truncated['restricted_valid_time'] == 300
assert truncated['restricted_waiting_time'] == 200
no_fit = summarize_curve([dict(step=i,train_acc=.2,valid_acc=.1) for i in range(5)])
assert no_fit['restricted_waiting_time'] == 0
assert no_fit['train_event']['observed'] is False
b = bootstrap_mean([1,2,3],repeats=1000)
assert b['mean'] == 2 and b['ci_low'] <= 2 <= b['ci_high']
print('PASS: isolated spikes rejected, sustained onset confirmed, censoring retained, collapse flagged, seed bootstrap')

assert bootstrap_mean([3])['ci_low'] is None
assert wilson_interval(0,8)['ci_high'] > .3
assert wilson_interval(8,8)['ci_low'] < .7
print('PASS: one-seed bootstrap uncertainty withheld; event intervals retain boundary uncertainty')

rows = [dict(step=i,train_acc=1.,valid_acc=.99) for i in [0,100,200]]
e = summarize_curve(rows)
assert e['zero_clock_boundary'] and e['log2_event_time_ratio'] is None
print('PASS: zero clock boundary remains explicit')
