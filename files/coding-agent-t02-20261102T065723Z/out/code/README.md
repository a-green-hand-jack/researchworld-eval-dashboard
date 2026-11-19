# Width and delayed generalization on modular tasks

This directory contains an autonomous empirical research study. The paper uses the **official ICLR 2027 template**, the latest available edition at execution (2026-11-02). It is a research artifact, not a conference submission. The paper explicitly discloses AI involvement and the absence of human review.

## Deliverables

- `paper/main.pdf`: complete compiled paper.
- `paper/main.tex`, `paper/references.bib`: LaTeX and bibliography.
- `src/`: all training, batching, analysis, audit, and result-writing code.
- `configs/main.json`, `configs/secondary.json`, `configs/features.json`, `configs/replication.json`: exact formal run specifications.
- `results/*.json`: every completed raw training history; `.pt` files contain final weights, split indices, and configuration.
- `paper/generated/`: machine-readable summaries, per-run CSV, audit report, empirical LaTeX tables and text.
- `paper/figures/`: vector PDF figures generated from actual measurements.
- `RESEARCH_LOG.md`: decision history, pilots, numerical amendment, and literature-access restrictions.
- `references/`: directly accessed starter papers and official template/instruction snapshots. No broad literature search or citation following was performed.

## Environment

Linux, CPython 3.11.2, CPU PyTorch 2.15.0+cpu. Exact installed versions are in `requirements-lock.txt`; observed CPU model, operating system, and package versions are in `environment.json`. The container exposes 40 logical CPUs but the cgroup quota is four CPU cores. Each training process uses one intra-op and one inter-op thread. The actual study used four-worker main/control batches and two-worker exploratory/replication batches, with up to six simultaneous training processes sharing the fixed four-core quota. The sequential commands below use four workers at a time and reproduce the same numerical experiments. No GPU or paid API is used.

Create the environment (network access is needed only to install software):

```bash
cd /work
uv venv .venv --python python3.11
uv pip install --python .venv/bin/python torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -r requirements-lock.txt --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match
```

`pdflatex` and `bibtex` are needed for compilation. The style and bibliography style are included unmodified. No OpenAI API, model download, external dataset, or account is needed.

## Expected runtime and completed checks

The completed 255-run study used **2.54 measured process CPU hours** for training and evaluation, excluding setup, interpreter startup, pilots, and analysis. Allow roughly **one hour on a comparable four-core CPU** for a fresh full study; this is a planning estimate, and raw per-run CPU/wall times are included. Regenerating analysis and the paper from the included results takes about a minute. The final PDF has **8 main-text pages, 12 pages total**, within ICLR 2027's 9-page main-text limit. All 255 checkpoint/split/numerical audits passed, and the included style files were verified byte-for-byte against the archived official ZIP.

## Data and randomness

Training data are generated in memory by `src/train.py`. There is no downloaded data version: dataset version is the arithmetic formula, prime, operation, fraction, and seed specified in each run. All ordered pairs are generated in lexicographic order. Arithmetic labels are computed exactly before conversion to the classifier input. A uniformly shuffled subset of `floor(fraction*p*p)` pairs is used for training and its complement is held out.

Grid/control model seeds are 10, 11, 12, 13, 14. An independent ten-pair replication uses seeds 20–29. Dataset permutations use `100000 + seed`; independent random labels use `200000 + seed`. Pilot runs use seed 0. Splits are paired across widths, decay strengths, activations, and operations for a fixed prime, fraction, and seed. Final checkpoint files store the exact split indices. One seed varies initialization and split together; uncertainty is across these paired experimental units.

## Reproduce

From `/work`, run all formal experiments:

```bash
.venv/bin/python src/batch.py configs/main.json --jobs 4
.venv/bin/python src/batch.py configs/secondary.json --jobs 4
.venv/bin/python src/batch.py configs/features.json --jobs 4
.venv/bin/python src/batch.py configs/replication.json --jobs 4
.venv/bin/python src/construct_circuit.py
.venv/bin/python src/analyze.py
.venv/bin/python src/write_results.py
.venv/bin/python src/audit.py
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
cd /work
.venv/bin/python src/check_paper.py
```

**Important:** batching skips an existing result JSON. To train afresh, move the existing `results/` directory aside before running the commands and create a new empty `results/` directory. Checkpoint files are written after the JSON, so do not launch analysis while training is active. Each run always executes its full configured horizon; a missing generalization event does not trigger stopping or exclusion. All formal runs use float32 with `torch.set_flush_denormal(True)`; the earlier pilots do not. This numerical amendment and interrupted pre-amendment work are disclosed in the research log.

A single reference run can be reproduced separately:

```bash
.venv/bin/python src/train.py --p 31 --fraction .5 --width 256 --seed 10 --decay 1 --steps 30000 --out results/example.json
```

