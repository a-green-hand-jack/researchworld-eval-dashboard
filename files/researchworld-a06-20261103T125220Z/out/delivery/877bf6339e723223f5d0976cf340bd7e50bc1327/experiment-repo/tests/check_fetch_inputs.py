"""Check actual acquisition CLI selections without touching/download of input bytes."""
import json, subprocess
expected_data={'data/raw/test.parquet','data/raw/validation.parquet'}
models={label:f'models/qwen2.5-{label.lower()}-instruct-q4_k_m.gguf' for label in ['0.5B','1.5B']}
for choice,wanted_models in [('none',set()),('0.5B',{models['0.5B']}),('1.5B',{models['1.5B']}),('all',set(models.values()))]:
 paths=json.loads(subprocess.check_output(['python3','scripts/fetch_inputs.py','--model',choice,'--list'],text=True))
 assert len(paths)==len(set(paths))
 assert set(paths)==expected_data|wanted_models,(choice,paths)
 print(choice,paths)
assert json.loads(subprocess.check_output(['python3','scripts/fetch_inputs.py','--list'],text=True))==json.loads(subprocess.check_output(['python3','scripts/fetch_inputs.py','--model','1.5B','--list'],text=True))
print('PASS: all four acquisition choices and default select exactly the pinned inputs; no download performed.')
