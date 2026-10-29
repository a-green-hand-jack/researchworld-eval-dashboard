# Research and access log

All work was performed in `/work` on 2026-10-28, using CPUs, without paid APIs or a GPU. The task was unattended. No subagents were used. An OpenAI Codex assistant designed and wrote the code, ran the experiments, inspected outputs, and drafted the paper; there was no independent human review.

## Independent-research access protocol

No topical web or scholarly search was performed. Literature was fetched directly using identifiers explicitly listed in `starter_literature.md`: Chiang et al. (2403.04132), Zheng et al. (2306.05685), Koh and Liang (1703.04730), Broderick et al. (2011.14999), Min et al. (2501.17858), and Huang et al. (2508.11847v1). These are expressly permitted starter references. We read their abstracts and relevant methods/dataset/discussion passages, not just search snippets. References in those papers were not followed. No attempt was made to identify the unnamed prohibited paper. No encounter with a separately identified prohibited source was recognized. This statement records the access procedure, not a claim to have identified that paper.

Direct requests to DOI 10.2307/2334029 and JSTOR's corresponding PDF returned a JavaScript/security page, and a direct OUP article request returned HTTP 403. The original Bradley--Terry paper was not successfully read and is not cited as a consulted source; the model is documented using the consulted Arena paper instead.

Data requests were confined to the task's four fixed snapshots, the MT-Bench file listing, and their dataset README files. Four full files passed the specified SHA-256 checks. No conversations were analyzed or included in the submission; exact prompt strings were hashed only to define Arena bootstrap clusters.

The official NeurIPS 2026 style page guessed at `https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles` returned 404. We selected ICML 2026 instead: its official Author Instructions linked the official `icml2026.zip`, which was downloaded without modification. The official Call for Papers was also consulted for impact, AI-use, and submission requirements. These formatting/policy accesses implement the mandatory deliverable rather than a literature search.

## Analysis decisions and corrections

- Chose outcome reversals at fixed pairings; no deletion, injection, prompt editing, or live-system intervention. This differs from the supplied deletion-robustness starter paper.
- Retained all Arena records and all six MT-Bench models. NBA uses `_iscopy == 0`, NBA league, regular season, years 2014 and 2015. No filtering based on stability results.
- Retained ties as half-wins and treated GPT-4's `tie (inconsistent)` as a half-win; later tested omission of these records and of all ties.
- Inspection revealed a completely balanced GPT-4 comparison graph. This motivated the exact balanced-design proposition and a matched schedule experiment. The study is exploratory; there was no preregistration.
- Inspected human annotation keys: one repeated question/pair/turn/judge key was retained in the primary analysis and removed in a documented sensitivity check.
- Main experiments were run once, then rerun after finding a reporting-only issue: the raw-win baseline's gain units had incorrectly been passed into a logit-gap predicted-budget field. That prediction is now explicitly null for this baseline. The baseline's refitted thresholds and all influence predictions were unaffected. The initial stdout is retained as `logs/experiment_initial.log`; final numerical artifacts use corrected code.
- No optimizer convergence failures occurred in completed experiments. The direct-head-to-head baseline could not reverse the NBA top pairs using available beneficial head-to-head outcomes; this is a reported negative result, not a missing run.
- Five broad pair audits did not cross within the 5% cap. Their thresholds are censored, not treated as stable certificates. Main top-pair searches allowed 20%, but all successful main thresholds fell below 5%.
- The planned all-challenger check revealed that Houston (original rank 3) can cross the 2015 NBA leader with fewer selected edits than Atlanta (rank 2). We therefore explicitly separated top-two reversal from loss of the leader position.
- No assertion of a globally minimal edit set is made for unbalanced data. Exact optimality is established only under the stated pair-balance condition.

## Environment/setup failures

The shell had `python3` but no `python`; the first probe failed. System Python lacked requests; a local virtual environment and locked dependencies resolved this. These failures preceded numerical experiments. Downloaded original-paper access failures and the template 404 are recorded above.

## Scope deliberately not attempted

No 140k Arena dataset, WebDev data, or optional judge dataset with unspecified license was used. No GPU, paid model evaluation, live vote submission, or attacker-identification experiment was performed. We did not attempt globally optimal discrete attacks for arbitrary comparison graphs. These are scope choices, not completed experiments. A one-week allowance was available; the completed CPU experiments did not require that duration.

## Final numerical and document checks

All ten independent BFGS calls on the five real-data baseline and edited fits terminated with precision-loss warnings at the requested tight tolerance. These checks were not silently treated as successful optimizer statuses: `results/verification.json` records each status/message. All passed a separate maximum gradient residual bound of 1e-5 and maximum score disagreement bound of 1e-5 with the main damped-Newton solver. The main experiment's own fits met their 1e-8 convergence test. Before/after crossing signs agreed across solvers.

Plot fonts were changed from Matplotlib's embedded TrueType output to LaTeX-rendered Type-1 fonts to conform to the official template's typography instructions. This changed rendering only. PDF audits check the main-body page count, reference resolution, overfull boxes, font type, and checksums of the unmodified conference style files. The final main body occupies seven pages.

After completing the scripts, `run_all.sh` was invoked again. It completed all numerical stages and independent verification, then ended with exit code 143 (SIGTERM), without an application traceback. The source of the signal was not established. Reporting and the LaTeX build were resumed as a separate command and checked. Reproduction hashes and stage status are recorded in `results/reproduction_check.json`; numerical results are compared byte-for-byte, with runtime and PDF timestamps intentionally excluded. A clean submission archive excludes `data/`, downloaded literature, the virtual environment, and temporary build files. No underlying raw data or literature PDFs are redistributed.
