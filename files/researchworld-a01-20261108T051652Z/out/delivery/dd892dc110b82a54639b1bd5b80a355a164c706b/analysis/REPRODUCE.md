# Reproduction notes

Everything in `analysis/` (this repository as delivered into `paper-repo`) regenerates from the public score tables with `./reproduce.sh TARGET`
(run from the directory that holds `reproduce.sh`). All numbers in the paper must come from `results/` (CSV) and `results/tables/` produced by the
scripts below; figures and tables are rendered by `figtab-repo` from those files and compute nothing new except display summaries stated in their captions.

## 1. Environment
| item | version |
|---|---|
| OS / hardware used | Linux 7.0, 2 CPUs and 4 GB per container, no GPU (shared host) |
| Python | 3.11.2 |
| numpy / scipy / pandas / pyarrow / pytest | 2.4.6 / 1.17.1 / 3.0.6 / 26.0.0 / 9.2.0 |
| MILP solver | HiGHS as bundled with scipy 1.17.1 (`scipy.optimize.milp`); per-solve time limit 120 s (Copeland 300 s) |

No other dependency. `pip install numpy==2.4.6 scipy==1.17.1 pandas==3.0.6 pyarrow==26.0.0 pytest==9.2.0` reproduces the environment.
Matplotlib/LaTeX are only used by `figtab-repo` / `paper-repo`.

