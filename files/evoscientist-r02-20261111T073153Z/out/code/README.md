# Evaluating conformal prediction regions for compositional (sum-to-one) outputs

Paper: `paper/main.pdf` (ICML 2026 template, LaTeX source in `paper/`; rebuild with `cd paper && bash build.sh`).
Everything reported in the paper is produced by the scripts below; every number in the paper's tables and
figures comes from `results/*.csv` written by these scripts.

## Layout
- `code/compconf.py` – library: scores (l2, TV, linf, Hellinger, KL, Aitchison, Mahalanobis-ilr, l2/sigma-hat), split / Mondrian
  conformal calibration, soft-label softmax regression, data-generating processes, evaluation (coverage, sizes, group coverage).
- `code/run_theory.py` – Prop. 1 (Beta law, one-run evaluation noise), Prop. 2 (K=2 closed form + simulation), Prop. 3 (zero-replacement slope).
- `code/run_synth.py {main|predq|eps} R nproc` – synthetic grids (main grid 36 cells x R; predictor-quality grid; epsilon grid).
- `code/run_cv.py R nproc` – split vs 5-fold cross-conformal at equal labelled budget.
- `code/prepare_cifar.py`, `code/predict_cifar_pretrained.py`, `code/run_cifar10h.py R nproc` – CIFAR-10H experiment.
- `code/verify_cifar_mirror.py` – checks the Hugging Face CIFAR-10 mirror against the official tarball.
- `code/analyze_synth.py`, `code/analyze_theory.py`, `code/analyze_aux.py`, `code/analyze_common.py` – tables, figures, summary CSVs.
- `results/` – raw per-replicate CSVs (`synth_*.csv`, `cifar10h.csv`, `theory_*.csv`), summaries (`summary_*.csv/json`), logs.
- `figures/`, `tables/` – generated figures (PDF) and LaTeX tables; `paper/figures`, `paper/tables` are copies used to build the paper.

## Environment
Python 3.11; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, matplotlib 3.11.2, pillow 13.0.0, pyarrow 26.0.1,
torch 2.15.0+cpu and torchvision 0.29.2+cpu (inference only; `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`).
LaTeX: TeX Live 2025 (pdflatex, bibtex). No GPU, no paid API. (See `requirements.txt`.)

## Data (versions, licences)
- CIFAR-10 (Krizhevsky 2009): official tarball md5 `c58f30108f718f92721af3b95e74349a`; no licence stated on the page (citation requested).
  We used the Hugging Face mirror `uoft-cs/cifar10` (parquet files `train-00000-of-00001.parquet` md5 `7170dcdaf6355deedaa01d9915ae0d31`,
  `test-00000-of-00001.parquet` md5 `a52165db3ae649545cf55cf1791cd12d`) because the official server was slow, and verified with
  `code/verify_cifar_mirror.py` (log: `results/log_verify_cifar_mirror.txt`) that test images/labels are identical and in the same order and
  that training images are identical as a set. Only the 10000 test images are used by our experiments.
- CIFAR-10H (Peterson et al. 2019): `cifar10h-probs.npy` (md5 `7b41f73eee90fdefc73bfc820ab29ba8`) from the authors' GitHub repository
  (https://github.com/jcpeterson/cifar-10h); the repository has no LICENSE file; used for research only, not redistributed here.
  Test order matches CIFAR-10 (argmax of human proportions = true label for 99.2% of images).
- Pretrained network: `cifar10_resnet20` from https://github.com/chenyaofo/pytorch-cifar-models via `torch.hub` (trained on the CIFAR-10
  training set only; 92.12% test accuracy in our run). Logits md5 `79cdfad1f87b37329711355e9d5b9ea6`.
- Synthetic data are generated on the fly (`compconf.gen_data`).

