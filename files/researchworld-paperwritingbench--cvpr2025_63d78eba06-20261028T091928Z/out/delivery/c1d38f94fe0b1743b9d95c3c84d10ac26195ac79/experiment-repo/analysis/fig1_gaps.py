"""Gap statistics from the digitized Fig. 1 (estimates, ~+-1 pt) and read-off check against logged CIFAR-10 values.
Writes results/figure1_gaps.csv and prints summary."""
import pandas as pd
d=pd.read_csv('results/figure1_digitized.csv')
v=d.pivot_table(index=['panel','group'],columns='method',values='value_est').round(1)
rows=[]
for (p,g),r in v.iterrows():
    rows.append(dict(panel=p,metric=g,Retrained=r['Retrained'],U_plus=r['Unlearned(+)'],U_minus=r['Unlearned(-)'],
        gap_Uminus_vs_Ret=round(abs(r['Unlearned(-)']-r['Retrained']),1),gap_Uplus_vs_Ret=round(abs(r['Unlearned(+)']-r['Retrained']),1),
        gap_Uminus_vs_Uplus=round(abs(r['Unlearned(-)']-r['Unlearned(+)']),1)))
o=pd.DataFrame(rows); o.to_csv('results/figure1_gaps.csv',index=False)
print(o.to_string(index=False))
print(o.groupby('metric')[['gap_Uminus_vs_Ret','gap_Uplus_vs_Ret','gap_Uminus_vs_Uplus']].mean().round(1))
# read-off check vs log for CIFAR-10 (Retrained 72/74/72/50; U(-) 70/71/68/51.4)
log={'Test':(72,70),'Remaining':(74,71),'Forget':(72,68),'MIA':(50,51.4)}
for m,(a,b) in log.items():
    r=v.loc[('CIFAR-10',m)]; print('readoff err',m,round(r['Retrained']-a,1),round(r['Unlearned(-)']-b,1))
