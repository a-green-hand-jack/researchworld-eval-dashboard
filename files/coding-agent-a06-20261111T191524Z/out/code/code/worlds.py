"""Outcome-matrix 'worlds': real (cached LLM outcomes) and synthetic (IRT-style)."""
import numpy as np, glob, os, sys
sys.path.insert(0, "/work/code")

def synth_world(K=40, N=20000, mu=-0.4, sd_q=1.2, tau=0.15, sd_int=0.8, seed=0, grid=True):
    """Y[k,i] ~ Bernoulli(sigmoid(mu + d_i + c_k + sd_int*e_ki)); d_i question difficulty, c_k config effect (spread tau),
    e_ki config x question interaction (controls how correlated configs are)."""
    rng = np.random.default_rng(seed)
    d = rng.normal(0, sd_q, N); c = rng.normal(0, tau, K); e = rng.normal(0, 1, (K, N))
    p = 1 / (1 + np.exp(-(mu + d[None] + c[:, None] + sd_int * e)))
    return (rng.random((K, N)) < p).astype(np.uint8)

def load_real(res_dir, n_pool, chunk, model_dir, kind='A'):
    """Assemble Y[K,N] from chunk files; only chunks completed for all configs are used (chunk-major run order)."""
    from common import build_pool
    from transformers import AutoTokenizer
    if kind == 'A':
        from common import config_list; K = len(config_list())
    else:
        from common_b import config_list_b; K = len(config_list_b())
    tok = AutoTokenizer.from_pretrained('/work/models/Qwen2.5-1.5B-Instruct')   # the pool is always defined with the Qwen tokenizer
    pool = build_pool(tok, n_pool); cols = []
    nopt = np.array([len(o) for o in pool.options]); ans = pool.answer_index.values
    c = 0
    while c < n_pool // chunk:
        fs = [f"{res_dir}/c{k}_k{c}.npz" for k in range(K)]
        if not all(os.path.exists(f) for f in fs): break
        Yc = []
        for k in range(K):
            z = np.load(fs[k]); lg = z['logits'].astype(np.float32)
            sl = slice(c * chunk, (c + 1) * chunk)
            assert (z['qid'] == pool.question_id.values[sl]).all()
            lg[np.arange(lg.shape[1])[None, :] >= nopt[sl][:, None]] = -1e9
            Yc.append((lg.argmax(1) == ans[sl]).astype(np.uint8))
        cols.append(np.stack(Yc)); c += 1
    return np.concatenate(cols, 1), pool.iloc[:c * chunk]
