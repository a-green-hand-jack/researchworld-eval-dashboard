# Conformal regions on the simplex: evaluating score geometry for compositional outputs

Code, results and LaTeX source for the paper in `paper/` (ICML 2026 template; compiled PDF: `paper/main.pdf`).
Everything in the paper is produced by the scripts below; `results/` holds the raw CSV/NPZ outputs of the runs reported in the paper
(`results/old_*.csv` are superseded first runs kept for transparency, see Appendix D of the paper).

## Layout
- `code/ccp/` library: scores (`geometry.py`), synthetic generators (`synth.py`), conformal helpers (`conformal.py`),
  importance-sampling reference-mass estimator (`volume.py`), slice/mass lookup tools (`evalkit.py`)
- `code/exp*.py` experiment scripts, `code/real/` logit extraction, `code/tests.py` self-tests
- `analysis/` table and figure generation, `paper/` LaTeX (`main.tex`, `appendix.tex`, `real_section.tex`, `tables/`, `figs/`)
- `run_all.sh` full pipeline in order; `requirements.txt` pinned versions (Python 3.11.2)

## Environment
```
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt          # torch is only needed for logits / MLP (CPU wheels are fine)
PYTHONPATH=code python code/tests.py     # self-tests
```
No GPU is needed. Tested on a shared 40-core Linux machine with a 16 GB memory limit (use `n_jobs<=14` for the joblib runs).

## Data (download steps, versions, licences)
```
mkdir -p data/cifar10h data/cifar10_hf data/models data/chaosnli
# CIFAR-10H human label distributions (repo states no licence; GitHub: NOASSERTION)
curl -L -o data/cifar10h/probs.npy  https://raw.githubusercontent.com/jcpeterson/cifar-10h/master/data/cifar10h-probs.npy
curl -L -o data/cifar10h/counts.npy https://raw.githubusercontent.com/jcpeterson/cifar-10h/master/data/cifar10h-counts.npy
# CIFAR-10 test images (HF mirror of the official test set; the Toronto server download stalled for us). Order verified against CIFAR-10H (99.21% label agreement).
curl -L -o data/cifar10_hf/test.parquet https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/test-00000-of-00001.parquet
# pretrained CIFAR-10 classifiers (BSD-3-Clause) + model definitions
B=https://github.com/chenyaofo/pytorch-cifar-models
curl -L -o data/models/cifar10_resnet56.pt $B/releases/download/resnet/cifar10_resnet56-187c023a.pt
curl -L -O --output-dir data/models $B/releases/download/resnet/cifar10_resnet20-4118986f.pt
curl -L -O --output-dir data/models $B/releases/download/vgg/cifar10_vgg11_bn-eaeebf42.pt
curl -L -o data/models/resnet.py https://raw.githubusercontent.com/chenyaofo/pytorch-cifar-models/master/pytorch_cifar_models/resnet.py
curl -L -o data/models/vgg.py    https://raw.githubusercontent.com/chenyaofo/pytorch-cifar-models/master/pytorch_cifar_models/vgg.py
# ChaosNLI (CC BY-NC 4.0; community mirror earino/chaosnli, sha bf8d66a)
for f in snli mnli_m; do curl -L -o data/chaosnli/chaosNLI_$f.jsonl https://huggingface.co/datasets/earino/chaosnli/resolve/main/raw/chaosNLI_$f.jsonl; done
```
NLI models are downloaded by `transformers` at run time: `cross-encoder/nli-distilroberta-base` (Apache-2.0) and `roberta-large-mnli` (MIT).
The absolute path `/work` is hard-coded in the scripts (data in `/work/data`, outputs in `/work/results`); change it with a search-and-replace if you clone elsewhere.

## Reproduction (order and approximate wall-clock on the shared machine)
| command | time | output |
|---|---|---|
| `python code/real/extract_logits.py` | 3 min | CIFAR logits (3 models) |
| `python code/real/extract_nli_logits.py` | 1-2 h (CPU, loaded machine) | ChaosNLI logits |
| `python code/exp1_calibration.py`, `exp1b_pool_check.py` | ~25 + 10 min | `results/e1*.csv` (Beta law, ties, mis-ranking, pool check) |
| `python code/exp2_geometry.py` | 11 min | `results/e2_geometry.csv` (main synthetic grid) |
| `python code/exp2b_theory.py` | 1.5 min | `results/e2b_*.csv` (Gaussian-limit check) |
| `python code/exp2c_dirmult.py`, `exp2d_ellipsoid.py` | 2 min each | `results/e2c_*.csv`, `e2d_*.csv` |
| `python code/exp3_learned.py`, `exp3b_misfit.py` | 4 + 1.5 min | `results/e3_*.csv`, `e3b_*.csv` |
| `python code/exp4_selection.py` | 2 min | `results/e4_selection.csv` |
| `python code/exp5_real.py [--data chaosnli] [--alpha a]` | 1-5 min | `results/e5_rep*.csv`, `e5_img*.npz` |
| `python code/exp5b_shift.py` | 1 min | `results/e5b_shift.csv` |
| `python code/exp6_worst_slice.py`, `check_mass_estimator.py` | <1 min | null worst-gap table, estimator check |
| `analysis/*.py` (see `run_all.sh`) | minutes | all tables in `paper/tables`, figures in `paper/figs` |

Seeds: problem seeds 0-4; calibration draws use `default_rng([problem, rep, tag])`; real-data splits `default_rng([5, rep])`
(T-fit permutation seed 0); bootstrap seed 0. Total compute is about 5 CPU-core-hours plus NLI inference.

## Table / figure -> script
| item | script |
|---|---|
| Fig. 1 (ternary regions) | `analysis/fig_ternary.py` |
| Table 1, App. Tables (E2 grid) | `exp2_geometry.py` -> `analysis/make_e2.py` |
| Fig. 2, App. theory table | `exp2b_theory.py` -> `analysis/make_rest.py theory` |
| Table 2 (misfit), App. E2c/E2d tables | `exp3b_misfit.py` -> `make_e3b.py`; `exp2c_dirmult.py` -> `make_e2c.py`; `exp2d_ellipsoid.py` -> `make_e2d.py` |
| Table 3, App. E3 table | `exp3_learned.py` -> `make_rest.py e3` |
| App. E4 table | `exp4_selection.py` -> `make_rest.py e4` |
| Table 4, Fig. 3, App. real-data tables, alpha table | `exp5_real.py` -> `make_rest.py cifar cifar_other nli alpha merged <model>`, `alpha_table.py` |
| Fig. 4, App. shift table | `exp5b_shift.py` -> `make_rest.py shift` |
| App. E1 tables | `exp1_calibration.py` -> `make_rest.py e1` |

## Notes on honesty
See Appendix D ("Deviations and honest notes") of the paper: data-source deviations (HF mirror of CIFAR-10), the small accuracy gap of the pretrained
models relative to the repository's reported numbers, superseded first runs, and which experiments were not done.
