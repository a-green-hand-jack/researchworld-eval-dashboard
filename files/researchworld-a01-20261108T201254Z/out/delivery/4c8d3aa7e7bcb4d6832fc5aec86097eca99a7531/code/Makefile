# Reproduction entrypoint. `make data` needs network; every other target is offline and CPU-only.
# Seeds: all drivers default to --seed 0 (rank-stratified target sample, Monte-Carlo draws); bootstrap B=1000, seed 0.
# `bash reproduce.sh` does the same without make. `make reproduce` (offline, from the delivered tree) restores the per-instance results (`unpack`), regenerates the one large file
# (`job_ollb_powmeans`), re-runs the analysis and theory checks and compares every output with results/MANIFEST.json (`verify`);
# measured time: see README section 5. `make experiments` re-runs every solver job from data/processed/ (3.25 CPU-h of recorded solver CPU
# plus the unrecorded robustness replicates, ~5 h of summed wall time on a shared host; the jobs are independent: `make -j8 experiments`).
PY=python3
CAPS=ceil front0 front2 gain5 gain10 gain20 emp95 emp99
ORD_CAPS=ceil emp95 gain10 front2   # the four main caps (plan section 8); plurality runs on all eight caps (cheap)
.PHONY: all data tests experiments analysis theory manifest unpack pack verify reproduce
all: tests experiments analysis theory manifest

data:
	$(PY) src/fetch_helm.py data/raw/helm_v1.13.0
	$(PY) src/fetch_ollb.py data/raw/ollb_contents.parquet                       # pinned dataset revision 9c09a7ca...
	$(PY) src/build_data.py data/raw/ollb_contents.parquet data/raw/helm_v1.13.0 data/processed
	$(PY) src/ollb_items.py data/processed/ollb_noise.json
	$(PY) src/build_dup_variants.py data/raw/ollb_contents.parquet data/processed         # duplicate-name rule variants (request #6.3a)
	$(PY) src/ollb_items_check.py results/analysis/ollb_item_counts_check.csv 60            # item counts across 60 models (network, #6.3b)
	$(PY) src/helm_subject_sizes.py data/raw/helm_v1.13.0 results/analysis/helm_subject_sizes.csv   # (#6.4a)

tests:
	$(PY) -m pytest -q tests

JOBS = $(addprefix job_ollb_score_,$(CAPS)) $(foreach r,borda condorcet,$(addprefix job_ollb_$(r)_,$(ORD_CAPS))) \
       job_helm_main job_helm_trimmed job_helm_powmeans job_helm_robust job_ollb_plurality job_ollb_powmeans job_ollb_variants job_ollb_robust job_ollb_eps \
       $(addprefix job_capcomp_,emp95_nochat emp95_nochatname emp95_chat empfrac95 empfrac95_nochat head0.25) $(addprefix job_dup_,first latest worst)
experiments: $(JOBS)
job_ollb_score_%: ; bash jobs/ollb_score_cap.sh $*
job_ollb_borda_%: ; bash jobs/ollb_ordinal.sh borda $*
job_ollb_condorcet_%: ; bash jobs/ollb_ordinal.sh condorcet $*
job_helm_main: ; bash jobs/helm_main.sh
job_helm_trimmed: ; bash jobs/helm_trimmed.sh
job_helm_powmeans: ; bash jobs/helm_powmeans_weighted.sh
job_helm_robust: ; bash jobs/helm_robust.sh
job_ollb_plurality: ; bash jobs/ollb_plurality.sh
job_ollb_powmeans: ; bash jobs/ollb_powmeans_weighted.sh
job_ollb_variants: ; bash jobs/ollb_variants.sh
job_ollb_robust: ; bash jobs/ollb_robust.sh
job_ollb_eps: ; bash jobs/ollb_eps.sh
job_capcomp_%: ; bash jobs/ollb_cap_composition.sh $*
job_dup_%: ; bash jobs/ollb_dup_rule.sh $*

analysis:
	$(PY) src/analyze.py --B 1000 --seed 0
	$(PY) src/analyze_robust.py --B 1000 --seed 0
	$(PY) src/analyze_fits.py
	$(PY) src/analyze_capcomp.py
	$(PY) src/analyze_dup_rule.py
	$(PY) src/score_cap_defence.py

theory:
	$(PY) src/theory_checks.py

manifest:
	$(PY) src/manifest.py

pack:
	$(PY) src/pack_instances.py pack
unpack:
	$(PY) src/pack_instances.py unpack
verify:
	$(PY) src/verify_manifest.py
reproduce: unpack job_ollb_powmeans analysis theory verify
