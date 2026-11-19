from analysis_common import *
df = load('e10_clusterres')
S = summarize(df, ['graph', 'design_res', 'mech', 'est'])
S.to_csv(f'{RES}/summary_e10.csv', index=False)
pd.set_option('display.width', 250)
for m in ['sat', 'thresh']:
    q = S[(S.mech == m)]
    print(m); print(q.pivot_table(index=['graph', 'design_res', 'K', 'cut'], columns='est', values='rmse').round(2).to_string())
