#!/usr/bin/env python3
"""Generate appendix proof tables with exact rational calculations, not empirical data."""
from pathlib import Path
from fractions import Fraction
import json
from counterexamples import exact_K,exact_score
ROOT=Path(__file__).resolve().parents[1]

def main():
    records=json.loads((ROOT/'artifacts/counterexamples.json').read_text())['examples'];matrices=[]
    for r in records:
        a=[[Fraction(x) for x in row] for row in r['matrix']]
        if a not in matrices:matrices.append(a)
    assert len(matrices)==4
    tasksets=[[2,4,5],[3,5],[1,4],[2,5]] # 1-based audited endpoint witnesses
    rows=[];kt=['\\begin{tabular}{lrrr}','\\toprule','Matrix & $K_{\\rm mean}$ & $K_{\\rm median}$ & $K_{\\rm Borda}$\\\\','\\midrule'];wt=['\\begin{tabular}{lll}','\\toprule','Matrix & Endpoint tasks & Updated $(B_0,B_1,B_2,B_3)$\\\\','\\midrule']
    for label,a,ss in zip('ABCD',matrices,tasksets):
        ks={r:exact_K(a,r) for r in ['mean','median','borda']};edited=[row[:] for row in a]
        for j in ss:edited[0][j-1]=Fraction(1)
        doubles=[int(2*v) for v in exact_score(edited,'borda')];assert doubles[0]>=max(doubles[1:]);assert len(ss)==ks['borda']
        kt.append('$'+label+'$ & '+' & '.join(str(ks[r]) for r in ['mean','median','borda'])+' \\\\')
        wt.append('$'+label+'$ & $\\{'+','.join(map(str,ss))+'\\}$ & $('+','.join(map(str,doubles))+')$ \\\\')
        rows.append({'label':label,'K':ks,'borda_tasks_1based':ss,'borda_updated_doubled_totals':doubles})
    for name,lines in [('exact_supports.tex',kt),('exact_borda_witnesses.tex',wt)]:
        lines+=['\\bottomrule','\\end{tabular}'];(ROOT/'paper/generated'/name).write_text('\n'.join(lines))
    (ROOT/'artifacts/exact_table_values.json').write_text(json.dumps(rows,indent=2));print('Exact proof tables regenerated')
if __name__=='__main__':main()
