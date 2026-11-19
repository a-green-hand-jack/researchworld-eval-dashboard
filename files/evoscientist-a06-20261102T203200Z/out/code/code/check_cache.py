import torch, numpy as np, pandas as pd, time
import local_run as lr
from transformers import AutoTokenizer, AutoModelForCausalLM, DynamicCache
torch.set_num_threads(1)
name="Qwen2.5-0.5B-Instruct"
tok=AutoTokenizer.from_pretrained(f"{lr.BASE}/data/{name}"); model=AutoModelForCausalLM.from_pretrained(f"{lr.BASE}/data/{name}",dtype=torch.float32).eval()
test=pd.read_parquet(lr.DATA+"/test-00000-of-00001.parquet"); pool=lr.pool_indices(50)
cfgs=lr.local_configs(41)
rows=[test.iloc[int(pool[j])] for j in range(3)]
for c in [cfgs[0],cfgs[5]]:
  for r in rows:
    q=lr.question_text(r)
    s=(lr.SUF_INSTR[c["ins"]]).rstrip()
    full=tok.apply_chat_template([{"role":"user","content":q+s}],tokenize=False,add_generation_prompt=True)+lr.CUES[c["cue"]]
    ids=tok(full,add_special_tokens=False,return_tensors="pt")["input_ids"]
    lid=torch.tensor(lr.letter_ids(tok,lr.CUES[c["cue"]]))
    with torch.no_grad(): lg=model(input_ids=ids).logits[0,-1,lid]
    print(c, torch.log_softmax(lg,-1).numpy().round(2))
print(full[-200:])