## 2. Data (both public, no account needed; snapshots pinned by commit and hash)
| dataset | source | version pin | SHA-256 |
|---|---|---|---|
| Open LLM Leaderboard `contents` (score table, 4576 rows, 6 tasks: IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO, each normalised and raw) | `huggingface.co/datasets/open-llm-leaderboard/contents`, file `data/train-00000-of-00001.parquet` | commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (2025-03-20) | `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` |
| Open LLM Leaderboard `results` (only used to read the number of items per task, i.e. the noise floor of the evaluation-noise robustness check and the normalisation floors) | `huggingface.co/datasets/open-llm-leaderboard/results` | commit `aa81ecc38fdc5708254b833923368970efdf5ef5` (2025-03-15) | the hash of the byte stream read is stored in `data/processed/ollb_noise.json` (`source_sha256`) |
| HELM MMLU, 57 subjects × 79 models | `storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (summary + `groups/json/`), release date 2025-01-10; the assignment allowed v1.13.0, no other version was used | release v1.13.0 | per-file hashes in `data/raw/helm/MANIFEST.sha256.json` (created by `fetch_helm.py`), hash of that manifest `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` |

Processed matrices (committed, `data/processed/`): `ollb6.csv` `3bf05871…a999`, `helm_mmlu57.csv` = `helm_mmlu_all.csv` `fae6683b…73c6`, `helm_mmlu_neval.csv` `cf6541fb…156a`,
`ollb_noise.json` `4e0b5eb0…`, `manifest.json` `8c2ecb17…` (full hashes: `sha256sum data/processed/*`; `ollb_noise.json` is rewritten by `ollb_items.py` with the same content).
`./reproduce.sh data` re-downloads and rebuilds them; the rebuilt `ollb6.csv` / `helm_*.csv` were byte-identical to the committed ones when checked.
Cleaning (all in `src/build_data.py`): OLLB — 79 duplicate `fullname` rows dropped (4576 → 4497), `Flagged` models excluded (→ 4496 targets/rivals); `Merged` models are kept in the main run
and removed in the `ollb_nomerge` variant (3789 models); HELM — only models with all 57 subjects (all 79). Number of evaluation items per task are read from `results` for the noise check.

**Licence judgement.** Neither score table carries a declared licence (HELM: the code repository is Apache-2.0, the bucket/site state no licence for the scores; OLLB `contents`: no licence field in the card,
a per-model `Hub License` column; `results`: no card). The scores are published evaluation facts, we redistribute only derived numbers (cost tables) and small processed matrices of scores (`data/processed/`, 2 MB)
that are needed to run the code; model names are public identifiers. Raw downloads (`data/raw`) are not committed. Per-model licences of the evaluated models are not relevant to our use (we analyse scores, not weights).
If a reader needs formal clearance they must ask the data owners (Stanford CRFM; Hugging Face / the leaderboard maintainers).

## 3. Seeds and determinism
Default seed 0 everywhere (`numpy.random.default_rng(0)`): rank-stratified target sample (`run_core.py --seed`), evaluation-noise / task-bootstrap / task-subset draws (`run_robust.py --seed`), Dirichlet weights (`run_weighted.py --seed`),
bootstrap confidence intervals in `summarize*.py` (1000 resamples over targets, seed 0). MILPs and closed forms are deterministic; results are tolerance-stable (tested to 1e-5/1e-6 in the consistency checks).
Re-running a target overwrites its result file.

## 4. Commands, order, expected wall-clock
Targets are independent except where an arrow says otherwise. Times: wall-clock of one 2-CPU container measured on this shared host (several jobs ran concurrently); a few are only lower bounds
(job observed running that long, finished before the next check). The full set of targets takes several CPU-hours (the sum of the table below at 2 CPUs per job is well above 4 CPU-hours), i.e. **more than the 4 CPU-hours estimated in `resources.md`**, which did not anticipate exact MILPs on 4496 models, the Copeland MILP, the robustness draws and the cap/rule/variant replicates; run sequentially on one 2-CPU container the targets add up to roughly 3–5 hours wall-clock (sum of the rough per-step times above; not measured as a single run); run in parallel the longest chain (`variants` → `uniform_var` → `summaries`) is about 1–1.5 hours.

| step | command | content | wall-clock |
|---|---|---|---|
| 0 | `./reproduce.sh data` | download, hash check, build `data/processed` | network-bound, not timed |
| 1 | `./reproduce.sh test` | solvers vs brute force, Copeland, Linf vs brute-force min-max (9 tests) | ~45 s |
| 2 | `./reproduce.sh theory` | closed-form propositions vs live solvers (`theory_checks.csv`), tidy prediction table (`theory_pred.csv`) | not timed (minutes) |
| 3 | `core_helm`, `core_helm_emp` | HELM, 8 rules × 6 caps (+ hemp95/99) × 79 targets → `helm_main.csv`, `helm_emp.csv` | 555 s, < 8 min |
| 4 | `core_ollb_closed`, `core_ollb_trim` | OLLB score rules on all 4496 targets (179 840 rows); trimmed mean MILP on the 57-target sample | ≈ 11 min (log), ≈ 1 min |
| 5 | `core_ollb_ord_a/b/c` | OLLB Borda/Condorcet/plurality, 57-target sample, caps (ceil, front0, front2 / gain5,10,20 / emp95,99) | 18–25 min, 8–10 min, ≈ 8 min (lower bounds: observed still running at the previous check) |
| 6 | `variants` | raw scores, no-merge, top-500 variants | > 40 min |
| 7 | `eps01` | tie margin 0.1 | ≈ 10–15 min |
| 8 | `robust_helm_noise`, `robust_ollb_noise`, `robust_helm_taskboot`, `robust_helm_tasksub` | evaluation noise (R=100), task bootstrap (R=100), task-subset size (R=50), gain10 cap | not timed (minutes each) |
| 9 | `loto_0` … `loto_5` | leave-one-task-out on OLLB | 80–130 s each |
| 10 | `copeland_helm` | exact Copeland optimum on HELM (7 caps × 79 targets; `proven_*` flags) | ≈ 15–40 min |
| 11 | `l2`, `weighted` | convex-cost plans; weighted mean (200 Dirichlet draws) | not timed (minutes) |
| 12 | after 3–6: `uniform_helm`, `uniform_ollb_closed`, `uniform_ollb_ord`, `uniform_var` | uniform-gain benchmark `u*`, `u_L1`, `u_K` | 95 s, not timed, 308 s, not timed |
| 13 | after 3–12: `./reproduce.sh summaries` | all `results/tables/*.csv` and `results/consistency_checks.csv` | ≈ 6–10 min |

`results/consistency_checks.csv` must show 0 violations in every row (`src/check_consistency.py` exits 1 otherwise).

Notes on the history of the results (disclosure):
* The rank-rule `Linf` and `u_star` columns were first computed with a convention that gave a tie at the rival's score no credit; this made `Linf` infinite on some `front0` plurality rows although `L1` was finite.
  It was detected by the consistency check, fixed in `mti/ordinal.py` (`eps_first` snaps the raise to the solvers' levels), covered by `tests/test_ordinal.py::test_linf_ordinal_vs_bruteforce_minmax`, and **every file containing rank-rule rows was regenerated** (steps 3, 5, 6, 7, 9, 12). Robustness files (`robust_*`) use only `L1`, `K` and were not affected; they were produced before the `unproven` flag was added, but the flag is zero in all other files, so no time-limit hits occurred (a hit is recorded as `unproven`, never as infeasible).
* A mid-run edit of `reproduce.sh` once made a few background jobs exit 2 spuriously; they were rerun. The script is now wrapped in `main(){…}` so that it is safe to edit while jobs run.

## 5. Script → result file → claim
| script | result files | used for |
|---|---|---|
| `run_core.py` | `helm_main`, `helm_emp`, `ollb_closed`, `ollb_trim`, `ollb_ord_*`, `var_*`, `eps01_*` | C3 (rule comparison), C4 (feasibility vs rank and cap), C5 (variants), D5 (ε) |
| `run_uniform.py` | `ustar_*` | C6 targeted vs uniform plan |
| `run_l2.py`, `run_weighted.py`, `run_copeland.py` | `l2_cost`, `weighted_*`, `copeland_helm` | D3, D4, D2 |
| `theory_checks.py`, `theory_table.py` | `theory_checks`, `theory_pred` | C1, C2 (closed forms vs solvers) |
| `run_robust.py`, `run_loto.py` | `*_noise_gain10`, `helm_taskboot/tasksub_gain10`, `loto_*` | C5 robustness |
| `summarize.py`, `summarize_robust.py`, `summarize_extra.py` | `tables/*.csv` (headers of the scripts list each table and its claim) | all uncertainty statements (bootstrap over targets, 95 % percentile CIs) |
| `check_consistency.py` | `consistency_checks.csv` | cross-checks C1–C5 |

The mapping from result files to every **figure and table of the paper** is kept by `figtab-repo` (`figures/scripts/*.py`, one generator per output, `<stem>.provenance.json` lists the SHA-256 of every input
file read); it is the authoritative script→figure/table map. Column conventions of the result files: `README.md`.

## 6. Withheld-paper rule
The task forbids searching for, accessing or using the published paper that studied the same question or anything citing it. In this position's work (data acquisition, solvers, experiments, theory checks)
no such page was searched for, opened or encountered; searches were limited to dataset locations given in `data.md` and package documentation (scipy/HiGHS). Nothing from such a source was read or used. (Related-work searches belong to `idea-repo`.)

## 7. What was not done / limits that affect reproduction
* Rank rules (Borda, Condorcet, plurality) and trimmed mean on OLLB are exact but expensive, so they run on a 57-target rank-stratified sample (ranks 2–21 plus a log-uniform tail); score rules run on all 4496 models. Group statistics that mix both use paired ratios or the complete top-20 set (`results/tables/head20_rule_comparison.csv`).
* Copeland is solved exactly only on HELM (dense MILP); on OLLB it is not computed (M = 4496).
* HELM has no base/fine-tune pairs, so empirical caps on HELM (`hemp95/99`) are a transfer from the OLLB MMLU-PRO gain quantile and are labelled as such.
* The OLLB top-500 / no-merge slices are leaderboard-slice variants, not new data.
