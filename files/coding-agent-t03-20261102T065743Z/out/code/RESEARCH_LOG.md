# Research conduct and source access

All work was carried out in /work on 2026-11-02 UTC by the unattended research agent. No people were contacted, no questions were asked, and no external paid service was used.

## Independence restriction
No topic-based literature or web search was issued. We did not try to infer the forbidden paper's identity. Literature was fetched directly using the supplied identifiers: arXiv 1705.07874, 2202.01602, 2204.11351, 2410.01917, 2006.16234, 2108.04884, 2106.11959, and JMLR 17-514. We read their abstracts, method sections relevant to the estimand/estimator, and conclusions; bibliography links and follow-up-work links were not followed. The supplied articles are explicitly allowed by the task. No identifiable restricted material was encountered. Because the forbidden work is deliberately unidentified, we cannot independently certify whether an otherwise allowed source happens to mention it; we did not investigate that identity.

Other direct access: UCI dataset/raw download, OpenML raw data, US Census downloads through folktables, PyPI package files, the SHAP library source installed from PyPI, official conference style/author-guideline pages, and public data license/terms pages. No SHAP-related search result, aggregator, third-party explanation blog, or unknown explanation repository was opened.

## Template
Official ICML 2026 archive downloaded from https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip ; official Author Instructions saved in literature/icml2026_author.html. Main-paper submission limit is 8 pages; references/appendices unlimited. ICML requires an Impact Statement. No NeurIPS-style paper checklist is specified in these ICML author instructions; a supplementary reproducibility/ethics checklist is supplied anyway, explicitly labeled as our own rather than a conference-mandated form. Initial probes of a guessed NeurIPS 2026 ZIP URL returned 404 and the general NeurIPS style URL had no useful style download. An ICLR 2027 raw style URL probe returned 404. These probes were only template checks, not research-literature searches.

## Failures and deviations
- System has python3, not python. Initial environment check failed; all scripts use .venv/bin/python after creating a Python 3.11 virtual environment.
- First prepare.py run trained German models, then failed because pandas 3.1 returned a read-only array. Fixed by explicitly requesting a writable copy. Original traceback preserved in logs/prepare_failed_pandas_readonly.log. Reran preparation deterministically. No explanation estimates had been analyzed then.
- No external preregistration: PROTOCOL.md is a prospective internal plan saved before explaining the models. The varying-column shortcut was clarified before explanation results to match SHAP's real-data implementation.
- SHAP low-budget singular-design warnings are retained, not filtered out of results. The package's least-squares fallback is part of the evaluated implementation.
- Exact enumeration is an offline audit expense. Timings of table-lookup explanation trials are not deployment timings. code/timing.py separately evaluates actual model calls from a real KernelExplainer.

## Completed validation
All 288 primary exact games finished. All 73,728 Kernel and 73,728 paired-permutation main estimates, 6,144 default-sparse estimates, and 1,152 independent-background exact games completed. None of the primary grid was dropped because of a warning or result. The independent subset/permutation and live-input/cached-game checks passed with maximum error below 1e-10 (see results/validation.json).

## Data-terms checks
Official UCI and OpenML metadata were retrieved directly. Census policies, privacy, information-quality pages and developer API terms were read directly; the latter confirms statistical-analysis purpose and prohibition on reidentification, and is not represented as a separate license for direct PUMS files. No reidentification or linkage was attempted. Guessed Census copyright.html and links.html URLs returned 404; these failures are not evidence of a data license. The retained policy pages do not supply separate PUMS license text. The public 2018 California PUMS file was downloaded via folktables without credentials. No third-party terms summaries were used.

## Post hoc solver investigation
After completing the prespecified grid and inspecting the averaging comparison, we observed extremely large low-budget package estimates (raw arrays preserved). We added code/solver_audit.py as an explicitly post hoc diagnostic. It replays the same 2d masks/payoffs/seeds, verifies exact equality with the original package outputs, and solves the same constrained regression using SVD least squares instead of normal equations. This does not change, exclude, repair or replace the primary results. Rank deficiency, extreme-error counts and SVD-control success rates are saved separately. It was not part of the prospective plan; every statement about it is labeled exploratory/post hoc.

Minor analysis-code failures: an initial Python raw-string construction in write_numbers.py caused a syntax error, followed by an indentation error during the correction. Both occurred after experimental outputs were complete; no experiment was rerun or altered for these errors. The corrected script generates all result macros from machine-readable outputs. The first traceback is preserved in logs/numbers_failed_syntax.log; the fixed generation succeeded.

## Final artifact verification
The PDF compiled successfully with the unmodified official ICML style files. Main text ends on page 7 (submission cap 8); references start on page 8; appendices start on page 9; total 12 pages. No unresolved references, missing-author errors or overfull boxes remain. The two remaining hyperref warnings concern the title linebreak and an empty affiliation anchor, not paper content.

The 19 MB lightweight ZIP was integrity-checked, extracted to /work/release_check, and independently ran make analyze paper using the pinned environment, without the large coalition/raw-data caches. The six checked result-macro/table/CSV files were byte-identical to the originals, and the rebuilt PDF had 12 pages. Logs and results/release_check.json record the check. Full raw coalition tables and raw public data remain in /work, omitted only from the lightweight download.
