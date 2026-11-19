# Research and access log

All work performed in /work on 2026-11-02, using CPU only.

## Independence / access

No literature or topic searches were performed. Only direct URLs for five
explicitly permitted starter papers were accessed (2107.07511, 1604.04173,
1904.06019, 2009.14193, 2402.10723). The downloaded versions, relevant sections,
and checksums are recorded in literature/READING_NOTES.md and provenance.json.
No prohibited material was encountered or deliberately sought. Conference-only
pages accessed: NeurIPS 2026 call for papers, official style archive, official
ethics guidelines, and ICML 2026 author instructions while selecting a venue.
The initially tried NeurIPS /2026/PaperInformation/StyleFiles URL returned HTTP
404; the correct archive was linked by the official call for papers. No academic
or conference paper listing was browsed.

## Setup and checks

The initial `python` command failed (not installed under that name); Python 3.11.2
is available as python3. A local uv virtual environment was installed. An initial
two-repetition smoke run (results/pilot; log metadata there) validated execution,
without the subsequently added oracle or response-stratified methods. The main
predeclared design used 100 repetitions, 15 scenario/dimension cells, and 13
methods including the pre-main-run oracle addition in PROTOCOL.md. That run is
retained in results/initial/ and logs/main_run.log. Its figures were not produced.

## Explicit post-initial-run addition

The initial run confirmed very low boundary coverage despite near-nominal
marginal coverage. To separate this failure from what conformal calibration can
repair, add two standard response-stratified controls: H-Z calibrates H within
zero/nonzero response strata; H-GZ calibrates within the Cartesian product of G
and zero/nonzero response strata. Membership selects the quantile using the
candidate y's zero status, not an oracle observation of the test target. This is
the usual label-conditional construction applied to a prespecified response
partition, not a novel algorithm. Tiny/empty strata use the exact rank rule and
infinity. All scenarios, sizes, seeds, scores, and hyperparameters stay fixed;
the earlier methods reproduce identically. This is an exploratory diagnostic
addition, not an independently confirmed hypothesis. The final run has 15 methods.

No failed scientific runs, discarded datasets, tuned test hyperparameters, or
unreported GPU runs. Additional numerical integration checks and PDF checks are
recorded below when completed.

## Completed verification and implementation corrections

- Seven substantive tests pass: exact ranks and small samples, raw boundary
  extension, an exhaustive small-sample check of the atom coverage identity,
  analytic oracle densities, constant-weight equivalence, structural-zero
  generation, and candidate-response stratum membership.
- The final 15-method experiment preserves every common initial-method metric
  exactly, checked against the retained initial run. It includes 1,500 independent
  scenario/dimension/repetition cells; methods share observations within a cell.
- The independent atom check generated 180,000 calibration score arrays, rather
  than substituting binomial answers for simulation. Exact formulas are plotted
  separately. Collapse uncertainty uses Wilson intervals, including at zero or
  one observed frequency; coverage uncertainty uses Rao--Blackwellized estimates.
- Higher-resolution randomized Sobol integration (2^18 versus 2^14) was run on 40
  fixed exchangeable K=3 cells. The largest absolute change in a scenario/method/
  component mean was 0.0008274078369140625; the largest individual change was
  0.0031890869140625. An independent analytic box-simplex formula integrated over
  covariates differed from high-resolution Sobol by at most 0.00018312229993389106.
  These values are saved in results/numerical_checks.json, not claimed as general
  worst-case integration bounds.
- A first analysis-script launch failed at parsing a Python raw string ending
  in a backslash; it was corrected before any analysis output was generated.
- The first LaTeX build failed because checklist answer macros require xcolor;
  the package was added. A subsequent build failed on an unescaped underscore in
  a checklist justification; it was escaped. Bibliographic accent escaping was
  corrected, and all subsequent references resolved. A rejected patch with a
  nonmatching context changed no files and was reapplied with the correct context.
- A setup-only `.venv/bin/python -m pip --version` command failed because uv's
  environment does not contain pip; all installation and freezing use `uv pip`.
- The paper uses the official unmodified 2026 style in main/preprint mode, with
  no claim of an actual conference submission. The official checklist's 16
  questions and all guidelines are preserved; the instruction block is removed
  and every answer is filled. The assets-license item is honestly answered No
  because the official style archive provides no explicit license statement.
- The compiled paper was visually inspected at its title, theory figure,
  main tables, shift figure, references, and an appendix result table. No
  overfull horizontal boxes or unresolved references remain. The main content
  is eight pages; appendices and the preserved checklist are additional pages.
- `bash reproduce.sh` was executed end to end after the numerical and formatting
  corrections. Its log and final machine-readable validation report are supplied.
  Timing macros are based on the latest actual run and therefore can differ from
  earlier retained logs. Scientific result estimates are identical across these
  deterministic reruns in the recorded environment.

## Scope not attempted

No real dataset, pretrained classifier, learned prediction model, estimated shift
weights, full conformal refitting, jackknife+, multi-zero support law, or
high-dimensional volume estimator was run. These are explicit scope limitations,
not completed experiments. There was no budget-truncated scientific run. The
efficient oracle is a known-DGP benchmark only; it is not a fitted model result.
