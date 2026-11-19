# Claim–evidence memo: single-run attribution reliability

**Scope.** A bounded audit of fixed probability-output, grouped-feature, finite empirical interventional games—not causal/population truth, clinical utility, all SHAP implementations, or training-population reliability. ACSIncome10 and Pima8 have exact enumerated references; **German20 has qualified approximate references**. No dataset-pooled headline mean, new estimator, empirical Bayes, significance test, or novelty-priority claim is warranted.

**Evidence units and uncertainty.** Full scheduled Tier A counts (with the RNG deviation below): 648 point-fit tasks, 54 cells, 248,832 main vectors; each cell has 72 distinct selected record IDs × 64 explainer runs = **4,608 runs**. The same 72 IDs recur across model classes; these are not 648 independent people. Three fixed nominal seed strata contain 24 IDs each. Learned-state audit reports **LR=1, HGB=1, RF=3 distinct fits per dataset**, not three independent LR/HGB fits. Reported 95% CIs are descriptive 2,000-draw, seed-stratified **point-cluster** percentile intervals carrying complete 64-run records—not run/pair/patient-independent intervals, training-seed inference, or simultaneous bands. Worst-case within-point run MCSE is 0.0625. Boundary intervals can degenerate; bounded-cluster Hoeffding sensitivities remain broad (e.g. Pima/LR/kernel/P16: bootstrap 98.24–100%, Hoeffding 67.81–100%). No multiplicity-adjusted significance claim is made; future tests need a prospectively fixed family and Holm correction.

**Definitions.** For reference r, D=max(||r||₁,0.02); error E=||estimate−r||₁/D. Primary success requires exact magnitude-ranked top-three set, E≤0.20, and no wrong sign on any |r_j|≥0.02; estimated numerical zero is wrong for a material feature. Top-one is identity, not ordering of the entire top three. Normalized mass regret is lost reference absolute top-three mass divided by max(reference top-three mass,0.02). Ties use the stored feature-order/rounded-magnitude rule. No reference L1 floor binds and no material set is empty in any of the 648 tasks. Thresholds and normalization are protocol choices, **not calibrated substantive-risk tolerances**.

## 1. Supported: increasing requests greatly improves these estimators; low-budget performance is method-dependent

`kernel` is the specified sampled, efficiency-constrained minimum-norm SVD variant; `perm` is antithetic permutation averaging. Neither represents every library implementation. At P=1/4/16, coalition requests M=2+2(d−1)P and charged B=16 model rows are:

| Dataset/reference | M | Charged rows |
|---|---|---|
| ACS / exact | 20 / 74 / 290 | 320 / 1,184 / 4,640 |
| Pima / exact | 16 / 58 / 226 | 256 / 928 / 3,616 |
| German / approximate | 40 / 154 / 610 | 640 / 2,464 / 9,760 |

**All primary cells.** Entries are `successful runs out of 4,608; percent [95% CI]`. Exact row keys are dataset/model/method/P in `cell_summary.csv`; counts and derived components are in `findings_evidence/cell_evidence.csv`.

