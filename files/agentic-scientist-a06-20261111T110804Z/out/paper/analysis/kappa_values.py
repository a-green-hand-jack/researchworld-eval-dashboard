"""Width-calibration factor kappa of the frozen reporter at each evaluation case's (N, K, data type).
Calls the reporter's own _kappa() from its source file.
# @evidence[[source_evidence/reporter_eb_irt/reporter.py#_kappa]]
# @evidence[[source_evidence/evaluator/evaluate_final.py#CASES]]
"""
import importlib.util, json
spec = importlib.util.spec_from_file_location("rep", "results/ideas/01_empirical_bayes_latent_difficulty_posterior_interval/program_1/src/program.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ef = importlib.util.spec_from_file_location("ef", "task/evaluate_final.py"); e = importlib.util.module_from_spec(ef); ef.loader.exec_module(e)
out = {c: {"N": p["N"], "K": p["K"], "world": p["world"], "searcher": p["searcher"], "R": p["R"],
           "kappa": m._kappa(p["N"], p["K"], p["world"] in ("real", "real_null"))} for c, p in e.CASES.items()}
json.dump(out, open("analysis/kappa_values.json", "w"), indent=1)
print({c: round(v["kappa"], 3) for c, v in out.items()})
