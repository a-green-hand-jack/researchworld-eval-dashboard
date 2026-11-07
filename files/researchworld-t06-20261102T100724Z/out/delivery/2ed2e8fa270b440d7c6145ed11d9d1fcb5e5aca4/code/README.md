# Reproduction notes: stability of Bradley-Terry leaderboards

All numbers in the paper are produced by the scripts below from the pinned public data. Raw data are kept in
`$DATA_DIR` (default `/hutian/data`), never in this repository.

## Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, pyarrow 26.0.0 (matplotlib 3.11.2 / scikit-learn only for
figures / not used by the analysis). CPU only; scripts use a 2-process pool. Run every script with `python3 -I` from
`code/` (the scripts add their own directory to `sys.path`).

## Data (download once with `sh fetch_data.sh [--judges]`, which fetches the pinned files below and checks their sha256; verified on 2026-11-02)
| id | source (pinned commit) | file -> `$DATA_DIR/` | sha256 |
|---|---|---|---|
| A | HF `lmarena-ai/arena-human-preference-55k` @ 18c298340948c0e7f7727399fd459cca6ce0ca6f | `arena55k/train.csv` | 0692154a...f5be2 |
| M-h | HF `lmsys/mt_bench_human_judgments` @ f7d2896d2cc5d80f8b55c2bbc722613555233c25 | `mtbench/human-00000-of-00001-25f4910818759289.parquet` | 4877bc46...2f5769 |
| M-g | same repo | `mtbench/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet` | 57068327...0a00e71 (LFS oid) |
| N | github `fivethirtyeight/data` @ 4c1ff5e3aef1816ae04af63218015066e186c147 | `nba/nbaallelo.csv` | d46ed354...8d616bc |
Download URLs: `https://huggingface.co/datasets/<repo>/resolve/<commit>/<path>`, and
`https://raw.githubusercontent.com/fivethirtyeight/data/<commit>/nba-elo/nbaallelo.csv`. Full sha256 values are in
`results/MANIFEST.json` (written next to every output). `potsawee/chatbot-arena-llm-judges` @ 638a7e3be3078e55d2eb0b789d34749747822c49 (`train.single-turn.json`, sha256
6ed8793f...c8f3; `llm-judges-prob-avg/{Meta-Llama-3-70B-Instruct,Athene-70B,Qwen2-72B-Instruct}.jsonl` saved as
`judges/<name>.avg.jsonl`, sha256 6a89941a..., dd6b1925..., bffcf2d5...) is used only for the matched crowd-vs-LLM-judge
contrast (`run_judges.py`). Terms: the repository declares no licence; its README says the battles are the Kaggle LMSYS
competition train data (the 55k HF copy is apache-2.0). We use it for research analysis only; the raw files are not
redistributed (only aggregate k* tables are in `results/`).

## Modelling choices (E0)
* Bradley-Terry MLE on aggregated cells (pair or pair x home-orientation), natural-log scores, mean-centred,
  ridge 1e-6; ties = half a win for each side (likelihood with fractional response); NBA: shared home-advantage
  column (neutral-site games get home=0), regular season only, `_iscopy==1` rows dropped.
* A *claim* is evaluated on the fitted ranking of the (possibly perturbed) data; "flip" requires a strictly negative
  margin (exact score ties do not count).
* k* = smallest number of edits found by greedy influence search with exact refits: at each step edits are ranked by
  their first-order effect on the claim margin (Koh & Liang / Broderick et al. influence, Hessian of the cell
  likelihood), a batch worth 30% of the remaining margin is applied, the model is refitted exactly, and the last
  batch is bisected. k* is a verified UPPER BOUND on the true minimum (`exact_check.csv` compares to exhaustive search
  on small instances; `approx_check.csv` gives the linearisation error; `k_lin` is the one-shot linear prediction).
* Perturbations: P1 remove, P2 relabel (win<->loss, tie<->win/loss), P3 add votes only in cells containing the
  challenger. Claims: C1 top-1 (min over the 8 nearest challengers), C2 order of adjacent pairs (r, r+1), r <= 10,
  C3 top-k set (k = 3, 5, 10), C4 "difference significant" (Wald z > 1.96 in the loop).