| Dataset/model | Method | P=1 | P=4 | P=16 |
|---|---|---|---|---|
| ACS/HGB | kernel | 1289; 27.97 [24.96,30.88] | 4315; 93.64 [90.91,96.05] | 4523; 98.16 [96.31,99.48] |
| ACS/HGB | perm | 3785; 82.14 [77.88,86.33] | 4254; 92.32 [89.21,95.05] | 4474; 97.09 [95.25,98.63] |
| ACS/LR | kernel | 1397; 30.32 [27.32,33.07] | 4364; 94.70 [91.82,97.24] | 4507; 97.81 [95.72,99.41] |
| ACS/LR | perm | 4005; 86.91 [82.70,90.63] | 4346; 94.31 [91.34,96.83] | 4491; 97.46 [95.46,99.07] |
| ACS/RF | kernel | 2076; 45.05 [43.08,46.90] | 4517; 98.03 [96.05,99.57] | 4563; 99.02 [97.59,100.00] |
| ACS/RF | perm | 4389; 95.25 [92.56,97.44] | 4510; 97.87 [95.90,99.41] | 4547; 98.68 [97.05,99.85] |
| Pima/HGB | kernel | 827; 17.95 [15.54,20.42] | 4058; 88.06 [83.79,91.91] | 4365; 94.73 [91.69,97.35] |
| Pima/HGB | perm | 2813; 61.05 [54.99,66.95] | 3966; 86.07 [81.45,90.28] | 4318; 93.71 [90.26,96.77] |
| Pima/LR | kernel | 1826; 39.63 [37.43,41.75] | 4513; 97.94 [96.03,99.33] | 4580; 99.39 [98.24,100.00] |
| Pima/LR | perm | 4223; 91.64 [87.74,95.03] | 4455; 96.68 [94.21,98.57] | 4557; 98.89 [97.48,99.76] |
| Pima/RF | kernel | 1603; 34.79 [32.10,37.39] | 4377; 94.99 [92.30,97.33] | 4535; 98.42 [97.03,99.57] |
| Pima/RF | perm | 3985; 86.48 [82.18,90.23] | 4344; 94.27 [91.15,96.94] | 4494; 97.53 [95.59,99.05] |
| German/HGB (approx.) | kernel | 116; 2.52 [1.82,3.34] | 3827; 83.05 [78.17,87.72] | 4238; 91.97 [88.28,95.23] |
| German/HGB (approx.) | perm | 2522; 54.73 [48.78,60.76] | 3676; 79.77 [75.48,84.07] | 4106; 89.11 [85.37,92.73] |
| German/LR (approx.) | kernel | 1304; 28.30 [25.28,31.36] | 4378; 95.01 [92.10,97.35] | 4508; 97.83 [96.16,99.18] |
| German/LR (approx.) | perm | 3906; 84.77 [79.97,88.98] | 4249; 92.21 [88.58,95.14] | 4468; 96.96 [95.03,98.52] |
| German/RF (approx.) | kernel | 427; 9.27 [7.47,11.07] | 4237; 91.95 [88.87,95.01] | 4456; 96.70 [94.51,98.70] |
| German/RF (approx.) | perm | 3501; 75.98 [71.11,80.84] | 4099; 88.95 [85.44,92.56] | 4397; 95.42 [92.92,97.74] |

Example paired effect sizes, **not tests**: permutation-minus-kernel at P1 is +54.17 percentage points [51.30,56.95] for ACS/HGB and +43.10 [38.74,47.22] for Pima/HGB. At P16 these differences reverse to −1.06 [−1.87,−0.35] and −1.02 [−2.15,−0.04] pp. Full contrasts are saved; no overall winner or universal safe budget follows. P1 kernel rank deficiency is 79.30/78.71/80.03% for ACS HGB/LR/RF and 77.11/76.56/76.74% for Pima; all P4/P16 kernel cells have zero observed rank deficiency. This supports a design-identifiability limitation, not a numerical blow-up diagnosis for the main SVD solver.

**Components matter.** Compact HGB diagnostics below are not asserted representative; all models/components and their CIs remain in the evidence table. At P1:

| Dataset | Method | Mean E [95% CI] | Top-three / top-one / sign-correct (%) |
|---|---|---|---|
| ACS exact | kernel | .2975 [.2855,.3108] | 45.86 / 84.01 / 80.77 |
| ACS exact | perm | .0894 [.0821,.0972] | 83.44 / 94.90 / 99.76 |
| Pima exact | kernel | .3537 [.3432,.3651] | 39.61 / 78.15 / 70.57 |
| Pima exact | perm | .1447 [.1342,.1565] | 72.22 / 91.21 / 97.31 |
| German approx. | kernel | .6322 [.5898,.6798] | 34.35 / 80.51 / 62.96 |
| German approx. | perm | .1623 [.1530,.1724] | 65.76 / 91.93 / 99.07 |

At P16 **every primary failure in every cell is a top-three mismatch**: all 4,608 runs/cell pass E≤.20 and material signs. HGB mean E falls to ACS .02068/.02164, Pima .02972/.03534, German .04257/.04056 (kernel/perm). High top-one or sign accuracy alone therefore does not establish joint success.

