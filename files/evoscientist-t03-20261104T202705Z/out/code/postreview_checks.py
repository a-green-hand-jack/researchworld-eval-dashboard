"""Regression checks for sensitivity manifest isolation; no model training."""
import tempfile,json
from pathlib import Path
import experiment as e

def main():
    original=e.OUT;checks={}
    try:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as td:
            e.OUT=Path(td)
            for ds in ('pima','acs'):
                a=e.load_data(ds,n_instances=30)
                before=(e.OUT/f'data_{ds}.json').read_bytes()
                b=e.load_data(ds,n_instances=10,manifest_suffix='_b16')
                assert (e.OUT/f'data_{ds}.json').read_bytes()==before
                ma=json.loads(before);mb=json.loads((e.OUT/f'data_{ds}_b16.json').read_text())
                assert ma['instances'][:10]==mb['instances']
                assert ma['background']==mb['background']
                checks[ds]={'main_n':len(ma['instances']),'sensitivity_n':len(mb['instances']),'main_manifest_unchanged':True}
    finally: e.OUT=original
    (Path(__file__).parent/'postreview_checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
