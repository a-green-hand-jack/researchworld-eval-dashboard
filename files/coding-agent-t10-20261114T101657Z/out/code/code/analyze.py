import json, numpy as np, sys
r=json.load(open('/work/code/results.json'))
M=['classical','PPI','PPI++','PPI++_t','recal-iso','recal-iso_t','recal-gbm','recal-gbm_t']
DS=['galaxies','forest','alphafold','gene_expression','census_income','census_healthcare']
rows=[]; L=[]
for d in DS:
  for n in (50,200,1000):
    base=np.array(r[f'{d}|{n}|PPI++'])[:,1]
    line=[d.replace('_','\\_'),str(n)]
    for m in M:
        a=np.array(r[f'{d}|{n}|{m}']); c=a[:,0].mean(); se=np.sqrt(c*(1-c)/len(a))
        w=a[:,1].mean()
        line.append(f'{100*c:.1f}'); 
        line.append(f'{w/base.mean():.3f}' if m!='classical' or True else '')
    rows.append(line)
with open('/work/paper/table.tex','w') as f:
    f.write('\\begin{tabular}{ll'+'rr'*len(M)+'}\\toprule\n')
    f.write('data & $n$ & '+' & '.join('\\multicolumn{2}{c}{'+m.replace('_','\\_')+'}' for m in M)+'\\\\\n')
    f.write(' & & '+' & '.join(['cov','w']*len(M))+'\\\\\\midrule\n')
    for l in rows: f.write(' & '.join(l)+'\\\\\n')
    f.write('\\bottomrule\\end{tabular}\n')
for l in rows: print(' '.join(l))
