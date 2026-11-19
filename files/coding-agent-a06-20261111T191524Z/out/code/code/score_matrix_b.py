"""World B outcome matrix. Usage: python score_matrix_b.py MODEL_DIR OUT_DIR N_POOL CHUNK THREADS [cfg_ids|all] [chunk_ids]"""
import sys, os, time, copy, numpy as np, torch
sys.path.insert(0, "/work/code")
from common import *
from common_b import *
from transformers import AutoTokenizer, AutoModelForCausalLM

def main():
    model_dir, out_dir, n_pool, chunk, threads = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    torch.set_num_threads(threads)
    cfgs = config_list_b()
    cfg_ids = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 and sys.argv[6] != "all" else list(range(len(cfgs)))
    chunk_ids = [int(x) for x in sys.argv[7].split(",")] if len(sys.argv) > 7 else list(range(n_pool // chunk))
    os.makedirs(out_dir, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(model_dir)
    m = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.float32).eval()
    pool = build_pool(AutoTokenizer.from_pretrained('/work/models/Qwen2.5-1.5B-Instruct'), n_pool); _, v = load_data()   # pool defined with the Qwen tokenizer for all models
    _, v = load_data(); dsets = demo_indices(v)
    ids_plain = [tok.encode(c, add_special_tokens=False)[0] for c in LETTERS]
    ids_space = [tok.encode(" " + c, add_special_tokens=False)[0] for c in LETTERS]
    assert len(set(ids_plain)) == 10 and len(set(ids_space)) == 10
    lm_head = m.get_output_embeddings()
    cfgm = m.config; kv_bytes = 2 * cfgm.num_hidden_layers * cfgm.num_key_value_heads * (cfgm.hidden_size // cfgm.num_attention_heads) * 4   # fp32 KV bytes per token
    max_cache_tokens = int(6e9 // kv_bytes)   # cap (batch x (prefix+suffix)) tokens so the expanded KV cache stays < ~6 GB (SmolLM2 has no GQA)
    for (k, c) in [(k, c) for c in chunk_ids for k in cfg_ids]:
        fn = f"{out_dir}/c{k}_k{c}.npz"
        if os.path.exists(fn): continue
        t0 = time.time(); cfg = cfgs[k]
        prefix_text, suf = build_prompt(cfg, v, dsets)
        sub = pool.iloc[c * chunk:(c + 1) * chunk]
        letter_ids = ids_space if letter_style(cfg[0]) else ids_plain
        pre_ids = tok(prefix_text, return_tensors="pt", add_special_tokens=False).input_ids if prefix_text else None
        P = 0 if pre_ids is None else pre_ids.shape[1]
        ids = [tok(suf(r), add_special_tokens=False).input_ids for r in sub.itertuples()]
        with torch.inference_mode():
            pc = m(pre_ids, use_cache=True).past_key_values if P else None
            order = np.argsort([len(x) for x in ids]); out = np.zeros((len(ids), 10), dtype=np.float32); i = 0
            while i < len(order):
                L0 = len(ids[order[i]]); bs = max(1, min(32, 2400 // max(L0, 1)))
                bidx = order[i:i + bs]; Lm = max(len(ids[j]) for j in bidx)
                while len(bidx) > 1 and (len(bidx) * Lm > 2800 or len(bidx) * (Lm + P) > max_cache_tokens): bidx = bidx[:-1]; Lm = max(len(ids[j]) for j in bidx)
                x = torch.full((len(bidx), Lm), tok.pad_token_id, dtype=torch.long)
                for r_, j in enumerate(bidx): x[r_, :len(ids[j])] = torch.tensor(ids[j])
                if P:
                    cache = copy.deepcopy(pc); cache.batch_repeat_interleave(len(bidx))
                    h = m.model(input_ids=x, past_key_values=cache, position_ids=(P + torch.arange(Lm)).unsqueeze(0).expand(len(bidx), -1), use_cache=True).last_hidden_state
                else:
                    h = m.model(input_ids=x, use_cache=False).last_hidden_state
                last = torch.tensor([len(ids[j]) - 1 for j in bidx])
                out[bidx] = lm_head(h[torch.arange(len(bidx)), last])[:, letter_ids].float().numpy(); i += len(bidx)
        np.savez(fn, logits=out.astype(np.float16), qid=sub.question_id.values)
        nopt = np.array([len(o) for o in sub.options]); lg = out.copy(); lg[np.arange(10)[None, :] >= nopt[:, None]] = -1e9
        print(f"cfg {k} {cfg} chunk {c}: acc {(lg.argmax(1) == sub.answer_index.values).mean():.3f} {sum(map(len, ids))/(time.time()-t0):.0f} tok/s prefix {P} {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__": main()
