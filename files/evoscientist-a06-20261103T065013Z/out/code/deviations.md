# Protocol amendments and failures

## Before scored response acquisition (2026-11-03)
- Model-list and non-benchmark arithmetic format probe succeeded. No MMLU correctness outcomes have yet been collected. No benchmark prompt or model comparison was used to choose the endpoint model alias.
- The planner's proposed USD250 ceiling cannot be enforced: the supplied endpoint exposes neither a tariff nor a balance. Proceed using an explicit 4,800 completed scored-call cap, maximum 192 output tokens per call, four transport attempts maximum, eight concurrent calls. This is a bounded token/call experiment, not a claim of verified dollar spend. Actual usage and unobservable currency cost will be disclosed. No paid third-party service is configured.
- Use 600 proportional-stratified cohort items as planned, including all available 3--10 choices. Explanation prompts request at most 50 words. The same 192-token cap applies to all prompts.
- The final report card will be a **precommitted replay illustration**, not an access-separated prospective audit: acquisition caches all responses before analysis. The selector function accepts only selection rows, but the investigator can access the cache. There is no claim of evaluator blinding.
- Literature/source agent calls twice terminated with provider overload after partial file retrieval. Successfully downloaded official/source files were retained and inspected directly. No topic searches were issued. Wrong-year style guesses and a 2027 AuthorGuide URL returned 404; official repository supplies ICLR 2027.
- Code generation is implemented directly by the main agent. No code-agent task was delegated (its mode-selection precondition would require unavailable human input).

All subsequent deviations, aborted runs, and incomplete planned ablations must be appended here, not concealed.

## Analysis implementation corrections (before real-cache outcomes were summarized)
- The first synthetic execution completed 58 settings in approximately 67 seconds. A code audit found that B-sensitivity runs with R=200 did not share the first 200 item vectors of R=2000 core runs because Gaussian arrays were drawn with different shapes. The generator now always draws R=2000 item vectors and then takes a prefix. All synthetic settings were rerun, retaining the same primary design. This fixes Monte Carlo pairing rather than changing the statistical method.
- A separately labeled no-finite-population-correction multiplier sensitivity was added to fulfill the planned FPC ablation. It changes only the multiplier radius, not the finite audit estimand.
- The correlation-aware multiplier uses covariance eigendecomposition rather than explicitly generating one multiplier per row. The two conditional Gaussian distributions are identical; a 100,000-draw numerical equivalence check is included. This computation reduces runtime without changing the method.

## Post-acquisition endpoint and manuscript audit
- All 4,800 cells completed, no unresolved/recorded transport errors; 40 content-format failures were retained as incorrect. Reported model alias remained constant.
- The requested `max_tokens=192` was **not an enforceable bound on provider-reported completion usage**: 1,292 calls reported more than 192 completion tokens, maximum 5,521; total reported completion tokens 1,282,295. The API may include unexposed reasoning or ignore the requested bound; its semantics cannot be verified. The 921,600-token product is only a requested nominal ceiling, not an observed hard cap. Actual reported usage replaces any earlier bound claim. Costs and GPU-equivalent compute remain unverified. See `artifacts/usage_audit.json`.
- Important negative/conditional result: real-cache naive Wilson coverage is 95.90%, despite 2.32pp winner optimism. Thus measured optimism does not imply empirical interval failure in every real setting. The real baseline is the lowest-accuracy prompt, so its nonpositive-effect replays are self-comparisons; zero real false promotions is not a meaningful real-data type-I stress test. Known-equal-quality simulations provide that check.
- Added an explicitly exploratory matched-answer-budget comparison (768 correctness evaluations: select on 96 questions vs select on64 plus128 paired audit), after synthetic findings. It targets each policy's own winner and is not included in the frozen58-setting count.
- First PDF build reached pdflatex but BibTeX refused an absolute output filename under TeX security. Build script now invokes BibTeX with subprocess cwd at the workspace root. The initial verification also found `pdftotext` absent; page/text checks now use locked pypdf, with PyMuPDF for rendering inspection. These are build/tool fixes, not statistical changes.

## Final review/build checks
- Dedicated paper-review expert failed with provider overload; planner-agent supplied a bounded reject-first/source/alpha review instead. No independent human review or exhaustive novelty assessment occurred.
- Corrected a figure legend handle/label mismatch identified visually, moved table captions above tables per official template, added exact Monte Carlo binomial intervals to CSVs, and verified the primary iid parameter labels. No data or method was selected based on improved results.
- One full offline reproduction passed all8 commands:127.6s wall,127.4 CPU seconds,433.4MiB peak child RSS; this scope excludes previous development/reruns and original inference/agent compute. Final PDF is14pages with8pages main text. All4800 response records are reverified.
