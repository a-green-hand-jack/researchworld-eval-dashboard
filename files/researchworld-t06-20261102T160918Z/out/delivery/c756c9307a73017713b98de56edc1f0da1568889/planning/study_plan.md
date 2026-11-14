# Study plan: sensitivity of fixed pairwise-comparison rankings

## Authority and chronology

The standard is story-repo issue #1, mapped to the five frozen files in `/initial-state/inputs/0/`. All five were read before this plan was drafted. The objective permits the researchers to select operational questions, public datasets, metrics and methods; it requires real evidence from at least two evaluation designs, justified edit scaling/comparison, uncertainty, applicability conditions and limitations, a complete conference-format paper, and reproducible code. A negative or conditional finding is acceptable. No requirement is replaced by a pilot or a demonstration.

This is an integration plan drafted after experiment-repo executed the main analysis and controls. Its methods, pilot and run records document the order of empirical decisions; this document is not a preregistration. In particular the fixed-reference MT-Bench follow-up was introduced after observing changes in the resampled runner-up. It must be reported as post-hoc. The context Brief and independent feasibility assessment were read before this revision; their provenance and remaining boundaries are recorded below.

## Questions and evidence required

1. **Conditional local sensitivity:** for each fixed ranking, how many distinct decisive outcomes does a specified search successfully reverse before the *original* leader–runner score contrast changes sign? Report actual successful edits, total N, decisive count, k/N, the original pair and margin, and the exact-refit witness. This is a found upper bound on a successful intervention, not the minimum attack cost. Search failure below its cap supplies no robustness certificate.
2. **Targeting and scope of disturbance:** at the same allowed budget, how do uniform random reversals, endpoint-only helpful reversals and influence-ranked prefixes affect that fixed contrast? Report global winner change and whole-ranking displacement separately, so a local reversal does not stand for a disrupted leaderboard. Show actual edit counts when candidate sets saturate; an at-most-k budget is not necessarily k realized edits.
3. **Differences across observed collections:** how do these conditional sensitivities and baseline uncertainties vary across crowd preferences, human annotations, model judgments and sports seasons? Compare absolute counts and fractions, accompanied by score gaps, sample sizes, entrant count/coverage and tie rates. These are descriptive snapshot comparisons. In MT-Bench, identical question–pair–turn schedules and observation count permit a more focused label-source comparison; they do not identify a causal effect of judging design.
4. **Dependence on analysis conventions:** do conclusions persist with altered regularization, coverage/tie handling, human annotation selection and sports home advantage? Separate preservation of a conditional contrast from changes in who becomes leader or runner-up. A change in the selected pair changes the estimand and must be labeled.

The contribution is a reproducible empirical audit with explicit threat model, uncertainty and controls. Neither method novelty nor being first to demonstrate ranking sensitivity is assumed. The context Brief identifies explicitly permitted starter work on influence-guided deletion audits and new-vote injection. Historical outcome reversals differ from those interventions; the report must explain the relationship without presenting the influence ingredients as new or mixing published thresholds with newly measured baselines. Related-work source verification and final manuscript positioning remain with their owners.

## Study units and public data

- Arena-55k: the pinned 57,477-comparison public crowd-preference snapshot, retaining all 64 observed entrants primarily. Coverage-restricted and decisive-only rankings are sensitivity analyses, not silent replacements.
- MT-Bench: the pinned human and GPT-4 pairwise judgment collections. Human data contain variable annotation replication and author/expert sources; do not rename all human labels as independent expert judgments. GPT-4 order inconsistencies and tie conventions must be disclosed. Analyze the full collections and the 1,814 common canonical question–pair–turn cells separately.
- NBA: ten separate 2006–2015 regular-season rankings, deduplicated to one observation per game. Seasons are separate strength estimates, not ten independent examples of different evaluation designs or a pooled timeless ranking. They provide within-design heterogeneity and a non-LLM comparison.

Experiment owns source URLs, exact pinned revisions, hashes, preprocessing/drop accounting and data audits. Raw data stay outside version control and the delivered artifact; downloads and checksums reproduce them. No optional larger dataset is needed to meet the objective. No prohibited study or derivative discussion may be sought or used. Allowed literature is read through the context owner's restricted, source-verified workflow; accidental encounters, if any, are logged honestly.

## Model, perturbation, scale and endpoints

