# Reproduction guide

Everything lives in `/work` (paths are hard-coded; adjust `ROOT` in `code/common.py` and the paths in `code/*.py` if you move it).
All numbers/figures/tables in the paper are produced by the scripts below from the cached LLM outcomes (`results/`).

## Environment
Python 3.11.2, packages in `requirements.txt` (CPU-only torch 2.15.0, transformers 5.22.2, numpy 2.4.6, scipy 1.17.1, pandas 3.1.1, matplotlib 3.11.2).
`python3 -m venv venv && . venv/bin/activate && pip install numpy scipy pandas matplotlib pyarrow huggingface_hub jinja2 && pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install transformers accelerate safetensors`
Hardware used: 4 CPU cores (cgroup quota), no GPU, no API calls.

## Data and models (pinned)
`python code/download_data.py` downloads MMLU-Pro (HF dataset `TIGER-Lab/MMLU-Pro`, revision `b189ec765aa7ed75c8acfea42df31fdae71f97be`; only the parquet files are used, none of the repository scripts are executed) and
Qwen2.5-1.5B-Instruct (rev `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`), Qwen2.5-0.5B-Instruct (rev `7ae557604adf67be50417f59c2c2f167def9a775`).

## Step 1 -- LLM outcome matrices (the only LLM inference; about 34 wall-clock hours at 3-4 threads on the 4-core quota in total)
Question pool: seed 12345, random sample of MMLU-Pro test questions with <=200 Qwen tokens (question+options); first 750 are used (`code/common.py::build_pool`).
```
python -I code/score_matrix.py   models/Qwen2.5-1.5B-Instruct results/q15 1500 150 4 all 0,1,2,3,4   # world A: 1.5B, 40 prompt/demo configs  (~12 h)
python -I code/score_matrix_b.py models/Qwen2.5-0.5B-Instruct results/b05 1500 150 4 all 0,1,2,3,4   # world B: 0.5B, format/demo grid (~3 h)
python -I code/score_matrix_b.py models/Qwen2.5-1.5B-Instruct results/b15 1500 150 3 all 0,1,2,3,4   # world C: 1.5B on the format grid (~11 h)
python -I code/score_matrix_b.py models/SmolLM2-1.7B-Instruct   results/s17 1500 150 4 all 0,1,2       # world D: SmolLM2-1.7B (first 450 questions; ~8 h)
python -I code/build_worlds.py 750                                                                     # -> results/world_{q15,b05,b15,s17}.npy (+ pool_ids.csv; s17 uses 450 questions)
```
(Our world-A run was launched with chunks 0..9 and stopped after chunk 4; chunk files beyond 4 are not used.) Deterministic: scoring is greedy argmax over the answer-letter logits; no sampling.
Each (config, chunk) writes `results/<world>/c{cfg}_k{chunk}.npz` (letter logits, fp16); `code/worlds.py::load_real` turns them into 0/1 correctness (letters beyond the question's option count are masked).

## Step 2 -- search-episode simulations (CPU; numpy). Random seeds are derived by md5 of (experiment, setting, replicate) in `code/exp_main.py::seed_of`.
```
for w in q15 b05 mix b15 s17; do for e in gap ksweep conclusions norepl optsens; do python -I code/exp_main.py $w results/sim $e 2000 4; done; done   # ~1-1.5 h per world/experiment 'gap', minutes for the others
python -I code/exp_synth.py results/sim 400 4                                                        # synthetic factor sweeps (~1 min)
python -I code/exp_poolboot.py q15 b05 mix                                                           # finite-pool uncertainty (Table poolboot)
python -I code/check_cond.py                                                                          # Gaussian sanity check of the conditional-inference implementation
```
## Step 3 -- figures and tables
`python -I code/make_figs.py all` and `python -I code/make_tables.py` write `paper/figs/*.pdf`, `paper/tables/*.tex`, `paper/numbers.tex`.
`cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main`.

## Artifact map (paper element -> script -> input)
| Paper element | Script | Inputs |
|---|---|---|
| Table 1 (worlds), Table 2 (gap), Table 3 (claims), Table 4 (protocols), Table 5 (splitting), appendix tables | `code/make_tables.py` | `results/sim/*.parquet`, `results/world_*.npy` |
| Fig. 1 (gap vs n), Fig. 2 (search effort), Fig. 3 (theory check), Fig. 4 (conclusions), protocol figures, K-sweep | `code/make_figs.py` | same; Fig. 3a,b from `results/sim/synth_sweep.parquet` (`code/exp_synth.py`) |
| conditional-inference sanity check (95.4%) | `code/check_cond.py` | none (`results/sim/check_cond.txt`) |
| pool-bootstrap table | `code/exp_poolboot.py` | `results/world_*.npy` |

Core library: `code/sim_lib.py` (optimizers + reporting protocols), `code/episodes.py` (one episode under all protocols), `code/exp_main.py` (experiments), `code/worlds.py` (loading/synthetic), `code/common*.py` (prompts/configs), `code/score_matrix*.py` (LLM scoring).


Download for world D: `huggingface_hub.snapshot_download("HuggingFaceTB/SmolLM2-1.7B-Instruct", revision="31b70e2e869a7173562077fd711b654946d38674", local_dir="models/SmolLM2-1.7B-Instruct")` (add to `download_data.py` if re-running).
`mix` (A union B, K=80) is built on the fly in `exp_main.py::get_world` from world_q15 and world_b05.

## Verification of reproducibility
Re-running `python -I code/exp_main.py q15 /tmp/chk gap 250 4` reproduces, bit-for-bit, the corresponding 250-episode blocks of the stored 2000-episode results (`results/sim/gap_q15.parquet`), i.e. the simulation stage is deterministic given the cached outcome matrices. The LLM scoring stage is deterministic up to floating-point nondeterminism of multi-threaded fp32 matrix products (letter logits are stored in fp16; we did not re-run the 34 h of scoring).

## Content restrictions (task rule on the excluded prior study)
Literature search used only scholarly-search tools for classical statistics/ML references and for the references listed in the paper. No page, abstract, preprint, review page, summary, repository, or follow-up discussion of the excluded study was knowingly retrieved or read. One query ("optimizer's curse ...") listed two 2025-2026 decision-analysis papers about policy evaluation in the result list (titles only, not opened); neither is the excluded study as far as we can tell.

## Paper
`paper/main.tex` (ICML 2026 style, 8-page main body limit; the body here ends on page 7), compiled PDF `paper/main.pdf`; `paper/sections/*.tex`, tables in `paper/tables/` and figures in `paper/figs/` are generated by the scripts above.
