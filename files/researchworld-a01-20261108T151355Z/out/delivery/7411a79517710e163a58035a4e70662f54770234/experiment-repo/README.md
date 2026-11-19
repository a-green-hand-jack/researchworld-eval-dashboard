# Minimum targeted investment to top a multi-task leaderboard

Analysis code for: *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to make it
rank first, as a function of the aggregation rule?* Exact solvers (closed form, bisection, MILP) for mean, geometric/harmonic mean,
median, minimum, trimmed mean, Borda, Condorcet winner and plurality, run on the Open LLM Leaderboard (OLLB, 4496 models x 6 tasks)
and HELM MMLU (79 models x 57 subjects). CPU only; every number in `results/` is produced by a script in `src/`.

## Reproduce
```
pip install -r environment.txt            # python 3.11, numpy, scipy (HiGHS MILP), pandas, pyarrow, pytest
./get_data.sh [RAWDIR]                    # downloads the raw inputs (network), checks their SHA-256, rebuilds data/processed (byte-identical to the shipped tables)
python3 -m pytest tests                   # solvers vs brute force
./run_all.sh JOB                          # one experiment (single-threaded; independent JOBs can run in parallel); JOB names are in results/README.md
python3 src/analyze.py                    # summary tables -> results/summary/*.csv
python3 src/provenance.py                 # results/MANIFEST.csv (SHA-256 of every result file)
```
Raw inputs (all public; exact versions, checked by `get_data.sh` against `data/raw_checksums.sha256`):

| input | where | SHA-256 |
|---|---|---|
| OLLB `contents` table, 4576 rows | `https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet` | `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` |
| OLLB `results`: one pinned lm-eval JSON (item counts per task, used by `src/ollb_items.py`) | `https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/aa81ecc38fdc5708254b833923368970efdf5ef5/0-hero/Matter-0.2-7B-DPO/results_2024-08-07T13-21-02.903091.json` | `c0386eb6b6b7ca3c6cc596b190dcd898b17fb7055b092229d00ff50727930856` |
| HELM MMLU v1.13.0 release summaries, 303 files | `gs://crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` via `python3 src/fetch_helm.py RAWDIR/helm/v1.13.0` | manifest `MANIFEST.sha256.json` (SHA-256 of every file): `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` |

`src/build_data.py` regenerates `data/processed/{ollb6.csv, helm_mmlu57.csv, helm_mmlu_all.csv, helm_mmlu_neval.csv, manifest.json}` and `src/ollb_items.py` `ollb_noise.json`
from them; `data/processed/CHECKSUMS.sha256` holds the SHA-256 of the shipped tables, and `get_data.sh` verifies the rebuilt files against it.

## Layout
- `src/mti/scorerules.py` — exact minimum-investment solvers for score rules; `src/mti/ordinal.py` — exact MILP solvers for rank rules; `src/mti/data.py` — data loading, caps (`ceil`, `front<m>`, `gain<h>`, `emp<q>`, `emp<q>r`).
- `src/run_core.py` (main grids), `run_hstar.py` (minimum uniform gain cap h*), `run_robust.py` (noise, task bootstrap, task subsets), `run_flip.py`, `run_spillover.py` — experiment drivers (tidy CSV out).
- `src/analyze.py` (summary tables), `margin_robust.py`, `cluster_bootstrap.py`, `convex_cost.py`, `emp_pairs_composition.py`, `emp_caps.py`, `theory_checks.py`, `peak_memory.py`, `provenance.py` — analyses and bookkeeping.
- `run_all.sh` — job entry point (every result file of `results/`); `docs/SOLVERS.md` — problem statements and propositions; `tests/` — solver checks; `results/README.md` — what each result file is, the measured findings and failed runs.
- Cost: `results/summary/cpu_total.csv` (scheduler-metered CPU seconds over all jobs), `results/summary/runtimes.csv` (per job), `results/summary/peak_memory.csv` (peak memory of the ordinal MILPs).
