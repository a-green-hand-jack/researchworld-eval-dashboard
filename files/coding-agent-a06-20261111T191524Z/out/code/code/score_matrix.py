"""Compute the (config x question) outcome matrix for one model, with prefix-KV caching.
Usage: python score_matrix.py MODEL_DIR OUT_DIR N_POOL CHUNK THREADS [cfg_ids comma] [chunk_ids comma]
Writes OUT_DIR/c{cfg}_k{chunk}.npz with letter-logits (float16, shape [chunk,10]) for each question.
Resumable: skips existing files."""
import sys, os, time, copy, numpy as np, torch
sys.path.insert(0, "/work/code")
from common import *
from transformers import AutoTokenizer, AutoModelForCausalLM

def main():
    model_dir, out_dir, n_pool, chunk, threads = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    torch.set_num_threads(threads)
    cfgs = config_list()
    cfg_ids = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 and sys.argv[6] != "all" else list(range(len(cfgs)))
    n_chunks = n_pool // chunk
    chunk_ids = [int(x) for x in sys.argv[7].split(",")] if len(sys.argv) > 7 else list(range(n_chunks))
    os.makedirs(out_dir, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(model_dir)
    m = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float32).eval()
    pool = build_pool(tok, n_pool)
    _, v = load_data(); dsets = demo_sets(v)
    letter_ids = [tok.encode(c, add_special_tokens=False)[0] for c in LETTERS]
    lm_head = m.get_output_embeddings()
    work = [(k, c) for c in chunk_ids for k in cfg_ids]  # chunk-major so partial results cover all configs
    for (k, c) in work:
        fn = f"{out_dir}/c{k}_k{c}.npz"
        if os.path.exists(fn): continue
        t0 = time.time()
        ins, ds = cfgs[k]
        msgs = []
        if INSTRUCTIONS[ins] is not None: msgs.append({"role": "system", "content": INSTRUCTIONS[ins]})
        for di in dsets[ds]:
            r = v.iloc[di]
            msgs += [{"role": "user", "content": user_text(r.question, r.options)},
                     {"role": "assistant", "content": f"The answer is ({r.answer})"}]
        sub = pool.iloc[c * chunk:(c + 1) * chunk]
        def full(r):
            return tok.apply_chat_template(msgs + [{"role": "user", "content": user_text(r.question, r.options)}],
                                           tokenize=False, add_generation_prompt=True) + "The answer is ("
        # prefix = everything before the final user turn
        probe = full(sub.iloc[0])
        marker = "<|im_start|>user\n" + user_text(sub.iloc[0].question, sub.iloc[0].options)
        pos = probe.rindex(marker)
        prefix_text = probe[:pos]
        suffixes = []
        for r in sub.itertuples():
            f = full(r); assert f.startswith(prefix_text); suffixes.append(f[len(prefix_text):])
        pre_ids = tok(prefix_text, return_tensors="pt", add_special_tokens=False).input_ids
        P = pre_ids.shape[1]
        with torch.inference_mode():
            pc = m(pre_ids, use_cache=True).past_key_values
            ids = [tok(s, add_special_tokens=False).input_ids for s in suffixes]
            order = np.argsort([len(x) for x in ids])
            out = np.zeros((len(ids), 10), dtype=np.float32)
            i = 0
            while i < len(order):
                # token budget per batch
                L0 = len(ids[order[i]]); bs = max(1, min(32, 2400 // max(L0, 1)))
                bidx = order[i:i + bs]; Lm = max(len(ids[j]) for j in bidx)
                # ensure budget with the max length in batch
                while len(bidx) > 1 and len(bidx) * Lm > 2800: bidx = bidx[:-1]; Lm = max(len(ids[j]) for j in bidx)
                x = torch.full((len(bidx), Lm), tok.pad_token_id, dtype=torch.long)
                for r_, j in enumerate(bidx): x[r_, :len(ids[j])] = torch.tensor(ids[j])
                cache = copy.deepcopy(pc); cache.batch_repeat_interleave(len(bidx))
                pos_ids = (P + torch.arange(Lm)).unsqueeze(0).expand(len(bidx), -1)
                h = m.model(input_ids=x, past_key_values=cache, position_ids=pos_ids, use_cache=True).last_hidden_state
                last = torch.tensor([len(ids[j]) - 1 for j in bidx])
                hl = h[torch.arange(len(bidx)), last]
                lg = lm_head(hl)[:, letter_ids]
                out[bidx] = lg.float().numpy()
                i += len(bidx)
        np.savez(fn, logits=out.astype(np.float16), qid=sub.question_id.values)
        ntok = sum(map(len, ids)); dt = time.time() - t0
        nopt = np.array([len(o) for o in sub.options]); lg = out.copy()
        for r_ in range(len(lg)): lg[r_, nopt[r_]:] = -1e9
        acc = (lg.argmax(1) == sub.answer_index.values).mean()
        print(f"cfg {k} chunk {c}: acc {acc:.3f}  {ntok/dt:.0f} tok/s  prefix {P}  {dt:.0f}s", flush=True)

if __name__ == "__main__": main()
