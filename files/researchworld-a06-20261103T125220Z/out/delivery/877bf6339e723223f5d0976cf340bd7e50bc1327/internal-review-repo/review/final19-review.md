# Independent final review of paper-repo PR #19

**Disposition: approve the exact head `a1ddbe20e72566c5ba71d5530c12a76717ce23bc` for final delivery.** No actionable scientific, reproduction, or presentation finding remains at this head. This is the review judgement recorded before submitting Forgejo approval, not a claim of conference acceptance.

The committed `paper.pdf` has SHA-256 `e94eb804eeaed864cb4ab4410ca735dc526ad0c96b6fe2562a68aeb7b4276939`, 29 pages, and eight main-text pages. The initially offered `6d45ca8094186ffb77a4b0794a9d8dcf36d75731` was inspected but never formally approved. The current head integrates compact presentation PR #20. I inspected its full diff, all current displays, and the reflowed committed PDF. The entire `analysis/` tree is identical between these heads; the changed captions, figure generator and reporting-cost columns preserve the measurements and inference distinctions.

## Governing requirements and scientific judgement

I reread Research objective #1 and all five frozen inputs, including the prohibition on seeking the withheld related paper, before judging this delivery. I refreshed/read idea's Brief at wiki revision `56daab68a389739be538484fa1be2a5f6fc73b36`, and applied `standard.md` and `venue-standard.md`. I inspected the settled `study/` plan, scope decision and ownership allocation in the delivered package. The analysis source manifest identifies experiment revision `af0b5e78a8809c1259fe102727ee5a414b22f4c0`; the current presentation handoff identifies figtab revision `1b1c1e7ce0a3cfe9b2c402f46dae0c44c23d8f71`.

The paper answers both research questions with executed evidence: magnitude and drivers of score optimism, a defined comparison consequence, and empirically evaluated reporting alternatives with uncertainty, quality and cost. Its 288 controlled settings cover question count, bank size, shared error and unequal candidate quality; known truth enables actual coverage/error measurements. The real component is newly generated Qwen2.5-1.5B-Instruct Q4_K_M output on the pinned MMLU-Pro benchmark, not a synthetic substitute. Disjoint auditing, simultaneous intervals and two budget-matched splits are compared with ordinary reuse. Distinct selected configurations and targets are retained when splitting changes the search.

The theoretical tools are established. The contribution is a controlled joint evaluation of score error, calibration, selected quality, decision behavior and resource costs, together with a carefully qualified real counterpoint. The related-work discussion identifies the relevant selection/inference antecedents and distinguishes fixed-bank reporting from adaptive data analysis, optimizer performance, and across-prompt distributions. This incremental contribution meets this objective; it does not establish a novel general correction or a universal empirical effect.

The real winner's 94/256 search score (36.72%) and 130/512 audit score (25.39%) support the reported 11.33 percentage-point gap. The default's substantial gap is preserved; the excess-gap interval crosses zero. Consequently the paper does not attribute the whole observed gap to selection. The audit supports paired improvement (61 wins, 17 losses; gain 8.59 points, exact interval [2.88,14.14]), whereas the conservative reused nonoverlap rule does not declare improvement. This is a measured change in reporting-based decision, not a demonstrated false-positive reuse event. In the empirical-cache experiment, positive optimism coexists with naive coverage 95.290–97.585% across all 15 tested cells. The paper reports this null undercoverage finding directly, rather than converting the synthetic large-bank result into a real-model conclusion.

## Targets, uncertainty and runtime choice

The primary real estimand is question-weighted accuracy on the 11,776 pinned items outside the entire retained 256-item search reservoir. The 512-item audit estimates it; its value is not known truth. Smaller search slices keep the same reservoir complement. The 768-row empirical-cache experiment instead has known empirical means and samples whole paired rows iid with replacement. Its nominal 95% binomial protocols and computational MC intervals do not estimate external-population coverage.

