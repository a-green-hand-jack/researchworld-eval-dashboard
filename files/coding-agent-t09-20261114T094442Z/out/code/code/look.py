import json,pandas as pd,sys
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
def load(e):
    d=pd.DataFrame(json.load(open(f'/work/results/{e}.json')))
    g=d['graph'].apply(json.loads); d['g']=g.apply(lambda s:s['kind']+str({k:v for k,v in s.items() if k not in('kind','n')}) ); return d
if __name__=='__main__':
    d=load(sys.argv[1]); d['rel']=d.rmse/d.truth
    print(d.pivot_table(index=['g','model','design']+sys.argv[2:],columns='est',values='rmse').round(3).to_string())
