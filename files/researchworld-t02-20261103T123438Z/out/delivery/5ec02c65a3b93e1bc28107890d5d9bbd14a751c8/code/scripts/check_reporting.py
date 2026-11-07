"""Software fixtures for terminal/onset and CPU sampling; never scientific data."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cell_summary import summarize_cells
from events import summarize_curve

rows=[dict(step=i*100,train_acc=1.,valid_acc=.96 if i<3 else .2) for i in range(6)]
events=summarize_curve(rows,horizon=300)
base=dict(family='main',p=31,task='add',fraction=.5,activation='relu',width=32,lr=.001,
    weight_decay=1.,steps=60200,onset_horizon=60000,eval_every=100,split_rule='ordered',frozen_hidden=False,
    split_seed=1100,init_seed=2100,block=0,path='SOFTWARE_FIXTURE',status='other_confirmed_generalization',
    cpu100_step=300,cpu100_recorded_s=99.,cpu100_acc=.2,horizon_completed_before_cpu100=False,
    execution_completed_before_cpu100=False,cpu_accounting_incomplete=False,**events)
cell=summarize_cells([base])[0]
assert cell['valid_events']==1 and cell['terminal_valid_events']==0
assert cell['terminal_train_events']==1
assert cell['cpu100_sampling']['min_step']==300
missing=dict(base,split_seed=1101,init_seed=2101,block=1,cpu100_step=None,cpu100_recorded_s=None,
    cpu100_acc=None,cpu_accounting_incomplete=True)
cell=summarize_cells([base,missing])[0]
assert cell['cpu100_acc'] is None and cell['cpu100_sampling']['available_n']==1
assert cell['cpu100_sampling']['incomplete_accounting']==1
repo=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    for rel in ['configs/confirmatory.json','results/gate-benchmarks/resource-quote.json','reproduction/deadline_ledger.json']:
        target=root/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((repo/rel).read_bytes())
    # Exercise current-format configs, which already contain derived/default keys.
    original=repo/'results/implementation-checks-v2/short'
    validation=root/'software-fixture/short'
    validation.mkdir(parents=True)
    metadata=json.loads((original/'metadata.json').read_text())
    metadata['config']['onset_horizon']=metadata['config']['steps']
    metadata['config'].setdefault('frozen_hidden',False)
    metadata['config'].setdefault('split_rule','ordered')
    (validation/'metadata.json').write_text(json.dumps(metadata))
    for filename in ['summary.json','curve.jsonl']:
        (validation/filename).write_bytes((original/filename).read_bytes())
    registry=root/'software-fixture-registry.json'
    registry.write_text(json.dumps(dict(runs=[dict(name='short',family='main',block=0,
        stage='software_fixture',**metadata['config'])])))
    destination=root/'software-fixture-analysis'
    subprocess.run([sys.executable,str(repo/'code/scripts/analyze.py'),str(validation),
        '--registry',str(registry),'--output',str(destination)],check=True,stdout=subprocess.DEVNULL)
    records=json.loads((destination/'runs.json').read_text())
    assert len(records)==1 and records[0]['onset_horizon']==metadata['config']['onset_horizon']
    assert records[0]['frozen_hidden']==metadata['config']['frozen_hidden']
    assert json.loads((destination/'cells-first8.json').read_text())[0]['n']==1
    output=root/'report.json'
    command=[sys.executable,str(repo/'code/scripts/monitor_resources.py'),'--root',str(root),
             '--phase','checkpoint','--output',str(output)]
    subprocess.run(command,check=True,stdout=subprocess.DEVNULL)
    report=json.loads(output.read_text())
    assert report['status_counts']=={'not_started':204}
    assert 22<report['projected_complete_study_with_remaining50percent_reserve_cpu_hours']<23
    directory=root/'results/confirmatory/main_w032_b00'
    directory.mkdir(parents=True)
    (directory/'metadata.json').write_text('{}')
    (directory/'curve.jsonl').write_text(json.dumps(dict(step=1000,cpu_s=10000.,elapsed_s=11000.))+'\n')
    subprocess.run(command,check=True,stdout=subprocess.DEVNULL)
    report=json.loads(output.read_text())
    assert not report['within_cpu_envelope'] and not report['continue_unchanged_affordable_work']
    assert report['status_counts']['started_incomplete']==1
print('PASS: onset/collapse distinction, CPU sample availability, current-format analyzer CLI, baseline204 quote and cost-overrun refusal. Software fixtures only.')