I checked the finite-population transformation and hypergeometric inversion independently, including the paired contrast. The frozen Tier C prefix `[0,10,14,13]` and `questions[::2]` subset preserve the original partition, while matrix axes correctly use actual candidate IDs. The previously recorded independent runtime-design check (`runtime-fallback-check.md` and its exhaustive artificial diagnostics) applies to the unchanged method. The delivered actual invocation and metadata use `design_count=2`, alpha .025 per possible B/C design, plus specified within-design multiplicity. The union argument supplies at least 95% unconditional protection separately for the stated endpoint families after runtime selection. It supplies neither trigger-conditional coverage/unbiasedness nor simultaneous protection across every endpoint. These restrictions are explicit in the final text/captions.

The paired-row bootstrap is labeled approximate sensitivity, retains question pairing and repeats selection. It is not represented as exact finite-population inference. Conditional reselection MCSE is separated from audit-pool sampling uncertainty. Zero observed errors have positive uncertainty bounds. The shared-error covariance formula is restricted to distinct candidates, with the Bernoulli diagonal reported separately. All three actually executed exact-null endpoints are named correctly.

## Independent evidence and reproduction checks

- Exported the exact paper heads into clean snapshots. `make check` passes on the current one: 119 analysis SHA/size entries, 18 plotting-input matches, 11 real output routes, 16 TeX inclusions, 13 figure inclusions and 15 README file links. Unmodified official assets, US Letter size, required statements, reference resolution, absence of overfull boxes and the eight-page main boundary pass. Rebuilding the current PDF reproduces its text identically on all 29 pages.
- Acquired only the pinned test/validation data through the supplied data-only command and verified their SHA/size values. Independently checked 12,032 test items, 70 validation items and 14 categories. No new model inference was performed by the reviewer.
- `check_final19.py` independently rescored all 6,144 raw responses, checked gold labels and prompt hashes against pinned data, verified complete question/candidate pairs, independently reconstructed the 768×4 retained matrix, regenerated the partition/prefix from seeds, and checked covariance/correlation axes and values. It imports only the prompt renderer, not production scoring/interval functions. Exhaustive independent hypergeometric tail inversion agrees with primary search/audit/gap/paired intervals. Counts, all main prompt/completion tokens (1,424,801/13,785), response times and calls reconcile with the ledger. Results: `final19-check.json`.
- Independently reproduced the complete cached disjoint/reselection and calibration analyses at 20,000 repetitions and the bootstrap at 1,000 outer/2,000 inner repetitions, using the delivered seeds and flags. Thirteen result files match byte for byte, including primary results, all candidate/category summaries, conditional-selection/frequency files, cache calibration/budgets and bootstrap results/summary. Input hashes, output hashes and reviewer run metadata are retained in `final19-reproduction.json`; changing runtime metadata is not treated as a measurement mismatch.
- The delivered measured-result validator passes all 15 cells, 210 probability/MCSE identities and 2,000 bootstrap records. Acquisition-choice checks pass none/0.5B/1.5B/all/default without model downloads. The unchanged synthetic pilot regression check passes all 75 metrics.
- `check_synthetic.py` checks all 7,200 summary rows/288 cells, grid invariants, table means and call costs. Independent binomial-tail calculations verify all 144 exact-null comparisons (48 settings × optimism/naive coverage/simultaneous coverage); maximum absolute discrepancy is 3.651 MCSE. Results: `final19-synthetic-check.json`.
- Reran both presentation generators on the initial head, and the changed real generator on the current head. All current 13 figure PDFs reproduce identical rendered pixels at 72 dpi, and all ten numerical table CSV/TeX files reproduce byte for byte. Binary PDF metadata is excluded from pixel comparisons. No statistical result was regenerated merely to create artwork.

Useful independent-review commands, run from this repository with an exact paper archive at `$PAPER_SNAPSHOT` (and the pinned data acquired into its analysis directory):

```sh
OPENBLAS_NUM_THREADS=1 python3 review/check_final19.py "$PAPER_SNAPSHOT" --revision a1ddbe20e72566c5ba71d5530c12a76717ce23bc
OPENBLAS_NUM_THREADS=1 python3 review/check_synthetic.py "$PAPER_SNAPSHOT/analysis" "$PAPER_SNAPSHOT" --archive-revision a1ddbe20e72566c5ba71d5530c12a76717ce23bc --output review/final19-synthetic-check.json
```

