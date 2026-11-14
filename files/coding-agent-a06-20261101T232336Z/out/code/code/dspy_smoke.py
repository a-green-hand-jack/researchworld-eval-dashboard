import os, sys, time
os.environ["NO_PROXY"]="localhost,127.0.0.1"; os.environ["no_proxy"]="localhost,127.0.0.1"
import dspy, numpy as np
sys.path.insert(0,"/work/code")
from common import *
df=load_test(); ids=population_ids(1500)
lm=dspy.LM("openai/qwen", api_base="http://localhost:8013/v1", api_key="x", temperature=0.0, max_tokens=40, cache=False)
dspy.configure(lm=lm)
class QA(dspy.Signature):
    """Answer the multiple choice question with the letter of the correct option."""
    question: str = dspy.InputField()
    options: str = dspy.InputField()
    answer: str = dspy.OutputField(desc="a single letter")
prog=dspy.Predict(QA)
def ex(i):
    r=df.iloc[int(ids[i])]
    return dspy.Example(question=r["question"], options="\n".join(f"{LETTERS[k]}. {o}" for k,o in enumerate(r["options"])), answer=r["answer"]).with_inputs("question","options")
ok=0;t=time.time()
for i in range(12):
    e=ex(i); p=prog(question=e.question, options=e.options)
    ok+= p.answer.strip()[:1].upper()==e.answer
    print(i, repr(p.answer), e.answer, round(time.time()-t,1), flush=True)
print(ok/12)
