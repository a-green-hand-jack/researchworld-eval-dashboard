import time, torch, pandas as pd
from huggingface_hub import snapshot_download
p=snapshot_download("TIGER-Lab/MMLU-Pro",repo_type="dataset",revision="b189ec765aa7ed75c8acfea42df31fdae71f97be",local_dir="mmlu")
import glob
f=glob.glob("mmlu/data/test-*.parquet")[0]
df=pd.read_parquet(f); print(len(df), df.category.value_counts().to_dict())
from transformers import AutoTokenizer, AutoModelForCausalLM
import sys
for name in sys.argv[1:]:
    tok=AutoTokenizer.from_pretrained(name); m=AutoModelForCausalLM.from_pretrained(name,dtype=torch.float32).eval()
    letters="ABCDEFGHIJ"; ids=[tok.encode(" "+l,add_special_tokens=False)[-1] for l in letters]
    def prompt(r):
        opts="\n".join(f"{letters[i]}. {o}" for i,o in enumerate(r.options))
        msg=f"Answer the multiple choice question with the letter only.\n\nQuestion: {r.question}\n{opts}"
        return tok.apply_chat_template([{"role":"user","content":msg}],tokenize=False,add_generation_prompt=True)+"The answer is"
    rows=[r for r in df.sample(16,random_state=0).itertuples()]
    t=time.time(); corr=0; ntok=0
    for r in rows:
        x=tok(prompt(r),return_tensors="pt"); ntok+=x.input_ids.shape[1]
        with torch.no_grad(): lg=m(**x).logits[0,-1]
        corr+= int(lg[ids[:len(r.options)]].argmax())==letters.index(r.answer)
    dt=time.time()-t; print(name,"items/s",16/dt,"avg tok",ntok/16,"acc",corr/16,flush=True)
