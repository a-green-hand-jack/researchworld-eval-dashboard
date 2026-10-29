# Research and execution log

Date: 2026-10-28 (UTC). This is a record of work actually carried out, not a
claim that a one-week budget was exhausted. All computation used CPU and one
numerical thread. No subagents, new judgment calls, paid APIs, or GPUs were used.

## Before primary results

- The workspace was empty. No applicable AGENTS.md was present.
- Downloaded fixed Arena 55k, MT human/GPT-4, and FiveThirtyEight NBA snapshots.
  All three task-supplied SHA-256 values matched. Saved computed fourth hash.
- Read only explicitly allowlisted starter PDFs, and official ICML 2026 template
  and call-for-papers. Did not use general literature/web search or source code
  from prior ranking robustness work.
- Wrote `protocol.md` before computing baseline ranks. Chose every adjacent
  boundary, one edit per original record, fractional ties, deletion/reversal,
  global/exposure denominators, random control, clustered uncertainty, same-item
  judge contrast, and modeling checks.
- Implemented centered, ridge-regularized BT with canonical row-level outcomes,
  aggregated comparison cells for speed, exact gradients/Hessians, Newton fits,
  and explicit influence derivatives. Core tests passed after the fixture fix
  recorded below.

## Primary execution

- `experiment.py` ran all six primary datasets plus matched human/GPT-4 and
  consistent-only GPT-4 auxiliary data. It generated 400 bootstrap fits per
  dataset, all adjacent attacks of both mechanisms and two scopes, and 200
  random permutations per primary dataset/mechanism at five budgets.
- The full primary program's initial measured runtime was 21.46901895198971 s.
  Reproduction timings in JSON supersede this historical initial-run value.
- Direct-only search used 91 deletions for the MT human leading pair, versus
  92 from the unrestricted static order. This valid, unexpected baseline result
  is explicitly reported; there is no claim of algorithmic dominance.
- All primary failed searches were retained as NF, not robust comparisons.

## Exploratory controls after primary results

These controls were implemented after seeing the primary fit/audit summaries.
They are not represented as preregistered confirmatory tests.

1. Expanded only the fixed matched leading-pair cap to 20%, because GPT-4's
   primary 5% deletion search failed. Found 95/1814 deletions versus 35/1814 for
   human judgments. Repeated with 300 paired question bootstrap draws and 50
   alternate label-independent human annotation selections. None of these
   bootstrap audits remained censored at the extended cap; samples already
   reversed at baseline receive zero edits.
2. Vary ridge through 1e-4, .01, 1, remove ties, and estimate home advantage.
   The consistent-only GPT-4 variant had been prepared before primary fitting.
3. Added all-pair simultaneous standardized-error bootstrap bands as a stricter
   exploratory counterpart to the planned pointwise intervals. Existing 400
   bootstrap score draws were reused; no extra data were fabricated.
4. Equal-size, 1200-row subsampling 50 times per source. Nine Arena subsets
   omitted at least one contestant. Ridge scores are finite, but this control
   was rejected as an equal-information or causal comparison; all its outputs
   and the coverage failure are retained and disclosed.
5. Approximation-error validation with 100 random fixed-boundary draws per
   mechanism/source at five budgets; repeated draws are with replacement.
6. Replayed all 535 saved successful attack witnesses independently using
   modified row weights/labels and an uninitialized full refit. All reversed
   the claimed fixed pair and met the optimization gradient criterion.

## Failed commands and corrections

- `python` was not installed; `python3` is used throughout.
- `pdftotext` was absent; local paper text and PDF checks use PyMuPDF instead.
- The first core finite-difference test used an integer-valued synthetic fixture.
  A small outcome perturbation truncated to an integer, so the test failed.
  Changed the fixture to floating point and reran all checks. Real-data labels
  had already been floating point. No scientific results came from the failed
  fixture. Exhaustive two-contestant edit checks also pass.
- The first report run failed because a Wilson endpoint near zero produced a
  tiny negative error-bar length by floating-point rounding. Plot error-bar
  lengths are clipped to zero; numeric interval endpoints are not changed.
- A direct DOI request for Bradley and Terry returned only a verification page.
  Its article was not read and is not cited as a consulted source.
- Initial LaTeX checks detected a long equation extending a column and a missing
  anonymized-correspondence field. The equation was split over two lines and the
  official anonymized field supplied. Main text was tightened without changing
  type size, margins, spacing, or official style. Final compile has no overfull
  boxes or missing references; the main paper fits within the eight-page cap.

## Final checks

The complete `reproduce.sh` pipeline was run after assembly. See
`results/reproduction_check.json` for result-file comparison and
`results/deliverable_checks.json` for PDF size, pages, font types, and verified
witness counts. The PDF includes the required impact statement, AI assistance
disclosure, explicit limitations, references, and a completed research checklist.
Raw/processed data, installed environment, and downloaded papers are excluded
from `submission.zip`. No described experiment is incomplete.
