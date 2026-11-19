"""Numerical check of the breadth lemma for trimmed means (Lemma 1 in the paper).
Claim: for 0<=k<=t, the maximal increase of the trimmed SUM (window = ranks t+1..m-t) obtainable by raising any k tasks
(to any values <= 1) equals  G_k = sum_{l=1..k} ( s_(m-t+l) - s_(t+l) )  (order statistics of the ORIGINAL scores, ascending),
attained by raising the k lowest tasks to the ceiling (needs s_(m-t+l) <= 1 trivially)."""
import itertools
import numpy as np

rng = np.random.default_rng(1)
bad = 0
n = 0
for trial in range(3000):
    m = int(rng.integers(3, 9))
    t = int(rng.integers(0, (m - 1) // 2 + 1))
    s = rng.random(m)
    srt = np.sort(s)
    tsum = lambda x: np.sort(x)[t:m - t].sum()
    for k in range(0, t + 1):
        best = 0.0
        for sub in itertools.combinations(range(m), k):
            x = s.copy()
            x[list(sub)] = 1.0
            best = max(best, tsum(x) - tsum(s))
        G = sum(srt[m - t + l - 1] - srt[t + l - 1] for l in range(1, k + 1))
        n += 1
        if abs(best - G) > 1e-9:
            bad += 1
            print('mismatch', m, t, k, best, G)
print('lemma checks', n, 'mismatches', bad)