## Scripts -> outputs (expected wall time with 2 cores)
| script | output (results/) | time |
|---|---|---|
| `test_btlib.py` | (assertions: fit vs scipy, influence vs refit, greedy vs brute force) | 10 s |
| `run_full.py` | `kstar_full.csv`, `random_curve.csv`, `boot_flip.csv`, `data_summary.csv` | 3 min |
| `run_units.py nba`, `run_units.py arena mt`, then `merge_units.py` | `kstar_units_nba.csv`, `kstar_units_arena_mt.csv`, merged `kstar_units.csv` (NBA seasons 1947-2015; Arena battle bootstrap, 60 reps; MT-Bench question-cluster bootstrap, 200 reps, shared by human / GPT-4 / matched boards) | ~25 min (host load 35-60; Arena replicates 8-150 s each) |
| `run_matched.py` | `matched_arena.csv` (size / sparsity-matched Arena subsets, size curve) | ~15 min |
| `run_exact.py` | `exact_check.csv`, `approx_check.csv` | 3 min |
| `run_sens.py` | `sensitivity.csv`, `elo_order.csv` (ties, home advantage, playoffs, pooled seasons, Elo vs BT) | 10 min |
| `run_extra.py` | `sanity_fit.csv`, `alignment.csv`, `sens_aba.csv` | 2 min |
| `run_judges.py` | `kstar_judges.csv` (49,938 shared Arena battles: human votes vs 3 LLM judges; 40 shared battle-bootstrap replicates + full fit; C1 C2 C4, P1 P2) | ~25 min |
| `run_secheck.py` | `se_check.csv` (Wald vs bootstrap s.e., from existing outputs) | seconds |
| `run_e4.py` (after all of the above) | `summary_claims.csv`, `paired_mt.csv`, `scaling_fit.csv` | 3 min |
Order: `test_btlib.py`, then `run_full`, `run_units`, `run_matched` (any order), `run_exact`, `run_sens`, `run_extra`,
finally `run_e4`. `btlib.py` (BT fit, influence, greedy search), `datasets.py` (loaders / board builders),
`experiments.py` (claim x perturbation rows, B1 / B2 baselines), `provenance.py` (CSV + MANIFEST writer) are libraries.

## Units of replication and known gaps
* NBA: one fit per season (69 regular seasons in the file), NBA league games only: the file also holds the ABA
  (1968-76), a second, disconnected comparison graph; a first run that fitted both leagues jointly gave se ~ 400 for
  cross-league gaps (BT scale between the leagues set by the ridge alone) and was discarded and rerun without ABA
  games (`sens_aba.csv` keeps the all / NBA-only / ABA-only comparison); Arena: battle bootstrap (60 replicates of the full
  55k fit); MT-Bench: question-cluster bootstrap (200), the same resampled questions for human, GPT-4 and matched
  boards, so paired contrasts are valid. `kstar_full.csv` holds the single full-data fit of each board.
* MT-Bench human: each (question, turn, model pair) may carry several human judgments; all are kept as separate
  comparisons, and `mtmatched_h1` keeps one random judgment per key as a check (units are then comparable to GPT-4).
* Judge contrast: the same bootstrapped battle multiplicities are applied to the human board and to every judge board
  (paired). Judge verdict = argmax of position-averaged A / B / tie probabilities; judges call ties far less often
  (4-26% vs 31% human), the main way the boards differ besides the labels.
* `matched_arena.csv`: 72 of 100 `nba_like` draws had all claims defined; the size curve has no row at N = 1000.
* Replicates of one dataset are dependent; intervals in `scaling_fit.csv` carry a `scheme` column (see SCHEMA).
* The Wald s.e. behind z treats ties as half-wins (quasi-likelihood); `se_check.csv`: Wald/bootstrap s.e. ratio over
  the 95 C2 gaps is 0.87-1.08 for NBA boards (median 0.96), 1.05-1.25 on Arena (median 1.19) and 1.15-1.41 on MT-Bench
  (median ~1.25), i.e. z is conservative (too small) by up to about 40% on Arena / MT-Bench.
* P3 adds votes only in cells that contain the challenger (rigging model); the unrestricted add family is not used.
* Exact search (`exact_check.csv`) covers 3-participant boards and k <= 14 only.

Seeds are in the scripts (`SEED`) and in `results/MANIFEST.json`; column definitions in `results/SCHEMA.md`.
Figure/table scripts are in `figures/` (figtab-repo).

## Excluded material
Starter-literature item 8 (arXiv 2508.11847) was never opened or searched for; no page citing it was read.
