"""Transcribe the experimental log (INSTRUCTIONS.md, [EXPERIMENTAL LOGS] section 2) into
tidy CSVs and recompute every 'Performance Gap' row. Nothing here is measured by us:
all accuracies are the log's numbers; derived columns are marked."""
import csv, math
M = ["test", "remain", "forget", "mia"]
# (table, setting, method, test, remain, forget, mia)
R = []
def add(t, s, m, *v): R.append((t, s, m) + v)
# forget-size ablation, CIFAR-10 linear classifier
add("forget_size_cifar10", "15%", "Retrained", 73, 75, 73, 50);   add("forget_size_cifar10", "15%", "Unlearned(-)", 59, 60, 59, 55.8)
add("forget_size_cifar10", "10%", "Retrained", 72, 74, 72, 50);   add("forget_size_cifar10", "10%", "Unlearned(-)", 70, 71, 68, 51.4)
add("forget_size_cifar10", "5%", "Retrained", 73, 74, 73, 49.4);  add("forget_size_cifar10", "5%", "Unlearned(-)", 73, 74, 73, 49.4)
# perturbation ablation
add("perturbations_cifar10", "ref", "Retrained", 72, 74, 72, 50)
for k, v in [("250", (57, 58, 57, 56.2)), ("500", (70, 71, 68, 51.4)), ("1000", (72, 74, 71, 49))]:
    add("perturbations_cifar10", k, "Unlearned(-)", *v)
# lambda ablation
add("lambda_cifar10", "ref", "Retrained", 72, 74, 72, 50)
for k, v in [("0", (70, 71, 68, 51.4)), ("0.0005", (71, 72, 71, 49.8)), ("0.001", (72, 73, 72, 50.9))]:
    add("lambda_cifar10", k, "Unlearned(-)", *v)
# mixed linear network CIFAR-100
for f, rt, up, um in [("20%", (62.2, 65.7, 62.6, 50), (60.1, 63.4, 59.3, 50.4), (60, 70, 63.2, 50.8)),
                      ("15%", (63.1, 68.9, 63.3, 50.2), (61.9, 67.9, 62.2, 50.7), (61.4, 70.1, 62.2, 51.7)),
                      ("10%", (63.7, 72, 63.9, 50), (63.3, 72.5, 64.9, 51), (62.8, 70.1, 61.2, 52.3))]:
    add("mixed_linear_cifar100", f, "Retrained", *rt); add("mixed_linear_cifar100", f, "Unlearned(+)", *up); add("mixed_linear_cifar100", f, "Unlearned(-)", *um)
# source-free baselines, CIFAR-10, 10% forget
for m, v in [("Retrained", (72, 74, 72, 50)), ("NegGrad", (51.9, 53.2, 51.2, 48)), ("Random Labels", (20.6, 21.6, 21.4, 47)),
             ("JiT", (52.1, 53.1, 51.1, 49.1)), ("Adversarial", (51.5, 52.7, 51.0, 50.0)), ("Unlearned(-)", (70, 71, 68, 51.4))]:
    add("baselines_cifar10", "10%", m, *v)

with open("results/log_numbers.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["table", "setting", "method"] + M); w.writerows(R)

# Log's reported gap rows (test, remain, forget, mia)
LOG_GAP = {("forget_size_cifar10", "15%"): (14, 15, 14, 5.8), ("forget_size_cifar10", "10%"): (2, 3, 4, 1.4), ("forget_size_cifar10", "5%"): (0, 0, 0, 0),
           ("perturbations_cifar10", "250"): (15, 16, 15, 6.2), ("perturbations_cifar10", "500"): (2, 3, 4, 1.4), ("perturbations_cifar10", "1000"): (0, 0, 1, 1),
           ("lambda_cifar10", "0"): (2, 3, 4, 1.4), ("lambda_cifar10", "0.0005"): (1, 2, 1, 0.2), ("lambda_cifar10", "0.001"): (0, 1, 0, 0.9),
           ("mixed_linear_cifar100", "20%"): (0.1, 6.6, 3.9, 0.4), ("mixed_linear_cifar100", "15%"): (0.5, 2.2, 0.0, 1.0), ("mixed_linear_cifar100", "10%"): (0.5, 2.4, 3.7, 1.3)}
idx = {(t, s, m): v for t, s, m, *v in R}
rows = []
for (t, s), lg in LOG_GAP.items():
    um = idx[(t, s, "Unlearned(-)")]
    rt = idx.get((t, s, "Retrained"), idx.get((t, "ref", "Retrained")))
    up = idx.get((t, s, "Unlearned(+)"))
    vs_rt = [round(abs(a - b), 1) for a, b in zip(um, rt)]
    vs_up = [round(abs(a - b), 1) for a, b in zip(um, up)] if up else [""] * 4
    ref = "Retrained" if all(abs(a - b) < 0.051 for a, b in zip(vs_rt, lg)) else ("Unlearned(+)" if up and all(abs(a - b) < 0.051 for a, b in zip(vs_up, lg)) else "MISMATCH")
    rows.append([t, s] + list(lg) + [ref] + vs_rt + vs_up)
with open("results/gap_audit.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["table", "setting", "log_gap_test", "log_gap_remain", "log_gap_forget", "log_gap_mia", "log_gap_is_relative_to",
                "abs_vs_retrained_test", "abs_vs_retrained_remain", "abs_vs_retrained_forget", "abs_vs_retrained_mia",
                "abs_vs_unlearned+_test", "abs_vs_unlearned+_remain", "abs_vs_unlearned+_forget", "abs_vs_unlearned+_mia"])
    w.writerows(rows)
for r in rows: print(r[:2], "gap rel. to:", r[6])

# Baselines: distance to Retrained per metric (derived)
rt = idx[("baselines_cifar10", "10%", "Retrained")]
with open("results/baseline_gaps_cifar10.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["method", "abs_gap_test", "abs_gap_remain", "abs_gap_forget", "abs_mia_dev_from_50"])
    for t, s, m, *v in R:
        if t == "baselines_cifar10" and m != "Retrained":
            w.writerow([m] + [round(abs(a - b), 1) for a, b in zip(v[:3], rt[:3])] + [round(abs(v[3] - 50), 1)])
# Binomial standard errors implied by finite eval-set sizes (derived, ASSUMES CIFAR-10 50k train / 10k test; the log does not state split sizes)
with open("results/binomial_se_assumed.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["quantity", "n_assumed", "p", "se_points"])
    for name, n, p in [("test acc", 10000, .72), ("forget acc 5%", 2500, .73), ("forget acc 10%", 5000, .70), ("forget acc 15%", 7500, .65)]:
        w.writerow([name, n, p, round(100 * math.sqrt(p * (1 - p) / n), 2)])