The analysis reads only the manifests, so an extra example run is not silently added to the paper. To regenerate figures and the PDF without retraining, start with `src/analyze.py` in the reproduction commands above. The original template ZIP is in `references/iclr-2027-style-files.zip`, downloaded from the link in the official ICLR 2027 author guidelines; the unmodified files are in `paper/template/`.

## Figure and table provenance

All plotted data are measured runs. Every manuscript figure, table, primary contrast, and threshold-sensitivity summary is made by `src/analyze.py`:

| Paper item | Generated artifact | Raw input |
|---|---|---|
| Figure 1, train/held-out learning curves | `paper/figures/curves.pdf` | Main grid, decay 1, all widths, all five seeds |
| Figure 2, width–decay map | `paper/figures/grid.pdf` | All 100 main runs |
| Figure 3, symmetry energy and norm | `paper/figures/diagnostics.pdf` | Main grid, decay 1, widths 64/256, all five seeds |
| Appendix Figure 4, feature direction intervention | `paper/figures/feature_freezing.pdf` | Main and exploratory runs, width 256, all five seeds |
| Table 1, full factorial outcomes | `paper/generated/main_table.tex` | All 100 main runs |
| Table 2, controls | `paper/generated/secondary_table.tex` | Main, secondary, and exploratory runs, widths 64/256 |
| Abstract and primary quantities | `paper/generated/numbers.tex` | Paired width 64/256 results at decay 1 |
| Additional details and empirical prose | `paper/generated/*_text.tex` | `paper/generated/summary.json`, through `src/write_results.py` |

`paper/generated/per_run.csv` gives individual event times, censoring, accuracy, structure, counts, CPU time, and file paths for every distinct formal run. `summary.json` includes exact seed-bootstrap intervals, exact binomial intervals for event proportions, alternative accuracy thresholds, and a matched width-times-steps budget comparison. For the five-seed cells, bootstrap resamples are all 3,125 ordered resamples of five seed pairs, with equal probability. The independent ten-pair replication uses 100,000 paired resamples with analysis RNG seed 20261102. Both primary cohorts also report exact two-sided sign tests; the cohorts are kept separate. Shaded learning-curve bands show the **minimum and maximum**, not confidence intervals.

The predefined formal design has 100 main-grid runs and 115 distinct controls; a later, explicitly exploratory feature-direction intervention adds 20 runs, and an independent ten-pair replication adds 20 more, for 255 distinct formal runs. The intervention projects each first-layer row back onto a fixed nonnegative ray after every AdamW update after the specified freeze step. Row magnitudes (including disabling a feature at zero), output weights, and decay remain active; it is not a claim to freeze every aspect of the optimizer. The audit checks exact agreement with the reference history up to the intervention and preservation of directions afterward.

## Interpretation and audit

Generalization requires held-out accuracy >=95% at three consecutive evaluations, spaced by 100 steps. The event time is the first of these checkpoints. Since training ends at 30,000, the common event-ascertainment horizon is 29,800. Non-events enter restricted waiting-time means at 29,800; these are not claimed to have generalized then. A delayed event additionally requires generalization time >= twice fitting time and held-out accuracy <=50% at the training event. Training events use a sustained 99% threshold. All thresholds and sensitivity analyses are described in the paper.

`src/audit.py` independently reloads every final model and verifies its held-out accuracy against the raw JSON, all train/test partition properties, matched seeds, parameter counts, event logic, numerical finiteness, and the addition projection's orthogonality. It does not certify the proposed scientific explanation or remove the limitations of five seeds.

The explicit oracle circuits in `src/construct_circuit.py` prove representability of addition within a bias-free ReLU network of width `2*p-1` and a square network of width 8. The script exhaustively evaluates both at both primes and writes `paper/generated/expressivity.json`. They directly encode the target formula, are not trained models, and are not counted as learning successes. In particular, width 64 at prime 31 can represent a correct ReLU solution even when the optimizer does not find one within the horizon. This says nothing about its norm efficiency.

## Pilots, failures, and access restrictions

The 20 pilot runs are retained under `results/pilot*`; the 16 follow-up pilot specifications are in `pilot_manifest.json`. The first four pilot commands are documented in `RESEARCH_LOG.md` and can also be recovered from their JSON configurations. Completed results superseded by the numerical amendment are retained under `results/superseded_pre_ftz/`. Interrupted runs and all formal failures to reach the event threshold are reported, not converted into successes.

Literature downloads were limited to the seven supplied starter papers actually cited. Official ICLR administrative pages and template files were also accessed. No search for the prohibited work, author/title inference, scholarly search, downstream citation browsing, or related-work page access was attempted. No known accidental encounter occurred. The restricted literature coverage is a limitation of the novelty assessment.
