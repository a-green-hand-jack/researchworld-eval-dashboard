import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from study_analysis import study_analysis
parser = argparse.ArgumentParser()
parser.add_argument('runs')
parser.add_argument('--output',required=True)
args = parser.parse_args()
result = study_analysis(json.loads(Path(args.runs).read_text()))
Path(args.output).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print('Registered study comparisons written; completeness and fit gate recorded')