Use the executed regularized Bradley–Terry specification: fractional-binomial logistic loss, ties as half-wins, summed loss plus lambda times squared score norm / 2, primary lambda=1, centered score logits. Fractional ties are a scoring convention, not a generative tie model. The summed-loss regularization and different N are part of the estimand; regularization sensitivity is relevant to comparing snapshots. Report convergence and graph checks, rather than assuming numerical success. This unweighted empirical-schedule ridge BT estimand is not the current official Arena leaderboard: the context owner reports that Chiang et al. describe inverse-sampling-weighted estimation for a uniform pair distribution and distinct simultaneous ranking-uncertainty procedures. Our selected-gap bootstrap is not a simultaneous rank confidence set.

The primary intervention reverses a distinct observed decisive label while preserving its participants and the comparison schedule; ties are unchanged. It is retrospective data sensitivity, not deletion, injected votes, real adversary access or a demonstrated vote-rigging exploit. Use absolute k and k/N, where N includes ties, and report decisive count/tie fraction to make this denominator interpretable. Fractions make differing sample counts visible but do not equalize information, score gaps, model counts or schedules.

Primary budgets follow the executed protocol: one edit and max(1, floor(N f)) for f in {0.001, 0.0025, 0.005, 0.01, 0.02, 0.05}, deduplicating coincident integer budgets. Influence scores rank candidate reversals for the original leading-pair contrast; every reported outcome is measured by a converged refit. Prefix/binary search gives a found successful count only, without global or prefix-minimality guarantees. Retain the actual successful witness and neighboring evaluated prefix. Uniform random distinct decisive reversals and random ordering of helpful endpoint reversals supply separate baselines. Randomness and search caps must be reconstructible from seeds/code.

The conditional primary endpoint is a sign reversal of the original fitted leader–runner margin. Any winner change, original leader's new rank, normalized Kendall pair disagreement and top-five overlap are separate reported endpoints. An initial pair reversal need not make the original runner-up the global winner. No single endpoint is promoted to a universal definition of leaderboard stability.

## Uncertainty, controls and follow-ups

Keep Monte Carlo uncertainty over randomly selected edits distinct from resampling uncertainty in the underlying dataset. The executed main analyses use 500 random-edit replicates, 50 endpoint-only permutations and 500 cluster-bootstrap fits per ranking. Deterministic influence outputs have no Monte Carlo interval. Random-event frequencies carry their computed binomial Monte Carlo intervals, not data-sampling intervals.

Bootstrap units follow the recorded analysis: Arena battle identifiers, MT questions, NBA dates. State their limitations: Arena has no user clusters or adequate temporal strata; question resampling does not remove arbitrary crossed annotator effects; date clusters do not solve within-season drift. Baseline original-pair gap percentile intervals are descriptive, conditional on the model, observed collection and initial pair selection. They are not simultaneous or post-selection confidence guarantees. Very small successful edit counts must be presented beside baseline gap uncertainty, including the possibility that the leading contrast was already poorly resolved.

Executed robustness/control families:

- lambda in {0.1, 1, 10}; Arena minimum incident support 500 and decisive-only fitting;
- expert-only human judgments and exclusion of GPT-4 inconsistent-order ties;
- identical MT cells with one human label sampled per cell (100 selections), then joint question bootstrap and human-label selection (500 paired replicates);
- NBA fitted home advantage, including date-cluster uncertainty;
- adjacent-pair exact-refit diagnostics, which widen the view beyond the selected leading contrast without certifying absence of unobserved attacks.

Keep the two paired MT bootstrap estimands distinct. One reselects each replicate's leading pair; the other fixes the original GPT-4–Claude-v1 reference contrast. The latter is a post-hoc follow-up motivated by observed pair-selection changes; already reversed reference pairs cost zero further edits. Report censoring/search-cap status and call intervals percentile ranges for the *found heuristic statistic*, not confidence intervals for globally minimum attack budgets. Neither matched schedule nor bootstrap converts label-source differences into general human-versus-LLM causal claims.

## Evidence and display priority

The authoritative empirical map is experiment-repo `notes/results_handoff.md` with methods in `notes/methods.md`, both supplied in release `analysis-v1`; final delivery preserves their paths under `analysis/`. Paper and presentation owners take numerical values from generated files, not from this plan or issue summaries.

