"""Transcribes the tables of experimental_log.md (INSTRUCTIONS.md) verbatim, recomputes every
'Performance Gap' row, and flags mismatches. Output: results_tables.csv, gap_audit.csv"""
import csv
M=['test','remaining','forget','mia']
# (table, setting, method, test, remaining, forget, mia)  -- verbatim from the log
rows=[
('forget_size','15%','Retrained',73,75,73,50),('forget_size','15%','Unlearned(-)',59,60,59,55.8),
('forget_size','10%','Retrained',72,74,72,50),('forget_size','10%','Unlearned(-)',70,71,68,51.4),
('forget_size','5%','Retrained',73,74,73,49.4),('forget_size','5%','Unlearned(-)',73,74,73,49.4),
('perturbations','250','Retrained',72,74,72,50),('perturbations','250','Unlearned(-)',57,58,57,56.2),
('perturbations','500','Retrained',72,74,72,50),('perturbations','500','Unlearned(-)',70,71,68,51.4),
('perturbations','1000','Retrained',72,74,72,50),('perturbations','1000','Unlearned(-)',72,74,71,49),
('lambda','0','Retrained',72,74,72,50),('lambda','0','Unlearned(-)',70,71,68,51.4),
('lambda','0.0005','Retrained',72,74,72,50),('lambda','0.0005','Unlearned(-)',71,72,71,49.8),
('lambda','0.001','Retrained',72,74,72,50),('lambda','0.001','Unlearned(-)',72,73,72,50.9),
('mixed_c100','20%','Retrained',62.2,65.7,62.6,50),('mixed_c100','20%','Unlearned(+)',60.1,63.4,59.3,50.4),('mixed_c100','20%','Unlearned(-)',60,70,63.2,50.8),
('mixed_c100','15%','Retrained',63.1,68.9,63.3,50.2),('mixed_c100','15%','Unlearned(+)',61.9,67.9,62.2,50.7),('mixed_c100','15%','Unlearned(-)',61.4,70.1,62.2,51.7),
('mixed_c100','10%','Retrained',63.7,72,63.9,50),('mixed_c100','10%','Unlearned(+)',63.3,72.5,64.9,51),('mixed_c100','10%','Unlearned(-)',62.8,70.1,61.2,52.3),
('baselines_c10','10%','Retrained',72,74,72,50),('baselines_c10','10%','NegGrad',51.9,53.2,51.2,48),
('baselines_c10','10%','RandomLabels',20.6,21.6,21.4,47),('baselines_c10','10%','JiT',52.1,53.1,51.1,49.1),
('baselines_c10','10%','Adversarial',51.5,52.7,51.0,50.0),('baselines_c10','10%','Unlearned(-)',70,71,68,51.4),
]
# gap rows as printed in the log: (table, setting) -> 4 values
logged={('forget_size','15%'):(14,15,14,5.8),('forget_size','10%'):(2,3,4,1.4),('forget_size','5%'):(0,0,0,0),
('perturbations','250'):(15,16,15,6.2),('perturbations','500'):(2,3,4,1.4),('perturbations','1000'):(0,0,1,1),
('lambda','0'):(2,3,4,1.4),('lambda','0.0005'):(1,2,1,0.2),('lambda','0.001'):(0,1,0,0.9),
('mixed_c100','20%'):(0.1,6.6,3.9,0.4),('mixed_c100','15%'):(0.5,2.2,0.0,1.0),('mixed_c100','10%'):(0.5,2.4,3.7,1.3)}
with open('results_tables.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['table','setting','method']+M); w.writerows(rows)
R={(t,s,m):v for t,s,m,*v in rows}
out=[]
for (t,s),lg in logged.items():
    un=R[(t,s,'Unlearned(-)')]; rt=R[(t,s,'Retrained')]
    gr=[round(abs(a-b),1) for a,b in zip(un,rt)]
    gp=[round(abs(a-b),1) for a,b in zip(un,R[(t,s,'Unlearned(+)')])] if (t,s,'Unlearned(+)') in R else [None]*4
    ok_r=all(abs(a-b)<1e-9 for a,b in zip(gr,lg)); ok_p=gp[0] is not None and all(abs(a-b)<1e-9 for a,b in zip(gp,lg))
    ref='Retrained' if ok_r else ('Unlearned(+)' if ok_p else 'NEITHER')
    out.append([t,s,*lg,*gr,*gp,ref])
with open('gap_audit.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(['table','setting']+['logged_gap_'+m for m in M]+['gap_vs_Retrained_'+m for m in M]+['gap_vs_Unl+_'+m for m in M]+['logged_gap_is_relative_to'])
    w.writerows(out)
for r in out: print(r[0],r[1],'| logged',r[2:6],'| vs Retrained',r[6:10],'| vs U+',r[10:14],'->',r[14])
