"""Transcribe every number of experimental_log.md into a long-format ledger and
re-derive the stated 'Performance Gap' rows. Inputs: the task's experimental log
(INSTRUCTIONS.md, section [EXPERIMENTAL LOGS]); no number here comes from elsewhere."""
import csv, sys
# (table, setting, method, test, remain, forget, mia); setting is the varied quantity.
T = []
def add(table, setting, rows): 
    for m, *v in rows: T.append((table, setting, m, *v))
add('forget_size_cifar10','15%',[('Retrained',73,75,73,50),('Unlearned-',59,60,59,55.8)])
add('forget_size_cifar10','10%',[('Retrained',72,74,72,50),('Unlearned-',70,71,68,51.4)])
add('forget_size_cifar10','5%', [('Retrained',73,74,73,49.4),('Unlearned-',73,74,73,49.4)])
add('perturbations_cifar10','250', [('Retrained',72,74,72,50),('Unlearned-',57,58,57,56.2)])
add('perturbations_cifar10','500', [('Retrained',72,74,72,50),('Unlearned-',70,71,68,51.4)])
add('perturbations_cifar10','1000',[('Retrained',72,74,72,50),('Unlearned-',72,74,71,49)])
add('lambda_cifar10','0',     [('Retrained',72,74,72,50),('Unlearned-',70,71,68,51.4)])
add('lambda_cifar10','0.0005',[('Retrained',72,74,72,50),('Unlearned-',71,72,71,49.8)])
add('lambda_cifar10','0.001', [('Retrained',72,74,72,50),('Unlearned-',72,73,72,50.9)])
add('mixed_linear_cifar100','20%',[('Retrained',62.2,65.7,62.6,50),('Unlearned+',60.1,63.4,59.3,50.4),('Unlearned-',60,70,63.2,50.8)])
add('mixed_linear_cifar100','15%',[('Retrained',63.1,68.9,63.3,50.2),('Unlearned+',61.9,67.9,62.2,50.7),('Unlearned-',61.4,70.1,62.2,51.7)])
add('mixed_linear_cifar100','10%',[('Retrained',63.7,72,63.9,50),('Unlearned+',63.3,72.5,64.9,51),('Unlearned-',62.8,70.1,61.2,52.3)])
add('baselines_cifar10','10%',[('Retrained',72,74,72,50),('NegGrad',51.9,53.2,51.2,48),('RandomLabels',20.6,21.6,21.4,47),('JiT',52.1,53.1,51.1,49.1),('Adversarial',51.5,52.7,51.0,50.0),('Unlearned-',70,71,68,51.4)])
with open('results_ledger.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow('table setting method test_acc remaining_acc forget_acc mia'.split()); w.writerows(T)
# stated gaps in the log: (table, setting) -> (test, remain, forget, mia)
STATED = {('forget_size_cifar10','15%'):(14,15,14,5.8),('forget_size_cifar10','10%'):(2,3,4,1.4),('forget_size_cifar10','5%'):(0,0,0,0),
 ('perturbations_cifar10','250'):(15,16,15,6.2),('perturbations_cifar10','500'):(2,3,4,1.4),('perturbations_cifar10','1000'):(0,0,1,1),
 ('lambda_cifar10','0'):(2,3,4,1.4),('lambda_cifar10','0.0005'):(1,2,1,0.2),('lambda_cifar10','0.001'):(0,1,0,0.9),
 ('mixed_linear_cifar100','20%'):(0.1,6.6,3.9,0.4),('mixed_linear_cifar100','15%'):(0.5,2.2,0.0,1.0),('mixed_linear_cifar100','10%'):(0.5,2.4,3.7,1.3)}
d={(t,s,m):v for t,s,m,*v in T}
rows=[]
for (t,s),st in STATED.items():
    ref = 'Unlearned+' if t.startswith('mixed') else 'Retrained'
    # In the mixed-linear table the stated gap is Unlearned(-) vs Unlearned(+), not vs Retrained.
    for name,r in (('vs_stated_ref',ref),('vs_retrained','Retrained')):
        g=[round(abs(a-b),2) for a,b in zip(d[(t,s,'Unlearned-')],d[(t,s,r)])]
        rows.append((t,s,name,r,*g,'MATCH' if all(abs(x-y)<0.051 for x,y in zip(g,st)) else 'differs'))
with open('gap_check.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow('table setting comparison reference gap_test gap_remain gap_forget gap_mia matches_stated_gap'.split()); w.writerows(rows)
for r in rows: print(*r)
