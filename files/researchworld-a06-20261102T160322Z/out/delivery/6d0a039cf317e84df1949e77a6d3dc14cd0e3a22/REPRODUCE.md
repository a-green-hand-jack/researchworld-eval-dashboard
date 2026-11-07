# REPRODUCE.md

Study: what a reported benchmark score means after prompt/pipeline auto-tuning on benchmark items (gap between search-set score and fresh-item performance, drivers, and more reliable reporting methods M0–M5).
Everything below was run in a CPU-only sandbox (2 vCPU / 4 GB per job, no GPU, no network at run time) on a shared host.

## Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, pyarrow 26.0.0, matplotlib 3.11.2 (figure scripts), llama-cpp-python 0.3.36 (llama.cpp CPU build). Full lock (`pip freeze` of the environment all code and figure scripts ran in): `code/requirements-lock.txt`; install with `pip install -r code/requirements-lock.txt` (torch is in the lock but not used by any script here). Model files: `qwen2.5-1.5b-instruct-q8_0.gguf` (Qwen2.5-1.5B-Instruct, Q8_0 GGUF). MMLU-Pro: `TIGER-Lab/MMLU-Pro` revision `b189ec765aa7ed75c8acfea42df31fdae71f97be` (test: 12 032 questions, validation: demo pool).

## Tiers and what each shows
* **T0 — synthetic world with exact truth** (`code/t0.py`, `code/lib.py`, `code/methods.py`, `code/run_t0.py`): latent-probit world, θ_c = Φ(a+δ_c), item effects shared across configs, config×item noise; grid over n ∈ {50..2000}, K ∈ {2..200}, τ (true spread of configs) ∈ {0, .05, .1, .2}, ρ, baseline accuracy, three search procedures (exhaustive, successive halving, greedy coordinate edit) and few-shot leakage from D. **216 distinct cells and 203 400 distinct replicates** (`runs_t0.parquet`; 208 cells without and 8 with few-shot leakage; 300–1000 replicates per cell). The separate `t0leak` job re-runs 16 of these cells with the same seeds; its rows are duplicates and are removed on load, so 232 cells / 219 400 replicates would double-count. Truth θ(ĉ) is exact, so bias/coverage of every method is measured directly.
* **T1 — real LLM on real MMLU-Pro** (`code/configs.py`, `code/score.py`, `code/t1.py`): the 24 base prompt configurations (4 instructions × 2 answer cues × {0-shot, two 3-shot demo sets from the validation split}) are scored once on a pool of MMLU-Pro test questions; the 10-way option log-probabilities are cached; 276 pairwise logit-average ensembles extend the candidate set to 300. Search is then *replayed* on resampled search sets D from the pool, the remaining pool items are the fresh set. Cached scoring was validated against uncached recomputation (max |Δ log-prob| ≈ 0.002, fp16 storage).
* **T2 (live auto-tuning tool run) — not done.** No tool was run live; the plan replaced it by replay in T1. `t2_live.csv` does not exist.

## Data and model acquisition
```
# MMLU-Pro, pinned revision (test and validation parquet files; `code/configs.py` reads them from /hutian/data/mmlu_pro/data/ -- edit DATA in code/configs.py if stored elsewhere)
huggingface-cli download TIGER-Lab/MMLU-Pro --repo-type dataset --revision b189ec765aa7ed75c8acfea42df31fdae71f97be --local-dir /hutian/data/mmlu_pro
# model: Qwen2.5-1.5B-Instruct Q8_0 GGUF (official repo Qwen/Qwen2.5-1.5B-Instruct-GGUF), expected at /hutian/models/gguf/ (path in code/score.py)
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct-GGUF qwen2.5-1.5b-instruct-q8_0.gguf --local-dir /hutian/models/gguf
sha256sum /hutian/models/gguf/qwen2.5-1.5b-instruct-q8_0.gguf   # d7efb072e7724d25048a4fda0a3e10b04bdef5d06b1403a1c93bd9f1240a63c8, 1 894 532 128 bytes
```
The files used here were supplied with the task (the HF download cache of the MMLU-Pro copy records revision `b189ec76…`); the GGUF file's size and sha256 equal those the Hugging Face repo `Qwen/Qwen2.5-1.5B-Instruct-GGUF` lists for `qwen2.5-1.5b-instruct-q8_0.gguf`, checked at 2026-11-04. The run itself needs no network. The Qwen2.5-0.5B files in the model directory were not used.

## Commands (order)
```
python3 code/score.py qwen2.5-1.5b-instruct-q8_0 2000 250 W 8      # W = 0..7, 8 parallel jobs; resumable; writes results/logits/...
for s in 0 1 2 3; do python3 code/run_t0.py $s 4; done            # T0 grid -> results/t0/shard*.parquet  (≈ 1 h CPU in total)
python3 code/run_t0.py 0 1 --only K=24 --out results/t0leak         # optional: leakage cells alone (also inside the main grid)
python3 code/aggregate.py T0                                         # merged files, summaries, decisions, theory curve
```
```
for s in 0 1 2 3; do python3 code/t1.py qwen2.5-1.5b-instruct-q8_0 $s 4 --reps 1000; done   # 52 replay cells -> results/t1/*.parquet (~3-4 min per job)
python3 code/t1_summary.py qwen2.5-1.5b-instruct-q8_0               # runs/methods/summary/decisions/subject_breakdown/t1_matrix_summary
for n in 50 100 200 500; do python3 code/t1_pairs.py qwen2.5-1.5b-instruct-q8_0 $n --reps 1000; done   # A-vs-B pair design
python3 code/t1_pairs_summary.py qwen2.5-1.5b-instruct-q8_0         # decisions_ab_t1.csv, summary_pairs_t1.csv
python3 code/t0_vs_t1.py                                            # results/t0_vs_t1_gap.csv
```