## 2. Supported: agreement can falsely reassure at P1, but the high-budget counterevidence must remain

Within each point, enumerate the 2,016 unordered pairs of 64 runs. A = equal estimated top-three sets. Agreement prevalence = agreeing pairs/all pairs. **False-any** = pairs in A with ≥1 primary failure / agreeing pairs; **false-member** = failed member incidences in A / (2 × agreeing pairs). These are different estimands, not independent-pair binomial proportions. Pool counts with equal scheduled point weights, not undefined per-point ratios. Every observed point has at least one agreeing pair; zero agreement would mean undefined risk.

HGB/P1 row keys in `cell_summary.csv`:

| Dataset/method | Agree / 145,152 pairs (%) | False-any numerator/denominator; % [CI] | False-member numerator/denominator; % [CI] |
|---|---|---|---|
| ACS/kernel | 39,381 (27.13) | 26,046/39,381; 66.14 [62.09,70.32] | 38,302/78,762; 48.63 [44.40,53.23] |
| ACS/perm | 110,707 (76.27) | 8,362/110,707; 7.55 [5.16,10.52] | 14,155/221,414; 6.39 [4.41,8.87] |
| Pima/kernel | 33,519 (23.09) | 27,586/33,519; 82.30 [78.64,85.95] | 44,285/67,038; 66.06 [61.84,70.37] |
| Pima/perm | 92,135 (63.47) | 28,743/92,135; 31.20 [24.83,38.25] | 41,864/184,270; 22.72 [18.13,28.16] |
| German/kernel (approx.) | 26,704 (18.40) | 26,504/26,704; 99.25 [98.70,99.69] | 50,395/53,408; 94.36 [92.35,96.18] |
| German/perm (approx.) | 80,394 (55.39) | 27,269/80,394; 33.92 [27.09,41.72] | 43,440/160,788; 27.02 [21.05,34.00] |

**Counterevidence:** ACS/HGB/P16 kernel false-any is only 723/141,246 = 0.512% [0.020,1.360], and permutation 858/138,462 = 0.620% [0.150,1.261]. Pima/HGB/P16 values are 1,809/134,332 = 1.347% [0.530,2.439] and 2,394/132,816 = 1.802% [0.635,3.433]. Adding sign agreement barely changes the P1 HGB examples (ACS kernel 65.56%, Pima kernel 81.33% versus 66.14/82.30%). Thus agreement is not a certificate, but “agreement is always uninformative” is also unsupported. This retrospective two-run diagnostic is not a validated deployment rule.

## 3. Supported: P16 failures concentrate near ties and often lose very little mass; P1 failures are not merely ties

Gap = (third−fourth reference absolute magnitude)/D; strata are near ≤.02, middle (.02,.10], separated >.10. Per-model point counts (near/middle/separated), retained without exclusions:

| Dataset | HGB | LR | RF |
|---|---|---|---|
| ACS exact | 28/43/1 | 32/38/2 | 30/38/4 |
| Pima exact | 25/40/7 | 19/40/13 | 19/50/3 |
| German approx. | 45/26/1 | 46/26/0 | 37/35/0 |

Pima/HGB/P16 near-stratum success is kernel **1,357/1,600 = 84.81% [78.13,91.31]**, permutation **1,310/1,600 = 81.88% [74.25,89.06]**; all 47 non-near points succeed in all 64 repeats for both methods. Near-stratum mean normalized regret is only .001138/.001486, with mean absolute lost attribution mass .000505/.000634 probability units. In ACS/HGB/P16, 84/85 kernel failures and 132/134 permutation failures are near; mean near regret .000222/.000531. German/HGB/P16 has 370/502 failures (kernel/perm), all near, with near success 87.15% [82.12,91.81] / 82.57% [77.67,87.08]. Small separated strata and degenerate bootstrap intervals are not reliability certificates. Raw gaps/absolute regret are saved in `gap_evidence.csv`; for example Pima/HGB near raw gaps span .000304–.013440.

