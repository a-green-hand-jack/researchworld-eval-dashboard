"""Real-tool case study: DSPy BootstrapFewShotWithRandomSearch on MMLU-Pro with a local llama.cpp server.
Per replicate: draw search/benchmark set S (n items) from the population (excluding the fixed test set T), compile with
trainset=valset=S (DSPy's default), record per-candidate per-item scores on S, the chosen program's accuracy on fresh T.
Usage: python exp_dspy.py PORT OUT_DIR REP_START REP_END [N] [NTEST] [NCAND]"""
import os, sys, json, time, random
os.environ["NO_PROXY"] = "localhost,127.0.0.1"; os.environ["no_proxy"] = "localhost,127.0.0.1"
import numpy as np, dspy
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
sys.path.insert(0, "/work/code")
from common import *

port, outdir, r0, r1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
n = int(sys.argv[5]) if len(sys.argv) > 5 else 100
ntest = int(sys.argv[6]) if len(sys.argv) > 6 else 300
ncand = int(sys.argv[7]) if len(sys.argv) > 7 else 6
os.makedirs(outdir, exist_ok=True)
df = load_test(); pop = population_ids(1500, seed=0)
test_pos = pop[-ntest:]              # fixed fresh test items (never in any S)
search_pool = pop[:-ntest]
lm = dspy.LM("openai/qwen", api_base=f"http://localhost:{port}/v1", api_key="x", temperature=0.0, max_tokens=30, cache=False)
dspy.configure(lm=lm)

class QA(dspy.Signature):
    """Answer the multiple choice question with the letter of the correct option."""
    question: str = dspy.InputField()
    options: str = dspy.InputField()
    answer: str = dspy.OutputField(desc="a single letter A-J")

def ex(p):
    r = df.iloc[int(p)]
    return dspy.Example(question=r["question"], options="\n".join(f"{LETTERS[k]}. {o}" for k, o in enumerate(r["options"])), answer=r["answer"]).with_inputs("question", "options")

def metric(gold, pred, trace=None):
    a = (pred.answer or "").strip().upper()
    return float(a[:1] == gold.answer) if a else 0.0

def acc_on(prog, exs):
    ok = []
    for e in exs:
        try: ok.append(metric(e, prog(question=e.question, options=e.options)))
        except Exception: ok.append(0.0)
    return np.array(ok)

test = [ex(p) for p in test_pos]
fn0 = f"{outdir}/baseline_zeroshot.json"
if not os.path.exists(fn0):
    t = time.time(); a0 = acc_on(dspy.Predict(QA), test)
    json.dump(dict(acc=float(a0.mean()), per_item=a0.tolist(), secs=time.time() - t), open(fn0, "w"))
    print("zero-shot test acc", a0.mean(), flush=True)

for rep in range(r0, r1):
    fn = f"{outdir}/rep_{rep:03d}.json"
    if os.path.exists(fn): continue
    t = time.time()
    rng = np.random.default_rng(10_000 + rep)
    S = rng.choice(search_pool, size=n, replace=False)
    train = [ex(p) for p in S]
    random.seed(rep)
    opt = BootstrapFewShotWithRandomSearch(metric=metric, max_bootstrapped_demos=3, max_labeled_demos=3, num_candidate_programs=ncand, num_threads=1)
    best = opt.compile(dspy.Predict(QA), trainset=train)
    cands = [dict(seed=c["seed"], score=c["score"], subscores=[float(x) for x in c["subscores"]]) for c in best.candidate_programs]
    top_score = cands[0]["score"]
    t_search = time.time() - t
    at = acc_on(best, test)
    json.dump(dict(rep=rep, S=[int(x) for x in S], reported_score=top_score, cands=cands, test_acc=float(at.mean()), test_per_item=at.tolist(),
                   secs_search=t_search, secs_total=time.time() - t), open(fn, "w"))
    print(f"rep {rep}: reported {top_score:.1f} test {100*at.mean():.1f} ({time.time()-t:.0f}s)", flush=True)