## Exact commands (run from the repository root; wall-clock observed on a heavily shared 40-core CPU machine, 30 worker processes)
```bash
mkdir -p data results figures tables
# --- data
curl -L -o data/cifar10h-probs.npy https://raw.githubusercontent.com/jcpeterson/cifar-10h/master/data/cifar10h-probs.npy
curl -L -o data/cifar10_test.parquet  https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/test-00000-of-00001.parquet
curl -L -o data/cifar10_train.parquet https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/train-00000-of-00001.parquet
python code/prepare_cifar.py                        # ~1 min   -> data/cifar10_uint8.npz
python code/predict_cifar_pretrained.py cifar10_resnet20   # ~1 min -> data/cifar_test_logits.npy
# --- experiments (single-threaded BLAS per worker)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python code/run_theory.py                           # ~10 min  -> results/theory_*.csv, beta_covs_*.npy
python code/run_synth.py main 200 30                # 2030 s   -> results/synth_main.csv   (36 cells x 200 replicates)
python code/run_synth.py predq 200 30               # 1390 s   -> results/synth_predq.csv
python code/run_synth.py eps 200 30                 #  270 s   -> results/synth_eps.csv
python code/run_cv.py 100 20                        #  430 s   -> results/synth_cv.csv
python code/run_cifar10h.py 100 20                  #  140-300 s -> results/cifar10h.csv, cifar10h_info.csv
# --- analysis, figures, tables (< 5 min)
python code/analyze_synth.py
python code/analyze_aux.py
python code/analyze_theory.py                       # needs synth_eps.csv and cifar10h.csv for Fig. 4b,c
# --- paper
cp -r figures tables paper/ && cd paper && bash build.sh
```
Total compute is about 3 CPU-hours for the experiments (the wall-clock above is inflated by machine load).

## Seeds
Synthetic runs: `np.random.SeedSequence([20261111, config_id, replicate])` (config ids: main 0-35, predq 1000+, eps 2000+);
cross-conformal: `[20261113, config_id, replicate]`; CIFAR-10H: `[20261112, n_cal, replicate]`; theory scripts: seeds 1, 2, 3.
Runs are deterministic given these seeds and the library versions above (multiprocessing order does not matter).

## Which script produces which table/figure of the paper
| Paper item | Produced by |
| --- | --- |
| Fig. 1 (Beta law, one-run noise, K=2 conditional coverage), Tables 4 (Beta), 5 (K=2 gaps), 6 (zero slope) | `run_theory.py` -> `analyze_theory.py` |
| Table 1 (main synthetic), Fig. 2 (relative size), Fig. 3 (entropy-conditional coverage), Tables validity / measure agreement / paired / full grids (appendix) | `run_synth.py main` -> `analyze_synth.py` |
| Predictor-quality table (appendix) | `run_synth.py predq` -> `analyze_aux.py` |
| Fig. 4a | `run_theory.py` (zero part) -> `analyze_theory.py` |
| Fig. 4b | `run_synth.py eps` -> `analyze_theory.py` |
| Cross-conformal table (appendix) | `run_cv.py` -> `analyze_aux.py` |
| Table 2 (CIFAR-10H), Fig. 4c, CIFAR appendix tables | `run_cifar10h.py` -> `analyze_aux.py`, `analyze_theory.py` |

## Honest notes
- A first attempt to train a ResNet-9-style CNN on CPU was abandoned (machine too loaded, no usable output); the pretrained ResNet-20 is used.
- CIFAR-10H uses 100 replicates (synthetic: 200; cross-conformal: 100). CIFAR-10H replicates are random subsets of a fixed 10000-image pool.
- Template: ICML 2026 (NeurIPS 2026 style files were not available at the time); ICML 2026 does not mandate a checklist, a short one is in Appendix D.
- Uniform-measure size is computed for K <= 5 only.
- Literature access: only the starter list and a few well-known papers verified by identifier/exact title via the arXiv API / Crossref.
  The excluded published paper (and pages citing it) was neither searched for nor, to our knowledge, encountered.
- The shell tool in the authoring environment occasionally corrupted a ` / ` division operator when files were written; all code was checked to compile
  and the corrupted lines were fixed before any result was produced from them (`python -m py_compile code/*.py` passes).
