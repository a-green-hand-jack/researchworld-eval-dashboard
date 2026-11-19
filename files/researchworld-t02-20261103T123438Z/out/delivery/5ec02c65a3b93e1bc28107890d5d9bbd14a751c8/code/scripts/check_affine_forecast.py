"""Software regressions only; no training or genuine authorization is created."""
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from resource_forecast import affine_prefix_quote
repo=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);directory=root/'results/confirmatory/active';directory.mkdir(parents=True)
    rows=[dict(step=100,cpu_s=.260782484,elapsed_s=58.1616365113),
          dict(step=36900,cpu_s=92.8288546,elapsed_s=150.7982446)]
    (directory/'curve.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    runs=[dict(name='active',status='started_incomplete',repriced_full_cpu_s=100.),
          dict(name='unstarted',status='not_started',repriced_full_cpu_s=200.),
          dict(name='historical',status='completed',repriced_full_cpu_s=999.)]
    historical=root/'results/confirmatory/historical';historical.mkdir()
    (historical/'curve.jsonl').write_text(json.dumps(dict(step=100,cpu_s=1.,elapsed_s=1e6))+'\n')
    slope=1.860141102946608
    q=affine_prefix_quote(root,runs,{'historical'},slope,8.)
    excess=58.1616365113-slope*.260782484
    assert math.isclose(q['max_positive_elapsed_excess_s'],excess)
    assert q['remaining_full_config_cpu_s']==300. # full active quote, no assumed checkpoint savings
    assert q['max_ratio_source']['step']==100 # later average must not erase earlier stall
    assert math.isclose(q['reserved_wall_hours'],1.5*(slope*308+2*excess)/3600)
    archived=directory/'curve.discarded-after-0.fixture.jsonl'
    archived.write_text(json.dumps(dict(step=100,cpu_s=1.,elapsed_s=1000.))+'\n')
    q2=affine_prefix_quote(root,runs,{'historical'},slope,8.)
    assert q2['max_positive_elapsed_excess_s']==1000.-slope
    assert 'discarded' in q2['excess_source']['path']
    q3=affine_prefix_quote(root,runs,set(),slope,8.)
    assert q3['max_positive_elapsed_excess_s']==1e6-slope # new/unexcluded stalls always reprice
    archived.write_text(json.dumps(dict(step=0,cpu_s=0.,elapsed_s=2000.))+'\n')
    q4=affine_prefix_quote(root,runs,{'historical'},slope,8.)
    assert q4['max_positive_elapsed_excess_s']==2000. and q4['positive_elapsed_zero_cpu_observations']==1
    (directory/'curve.jsonl').write_text((directory/'curve.jsonl').read_text()+'{"step":')
    assert affine_prefix_quote(root,runs,{'historical'},slope,8.)['max_positive_elapsed_excess_s']==2000.
# Existing guard regression confirms default method is unchanged and pending scenarios block trainer.
subprocess.run([sys.executable,str(repo/'code/scripts/check_resource_guard.py')],check=True)
# Check actual proposal remains held, not a fixture approval or launch permit.
with tempfile.TemporaryDirectory() as temporary:
    output=Path(temporary)/'proposal.json'
    subprocess.run([sys.executable,str(repo/'code/scripts/monitor_resources.py'),'--root',str(repo),
        '--phase','checkpoint','--output',str(output),'--schedule',str(repo/'reproduction/guard-recovery01-proposal.json')],check=True,stdout=subprocess.DEVNULL)
    q=json.loads(output.read_text())
    assert q['affine_prefix_forecast']['max_positive_elapsed_excess_s']>0
    assert q['selected_gate']['wall_forecast_model']=='elapsed_prefix_affine_v1'
    assert not q['selected_gate']['authorized'] and not q['selected_gate']['continue_unchanged_affordable_work']
    assert 'unchanged_latest_ratio_selected_gate' in q
with tempfile.TemporaryDirectory() as temporary:
    output=Path(temporary)/'held-original.json'
    subprocess.run([sys.executable,str(repo/'code/scripts/monitor_resources.py'),'--root',str(repo),
        '--phase','checkpoint','--output',str(output),'--schedule',str(repo/'reproduction/recovery_scenario.json')],check=True,stdout=subprocess.DEVNULL)
    q=json.loads(output.read_text())
    assert q['selected_gate']['unresolved_explicit_guard_holds']
    assert not q['selected_gate']['continue_unchanged_affordable_work']
print('PASS: all prefix/discarded/zero-CPU stalls retained,full unfinished CPU priced,50%reserve,default guards unchanged,pending proposal blocks training,and later averaged original ratios cannot clear an explicit hold.')
