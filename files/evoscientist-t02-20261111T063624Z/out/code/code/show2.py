import json, os, sys
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(H, '..', 'results', 'summary.json')))
for k in sys.argv[1:]:
    v = S[k]
    if isinstance(v, dict):
        for a, b in v.items():
            print(k, a, b)
    else:
        print(k, v)
