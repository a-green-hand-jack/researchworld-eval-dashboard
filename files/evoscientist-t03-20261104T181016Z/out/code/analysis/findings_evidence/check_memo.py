"""Read-only memo/table check; writes only validation.json next to this file."""
from pathlib import Path
import re
import hashlib
import json
import pandas as pd

root=Path('/work')
a=root/'analysis/findings_evidence'
p=root/'analysis/findings.md'
text=p.read_text()
c=pd.read_csv(a/'cell_evidence.csv')
checked=0
for line in text.splitlines():
    match=re.match(r'^\| (ACS|Pima|German)/(HGB|LR|RF)(?: \(approx\.\))? \| (kernel|perm) \| (.+) \|$',line)
    if not match:
        continue
    ds,mo,me,values=match.groups()
    ds=ds.lower(); mo=mo.lower()
    fields=values.split(' | ')
    assert len(fields)==3
    for budget,field in zip([1,4,16],fields):
        m=re.fullmatch(r'(\d+); ([0-9.]+) \[([0-9.]+),([0-9.]+)\]',field)
        assert m,(budget,field)
        count,rate,lo,hi=m.groups()
        row=c[(c.dataset==ds)&(c.model==mo)&(c.method==me)&(c.p==budget)].iloc[0]
        assert int(count)==row.success_count
        for got,col in [(rate,'success'),(lo,'success_lo'),(hi,'success_hi')]:
            assert got==f'{row[col]*100:.2f}',(ds,mo,me,budget,got,col)
        checked+=1
assert checked==54
manifest=json.loads((a/'provenance.json').read_text())
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h
           for f,h in manifest['input_sha256'].items())
result=dict(primary_cells_checked=checked,all_input_hashes_unchanged=True,
            memo_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            scope='All 54 primary table counts/rates/CI endpoints checked against frozen CSV; input hash invariance checked; prose separately reviewed.',
            command='python /work/analysis/findings_evidence/check_memo.py')
(a/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
