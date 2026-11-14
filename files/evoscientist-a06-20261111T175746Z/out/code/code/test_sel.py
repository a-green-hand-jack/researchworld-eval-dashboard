import sys, time, json; sys.path.insert(0, "code")
import numpy as np, sel
Y = sel.synth_matrix(32, 20000, base=0.25, tau=0.0, rho_noise=0.3, seed=1)
print("true acc range", Y.mean(1).min(), Y.mean(1).max(), "corr between configs", np.corrcoef(Y[:8, :]).mean())
for opt in ["exh", "sh"]:
    t = time.time(); r = sel.run_many(Y, 32, 400, opt, 200, 0, B=100)
    print(opt, "time", time.time() - t)
    print(json.dumps(sel.summarize(r), indent=0)[:1800])
