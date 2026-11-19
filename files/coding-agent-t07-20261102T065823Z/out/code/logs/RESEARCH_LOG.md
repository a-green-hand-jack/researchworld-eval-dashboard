# Research and access log

2026-11-02: started in an empty /work. No local task files existed; the user's
embedded task is the specification. No subagents used. Direct clone of the
explicitly permitted benchmark-prediction repository, detached at the supplied
commit. Read README, data_utils.py, LICENSE.txt and relevant baseline modules.
No search for the unidentified prohibited paper was performed. No prohibited
content was knowingly encountered. All literature PDFs were obtained by direct
URLs of the explicitly permitted starter papers; no citation graph or broad
search was used. This log will record accidental encounters if any occur.

Environment: python command absent, used python3. pdftotext absent, used pypdf.
Initial guessed NeurIPS style URLs returned 404; the official 2026 CallForPapers
page linked the actual Formatting_Instructions_For_NeurIPS_2026.zip, downloaded
without modification. Its source explicitly sets a nine-page main-text limit
excluding references, appendix and checklist.

Audit before experiment: all 13 matrices are finite and binary. Observed model
counts differ from task's list-file line counts. openllm_math contains 53
all-zero rows. Upstream's get_scores removes all-zero rows; we follow that and
add exact full-profile deduplication. These operations define the cohort, not
the item predictor. Preserving original columns means GPQA concatenated
subsets may contain overlapping question identities; no question text is used.

Baseline implementation inspection: upstream AIPW fits an intercept-bearing
Ridge on sampled item responses, then combines the mean prediction on unseen
items with mean in-sample residual/(1+n/N_unseen). The latter is numerically
zero because of the intercept. We reproduce that labeled implementation and
also implement a mathematically unbiased cross-fitted regression difference
estimator. We do not call the repository's estimator an unbiased oracle.

PROTOCOL.md locked before prediction runs. Data audit is not a prediction run.

Pilot: commonsense MIRT reached the initial 200-iteration limit, objective
5707.280535. A convergence-only rerun with ceiling 1000 converged at iteration
259, objective 5707.249145. All main fits use ceiling 1000. Pilot remains in
results/pilot and logs/pilot.log. Main results are separate.

Direct arXiv URLs initially delivered the latest versions of the explicitly
allowed starter papers. The Zhang et al. PDF was v2 (July 2026); its abstract
and introduction were read, then v1 was downloaded and used for the actual
method equations and citation. The rankings starter similarly delivered v2;
its first page was read. Neither is an identification of the prohibited paper;
we did not follow any references or search to infer that paper's identity.

Equation check: Eq. (3) of Zhang et al. v1 uses sample mean plus
(1-k/N)*(mean prediction unseen - mean prediction seen). This differs from
the pinned repository formula. Added the paper equation baseline before main
experiments, alongside the separately labeled repository reproduction.

During method write-up, recognized that a fixed source-mean control variate is
a shared additive offset across target models tested on the same items. It
cannot change their rankings. Added an explicitly exploratory same-strata,
same-sample, same-allocation no-offset ablation (augment_results.py); the locked
raw-strata ablation changes both clustering and offset and cannot isolate this.
This is not a replacement for the primary method or comparison.

Numerical correction: ranking metrics round predictions and truth to 12 decimal
places before computing tied ranks. Residual sums can differ by ~1e-16 for
mathematically identical binary counts. augment_results.py recalculates all
main rank metrics from saved predictions, so early worker imports cannot leave
inconsistent tie handling. Score-error results are unaffected. The script also
asserts the uniform/difference ranking identity for every saved split and budget.

Main run failure: the first eight-worker invocation completed 120/390 tasks,
then the process pool broke on reaching the first MMLU-Pro tasks. cgroup
memory.events recorded an OOM kill. The visible host has 40 CPUs and ~251 GiB,
but the actual container limits are 16 GiB and four CPU equivalents. Original
correlation_distance created multiple float64 N-by-N temporaries. Changed the
same float64 subtraction/max operations to in-place operations, preserving
the calculation, then reduced main concurrency to four. The original run
summary is preserved as logs/main_initial_oom_summary.json and original stdout
as logs/main.log. Restart skips complete result files and repeats unfinished
tasks. No partial failing prediction was used. This is an engineering fix, not
a change in experimental method or source/target population.

Independent rerun: arc_challenge/random/seed0 was recomputed in a separate
output directory using the final memory-efficient implementation. All 163
saved arrays matched exactly (maximum absolute difference 0). The correlation
distance refactor was separately checked bit-for-bit against the original.

The diagnostic suite was rerun once with final twelve-decimal rank handling
so its source-size CSV uses the same tie convention as the main results.
The initial diagnostic timing is retained in logs/diagnostics_initial_summary.json.
This correction affects numerical tie handling, not score-error computations.

The descriptive longer-benchmark table (N>=1000, k=100) was added to expose
query fractions <=10%; it is not a replacement primary population or a
target-error-based benchmark selection.

Final manuscript uses the official NeurIPS 2026 preprint option with an
anonymous artifact byline, avoiding fictitious affiliation/contact details or
a claim of actual submission. Initial TeX compilation exposed an unescaped
underscore in a checklist filename; corrected in the checklist generator.
The PDF-pagination validator was corrected to handle headings with merged
line numbers from pypdf. These are rendering/validation corrections only.
