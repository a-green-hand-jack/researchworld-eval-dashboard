import asyncio, time, anthropic, pandas as pd, warnings, sys
warnings.filterwarnings("ignore")
d = pd.read_parquet("data/mmlu_pro/data/test-00000-of-00001.parquet").sample(40, random_state=0)
L="ABCDEFGHIJ"
def prompt(r):
    return "Answer the following multiple-choice question. Reply with only the letter of the correct option.\n\nQuestion: "+r.question+"\n"+"\n".join(f"{L[i]}. {o}" for i,o in enumerate(r.options))+"\nAnswer:"
async def main(model):
    c = anthropic.AsyncAnthropic(max_retries=2)
    sem = asyncio.Semaphore(16)
    async def one(r):
        async with sem:
            try:
                x = await c.messages.create(model=model, max_tokens=5, messages=[{"role":"user","content":prompt(r)}])
                return x.content[0].text.strip()[:1], x.usage.input_tokens
            except Exception as e:
                return "ERR:"+str(e)[:60], 0
    t=time.time()
    out = await asyncio.gather(*[one(r) for r in d.itertuples()])
    acc = sum(o[0]==r.answer for o,r in zip(out,d.itertuples()))/len(d)
    print(model, "acc",acc, "time",round(time.time()-t,1), "errs",sum(o[0].startswith("ERR") for o in out), out[:5], "in_tok", sum(o[1] for o in out))
for m in sys.argv[1:]: asyncio.run(main(m))
