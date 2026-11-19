"""Descriptive statistics of the cached correctness matrices (used in the paper's Setup section / Table 1)."""
import json, sys
import numpy as np
sys.path.insert(0, "code")
from common import load_matrix, to_py

out = {}
for tag in ("Qwen2.5-0.5B-Instruct_fp32", "Qwen2.5-1.5B-Instruct_fp32"):
    try:
        Y, meta = load_matrix(tag)
    except Exception as e:
        print(tag, "unavailable", e); continue
    K, N = Y.shape
    mu = Y.mean(1)
    C = np.corrcoef(Y); off = (C.sum() - K) / (K * (K - 1))
    cov = np.cov(Y); var = Y.var(1).mean(); rho = (cov.sum() - np.trace(cov)) / (K * (K - 1)) / var
    # fraction of questions answered correctly by all/none of configs
    allc = (Y.min(0) == 1).mean(); none = (Y.max(0) == 0).mean()
    # chance level: expected accuracy of random guess = mean(1/n_opts)
    chance = float(np.mean(1.0 / np.array(meta["n_opts"])))
    # between-config sd of true accuracy vs sampling sd for n=400 questions
    se400 = np.sqrt(mu * (1 - mu) / 400).mean()
    top = np.sort(mu)[::-1]
    out[tag] = dict(K=K, N=N, acc_min=mu.min(), acc_median=np.median(mu), acc_max=mu.max(), acc_sd=mu.std(ddof=1),
                    mean_pairwise_corr=off, rho_cov=rho, sigma=np.sqrt(var), frac_all_correct=allc, frac_none_correct=none,
                    chance=chance, se_n400=se400, top3=top[:3], bottom3=top[-3:], stem_share=float(np.mean([c in {"math", "physics", "chemistry", "biology", "engineering", "computer science"} for c in meta["category"]])))
    print(tag, json.dumps(to_py(out[tag])))
json.dump(to_py(out), open("results/matrix_stats.json", "w"), indent=1)
