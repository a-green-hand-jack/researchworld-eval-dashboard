"""Apply the fitted size-holdout predictor to four graph statistics."""
import argparse
import json
import math
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--n', type=int, required=True)
p.add_argument('--m', type=int, required=True)
p.add_argument('--max-degree', type=int, required=True)
p.add_argument('--diameter', type=int, required=True)
a = p.parse_args()
if not (2 <= a.n <= 30 and a.n-1 <= a.m <= a.n*(a.n-1)//2
        and 1 <= a.max_degree <= a.n-1 and 1 <= a.diameter <= a.n-1):
    p.error('statistics must describe a simple connected graph with 2 <= n <= 30')
fit = json.loads((Path(__file__).resolve().parent/'results/summary.json').read_text())['fitted_log_formula']
x = [a.n, 2*a.m/a.n, a.max_degree, a.diameter]
prediction = math.exp(fit['intercept']+sum(b*math.log(v) for b,v in zip(fit['coefficients'],x)))
print(f'{prediction:.6f} expected steps (uniform starting vertex; empirically evaluated only for n >= 6)')
