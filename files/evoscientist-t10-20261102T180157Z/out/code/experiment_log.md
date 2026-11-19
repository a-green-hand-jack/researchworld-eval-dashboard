# Experiment and revision log

All stages2026-11-02 UTC. Plans are local records, not independently timestamped registrations.

## Stage1: intake and source restrictions
- Workspace initially empty. Memory preflight query found no relevant observation; no prior experimental artifact imported.
- Wrote TASK.md/research_request.md; adopted direct-URL allowlist. Research agent read five explicitly permitted originals. Main thread read2009 empirical-Bernstein theorem and official format files. No topical/citation-chain search. No identifiable restricted-material incident.
- First environment import failed on missing sklearn; installed dependencies. pdflatex/latexmk were present. pdftotext was absent; used Python PDF extraction.
- Selected official ICML2026 style after direct ICML2027 style URL404. Initial NeurIPS2026 style probe also404; no paper/review pages visited.
- Downloaded pinned ppi-python0.2.3 wheel and two original GoogleDrive data files. Checksums verified by download_data.py; no missing data, binary outcomes, probability scores in[0,1]. Separate dataset license not asserted.

## Stage2: code, proof and baseline
- Fixed recipes in methods.py; initial planned7feature hinge basis reduced to4features before main results, because it exactly represents intended mechanisms without redundant features. Fixed ridge changed to vanishing1e-4/n_train before main results.
- Independent proof audit accepted projection/EB identities but rejected an overbroad balanced-fold statement; repaired to observation-independent folds. Clarified ridge coefficient shrinkage rate and explicit Bernoulli laws.
- Package default uses clippedlambda and biased moments; retained separate unrestricted original-paper PPI++ main reference. Direct endpoint test uses installed package.
- First endpoint test failed due (2,) versus(2,1) output shape only. Flattened reference array; numerical values unchanged. Five baseline tests passed.
- Smoke:3cells×30repetitions. Preserved outputs in artifacts/smoke/. Used only to check execution, not claim coverage or tune methods.
- Planner baseline reflection accepted proceed; froze hashes for methods.py,run_experiments.py,test_methods.py,originalplan andamendment.

## Stage3: full repeated sampling
- Command: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python run_experiments.py --reps2000 --jobs4 (spaces in actual command reflected in README; shorthand here).
- 32cells,2000repeats each; actual wall127.20465059485286sec, CPU-only4workers. No worker error. Log artifacts/confirmatory.log. Per-method summary seconds are cumulative cell elapsed and unusable for speed ranking.
- Added fixed-threshold exact stratified comparator while main run pending and before full output inspection; separately declared artifacts/exact_baseline_addition.md. Proof conditional on random label counts; pooledscore mass uncertainty included without assuming independent confidence events.
- Supplemental command run_stratified.py --jobs4;12.1sec wall, same64k datasets replayed, not new independent replication. No worker error. Logs artifacts/stratified.log; twoadditionaltests including small exact enumeration passed.

## Stage4: analysis and failures retained
- Full data audit:820,000primaryintervals; supplement adds64,000for884,000total.32cells and442methodcells. Coverage containment, endpoint order, pairing keys, summaries and allpaper tables cross-checked.
- Nonlinear gains only favorable mechanisms; real cases no widthgains. Rare-event normal intervals fail. Exact strata helpful only3stepcorecells. EB selection practically inefficient. Allcells reported, no post-outcome methodtuning.
- pandas default NA parser initially displayed scenario`null` asmissing; all final analysis explicitly keep_default_na=False. No raw data altered.
- Plot initially rejected tiny negative yerr atcoverage1 due floating point. Clamped display errorbar lengths tozero; coverage limits unchanged.
- Statistical screen originally exported extreme p-values as0 by underflow. Independent review confirmed counts via log-space calculation. Final analyze.py now uses logsumexp tails/log-spaceHolm, scientific strings/log10values/underflowflags. This is an audit-export fix, not a change to inference or observations. Existing reusable memory O-6c555d2c10a732e8 consulted for remedy.
- Independent review sampled32cells×first3draws;1326endpointtriples reproduced to~5e-12exportprecision. Full sampling rowIDs were not stored; do not invent them. Released validate.py reproduces same check.

## Stage5: writing, self-review and release corrections
- Full19pagepaper compiled in official style; bodythroughp7,referencesp7,appendixp8. Initialoverfullformula/longcommand split, missinganonymouscorrespondence macro supplied; no stylemodification.
- Independent three-pass paper-review found no fatal math/implementation error and verified all26macros,442summaryrows,1768pairedcomparisons,alltables. It judged novelty/significance insufficient for a strongICMLmethodsclaim. This is retained as unresolved scholarly limitation.
- Corrected unsupported thresholdnecessity wording: polynomial→rich adds cubic+thresholdjointly. No unrun ablation fabricated.
- Moved Table1–3captions above tables pertemplate; addedobjectreferences and clarified widthSE, denominators, nuisancefitting vs predictortraining.
- Figure1source/assetlegenddrift synchronized by rerender. Distinctmarkers improve colorindependent reading. PGF/pdflatex PDF rendering replacedType0fonts with embeddedType1; statistical data unchanged. FinalPDF recursivelyverifiedallType1embedded.
- Restricted systemhardwareinspection command was blocked; not retried through another route. HostCPUcount/platformcome frompermittedruntimeAPI; noCPUmodelclaim.
- Final9tests and artifactvalidation logged separately. No newmethodexperimentsafter frozenruns; strongerbettingMeanCIcomparison remains explicitlyunimplemented.

## Reproducibility boundaries
- Fullenvironmentversions requirements-lock.txt; directpins requirements.txt; datahashes data/manifest.json.
- Prerunhashesandamendmentsare local evidence, not thirdpartytimestampattestation.
- No human consultation, no code-agentdelegationrequiringunavailablemodechoice, no paidAPI/GPU, no actualconference submission.
