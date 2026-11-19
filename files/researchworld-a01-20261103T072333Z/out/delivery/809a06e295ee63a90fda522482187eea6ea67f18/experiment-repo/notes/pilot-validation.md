# Timed pilot and independent validation

- HELM pilot: five targets, five rules, five intervention settings (125 records), 32 random permutations where reachable; measured elapsed 0.47 seconds, sum per-record compute times 0.399 seconds. Full 79-target run with 256 permutations projected at tens of seconds (planning estimate, not a measured full runtime).
- Open LLM pilot: ten targets, same 25 settings (250 records), exhaustive random-subset baseline; measured elapsed 0.22 seconds, sum per-record compute times 0.144 seconds. Full 4,575-target run projected at about 100 seconds (planning estimate).
- Independent validation: `tests/test_solvers.py` passed 120 comparisons of analytic/MILP solvers with independently recomputed aggregation over all 2^11 subsets. Cases use tied scores, zero scores, alpha 1 or 0.4, co-first and strict-first, all five rules. Actual local-compute job elapsed 8.898 seconds, CPU spend 9.234 seconds. Tests compare minimum counts, and recompute Borda opponent ranks from the full modified matrix rather than recycling solver constraints.
- Actual pilot output remains `results/pilot.csv`, `results/pilot_open_llm.csv`. These are pilot subsets by lexicographic model order, not representative estimates and not study results.

Jobs: job-3807fdf1f5 (HELM pilot), job-29b5a2e162 (Open LLM pilot), job-977ca32b78 (independent validation). All succeeded. Acquisition initially attempted Python requests but that optional package was absent; switched to Python standard-library urllib without changing data or methods.
