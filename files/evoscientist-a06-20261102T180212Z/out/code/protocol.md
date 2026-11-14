# Frozen protocol (before test-set inference)

## Aim and contribution
An estimand-aware empirical audit, not a claim to invent postselection inference. Distinguish (a) accuracy of the realized selected configuration, (b) expected accuracy of the search algorithm, and (c) accuracy over a fixed response cache. Study whether paired contrast reporting can be substantially more informative than separately bounding two absolute accuracies.

## Data and population
MMLU-Pro revision b189ec765aa7ed75c8acfea42df31fdae71f97be. Normalize question strings with whitespace collapse and casefold; keep first occurrence, sample unique questions uniformly. No rationale or answer metadata enter requests. Data inspection before inference found 231 literal duplicate question strings and options ranging from 3 to 10; model receives the actual choices, no constant-ten assumption. Population is the deduplicated finite benchmark, NOT a claim about all future language tasks or contamination-free generalization.

## Stage 1: real inference
16 fixed factorial prompts: expert framing, brief reasoning, verification instruction, instruction order; each binary. Fixed answer syntax FINAL: A and stable choice order. Temperature 0, max_tokens 256, model env RWE_MODEL; all transport attempts logged, invalid model outputs scored incorrect, technical retries only. No candidate creation using test feedback. Selection pool 360 unique items, fixed seed 20261102; all prompts evaluated on all items. Interleave/shuffle request order. Max concurrency 32. Select winner by accuracy, ties smaller prompt ID. Baseline ID0. Half-split winner chosen on first 180 items. Freeze decision before audit.

Untouched audit: 400 iid question draws with replacement from deduplicated population excluding ALL selection questions. Generate outputs for locked full winner, baseline and split winner only (duplicates of same selected configuration reused across methods, but repeated audit draws each receive a new request). Audit inference conditional on a stable deterministic response policy, or independent API randomness; backend version/determinism not guaranteed and acknowledged. All raw model responses cached. Main comparison: full winner vs baseline, paired audit CI and exact McNemar test. Report gap with uncertainty, not as universal bias. Absolute accuracy on audit has Wilson and exact binomial intervals. Audit is a different remaining-item population from selection; no pretending its sample proportion is true population accuracy.

## Stage 2: fixed-cache replay
Ground truth per candidate = mean over all 360 cached items; sample n rows WITH replacement (iid uniform over a fixed response matrix). 3000 replay repetitions, n=40,80,160; nested K=1,4,8,16, fixed family prefix. This is conditional finite-cache inference, NOT iid superpopulation coverage. Evaluate naive Wilson, exact Clopper-Pearson, simultaneous Bonferroni Clopper-Pearson, row-preserving Gaussian multiplier simultaneous intervals (heuristic), and honest 50:50 split + exact CI for its OWN split-selected target. All methods use same draws. Estimate optimism, RMSE, coverage, width, selection regret, apparent-win vs true-win rates, paired decision false-superiority. Cache mean used as exact truth is valid ONLY for this explicitly finite target. Row resampling preserves within-question prompt dependence.

## Stage 3: synthetic iid calibration and mechanism
Gaussian-copula Bernoulli: Y_ij=1{sqrt(rho) U_i + sqrt(1-rho) E_ij <= Phi^-1(p_j)}. n=40,80,160, K=1,4,8,16 (nested prefixes), rho=0,0.5,0.9, equal means .6 or heterogeneous means .56..64. 3000 repetitions per cell (nested cells share random draws). Independent items. Actual marginal truth known. Compare same intervals; Gaussian multiplier 199 draws on a prespecified subset (n=80,K=16), to bound CPU usage. Monte Carlo SE/95% intervals for all rates, not independent-real-world replication claims.

## Inference methods
Alpha=.05, two sided. Selected absolute bounds: naive Wilson / exact CP; family CP alpha/K union bound; paired Hoeffding contrasts radius sqrt(2 log(2(K-1)/alpha)/n) for outcome differences in [-1,1]. Agreement-adaptive contrast: estimate discordances +1 and -1 using exact binomial intervals at alpha/[2(K-1)] each, subtract endpoints (union over both probabilities/all contrasts). This may still be conservative; no improvement claimed until measured. Independent audit paired interval uses same discordance construction with K=2 (one contrast). Multiplier uses shared Gaussian item multipliers, not independent prompt multipliers, centered unstudentized empirical mean max; asymptotic heuristic only. Negative control includes identical-column synthetic family and label-independent selection K=1. Any added diagnostic will be labeled exploratory.

## Outputs, uncertainty and success signals
Primary: selection optimism and 95% coverage; paired decision validity and CI width. Rates include MC uncertainty. Effect sizes in percentage points. Scientific success is calibrated evidence, not positive significance. No correction needed for descriptive grids; confirmatory real winner-baseline test is one prespecified comparison. Audit absolute intervals for several methods are individually 95%, not family claims.

## Compute/reproducibility
Use API exposed by environment, record returned model identifier/token use, never save key. No GPU. Background inference with resumable JSONL. CPU simulations constrained to manageable batches. Log failures. Official ICLR2027 template, nine-page main body, plus references/appendix/AI statement.

## Rejection risks and scope
Not open-ended adaptive prompt generation; not novel universal selective inference; one opaque API model; no independent real searches; small audit may be inconclusive; training contamination unknown; fixed-cache replays measure one realized response matrix; prompt score stochasticity and service drift may break iid interpretation; no claim of automatic unbiased correction from bootstrap. Report all.

## Commands/artifacts
python fetch_data.py -> parquet/manifests
python run_llm.py prepare; python run_llm.py pilot; python run_llm.py selection; python run_llm.py audit -> prompts, splits, raw JSONL, lock, scores
python run_statistics.py -> real/synthetic/replay results
python make_figures.py -> every numbered figure, generated table macros
pytest -q test_statistics.py -> validation
latexmk -pdf paper.tex -> official-template paper.pdf