Full production reproduction commands are `README.md` and `analysis/docs/real-reproduction.md` in the delivery. Cached numerical reproduction required no inference backend. Native parser/assembly passes are supplier evidence, not a new reviewer backend run; independent raw-response scoring and matrix reconstruction provide a separate check of that contract. GNU Make was initially absent from this review sandbox; a resource-side install failed because that container had no DNS, then the documented sandbox package route installed Make 4.4.1 successfully. This reviewer setup issue did not require changing the delivered methods or dependencies. An archive-only metadata assumption in the old reviewer script was corrected to accept explicit revision/output arguments, preserving its historical output.

## Visual inspection and artifact resolution

I opened every standalone figure PDF after rasterizing the exact current artifacts, all five source-compiled table previews, and all 29 committed root-PDF pages in contact sheets. Main figures on pages 7/8 and integrated numerical tables on pages 22/23 were additionally opened at full page resolution. All displays are nonempty, readable, labeled, and consistent with the surrounding text and captions. Source/output maps and inclusions resolve. Native plot width is 5.5 inches; compact artwork changes height rather than shrinking type. Table estimates, intervals, decisions and selected-only versus paired calls agree with their inputs.

| Display | Artifact | Root PDF page |
|---|---|---:|
| Figure 1 | synthetic-selection.pdf | 5 |
| Figure 2 | real-primary.pdf | 7 |
| Figure 3 | real-cache-main.pdf | 8 |
| Figure 4 | synthetic-decisions.pdf | 12 |
| Figure 5 | synthetic-optimism-grid.pdf | 13 |
| Figure 6 | synthetic-coverage-grid.pdf | 14 |
| Figure 7 | synthetic-mse.pdf | 15 |
| Figure 8 | synthetic-budgets.pdf | 17 |
| Figure 9 | real-cache.pdf | 24 |
| Figure 10 | real-conditional.pdf | 25 |
| Figure 11 | real-cache-coverage-grid.pdf | 26 |
| Figure 12 | real-cache-mse.pdf | 28 |
| Figure 13 | real-diagnostics.pdf | 29 |
| Table 1 | synthetic-methods.tex | 16 |
| Table 2 | real-reporting.tex | 22 |
| Table 3 | real-cache-methods.tex | 23 |
| Table 4 | real-bootstrap.tex | 23 |
| Table 5 | real-cache-decisions.tex | 27 |

## Completeness, limitations and release decision

The report contains the required scientific sections, references, PDF/LaTeX, full scripts, raw outputs, environment records, model/data acquisition, seeds, timings, failures and a generator/input map for every figure/table. Official ICLR 2027 anonymous assets are unchanged. Eight main pages fit the verified nine-page limit. The AI-use statement truthfully distinguishes agents' checks from human verification. No separately attached checklist was established by the consulted official requirements; no actual conference submission or acceptance is implied. Literature-source/access records distinguish organization-level primary reading from manuscript-owner reading. No prohibited material was sought or encountered by this reviewer.

Actual inference cost includes all 6,144 parent responses, including excluded candidates, and both pilots (6,258 successful calls cumulatively), setup failures and interrupted acquisition. The reported 75.66 process-elapsed hours, 15.58 CPU hours and 7.63 resource-active hours have different boundaries and an unresolved discrepancy. The paper records rather than invents a cause. The pre-unblinding exposure/timing record is owner-supplied provenance; its historical subjective state cannot be independently reconstructed retrospectively. The frozen commits, response manifests and measured outputs are available and internally consistent.

Generalization remains limited by one small quantized model, one realized benchmark partition, four fixed candidates, deterministic short-answer decoding, and substantial candidate-specific format failures. Candidate-count changes in heterogeneous banks also change available true qualities. Benchmarks may have pretraining contamination; the study does not measure it. Fixed-bank guarantees do not cover feedback-driven candidate creation. These are material limitations, explicitly reflected in claims and discussion, not missing evidence for a stronger claim the paper makes.

External-review-repo has no open substantive finding at the final-state check; its commitment is not treated as an unseen external endorsement. Figtab's supplier placement check independently confirms the same exact PDF, and was read as supply rather than substituted for this review. The final PR's head is the revision above and `hutian/delivery` succeeds. Approval is justified by the inspected complete study and its bounded conclusions. Any later head change requires a new exact-revision review.