**Not all failure is harmless tie swapping:** Pima/HGB/kernel/P1 mean normalized regret is .07055 [.06377,.07794] overall; in the separated stratum (n=7), success is only 20.31% [15.17,25.45] and mean regret .10156. Its error and sign components also fail frequently (above).

**Threshold sensitivity**, HGB success percentages at error cutoffs **.10 / .20 / .40**, keeping top-three/sign criteria fixed (`cell_summary.csv`; intervals for each cutoff are supplied there):

| Dataset/method | P1 | P4 | P16 |
|---|---|---|---|
| ACS/kernel | 8.94 / 27.97 / 39.08 | 89.67 / 93.64 / 93.66 | 98.16 / 98.16 / 98.16 |
| ACS/perm | 57.12 / 82.14 / 83.20 | 90.60 / 92.32 / 92.32 | 97.09 / 97.09 / 97.09 |
| Pima/kernel | 4.80 / 17.95 / 29.54 | 77.80 / 88.06 / 88.13 | 94.66 / 94.73 / 94.73 |
| Pima/perm | 21.12 / 61.05 / 70.49 | 73.20 / 86.07 / 86.28 | 93.36 / 93.71 / 93.71 |
| German/kernel (approx.) | .04 / 2.52 / 17.53 | 55.79 / 83.05 / 83.96 | 91.64 / 91.97 / 91.97 |
| German/perm (approx.) | 7.20 / 54.73 / 65.19 | 65.02 / 79.77 / 79.95 | 88.87 / 89.11 / 89.11 |

The P1 severity depends materially on threshold; the large budget effect survives these sensitivities. At P4 the German/HGB ordering reverses at .10 (perm 65.02% versus kernel 55.79%), so even local “winner” language is endpoint-dependent.

## 4. Supported: changing the background moves the target, independently of approximation error

Eight fixed seed-11 points per exact dataset/model; **one shared nested background at each B=4/16/64**, not independent background replicates. Drift is ||r_B−r_16||₁/max(||r_16||₁,.02), averaged once per point, not once per method/budget. No background-sampling CI can be inferred.

| Dataset/model | Mean drift B4 | B16 | B64 |
|---|---|---|---|
| ACS/HGB | 1.00740 | 0 | .21712 |
| ACS/LR | .80706 | 0 | .15237 |
| ACS/RF | .55619 | 0 | .25756 |
| Pima/HGB | .27752 | 0 | .45998 |
| Pima/LR | .19789 | 0 | .49425 |
| Pima/RF | .20466 | 0 | .47666 |

Own-game error remains small at P16: ACS/HGB/kernel mean E for B4/16/64 = .01657/.01624/.01556, while success = 97.27/100/94.34%; Pima/HGB/kernel = .04045/.03389/.03423, success 93.55/95.70/94.53%. Thus lower approximation error need not improve exact-set success. Pima B64 is farther from B16 than B4 is; neither monotonic background “stability” nor optimal B follows from these nested draws. Full P1/4/16 own-game results: `background_own_game.csv`.

## 5. Supported: uncached latency is measured, but cached instrumented CPU is not whole-program or deployment cost

Timing has 540 fresh uncached records: **2 fixed seed-11 points × 5 run seeds per cell**, randomized method order, all nominal coalitions evaluated including duplicates, B16, bounded batching, warm-up/fitting excluded. IQRs below are latency spread, not CIs. All 54 cells are in `uncached_timing.csv`.

HGB CPU milliseconds, `median [Q25,Q75]`, kernel / perm:

| Dataset | P1 | P4 | P16 |
|---|---|---|---|
| ACS | 10.97 [9.75,12.06] / 9.76 [9.10,11.41] | 65.25 [62.95,79.48] / 63.16 [62.28,67.17] | 334.75 [326.04,344.57] / 322.02 [316.35,351.82] |
| Pima | 4.16 [3.49,4.35] / 3.82 [3.67,3.88] | 10.20 [9.45,10.31] / 9.66 [9.57,9.76] | 34.82 [34.68,35.52] / 32.41 [32.12,32.68] |
| German | 9.39 [8.83,9.59] / 8.21 [7.59,8.81] | 32.89 [29.84,33.22] / 31.38 [30.91,32.06] | 157.46 [133.59,180.70] / 191.10 [179.24,195.78] |

