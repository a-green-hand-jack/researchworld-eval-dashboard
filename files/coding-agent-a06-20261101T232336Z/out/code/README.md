# Reproduction guide — "What does a tuned system's benchmark score mean?"

Everything in the paper (all numbers, tables, figures) is produced by the scripts in `code/` from (i) a cache of real LLM per-item
scores (`cache/`) and (ii) Monte-Carlo simulation. Nothing in the paper is hand-entered: quoted numbers are written to
`paper/numbers.tex` by `code/gen_numbers.py` and tables to `paper/tables/*.tex`.

**Authorship note.** The research (design, code, experiments, analysis, writing) was carried out by an autonomous LLM agent (Claude, Anthropic)
running unattended in a sandbox, following a task description. No human reviewed intermediate results.

## Environment
* Linux x86-64, **4-CPU cgroup quota (no GPU), 251 GB RAM**, Python 3.11.2 in `venv/`.
* Packages: numpy 2.4.6, scipy 1.17.1, pandas 3.1.0, matplotlib 3.11.2, pyarrow, huggingface_hub, llama-cpp-python 0.3.36
  (built from source with `CMAKE_ARGS="-DGGML_NATIVE=ON -DGGML_OPENMP=ON"`), dspy 3.4.1 (only used for the abandoned smoke test, see below), pymupdf (PDF page rendering for inspection only).
  Re-create: `python3 -m venv venv && . venv/bin/activate && pip install numpy scipy pandas matplotlib huggingface_hub pyarrow cmake ninja && CMAKE_ARGS="-DGGML_NATIVE=ON -DGGML_OPENMP=ON" pip install llama-cpp-python`.
* LaTeX: TeX Live (pdflatex, latexmk, bibtex). Template: NeurIPS 2026 (`Formatting_Instructions_For_NeurIPS_2026.zip` from media.neurips.cc), files `paper/neurips_2026.sty`, checklist in `paper/checklist_filled.tex`.

## Data and models (all public, no account needed)
* MMLU-Pro, HF dataset `TIGER-Lab/MMLU-Pro`, revision `b189ec765aa7ed75c8acfea42df31fdae71f97be` (MIT): `huggingface_hub.snapshot_download(..., repo_type="dataset", revision=...)` into `data/mmlu-pro/`. Test split 12,032 q; validation split (70 q) supplies few-shot demonstrations.
* Models (GGUF, 8-bit unless stated; Hugging Face repos): `Qwen/Qwen2.5-1.5B-Instruct-GGUF` (`qwen2.5-1.5b-instruct-q8_0.gguf`, main model),
  `Qwen/Qwen2.5-0.5B-Instruct-GGUF`, `Qwen/Qwen2-1.5B-Instruct-GGUF`, `Qwen/Qwen3-0.6B-GGUF`, `Qwen/Qwen3-1.7B-GGUF` (Real-II pool). `Qwen2.5-3B` was downloaded but not used. Put them in `models/`.

## Seeds (all fixed in the scripts)
population = 1000 of the first 1500 items drawn with `population_ids(1500, seed=0)` and processed in the permutation `default_rng(1)`; demo sets `demo_sets(val, seed=123)`;
synthetic worlds: `seed=11` (main), `21` (robust), `31` (matched); every Monte-Carlo cell uses `default_rng(seed0 + cell_index)`; see `runner.py`, `exp_conclusions.py`.

