import pandas as pd, numpy as np
pd.set_option('display.width',250)
d=pd.read_csv("artifacts/results/e6_paired.csv")
a=d[d.tag=="arena_st"]
c=a[a.dataset=="st_crowd"].set_index("pair")
rows=[]
for ds in a.dataset.unique():
    s=a[a.dataset==ds].set_index("pair").reindex(c.index)
    agree=np.mean(s.higher==c.higher)
    kl=s.z_sand*np.sqrt(s.local)/s.k
    rows.append(dict(ds=ds, agree=agree, med_k=s.k.median(), med_z=s.z_model.abs().median(), med_kloc=kl[s.k>=3].median(),
        ratio_k_vs_crowd=np.exp(np.median(np.log((s.k+1)/(c.k+1)))), frac_k_le_1pct=np.mean(s.k/s.N<=0.01),
        med_gap=s.gap.median()))
print(pd.DataFrame(rows).round(3).to_string())
m=d[d.tag=="mtbench"]
for ds in ["mt_human","mt_gpt4"]:
    s=m[m.dataset==ds]; print(ds, s.k.median(), (s.k/s.N).median(), s.z_model.median(), (s.z_sand*np.sqrt(s.local)/s.k).median())
sub=m[m.dataset.str.startswith("mt_human_sub")]
print("sub", sub.groupby("dataset").k.median().describe(), (sub.k/sub.N).median())
print(m[m.dataset.isin(["mt_human","mt_gpt4"])].pivot_table(index="pair",columns="dataset",values="k"))
print(sub.groupby("pair").k.agg(["median",lambda x:x.quantile(.05),lambda x:x.quantile(.95)]))