No universal speed advantage: German/HGB/P16 reverses the modest advantage seen in its lower budgets. CPU and wall time differ materially (ACS/HGB/kernel/P16 wall median .69416 s versus CPU .33475 s); do not substitute either for the other or generalize this tiny timing subset to deployment.

`resource_summary.json`: **3,039.553 instrumented CPU seconds (0.8443 h)**, including main/reference tasks 2,748.585 s, fitting 61.718 s, pilot 61.684 s, B4 36.498 s, B64 98.358 s, library 15.190 s, timing 17.520 s. Main actual rows 341,334,880 include reference/cache work; aggregate primary/reference/background/pilot actual rows 349,308,960 and nominal main charged rows 658,243,584 are **different scopes**, not a cache speedup ratio. Peak reported main-worker RSS 413,540 KiB is not simultaneous process-tree peak; workspace snapshot 365,991,612 bytes is not final release size. B4/B64 prediction-CPU entries of zero reflect missing subcomponent instrumentation, not zero prediction work. Installation, retrieval, startup, analysis, TeX and the later numerical diagnosis are outside this ledger: it does not certify whole-program 24-CPU-hour compliance.

### German extension and library diagnostics: essential qualifications

- **German reference gate:** 216/216 qualify, 72/72 per model; 2×1,024 independent antithetic pairs/task, all six prescribed additional audits contain **4,096 pairs each**, no escalation triggered. Maximum split normalized discrepancy HGB/LR/RF = .011351/.006350/.007601; max coordinate discrepancy .002833/.002179/.000517; all split top-three/sign checks pass. Maximum audit discrepancies = .005220/.001171/.003456. Full-denominator unresolved lower/upper values coincide with nominal success because none are unresolved—this is not a bound against exact truth. Reference-bootstrap maximum coordinate-band widths reach .003064/.003786/.000650 (200 reference-only draws), not convergence certificates.
- Passing the gate does not freeze every label: German/HGB/perm/P1 A-versus-B success labels disagree on **35/4,608 runs across 24/72 points**. The six audited tasks' standalone-audit sensitivity changes one label in HGB/kernel/P4, HGB/perm/P1, RF/kernel/P1 (each 1/128 runs across two points/model); the 6,144-pair union changes the first two, not RF. P16 audit labels are unchanged. These new calculations use stored vectors only (`german_audit_label_sensitivity.csv`). No German reference is exact, even when these diagnostics agree.
- **Official-library diagnostic is separate:** SHAP 0.49.1, identity mask-game adapter; four low-d points/model × 16 repeats versus two German points/model × eight repeats, P1/P16 only. All 1,728 records remain. All 12 exact low-d dataset/model/mode/P16 summary rows report 64/64 successes, countering a blanket low-budget-derived indictment. Default/no-l1 streams differ, so they are not paired RNG comparisons; sampling/feature selection differs from the main minimum-norm variant despite matching observed adapter request counts.
- Four warning-free `no_l1/P1` runs have huge finite normalized errors: ACS/HGB slot0 repeat12 **4.80617e15**, ACS/LR slot0 repeat2 **2.16262e14**, Pima/HGB slot1 repeat2 **1.77821e15**, Pima/LR slot0 repeat11 **1.43045e13** (seed11). There are **2/192 ACS** and **2/192 Pima** such runs, none of 48 German no-l1/P1 runs. Default and P16 have none. Same-mask diagnosis identifies singular normal-equation solves, not adapter/reference corruption; same-mask SVD removes the blow-ups diagnostically but does not identify unsampled contrasts. **Do not trim, replace, or silently stabilize these library results.** Their enormous means must be disclosed alongside counts/robust summaries, not generalized to other versions/settings.

## Contradictions, paper-blocking fixes, and next experiments

