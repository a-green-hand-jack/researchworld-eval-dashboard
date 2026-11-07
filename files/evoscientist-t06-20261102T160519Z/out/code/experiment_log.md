# Experiment log and deviations

## Intake / protocol
- 2026-11-02: /work/todos.md written before data parsing and BT fitting. Direct implementation by main agent, no code-agent delegation. Source-bounded literature reading only; no open search.
- Allowed NeurIPS2026 official style archive downloaded and preserved unmodified.

## Stage 1
- Installed requests, pyarrow, pytest, pypdf, threadpoolctl. Initial dependency probe failed because requests absent; resolved by installation.
- All supplied data hashes verified. Arena label one-hot validation passes; 64 participants all pass >=100 appearance inclusion, no votes removed.
- First parser run stopped rather than guessing on GPT label `tie (inconsistent)`. Actual data: 380 inconsistent plus 220 ordinary ties. Explicitly map both to .5; no ties eligible for binary reversal.
- GPT has one exported pair-result row per ordered question/model-pair/turn cell, not exposed separate reciprocal calls. Deviates from provisional plan wording. Edit unit is an exported result, not underlying GPT API call.
- Six baseline unit tests pass. Newton derivatives and canonical orientation checked. NBA includes regular season and playoffs in each year_id 2013,2014,2015; no cross-season pooled stationary model.

## Stage 2 / first run
- Command: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python src/run.py --repeats 100 --bootstrap 200
- Initial six primary witnesses found, all independently reconstructed from raw row IDs by local audit. This is not a combinatorial minimum certificate.
- Main run ~42 seconds as observed process elapsed (precise times in overwritten corrected runtime artifacts; initial elapsed not used as paper benchmark).

## Independent code audit / corrections
- /work/artifacts/code_audit.md found an INVALID planned Arena size control: top6 pool has 3222 rows <3355. Initial code used min(pool,3355), silently selecting whole pool on all 20 seeds. These pseudo-replicates were NOT used as paper evidence. Corrected to N=2400 (the GPT release size), strictly below pool, with assertions and SHA256 selected-row-set identities. This is a descriptive size/cohort control, not matched model identities or margins.
- Secondary argmax-based top1 metric counted exact ties as winner changes. Replaced by strict excess of 1e-7; added regression test. Primary runner-up crossing metric was already strict and unaffected.
- Added explicit statuses for first30 bootstrap witness attempts; counts condition on positive original-target margins and refer to resampled slots (including repeated original IDs), not physical original votes. These auxiliary budgets will not be promoted as confidence intervals for minimum attacks.
- Bootstrap is empirical row/question-cluster resampling, NOT conditional fixed-schedule outcome generation. Original targets remain fixed; selected-target percentile bands are descriptive, not post-selection-valid population intervals. Stage1 provisional bootstrap alternatives resolved explicitly here.
- Matched MT uses one sampled human row per exact ordered cell and the matching GPT exported row, not soft-label cell averaging. This preserves binary-row units. The ordered subset is 1232 shared cells; reversed presentation human cells not in exact shared support are excluded. Twenty human seeds change chosen judge only; GPT is run once, not pseudo-replicated.
- Reselecting target names in ridge/tie/home ablations is labeled explicitly. Additional fixed-target ablations and deletion/adaptive baselines are being run separately.
- Tightened return gradient gate from 1e-6 to 1e-7; observed gradients were already <1e-8.

## Planned supplementary checks
- Exact same-estimator deletion influence/refit baseline, not a reproduction of published filtering/unregularized analysis; deleting versus flipping are distinct interventions.
- Sequential relinearized flip selection as baseline; no assumption that adaptive is globally optimal.
- Keep baseline target identities fixed for estimator ablations; if already reversed, label k=0 with status instead of manufacturing a positive-margin witness.