Main-text priority is: (1) a compact dataset/method audit and found-cost summary, including baseline pair gaps/uncertainty; (2) local-versus-global perturbation curves comparing all strategies and showing actual budgets; (3) matched MT evidence with explicitly named pair-selection statistic; (4) a compact convention sensitivity result. Ten-season heterogeneity, all-adjacent diagnostics, fuller robustness and estimator details can appear in the appendix. This priority is editorial guidance, not permission to discard a required evaluation item. Every figure/table must map to executed results and a delivered generator. Presentation owns final captions/rendering; paper owns placement and final interpretation.

## Work division and delivered paths

| Requirement/work | Owner | Delivery or handoff |
| --- | --- | --- |
| Study questions, comparison logic, requirement coverage and split | story-repo | `planning/`, `.forgejo/CODEOWNERS` |
| Objective Brief, permitted literature verification and positioning | idea-repo | Published Brief/wiki/release dossier; paper integrates into its report/bibliography |
| Independent feasibility/scope judgement | idea-review-repo | Release/wiki/issue supplied to story; no inaccessible code dependency |
| Data acquisition, models, perturbations, uncertainty, controls, diagnostics, numerical validity and reproduction | experiment-repo | `analysis/` |
| Checkable rendered figures/tables, captions, provenance and generators | figtab-repo | `figures/`, `tables/`, `presentation/` |
| Current official conference template, page/checklist requirements and provenance | venue-repo | `venue/` and declared artifact requirements |
| Complete manuscript, integrated bibliography, completed checklist/disclosures, build and PDF | paper-repo | `paper.tex`, `paper.pdf`, `references.bib`, `manuscript/`, `build/`, `Makefile`, root `README.md`, `.gitignore` |
| Independent delivery/objective review and release approval | internal-review-repo | Review of the exact proposed release/final commit |
| Outside-reader report review | external-review-repo | Its review supply through the report/review workflow |

Context and feasibility remain with their owners and feed others; they need no final path solely to give every role a directory. Story does not produce another owner's final part. CODEOWNERS change requires story review; paper merges component PRs. Any new delivered path or disputed responsibility must be settled before integration.

## Completion and acceptance gates

The detailed objective coverage map is `planning/requirements.md`. Available evidence permits writing/rendering/integration without waiting for unrelated input. The actual context Brief and independent feasibility judgement support this bounded study scope; neither supplies final-paper approval or guarantees conference novelty. Any material concern is returned to its owning position with a concrete request, not worked around by narrowing the objective.

Before story marks its commitment complete: re-read objective and Brief, incorporate feasibility judgement, confirm all required paths have owners, deliver planning through a PR to paper main, and check the report's built text for the plan's key distinctions. The objective/Brief/feasibility and ownership checks are complete for this planning revision; PR integration and the assembled-report check remain open. The report owner prepares the version; internal review approves the exact commit with passing system checks before a merge to release/final. A local commit, an analysis release or a draft paper is not the world's completed research delivery.

## Input reconciliation and remaining work

- Context input: idea-repo `context/brief.md` at `acb49911b146ca88535b888fe04fd43a728bd322` is the initial Brief revision; the identical Brief is published in its wiki. It maps the full frozen objective, allowed source boundaries and prior deletion/injection distinctions. This plan conforms to its empirical-scope, uncertainty and non-novelty bounds. Subsequent source dossiers feed the manuscript rather than requiring a new empirical scope.
- Feasibility input: idea-review-repo releases `feasibility-v1` and the context-reconciled `feasibility-v2`, “Feasible scope, resource evidence and remaining delivery risks,” read in full. It independently inspected experiment revision `36eb7c0b781382017a3983c1e57b85306933582d`, supports proceeding with the bounded scope, and recommends prioritizing integration over extra datasets/methods. It is a post-execution inspection, not an independent rerun or ex-ante approval. Its cautions on relative ridge strength, actual edit counts, conditional intervals and unresolved baseline gaps are incorporated above.
- Ownership: paper-repo PR #4 merged the directory/function split. Exact venue artifact declarations must stay aligned with those allocations; final manuscript, figure-source mapping, reproducibility execution and independent review remain their owners' work.
- Venue input: the delivered `venue/requirements/venue.md` verifies the latest official NeurIPS 2026 main-track format: nine substantive content pages, unmodified official style, default review mode, and all 16 completed checklist questions after references/appendices. Existing CODEOWNERS allocations cover every declared artifact; no ownership change is needed. Rendered page-count/checklist checks remain with paper and independent review.
- No new computational requirement is introduced by this reconciliation. If a later review identifies missing evidence for a claimed result, the appropriate owner must either execute the necessary analysis or bound the claim without omitting a required objective item.
