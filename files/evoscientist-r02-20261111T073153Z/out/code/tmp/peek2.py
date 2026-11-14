import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
A=pd.read_csv('results/summary_synth_main.csv')
s=A[(A.n_cal==200)&(A.K==5)]
print(s.pivot(index='method',columns='dgp',values='ent_gap').round(3))
print(s.pivot(index='method',columns='dgp',values='arg_gap').round(3))
print(s[s.dgp=='mult'][['method','cov_zero0','cov_zero1']].round(3))
print(s[s.dgp=='ln_het'][['method','ent_cov0','ent_cov2']].round(3))
print(s[s.dgp=='ln'][['method','ent_cov0','ent_cov2']].round(3))
s=A[(A.n_cal==200)&(A.K==10)]
print(s.pivot(index='method',columns='dgp',values='ent_gap').round(3))
print(s.pivot(index='method',columns='dgp',values='size_pool').round(3))
print(A[A.n_cal==50].pivot_table(index='method',columns=['dgp','K'],values='size_pool').round(3).iloc[:, :6])
