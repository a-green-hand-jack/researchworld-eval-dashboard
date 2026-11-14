# experiment-repo — minimum targeted investment to top a multi-task leaderboard

Analysis code and results for: *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to make it
rank first on a multi-task leaderboard, and how does it depend on the aggregation rule?* Delivered into `paper-repo` under `analysis/`.
Semantics of every result file, claim verdicts and the table/figure → file map: **`docs/HANDOFF.md`**. Closed forms and what is *not* true: `docs/PROPOSITIONS.md`.

## Model in one paragraph
Target model i may raise its score on task t to any y_t ∈ [x_t, cap_t]; every rival is fixed. i is *first* iff it is strictly above every rival under the rule
by a margin ε = 1e-3 (ordinal rules: strictly better outcome, on a discrete level model with tie = half credit). Three investment measures, **each minimised
separately**: K (tasks touched), L1 (total points), Linf (largest single-task raise). Caps: `ceil` (100), `front0`/`front2` (best rival's score on the task +0/+2,
feasible by construction), `gain5/10/20` (at most that many points per task), `emp95/emp99` (empirical 95th/99th percentile of observed fine-tune gains over the base model on OLLB).
Infeasible = `inf`; unresolved solver status = NaN (none in the delivered files). Rules: mean, geometric/harmonic/power means (offset 1), median, min,
trimmed mean (drop best and worst task, n=6), weighted mean (Dirichlet weights), Borda, plurality, Condorcet winner.

## Layout
- `src/mti/scorerules.py` — exact solvers for score rules (closed form / water-filling / enumeration / MILP for trimmed L1); `src/mti/ordinal.py` — exact MILP (HiGHS via scipy) with lazy rival constraints for Borda, plurality, Condorcet, and exact ordinal Linf; `src/mti/data.py` — loaders, standard errors.
- `src/run_core.py` (main grids), `run_robust.py` (noise / task bootstrap / n-sweep / shuffle control), `run_weights.py`, `run_replay.py` (fixed-strategy first-place probability), `condorcet_exist.py`.
- Added 2026-11-08 (issues #7–#11): `gstar.py` (smallest uniform gain cap), `run_replay2.py` + `replay2_summary.py` (36-target replay, SE × 1/1.5/2, shrunk-truth model, redrawn targets), `cluster_boot.py` (base-model cluster bootstrap), `seed_stability.py` and `noise_seed_check.py` (seed checks), `normalised_costs.py` and `nozero_diag.py` (rule-normalised and rank-matched costs, OLLB-zero diagnostic). Meaning of every output: `docs/HANDOFF.md` (last section).
- `src/assemble.py`, `summarize.py`, `claims.py`, `robust_summary.py`, `make_manifest.py` — assembly, summaries, claim tables, audit (`results/MANIFEST.csv`, `results/infeasibility_summary.csv`, `results/input_hashes.json`).
- `tests/` — every solver against brute force on small random instances (`python3 -m pytest tests`, ~1 min).
- `run_all.sh [fast|full]` — the entrypoint (every command that produced `results/`). `logs/` — run logs. `data/processed/` — derived tables (rebuilt byte-identically from the raw downloads; hashes in `data/processed/manifest.json`).

## Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1 (HiGHS MILP), pandas 3.0.6, pyarrow 26.0.0, pytest 9.2.0. 2 CPUs, 4 GB; the longest jobs (OLLB score rules over 7 caps ≈ 5.6 h in one job, parallelisable per cap; OLLB ordinal sample and trimmed mean ≲ 40 min per cap, see `logs/`) need < 700 MB each; they are independent and were run in parallel.

## Data (public; nothing else is used)
- Open LLM Leaderboard `open-llm-leaderboard/contents`, Hugging Face commit `9c09a7cae43334062a82cb164f2ef255013dafa2`, parquet sha256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5`; 4576 rows, submissions 2024-06-08 … 2025-03-13 (leaderboard frozen); 79 duplicate `fullname` rows dropped (default keep the best variant; the variant that keeps the worst is `ollb_dedupe_worst_scores.csv`); 4497 models; the 1 model flagged by the leaderboard is removed (`Flagged`) ⇒ 4496 models in the grids, of which the mean leader is not a target ⇒ 4495 targets.
- HELM MMLU v1.13.0 (public release summaries; manifest sha256 `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b`): 79 models × 57 subjects, EM accuracy; 78 non-leader targets.
- Evaluation-noise model: per-cell binomial SE with item counts from one pinned lm-eval results file (`src/ollb_items.py`, `data/processed/ollb_noise.json`) and HELM `# eval` counts.
- **Licences.** Neither Hugging Face dataset card declares a licence (the `contents` card has no licence field; it carries each model's own `Hub License` column). Judgement: only benchmark *scores* (facts about public models) are used, for non-commercial academic analysis, with attribution; no model weights, text or prompts are used or redistributed. `data/processed/` holds derived score tables so the analysis is checkable, but the raw sources should be re-fetched from their origin (`src/fetch_*.py`) and are the authority; anyone redistributing the derived tables should check the sources' terms first. I did not verify a separate licence statement for the HELM published results.

## Seeds (and one deviation)
Study seed 20261108 (plan). It is used for: bootstrap over targets (summaries), `run_weights.py`, `run_replay.py`, `condorcet_exist.py`, and the n-sweep runs. **Deviation (stated, and now checked):** `run_robust.py noise|taskboot`, the powmean/offset/eps runs' sampling and the rank-stratified OLLB target sample of `run_core.py … sample` ran with the script default `--seed 0` (the sample is the same for every cap and rule; the fixed-seed deterministic grids do not depend on it). Rerun with `--seed 20261108` changes which noise draws / sampled targets are used, not the method.

Sample seeds (#10): `run_core.py … sample` has `--sampler grid` (default; deterministic, the delivered sample, `--seed` has no effect) and `--sampler random --seed S` (tail ranks drawn log-uniformly; used for seeds 20261108, 1, 2 in `results/seeds/`). `run_replay2.py` has the same two samplers for its 36 targets. The noise/task-bootstrap score-rule runs were repeated with seed 20261108 at R = 200 (`results/seeds/*_R200.csv`). Exact R and target counts of every replicate run: `docs/HANDOFF.md`, #8.
