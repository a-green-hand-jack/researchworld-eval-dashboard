# Reproduction and evidence scope

The manuscript reports the existing frozen final evaluation in `paper_data.json`.
Manuscript preparation only derives figures, tables, and summaries; it does not
rerun the evaluator, fit scientific models, or create new performance observations.

## Recorded scientific environment

The frozen manifest records Linux x86_64, CPython 3.12 and NumPy 2.1.3, CPU-only,
single-threaded BLAS, evaluator allowance six cores/10 GiB and learner allowance
two cores/6 GiB. These are declared evaluation settings, not method-only resource
measurements. Data are original task-owned synthetic logistic-normal-v1 examples;
there are no external data downloads or account requirements. The generator,
parameters, partitions, and reference probes are inspectable in
`source_evidence/evaluate_final.py:604` and `source_evidence/evaluate_final.py:716`.

Final seeds: 1009, 2003, 3001, 4001, 5003, 6007. Each evaluates H3, H10, B3, B10,
S3, S10 at nominal coverage 0.95 and 0.90. Center/scale/calibration/test sizes are
1024/1024/512/2048. All numerical claims derive from final records, never global
memory. No external real dataset is evaluated.

## Rebuild manuscript artifacts

Install plotting tools outside the manuscript workspace:

```sh
python -m venv --system-site-packages /tmp/paper-tools
/tmp/paper-tools/bin/pip install numpy matplotlib pillow
/tmp/paper-tools/bin/python build_figures.py
python build_claims.py
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python .codex/skills/write-paper-standalone/scripts/validate_claims.py --paper-data paper_data.json --references references_provenance.json --bib references.bib --claims claims_grounding.json --paper-dir .
python .codex/skills/validate-paper/scripts/validate_figures.py --paper-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
```

Figure/table generation takes seconds on a CPU; compilation typically takes
less than a minute, excluding tool installation. These are workflow expectations,
not benchmarked scientific runtimes. Exact manuscript-building package versions
are recorded in `manuscript_environment.txt`.

`build_figures.py` writes both vector PDF and 300-DPI PNG for the coverage and
reference-mass figures, plus `analysis_summary.json` and both supplementary
table inputs. The aggregate main table and result prose use those same arithmetic
summaries. Bootstrap intervals are read from the stored evaluator results; no new
bootstrap analysis is substituted. The conceptual overview is rendered by the
parent orchestration step: its guarded placeholder is not a measured result and
must not overwrite a completed render. `figure_manifest.json` records ownership.
The manuscript references PDF for quantitative figures.

## Scientific execution interface

A portable copy of the selected learner, exact evaluator, pinned dependency file,
and frozen final raw resources is included under `reproduction/`. On a compatible
Linux x86_64 host with Landlock ABI 4 and seccomp BPF, the original native runner
can be invoked as follows. This is an unexecuted reproduction command, not a
claim that a second scientific evaluation was performed during writing:

```sh
python3.12 -m venv /tmp/composition-study
/tmp/composition-study/bin/pip install -r reproduction/requirements.txt
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /tmp/composition-study/bin/python reproduction/evaluate_final.py \
  --program_path reproduction/scale_model/src/program.py \
  --results_dir /tmp/composition-study-results
```

The evaluator declares a 2,400-second wall budget. A compatible host and exact
NumPy version matter for bitwise raw-generator checks. Scientific runtime has not
been independently timed here; stored per-seed durations include evaluator work.
The CLI accepts a source-file path, not its enclosing directory. Do not set a
broker socket for the native source-file invocation.

The copied `source_evidence/scale_learner.py` exposes the original finite-JSON
RPC interface with reset, fit and predict operations, array encoding, and positive
scale outputs. `source_evidence/program_spec.toml` identifies the script entrypoint.
The evaluator owns calibration, the center and all region construction. The
original task tree is also accessible as `task/` in this workspace. Native
scientific execution requires the Linux sandbox facilities recorded in the task
manifest; no scientific runtime test of the packaged invocation was performed.
The copied evaluator's file digest matches the stored final evaluator identifier.
That byte-level match does not establish a match for the complete selected source
tree, and no evaluator rerun was performed during writing. Consequently this
submission does not claim independently regenerated raw scientific measurements
or a newly verified exact match to the frozen selected-source-tree hash.

## Literature safety and consultation

The initial retrieved bibliography contained unrelated results and was replaced
with exactly identified foundational sources. `prepare_references.py` accesses
Crossref by exact DOI, arXiv by exact known identifier, and the known JMLR
quantile-forest landing page. `consult_abstracts.py` accesses OpenAlex by exact DOI
only. `literature_evidence/` stores the consulted metadata and abstracts; provenance
records explicitly distinguish abstract consultation from metadata-only access.
No citation networks, broad composition/conformal searches, or prohibited related
work were accessed. No accidental prohibited-literature encounter was documented.
References with unavailable abstract text support only narrow bibliographic
background statements, not detailed claims about uninspected experimental results.

## Missing evidence and qualification

The final qualification record is completed/qualified, with its declared checks
satisfied. That status is not a validity or generalization theorem. Additional gate
diagnostics, selected-component labels, and a matched repeated-final original
ridge-scale comparator are unavailable. The latent-count extension was not
implemented; the interaction-tree extension has no measured performance and an
unknown failure cause. Neither is a numerical ablation or a measured loss.
Stored episode durations include evaluator overhead and are not learner-only
runtime claims. Six seeds leave bootstrap uncertainty imprecise. Reference mass
is not intrinsic volume. Shift results are empirical, and fixed-group diagnostics
do not establish conditional validity. The manuscript, claim map and evidence
sidecars preserve these limitations.
