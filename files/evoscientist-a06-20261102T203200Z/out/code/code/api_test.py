import anthropic, time, sys, pandas as pd, concurrent.futures as cf, os
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test=pd.read_parquet(BASE+"/data/mmlu-pro/data/test-00000-of-00001.parquet")
c=anthropic.Anthropic(max_retries=0)
L="ABCDEFGHIJ"
def ask(model,i):
    r=test.iloc[i]
    q=r["question"]+"\n"+"\n".join(f"{L[k]}. {o}" for k,o in enumerate(r["options"]))+"\n\nRespond with only the letter of the correct option."
    t=time.time()
    try:
        m=c.messages.create(model=model,max_tokens=8,messages=[{"role":"user","content":q}])
        txt=m.content[0].text.strip() if m.content else ""
        return (txt[:1]==r["answer"], time.time()-t, m.usage.input_tokens, txt)
    except Exception as e:
        return (None,time.time()-t,0,str(e)[:80])
model=sys.argv[1]; n=int(sys.argv[2]); conc=int(sys.argv[3])
t=time.time()
with cf.ThreadPoolExecutor(conc) as ex: res=list(ex.map(lambda i:ask(model,i),range(n)))
ok=[r for r in res if r[0] is not None]
print(model,"n",n,"ok",len(ok),"acc",sum(r[0] for r in ok)/max(1,len(ok)),"wall",round(time.time()-t,1),"mean lat",sum(r[1] for r in res)/n,"in_tok",sum(r[2] for r in ok)/max(1,len(ok)))
print([r[3] for r in res if r[0] is None][:3], [r[3] for r in ok[:5]])
