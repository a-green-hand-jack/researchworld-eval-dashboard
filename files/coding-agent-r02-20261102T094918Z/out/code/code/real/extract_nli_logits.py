"""Logits of two pretrained NLI classifiers on the ChaosNLI SNLI+MNLI-m items (order of columns: entailment, neutral, contradiction).
Writes /work/data/chaosnli/{labels.npy, logits_<model>.npy}"""
import json, numpy as np, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
torch.set_num_threads(16)
items = []
for f in ("snli", "mnli_m"):
    for line in open(f"/work/data/chaosnli/chaosNLI_{f}.jsonl"):
        d = json.loads(line)
        items.append((f, d["example"]["premise"], d["example"]["hypothesis"], d["label_dist"], d["label_count"]))
np.save("/work/data/chaosnli/labels.npy", np.array([it[3] for it in items]))
np.save("/work/data/chaosnli/counts.npy", np.array([it[4] for it in items]))
np.save("/work/data/chaosnli/source.npy", np.array([0 if it[0] == "snli" else 1 for it in items]))
# id -> column index in (e, n, c)
models = {"distilroberta": ("cross-encoder/nli-distilroberta-base", None), "roberta-large": ("roberta-large-mnli", None)}
import os
for short, (name, _) in models.items():
    if os.path.exists(f"/work/data/chaosnli/logits_{short}.npy"):
        continue
    tok = AutoTokenizer.from_pretrained(name)
    m = AutoModelForSequenceClassification.from_pretrained(name).eval()
    id2l = {i: l.lower() for i, l in m.config.id2label.items()}
    print(short, id2l)
    order = [[i for i, l in id2l.items() if l.startswith(p)][0] for p in ("entail", "neutral", "contradict")]
    out = np.zeros((len(items), 3), dtype=np.float32)
    by_len = np.argsort([len(x[1]) + len(x[2]) for x in items])   # length-sorted batches (faster, same result)
    with torch.no_grad():
        for i in range(0, len(items), 32):
            ids = by_len[i:i + 32]
            b = [items[j] for j in ids]
            enc = tok([x[1] for x in b], [x[2] for x in b], return_tensors="pt", padding=True, truncation=True, max_length=256)
            out[ids] = m(**enc).logits[:, order].numpy()
    L = out
    np.save(f"/work/data/chaosnli/logits_{short}.npy", L)
    maj = np.array([it[3] for it in items]).argmax(1)
    print(short, "agreement of argmax with human majority:", (L.argmax(1) == maj).mean())
