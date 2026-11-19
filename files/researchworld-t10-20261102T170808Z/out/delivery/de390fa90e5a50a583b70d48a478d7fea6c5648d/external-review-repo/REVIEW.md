# External review standard

Commitment: issue #2. Governing task: Research objective, issue #1, and its frozen materials in `/initial-state/inputs/0`.

Review input is a published `world/result` version, including the delivered report and reproduction material. Record the release tag, delivery revision and files actually read. Judge what that version establishes, without inferring results from an owner's activity or inspecting its production history.

## Questions for each version

| Area | Evidence an outside reviewer needs |
| --- | --- |
| Question and contribution | A justified estimand and explicit question; a clear distinction from existing effective methods; conclusions whose scope matches the evidence. |
| Fixed resources and sampling | An explanation of which inputs are held equal across methods within a replication, what varies across replications, and the population or finite population targeted. The frozen predictor and permitted postprocessing must be explicit. |
| Validity | Assumptions for labels and unlabeled data, predictor independence or dependence, sample splitting and tuning; the distinction between finite-sample guarantees, asymptotic guarantees and empirical coverage. |
| Comparisons | Relevant available valid baselines with the same information and justified tuning; no width advantage claimed without its coverage context. Any oracle benchmark identified as such. |
| Repeated experiments | Replication counts, nominal level, coverage with Monte Carlo uncertainty, average width with uncertainty and an appropriate comparison using the shared inputs. |
| Boundary conditions | Evidence for conditions of improvement and no improvement or failure; limits of the theoretical or empirical claims. A measured negative finding is distinct from a missing experiment. |
| Theory | Stated assumptions, justified conclusions and experimental checks of the claimed regime; no universal optimality inferred from a limited comparison. |
| Presentation | Figures and tables make comparisons and uncertainty checkable; PDF claims agree with their displayed evidence and identify the tested settings. |
| Reproduction | Supplied code, environment versions, data provenance and acquisition, predictor provenance, seeds, commands, runtime guidance, and the scripts producing every reported figure and table. |
| Delivery | Complete PDF and LaTeX source; the chosen conference's current official template, applicable main-text limit, and required completed checklist. |

The task permits synthetic-only data. The absence of real-data experiments is not itself a violation; any external-validity claims must still match the tested scope. Observing empirical coverage near the nominal level is evidence with simulation uncertainty, not proof of a finite-sample guarantee.

Do not search for, identify, or consult the prohibited paper or any material discussing it. The supplied starter literature is allowed. If prohibited material is encountered accidentally, stop reading it and record the location and exposure as required by the task.

## Feedback protocol

Open one issue for each distinct substantive problem. Include the release tag and delivery revision, a precise location or quotation, the claim affected, why the evidence is insufficient or inconsistent, and the change or answer needed to resolve it. Make severity proportionate to its effect on validity, novelty, interpretation or reproducibility. Consolidate duplicate manifestations of the same problem; do not turn preferences into acceptance requirements.

Read replies and revised released evidence before resolving an issue. An author's explanation can resolve a misunderstanding; a promised analysis cannot substitute for delivered evidence. Longer integrated reviews may go in the wiki. Internal approval and report production remain with their owners.

## Version register

At initial activation, `world/result` has no published releases. No report has been reviewed and no substantive findings have been asserted.
