"""Fourier-sparsity and restricted/excluded-loss tracking for the addition task (rival (a), circuit efficiency).

python3 fourier.py OUTDIR --model mlp|tfm --widths 16,64,256 --seeds 0,1,2 [--train_frac 0.5 --p 59]

Re-runs the E1 configuration (same seed, so the same init and split and the same training trajectory; grok.run is deterministic
and the read-only hook does not touch the RNG) and, at snapshot steps, computes from the model on the full p x p input grid:
  s_top5  fraction of the token-embedding power (DFT over the token index, frequencies 1..(p-1)/2 pooled with their mirror) in the 5 strongest
          frequencies (chance for a random embedding ~ 5/((p-1)/2));
  restricted / excluded loss  the logits L[a,b,c] are transformed by a 2-D DFT over (a, b); 'restricted' keeps only the components whose both
          frequencies lie in {0} + (+-K), K = the 5 strongest embedding frequencies at the LAST snapshot (so K is chosen post hoc, from the
          trained model, and applied to all earlier snapshots), 'excluded' keeps the rest; cross-entropy of each against the true labels (a+b) mod p over all
          p^2 inputs (train and validation together). The full-logit loss on all inputs is also stored.
Per-run JSON: config, t_fit/t_gen (from the run's own log), key frequencies and one row per snapshot.
"""
import argparse, json, os, sys
import numpy as np, torch
import torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grok
from sweep import run_id


def emb_power(E, p):
    """E: (p+1, d) embedding; returns power per frequency k = 1..(p-1)/2 (k and p-k pooled)."""
    Fm = np.fft.fft(E[:p], axis=0)                       # over token index
    P = (np.abs(Fm) ** 2).sum(1)
    return np.array([P[k] + P[p - k] for k in range(1, (p - 1) // 2 + 1)])


def pr_entropy(Pw):
    """Selection-free sparsity of a non-negative power vector: participation ratio 1/sum(q^2) (effective number of components) and
    spectral entropy exp(H(q)) (the same unit), q = P/sum(P). No frequency is selected, no later snapshot is used."""
    q = np.asarray(Pw, float).ravel(); q = q / q.sum()
    return float(1.0 / (q ** 2).sum()), float(np.exp(-(q[q > 0] * np.log(q[q > 0])).sum()))


def logit_power(L, p):
    """Power of the 2-D DFT over (a, b) of the logits, summed over the output index c, with the a- or b-marginal components
    (frequency 0 in either argument, which carry no a-b interaction) removed; (p-1)^2 components."""
    Fh = np.fft.fft2(L, axes=(0, 1))
    return (np.abs(Fh[1:, 1:, :]) ** 2).sum(2)


def grid_logits(m, p):
    a, b = np.meshgrid(np.arange(p), np.arange(p), indexing="ij")
    X = torch.tensor(np.stack([a.ravel(), b.ravel(), np.full(p * p, p)], 1), dtype=torch.long)
    with torch.no_grad():
        return m(X).numpy().reshape(p, p, p)


def losses(L, K, p):
    y = (np.arange(p)[:, None] + np.arange(p)[None, :]) % p
    Fh = np.fft.fft2(L, axes=(0, 1))
    keep = np.zeros(p, bool); keep[0] = True
    for k in K:
        keep[k] = keep[p - k] = True
    mask = keep[:, None] & keep[None, :]
    def ce(Lx):
        Lx = torch.tensor(Lx, dtype=torch.float32).reshape(-1, p)
        return F.cross_entropy(Lx, torch.tensor(y.ravel())).item()
    restr = np.real(np.fft.ifft2(Fh * mask[:, :, None], axes=(0, 1)))
    excl = np.real(np.fft.ifft2(Fh * (~mask)[:, :, None], axes=(0, 1)))
    return ce(L), ce(restr), ce(excl)


def snapshot_step(step):
    return step <= 1000 or step % 150 == 0


def track(cfg, topk=5):
    p = cfg["p"]; snaps = []
    def hook(step, m):
        if snapshot_step(step):
            snaps.append((step, m.emb.weight.detach().numpy().copy(), grid_logits(m, p)))
    r = grok.run(cfg, hook=hook)
    Pend = emb_power(snaps[-1][1], p); K = (np.argsort(-Pend)[:topk] + 1).tolist()
    rows = []
    for step, E, L in snaps:
        P = emb_power(E, p); top = np.sort(P)[::-1][:topk].sum() / P.sum()
        full, restr, excl = losses(L, K, p)
        pre, ene = pr_entropy(P); plg, elg = pr_entropy(logit_power(L, p))
        rows.append(dict(step=step, emb_pr=pre, emb_expH=ene, logit_pr=plg, logit_expH=elg, s_top5=float(top), s_key=float(P[np.array(K) - 1].sum() / P.sum()), loss_all=full, loss_restricted=restr, loss_excluded=excl))
    return dict(config=cfg, summary=r["summary"], key_freqs=K, rows=rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out")
    ap.add_argument("--model", default="mlp"); ap.add_argument("--widths", default="16,64,256"); ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--train_frac", type=float, default=0.5); ap.add_argument("--p", type=int, default=59)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for d in map(int, a.widths.split(",")):
        for s in map(int, a.seeds.split(",")):
            cfg = {**grok.DEFAULT, "model": a.model, "p": a.p, "width": d, "train_frac": a.train_frac, "seed": s, "max_steps": 25000, "eval_every": 50}
            path = os.path.join(a.out, run_id(cfg) + ".json")
            if os.path.exists(path):
                continue
            res = track(cfg); json.dump(res, open(path + ".tmp", "w")); os.replace(path + ".tmp", path)
            sm = res["summary"]; print(f"HUTIAN_PROGRESS {os.path.basename(path)} fit99={sm['t_fit99']} gen99={sm['t_gen99']} keyfreq={res['key_freqs']}", flush=True)
    print("HUTIAN_WAKE: fourier done", a.model, a.widths, flush=True)