## Runtime per command (2 vCPU / 4 GB job on the shared 40-core host; measured, see `results/compute.csv`)
| command | measured wall time |
|---|---|
| `score.py ... W 8` (8 parallel jobs, 192 tasks of 250 items) | **81 172 s elapsed** (≈22.5 h; 1.6k–5.6k s per task) on a host at load ≈ 50–110 on 40 cores; about 5x faster on an idle host |
| `run_t0.py s 4`, s = 0..3 | 742 / 1172 / 695 / 1030 s (≈1 h in total, run in parallel) |
| `run_t0.py 0 1 --only K=24 --out results/t0leak` | 168 s |
| `aggregate.py T0` | ≈ 22 s (outputs byte-identical on re-run) |
| `t1.py ... s 4 --reps 1000`, s = 0..3 | 155 / 166 / 253 / 227 s |
| `t1_summary.py` | ≈ 17 s |
| `t1_pairs.py ... N`, N = 50, 100, 200, 500 | 60 / 66 / 99 / 191 s |
| `t1_pairs_summary.py`, `t0_vs_t1.py` | seconds |
| figure and table scripts (`figures/`, `tables/`) | seconds each |

## Seeds
T0: 20261102; T1 replay: 20261103; T1 pair design: 20261104. Every replicate uses its own stream `default_rng([seed, crc32(cell_id), rep])`, so any cell or replicate reproduces independently of the sharding.

## Compute actually used
See `results/compute.csv` (per job) — T0 ≈ 1.06 CPU-hours wall in total over five jobs; the LLM scoring is the dominant cost (24 configs × pool items, prompts up to ~1.5k tokens, 2 threads/job, shared host with load average ≈ 110 on 40 cores, so throughput was ~5× below an unloaded host). No LLM calls beyond the scoring job.

## Script → output map
`aggregate.py` → `results/{runs,methods}_t0.parquet`, `summary_gap_t0.csv` (Fig A/B data), `summary_methods_t0.csv` (calibration table), `decisions_t0.csv`, `decisions_ab_t0.csv` (decision-error table), `theory_curve_t0.csv` (closed-form vs simulation). Columns: `results/SCHEMA.md`; provenance: `results/MANIFEST.md`.

## Access log
The published paper that addresses this question, and work citing it, were not searched for or read. No accidental encounter occurred.

## Known limits (status at this revision)
* T1 uses one model (Qwen2.5-1.5B, 20–30 % MMLU-Pro accuracy per config; the 0.5B model of plan §7 was not run) and a configuration family of prompt formats, so the real-arm true spread τ between configs is small; it is a lower-signal, high-noise regime, not a general statement about frontier systems or search-heavy pipelines.
* T0 is a model of the mechanism (its fit to T1 is checked, not assumed); conclusions about real systems rest on T1 only.
* M4_cond / M4_hybrid apply to argmax selection only (exhaustive search); they are `NaN` for halving/greedy.
* M5_eb (empirical Bayes from disclosed scores) assumes independent estimation noise across candidates; candidates share the same items, and its coverage in T0 is far below nominal (0.15–0.9 depending on K, n, τ) — reported as a negative result.
* T1 truth is a finite-sample value: "fresh" = the pool items outside D and outside the left-out block (1 300–1 750 items), so θ(ĉ) carries binomial noise (`theta_se`, ≈0.011–0.013) that is independent of the search; it does not bias the gap. The pool is fixed (2 000 random MMLU-Pro test items), so T1 uncertainty is over search sets D *given the pool*; between-pool uncertainty is not estimated. Replicates share items, so MC SEs treat them as independent while they are not: use `gap_block_se` (10 delete-a-block groups).
* The 276 ensembles are a pipeline-like extension of the 24 base prompts (two-call logit average), not independently tuned systems; the candidate-set spread (τ ≈ 0.017–0.023 on the probability scale) is small and the configs are strongly correlated (binary item-correlation 0.57–0.68). The baseline (`terse|is|0shot`, 0.227) is the weakest config but two, so "tuned beats baseline" is nearly always truly so in T1; false-claim rates are read from the pair design.
* T1 compared with T0: the closed-form Gaussian-max prediction fed with the matrix's own (σ, r, τ) reproduces the measured exhaustive gap (`summary_gap_t1.csv`, `gap_theory_from_matrix`); T0's grid cells at rho 0.6 / tau 0.05–0.1 over-predict it, typically by a factor 1.2–2 (rho 0.9 under-predicts at one cell), because the matrix's correlation sits between the two grid rho values (`t0_vs_t1_gap.csv`). T0 is a model of the mechanism, not a calibrated replica.
* Not done: Qwen2.5-0.5B arm; a second real task or model; live auto-tuning tool run (T2); subject-stratified sampling; pool-level (between-pool) uncertainty.
