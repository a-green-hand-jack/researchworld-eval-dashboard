# Research, access, and execution log

All activity was performed under `/work`, beginning 2026-11-02 UTC. The report is
autonomously generated; no person answered questions or independently reviewed it.
The task's excluded-paper constraint was treated as an access restriction, not as
a request to discover which paper was excluded.

## Access protocol

No general search for the research question was performed. No scholarly search
engine, citation graph, recommendation list, aggregator, social-media discussion,
or forward/backward citation search was used. No attempt was made to identify the
excluded work. No recognized incidental encounter with excluded material occurred.
This statement reports the actual access procedure; it does not claim an exhaustive
novelty search or guarantee identification of an unnamed work.

The following permitted starting-list PDFs were downloaded directly from their
supplied arXiv identifiers, and the first three pages were read (abstract and
introductory/methodological positioning). References cited within these pages were
not followed. No claims about uninspected detailed results of those papers are used.

| Local name | Direct source | Consulted use |
|---|---|---|
| `mmlu` | https://arxiv.org/pdf/2009.03300 | Benchmark purpose, subject scope |
| `helm` | https://arxiv.org/pdf/2211.09110 | Evaluation transparency and coverage |
| `lottery` | https://arxiv.org/pdf/2107.07002 | Dependence on task selection |
| `social_choice` | https://arxiv.org/pdf/2312.03121 | Ordinal/voting evaluation framing |
| `cheater` | https://arxiv.org/pdf/2311.01964 | Leakage motivation, possible adverse effects elsewhere |
| `rephrased` | https://arxiv.org/pdf/2311.04850 | Contamination can escape string-overlap detection |
| `strategic` | https://arxiv.org/pdf/2603.08371 | Multi-developer Stackelberg/equilibrium positioning |

The Zenodo record https://zenodo.org/records/10256836 was also fetched for
software metadata. It was not needed for a manuscript claim and is not cited.

To extend the conceptual positioning without a topic search, an older, directly
addressed known work was retrieved: Faliszewski, Hemaspaandra and Hemaspaandra,
*How Hard Is Bribery in Elections?*, https://arxiv.org/pdf/cs/0608081. The first
three pages of its version revised August 22, 2008 were inspected. Its bounded
intervention framing is cited; it is not used as a source for our empirical results.

Data accesses were restricted to the supplied HELM bucket, its frozen v1.13.0
release listing/summary/subject tables, and the supplied Open LLM `contents`
repository at the pinned SHA. No model-result repository was mirrored. The exact
61 required data-file URLs and checksums are in `data/manifest.json`. A redundant
one-subject exploratory download was initially made to inspect its schema; the
production download then fetched the 57 selected summaries, not duplicate group
tables. No evaluation examples were downloaded.

## Template and policy inspection

The ICLR official GitHub template repository listing was inspected directly:
https://api.github.com/repos/ICLR/Master-Template/contents . It includes ICLR 2027.
The template was downloaded first from
https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip and then
from the exact link in the official author guidelines:
https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip .
The two archives were identical. The official `.sty` and `.bst` are copied
unchanged into `paper/`. The manuscript changes only its running header to avoid
claiming an actual submission or publication.

Read official pages:

- https://iclr.cc/Conferences/2027/CallForPapers
- https://iclr.cc/Conferences/2027/AuthorGuidelines
- https://iclr.cc/Conferences/2027/AIPolicyForAuthors
- https://iclr.cc/public/CodeOfEthics

The guidelines impose 9 pages for the initial main text, excluding references,
appendices and the specified statements. A mandatory AI use statement and
recommended ethics/reproducibility statements are included. No separate mandatory
paper checklist was found in these inspected instructions; an additional completed
reporting/artifact checklist is included voluntarily.

Initial format discovery also fetched the official ICML 2026 AuthorInstructions
page and its official style archive, and the NeurIPS 2026 CallForPapers page. Those
formats were not selected after the latest ICLR template was verified. No
conference paper or review page was opened.

## Failed accesses and development corrections

- The following initial template probes returned HTTP 404; their contents were not
  used: `https://media.neurips.cc/Conferences/NeurIPS2026/Styles/neurips_2026.zip`,
  `https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles`,
  `https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles`, and
  `https://iclr.cc/Conferences/2027/AuthorGuide`. The actual ICLR guideline path is
  `AuthorGuidelines`, as linked by its official call.
- The system has `python3`, not `python`; `requests` was initially unavailable.
  A local virtual environment and pinned packages resolved setup.
- `pdftotext`/`pdfinfo` were unavailable. PDF text was inspected with pypdf and
  layout with PyMuPDF instead.
- Some patches to the manuscript failed to match a line and made no edits; they
  were reapplied with exact context. This did not affect any scientific result.
- A baseline threshold-cache edit was initially placed in the wrong function and
  corrected before the first experiment invocation. No results came from that
  unexecuted intermediate version.
- No optimizer failure, timeout, incomplete run, or failed test was hidden. The
  full executed test suites passed. Infeasible improvement scenarios are scientific
  results and are recorded explicitly, not treated as software failures.

## Executed analysis and changes of scope

1. Prepared both public panels. Audit: HELM 79 x 57 complete; Open LLM 4,576 raw
   entries, 1 flagged removal, 79 score-independent duplicate-name removals,
   4,496 retained models. The provided average reconstructs exactly.
2. Ran the exact four-rule support audit at two ceiling types, five response
   strengths and two winning conventions, plus three panels' continuous mass
   optima. Added random/lowest-first baselines, task perturbations and weighting
   controls. `logs/experiments_initial.log` and `runtime_initial.json` retain this
   first successful development run (90.19 CPU seconds).
3. The ceiling reversal was an observed result, not an assumption. The continuous
   score-mass comparison contradicted a simple "median needs more investment"
   reading, so both metrics were retained and emphasized. Partial-response
   infeasibility was retained rather than discarded.
4. Expanded the task perturbation and strategy-baseline controls to include
   observed ceilings. The second successful run is in `experiments_expanded.log`
   and `runtime_expanded.json` (116.66 CPU seconds).
5. Added Monte Carlo standard errors for the randomized HELM baseline and an exact
   mixed task-overhead/score-mass analysis for mean and odd median, with a proof
   and independent small-instance check. A final complete run regenerates the
   primary experiment outputs; timing is in `artifacts/runtime.json` and stdout
   in `logs/experiments.log`. Mixed-cost results derive from the already computed
   exact optima and are written by `src/report.py`.
6. Source-level tests cover exhaustive support optimality, zeros and ties,
   independently formulated LP checks for median mass, constrained optimization
   for geometric mass, the fixed-matrix ceiling reversal, and simultaneous
   attainment for mixed costs. Final pytest output is recorded in `tests.xml`.
7. Raw-column normalization and task-multiset perturbations weaken the broad
   ranking claim; those negative qualifications remain in the abstract, main
   results, and limitations. No empirical result is represented by synthetic
   data. Small constructed vectors occur only in proofs and tests.

No training experiment or causal cost calibration was attempted. No required
experiment was left incomplete for lack of budget. The resulting claims remain
conditional on independent coordinate control and fixed rivals. Population-level
accuracy confidence intervals, actual data/compute costs, and reacting developers
are outside the identified scope, rather than unreported completed experiments.

The final artifact checks raw-file SHA-256 values, unchanged template bytes,
response/ceiling monotonicity, common-cohort reversal, generated-object counts,
PDF main-text length, unresolved references and overfull boxes. Results are in
`artifacts/verification.json`.
