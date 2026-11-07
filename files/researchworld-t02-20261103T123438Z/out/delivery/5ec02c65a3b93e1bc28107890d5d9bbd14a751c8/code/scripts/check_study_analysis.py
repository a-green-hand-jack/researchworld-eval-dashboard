"""Pure software fixtures. These are not measured scientific results."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from study_analysis import study_analysis
records = []
for family in ['main','frozen','decay']:
    for b in range(12 if family=='main' else 8):
        for width in [32,512]:
            rg = 50000 if width==32 else 20000 if family=='main' else 50000
            records.append(dict(family=family,width=width,block=b,split_sha256=str(b),path='software-fixture',
                restricted_valid_time=rg,restricted_train_time=100,restricted_waiting_time=rg-100,
                horizon_valid_acc=.99,cpu100_acc=.3,train_event=dict(observed=True),
                valid_event=dict(observed=True),delayed_event=True,zero_clock_boundary=False,
                event_delay=rg-100,log2_event_time_ratio=7.,censored_lag_lower_bound=None))
result = study_analysis(records)
assert result['P1']['interpretation']=='supported'
assert result['P2']['interpretation']=='supported'
assert result['P3']['interpretation']=='supported'
for r in records:
    if r['family']=='frozen' and r['width']==32:
        r['train_event']['observed']=False
result = study_analysis(records)
assert 'gate failed' in result['P3']['interpretation']
assert 'not established' in result['complete_account']
missing = study_analysis(records[:-1])
assert not missing['scope_width_contrasts'][0]['complete']
assert study_analysis([])['P1']['interpretation']=='incomplete'
print('PASS: registered contrast direction, P2 score decision, paired P3 interaction, failed fit gate and missing-block handling')
