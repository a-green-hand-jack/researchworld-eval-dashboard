from grok import *
if __name__ == "__main__":
    cfgs = [base(d=d, frac=f, seed=0, max_steps=20000) for d in (8, 16, 32, 64, 128) for f in (0.3, 0.5)]
    sweep(cfgs, "results/pilot.jsonl", 10)