The core story must retain its counterweights: permutation's P1 advantage reverses/shrinks at larger budgets; P16 failures are mostly tiny-mass tie errors; agreement becomes quite reassuring in several high-budget cells; background drift is not monotone; low-d library P16 succeeds throughout its small subset. This is an audit contribution, not a uniformly alarming failure narrative.

**Fix before paper:**
1. **Verified RNG deviation:** all **18/18 pilot tasks** are bitwise identical to the corresponding main attribution prefixes: 2 methods × 3 budgets × 8 repeats × 18 tasks = **864 reused vectors** (maximum difference zero; `pilot_main_overlap.csv`). The `rng_for` key omits stage/folder. This contradicts the no-pilot-draw-reuse promise; it does not mean the 64 main repeats are duplicates of each other, and pilot metrics were not used to choose scope according to the gate log. Disclose the deviation; do not claim a wholly fresh confirmatory sweep or silently replace records. If protocol-conforming replication is required, prospectively regenerate affected main batches with stage-separated streams under a dated amendment, retaining originals. German references also match pilot references; their six 4,096-pair audits extend the same pilot 128-pair streams. The pilot German/HGB/slot0 failure was its 128-pair audit (.020967 discrepancy), not the split (.010855); the extended audit passes (.005220). Thus no main escalation was triggered, but the pilot/main independence claim is false.
2. **Inference and chronology:** explicitly separate prespecified descriptive endpoints from exploratory paired contrasts/diagnostic interpretations; retain all nine panels, point-cluster units, distinct-fit counts, boundary/Hoeffding intervals and seed-stratum outputs. Do not infer training variability. The runner computes references and attributions inside each task rather than enforcing separate global stages; document global reference qualification/freeze before scoring, which current tables alone cannot certify. Quantile labels `error_median_instances`/`error90_instances` are medians of within-instance summaries, not pooled-run median/P90.
3. **Source/data limits:** bounded local source notes are not a comprehensive novelty search. ACS is an unweighted 20,000-record computational subsample, not California population inference. Selected feature rows have zero duplicates and 72 unique IDs/dataset; ACS has 28 **full-test** feature rows also seen in training, not 28 demonstrated duplicate people or selected leaks. Disclose source-person/household dependence and unknown categories. Resolve release permissions from archived terms: folktables' software license does not license ACS; Census terms-access status/hash is not a reuse interpretation; OpenML Pima's “Public” is not a concrete license. No new web verification occurred here.
4. **Accounting and scope:** obtain a child-inclusive whole-program CPU/warm-up/startup/diagnosis ledger and process-tree memory scope before claiming the cap; retain hashes, warning/failure ledgers and outliers. State the absence of risk calibration for thresholds/floor/material signs rather than retune. One nested background per B and one split cannot support background-sampling or training-population claims; narrow the manuscript if these are not expanded.

**Recommended next experiments (separate prospective budget; not performed):** (i) independent replicated background draws at each B on the same frozen points, separating target drift from own-game estimation error; (ii) independent train/split replication if claiming robustness beyond these fixed fits; (iii) if German becomes central rather than supplementary, larger independent reference streams on threshold-near tasks selected by a frozen rule, not main failure severity. None is necessary to rename these exact-game results as a narrow descriptive audit.

**Artifacts/provenance.** Memo: `/work/analysis/findings.md`. Analysis-only command: `python /work/analysis/findings_calculations.py`. Tables and input SHA256 manifest: `/work/analysis/findings_evidence/` (`cell_evidence.csv`, `paired_success_contrasts.csv`, `gap_evidence.csv`, `p16_failures_by_gap.csv`, `background_drift.csv`, `background_own_game.csv`, `german_reference_summary.csv`, `german_label_sensitivity.csv`, `german_audit_label_sensitivity.csv`, `pilot_main_overlap.csv`, `reference_scale.csv`, `uncached_timing.csv`, `library_extremes.csv`, `provenance.json`, `calculation_log.txt`). No figures requested/produced; no experiment code or raw result was modified. Input hashes were rechecked after calculations.
