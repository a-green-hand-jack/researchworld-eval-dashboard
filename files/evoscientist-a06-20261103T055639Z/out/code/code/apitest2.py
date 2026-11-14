import anthropic, warnings, pandas as pd, sys, time, collections
import concurrent.futures as cf
warnings.filterwarnings("ignore")
c = anthropic.Anthropic(max_retries=0)
d = pd.read_parquet("data/mmlu_pro/data/test-00000-of-00001.parquet").sample(60, random_state=1)
L="ABCDEFGHIJ"
def prompt(r):
    return "Answer the following multiple-choice question. Reply with only the letter of the correct option.\n\nQuestion: "+r.question+"\n"+"\n".join(f"{L[i]}. {o}" for i,o in enumerate(r.options))+"\nAnswer:"
def one(r, m):
    try:
        x = c.messages.create(model=m, max_tokens=4, messages=[{"role":"user","content":prompt(r)}])
        t = x.content[0].text.strip() if x.content and hasattr(x.content[0],'text') else ""
        return ("ok" if x.usage.input_tokens>0 and t[:1] in L else "notice:"+t[:20]), t[:1], x.model
    except Exception as e: return ("err:"+str(e)[:40],"","")
for m in sys.argv[1:]:
    t=time.time()
    with cf.ThreadPoolExecutor(8) as ex: a = list(ex.map(lambda r: one(r,m), d.itertuples()))
    print(m, collections.Counter(x[0] for x in a), "acc_ok", sum(x[1]==r.answer for x,r in zip(a,d.itertuples()) if x[0]=="ok"), round(time.time()-t,1))
