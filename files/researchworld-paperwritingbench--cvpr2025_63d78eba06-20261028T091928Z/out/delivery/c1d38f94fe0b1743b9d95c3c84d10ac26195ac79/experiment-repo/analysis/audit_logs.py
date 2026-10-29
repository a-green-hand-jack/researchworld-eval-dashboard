"""Transcribe the experimental-log tables (values exactly as logged) and audit the logged
'Performance Gap' rows. Writes results/log_tables.csv and results/gap_audit.csv.
Source: Research objective issue (experimental_log.md section 2); nothing here is measured by us."""
import csv, itertools
# (table, setting, method, test, remaining, forget, mia, logged_gap or None)
T=[]
def add(table,setting,method,vals,gap=None): T.append((table,setting,method,*vals,gap))
# --- forget-size ablation, CIFAR-10 linear classifier
add('forget_size_cifar10','15%','Retrained',(73,75,73,50))
add('forget_size_cifar10','15%','Unlearned(-)',(59,60,59,55.8),(14,15,14,5.8))
add('forget_size_cifar10','10%','Retrained',(72,74,72,50))
add('forget_size_cifar10','10%','Unlearned(-)',(70,71,68,51.4),(2,3,4,1.4))
add('forget_size_cifar10','5%','Retrained',(73,74,73,49.4))
add('forget_size_cifar10','5%','Unlearned(-)',(73,74,73,49.4),(0,0,0,0))
# --- perturbation ablation
add('perturbations_cifar10','-','Retrained',(72,74,72,50))
add('perturbations_cifar10','250','Unlearned(-)',(57,58,57,56.2),(15,16,15,6.2))
add('perturbations_cifar10','500','Unlearned(-)',(70,71,68,51.4),(2,3,4,1.4))
add('perturbations_cifar10','1000','Unlearned(-)',(72,74,71,49),(0,0,1,1))
# --- lambda ablation
add('lambda_cifar10','-','Retrained',(72,74,72,50))
add('lambda_cifar10','0','Unlearned(-)',(70,71,68,51.4),(2,3,4,1.4))
add('lambda_cifar10','0.0005','Unlearned(-)',(71,72,71,49.8),(1,2,1,0.2))
add('lambda_cifar10','0.001','Unlearned(-)',(72,73,72,50.9),(0,1,0,0.9))
# --- mixed linear network, CIFAR-100
for f,r,p,m,g in [('20%',(62.2,65.7,62.6,50),(60.1,63.4,59.3,50.4),(60,70,63.2,50.8),(0.1,6.6,3.9,0.4)),
                   ('15%',(63.1,68.9,63.3,50.2),(61.9,67.9,62.2,50.7),(61.4,70.1,62.2,51.7),(0.5,2.2,0.0,1.0)),
                   ('10%',(63.7,72,63.9,50),(63.3,72.5,64.9,51),(62.8,70.1,61.2,52.3),(0.5,2.4,3.7,1.3))]:
    add('mixed_linear_cifar100',f,'Retrained',r); add('mixed_linear_cifar100',f,'Unlearned(+)',p)
    add('mixed_linear_cifar100',f,'Unlearned(-)',m,g)
# --- source-free baseline comparison
for n,v in [('Retrained',(72,74,72,50)),('NegGrad',(51.9,53.2,51.2,48)),('RandomLabels',(20.6,21.6,21.4,47)),
            ('JiT',(52.1,53.1,51.1,49.1)),('Adversarial',(51.5,52.7,51.0,50.0)),('Unlearned(-)',(70,71,68,51.4))]:
    add('baselines_cifar10','10%',n,v)
M=['test','remaining','forget','mia']
with open('results/log_tables.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['table','setting','method']+M+['logged_gap_'+m for m in M])
    for t in T: w.writerow(list(t[:7])+(list(t[7]) if t[7] else ['']*4))
# audit gaps: for each logged-gap row, compare |U(-)-Retrained| and |U(-)-U(+)| with logged values
rows=[]
for i,t in enumerate(T):
    if not t[7]: continue
    tab,st,_,*v,g=t
    ref={r[2]:r[3:7] for r in T if r[0]==tab and (r[1]==st or r[1]=='-') and r[2] in('Retrained','Unlearned(+)')}
    gr=[round(abs(a-b),1) for a,b in zip(v,ref['Retrained'])]
    gp=[round(abs(a-b),1) for a,b in zip(v,ref['Unlearned(+)'])] if 'Unlearned(+)' in ref else None
    rows.append([tab,st]+list(g)+gr+(gp or ['']*4)+
        ['vs_Retrained' if all(abs(a-b)<0.051 for a,b in zip(g,gr)) else ('vs_Unlearned(+)' if gp and all(abs(a-b)<0.051 for a,b in zip(g,gp)) else 'MISMATCH')])
with open('results/gap_audit.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['table','setting']+['logged_'+m for m in M]+['recomp_vs_retrained_'+m for m in M]+['recomp_vs_U+_'+m for m in M]+['logged_gap_is'])
    w.writerows(rows)
for r in rows: print(r[0],r[1],r[-1],'| logged',r[2:6],'| vs Retrained',r[6:10])
