"""Check of the method of paper-repo template.tex Sec. 3 on richer tokenizers (MPE and BPE).

For a random token-level LM that satisfies Assumption 1 by construction (at each step it puts
mass only on next tokens that keep the sequence a valid encoding), checks on random byte
strings over {a,b,c}:
 (i)   Lemma 1 sum over cover encodings (brute force) == Algorithm 1 output;
 (ii)  Proposition 1 recursion (Eq. sampling) == Algorithm 1 rerun on x_1^{n+1};
 (iii) Eq. (sampling) gives a normalised next-byte distribution;
 (iv)  prefix-closedness: every prefix of a valid encoding is valid (used implicitly when
       Algorithm 1 returns exactly cover(x));
 (v)   how often enc(x_1^{n-i}) is not a prefix of enc(x_1^n) (the "share their prefix"
       wording of Sec. 3.4).
Inputs: none (synthetic). Run: python3 method_check.py
"""
import itertools, random, sys, zlib
random.seed(0)
ALPH = "abc"
V = ["a", "b", "c", "ab", "bc", "ca", "abc", "bca", "cab", "aa", "bb", "aab"]
L = max(map(len, V))
MERGES = [("a", "b"), ("b", "c"), ("c", "a"), ("ab", "c"), ("bc", "a"), ("ca", "b"),
          ("a", "a"), ("b", "b"), ("aa", "b")]  # BPE merge list, priority order

def enc_mpe(s):
    out, i = [], 0
    while i < len(s):
        t = max((t for t in V if s.startswith(t, i)), key=len); out.append(t); i += len(t)
    return out

def enc_bpe(s):
    seq = list(s)
    while True:
        best = None
        for j in range(len(seq) - 1):
            pr = (seq[j], seq[j + 1])
            if pr in MERGES and (best is None or MERGES.index(pr) < MERGES.index(best[1])):
                best = (j, pr)
        if best is None: return seq
        j = best[0]; seq[j:j + 2] = [seq[j] + seq[j + 1]]

W = {t: random.random() + 0.1 for t in V}
def run(enc, name):
    valid = lambda seq: enc("".join(seq)) == list(seq)
    cache = {}
    def cond(hist):  # P(. | hist): random weights restricted to valid continuations
        hist = tuple(hist)
        if hist not in cache:
            w = {t: W[t] * (1 + zlib.crc32(repr((hist, t)).encode()) % 7) for t in V if valid(hist + (t,))}
            z = sum(w.values()); cache[hist] = {t: v / z for t, v in w.items()}
        return cache[hist]
    def P(seq):
        p = 1.0
        for k in range(len(seq)):
            p *= cond(seq[:k]).get(seq[k], 0.0)
            if p == 0: break
        return p
    def brute(x):
        tot, st = 0.0, [()]
        while st:
            s = st.pop(); d = "".join(s)
            if len(d) >= len(x):
                if d.startswith(x) and valid(s): tot += P(s)
            elif x.startswith(d): st += [s + (t,) for t in V]
        return tot
    def alg1(x):
        C = {}
        for i in range(1, min(L, len(x)) + 1):
            hist = tuple(enc(x[:len(x) - i]))
            for t in V:
                if len(t) >= i and t[:i] == x[len(x) - i:] and valid(hist + (t,)):
                    C[hist + (t,)] = P(hist) * cond(hist).get(t, 0.0)
        return {k: v for k, v in C.items() if v > 0}
    def step(C, x):
        n, Px = len(x), sum(C.values()); canon = tuple(enc(x)); Pc = C.get(canon, 0.0)
        dist, nxt = {}, {}
        for b in ALPH:
            D = {t: p for t, p in C.items() if len("".join(t)) > n and "".join(t)[n] == b}
            for t, q in cond(canon).items():
                if t[0] == b and Pc * q > 0: D[canon + (t,)] = Pc * q
            dist[b] = sum(D.values()) / Px; nxt[b] = D
        return dist, nxt
    ok, nonprefix, total, worst = True, 0, 0, 0.0
    for _ in range(150):
        x = "".join(random.choice(ALPH) for _ in range(random.randint(1, 7)))
        C = alg1(x)
        ok &= abs(sum(C.values()) - brute(x)) < 1e-12
        for i in range(1, min(L, len(x)) + 1):
            e, f = enc(x[:len(x) - i]), enc(x)
            total += 1; nonprefix += f[:len(e)] != e
        for _ in range(4):
            dist, nxt = step(C, x)
            worst = max(worst, abs(sum(dist.values()) - 1))
            b = random.choice([k for k in ALPH if dist[k] > 0])
            C, x = nxt[b], x + b
            A = alg1(x)
            ok &= set(C) == set(A) and all(abs(C[k] - A[k]) < 1e-12 for k in A)
    ok &= worst < 1e-12
    # (iv) prefix-closedness over all strings up to length 7
    pc = all(valid(tuple(enc(s))[:j]) for n in range(1, 8)
             for s in map("".join, itertools.product(ALPH, repeat=n)) for j in range(len(enc(s))))
    print(f"{name}: (i)-(iii) {'pass' if ok else 'FAIL'} (normalisation err {worst:.1e}); "
          f"(iv) prefix-closed: {pc}; (v) enc(x_1^(n-i)) not a prefix of enc(x_1^n) in "
          f"{nonprefix}/{total} histories")
    return ok and pc
ok = run(enc_mpe, "MPE") & run(enc_bpe, "BPE")
print("ALL CHECKS PASS" if ok else "CHECK FAILED"); sys.exit(0 if ok else 1)