## Pipeline and run times (wall-clock on the 4-core quota)
| step | command | time | produces |
|---|---|---|---|
| real score cache, Qwen2.5-1.5B, 72 configs x items | `python code/grid.py models/qwen2.5-1.5b-instruct-q8_0.gguf cache/q15 W 3 1500 25` for W=0,1,2 (+ `... 3 3 1500 25 rev`) in parallel; stopped after 40 chunks = 1000 items | ~16 h on 3-4 cores | `cache/q15/chunk_*.npz` (log-probs of option letters) |
| Real-II cache | `bash code/run_real2.sh` (then stop after 16 chunks = 400 items) | see below | `cache/m_*/` |
| demo self-leak | `python code/exp_leak.py results/leak.npz 40 12` | ~1.5 h, 1 core | `results/leak.npz` |
| theory check | `python code/exp_theory.py` | ~10 min | `results/theory.csv` |
| synthetic main sweep | `python code/exp_synth_main.py 1 300` | ~100 min | `results/synth_main.parquet` |
| synthetic extras (EB, conditional, simultaneous, Ladder, Thresholdout) | `python code/exp_rs_extras.py 1 300` | 5 min | `results/synth_extras.parquet` |
| synthetic robustness | `python code/exp_robust.py 1 200` | ~35 min | `results/synth_robust.parquet` |
| synthetic dense (n,B,tau,rho,a) sweep | `python code/exp_synth_sweep.py 1 1000` | 6 min | `results/synth_sweep.parquet` |
| matched simulation | `python code/exp_synth_matched.py 1 400` | ~40 min | `results/synth_matched*.parquet` |
| conclusions (synthetic) | `python code/exp_conclusions.py synth 1 150` | ~15 min | `results/conclusions_synth.parquet` |
| real audit | `bash code/run_real_all.sh` (= `exp_real_main.py 4 400`, `exp_conclusions.py real 4 300`, `exp_permnull.py cache/q15 300`) | ~35 min on 4 cores | `results/real_main*.parquet`, `real_sweep_naive.parquet`, `conclusions_real.parquet`, `permnull.parquet` |
| hold-out frontier | `python code/exp_frontier.py 1 600` | 30 min | `results/frontier.parquet` |
| Real-II audit | `python code/exp_real2.py 3 400` | minutes | `results/real2_*.parquet` |
| numbers, tables, figures | `python code/gen_numbers.py; python code/tables.py synth; python code/tables.py real; python code/fig_theory.py; python code/fig_sweep.py; python code/fig_methods.py synth; python code/fig_methods.py real; python code/fig_real2.py` | 1 min | `paper/numbers.tex`, `paper/tables/`, `paper/figs/` |
| paper | `cd paper && latexmk -pdf main.tex` | 1 min | `paper/main.pdf` |

## Which script makes which table / figure
* Fig. 1 (`figs/fig_sweep.pdf`): `fig_sweep.py` <- `real_sweep_naive`, `synth_sweep`.  Fig. 2 (`fig_theory.pdf`): `fig_theory.py` <- `theory.csv`.
* Table 1 (`tables/conclusions.tex`): `tables.py real` <- `conclusions_real`, `conclusions_synth`.  Fig. 3 (`fig_methods_real.pdf`): `fig_methods.py real` <- `real_main`.
* Appendix: `tables/real_optimism.tex`, `synth_methods.tex`, `real_extras.tex`, `robust.tex` (`tables.py`); `fig_methods_synth_tau*.pdf` (`fig_methods.py synth`); Real-II (`fig_real2.py`).
* All numbers in the text: macros in `numbers.tex` from `gen_numbers.py`.

## Code map
`common.py` data/prompts; `scorer.py` llama.cpp scorer with prefix KV reuse; `grid.py`, `grid2.py` score caches; `sel.py` search algorithms (random search, successive halving,
coordinate ascent, MIPRO-like), conditional (polyhedral) inference; `mc.py` reporting methods and trial functions; `synth.py` synthetic worlds; `runner.py` parallel Monte-Carlo runner;
`summ.py` summaries; `realdata.py` cache loaders; `exp_*.py` experiments; `figstyle.py`, `fig_*.py`, `tables.py`, `gen_numbers.py` outputs. `test_*.py`, `bench2.py`, `speedtest.py`, `dspy_smoke.py` are pilots/smoke tests kept for transparency.

## Honest notes
* **DSPy was not run end-to-end.** `dspy_smoke.py` (DSPy 3.4.1 `Predict` against a local llama.cpp server with Qwen2.5-0.5B/1.5B, 1 core) produced empty/unparsable answers and ~45 s per request; abandoned. The search procedures in the paper are our own reimplementations of the algorithm families, replayed on the cached score matrix.
* Pilot runs (`test_mc*.py`) on synthetic data were used to fix method hyper-parameters (30% hold-out, 5 folds, 100 bootstrap replicates, EB variance term) before the real cache was analysed. One failed attempt is kept: the first Thresholdout parameterisation (noise too large) is in `mc.py` as `thresholdout` (reported along with two other settings).
* A first real-data analysis scored benchmarks drawn without replacement against the remaining items; this has a finite-pool artefact (paper, App. "Why the primary real analysis draws benchmarks with replacement"). The corrected design is the primary one; the earlier design is kept as `results/real_main_fresh.parquet` (small n only).
* The real score cache was stopped at 1000 of the planned 1500 items (time budget); Real-II uses 400 items.
* No forbidden material (the paper this task is based on, or anything citing it) was searched for, accessed or read. Literature lookups were by exact title of the starter-list and classical references (OpenAlex/S2 abstracts only).
