# Study plan: stability of pairwise-comparison leaderboards

Owner: `story-repo` (plan). This file is the division of the work and the study design the
other positions work from. It states questions, definitions and required comparisons, not
conclusions. Where an analysis choice is marked *analysis-owner's call*, `experiment-repo`
decides and records why. Objective: issue #1 (`Research objective`).

## 0. Constraints that shape the plan
- CPU only, one week, public data only; the world's shared model-time budget is small
  (7200 s, 96 turns), so the core study must be compact. Optional data are staged *after* the
  core is done.
- Required: conclusions on >= 2 different evaluation designs with real data; scale of
  perturbation and cross-dataset comparison defined and justified by us; applicability
  conditions and limitations; uncertainty reported.
- **Excluded material** (`deliverable.md`): the published paper that already studies this
  question, plus anything citing/discussing/mirroring it. Starter-literature item 8
  (Huang et al. 2025, "Dropping Just a Handful of Preferences...") matches that description
  by title and abstract line. **Nobody opens or searches for item 8, or any page that
  cites it. Decision (taking idea-repo's Brief, section 6): item 8 may be listed in related
  work only as the starter list describes it, stated as not read; no "first to study
  dropping/perturbing preferences" claim is made; novelty rests on what we do (flips,
  additions, noise baselines, scales, matched cross-design contrasts).** We cite nothing else
  we have not read. Its methodological ancestors
  (items 4 and 5, Koh & Liang; Broderick et al.) are fine. Searches must be topic-specific
  (Bradley-Terry inference, influence functions, rank uncertainty, Elo) and a hit on the
  excluded kind of page is dropped at once and logged in the reproduction notes (where,
  how much was read).

## 1. Research question (operational)
RQ. For a leaderboard built by fitting a Bradley-Terry (BT) model to pairwise comparisons,
how small a change to the comparison data suffices to change a *ranking claim*, and does
that size differ across evaluation designs?

Ranking claims (the things that get changed), fixed before any result is seen:
- C1 top-1: the identity of the top-ranked participant.
- C2 adjacent-pair order: for every adjacent pair (i, i+1) in the fitted ranking, the sign of
  theta_i - theta_{i+1}.
- C3 top-k set (k = 3, 5, 10 where participants allow).
- C4 significance claim: "i is better than j" at 95% (the BT-bootstrap interval for
  theta_i - theta_j excludes 0), i.e. what a published CI/overlap table asserts. Search
  with a Wald/sandwich z inside the loop; re-verify with the bootstrap only at the end
  (bootstrap-in-the-loop costs ~1000x); that makes C4 affordable on Arena too.
- **Primary claims: C1, C2 (restricted pair sets, e.g. top-10 adjacent pairs, fixed in
  advance) and C4. C3 and Kendall tau are secondary and the first thing to cut.** Per-pair
  NBA results are exploratory (multiplicity).
(Rank correlation drop, e.g. Kendall tau < threshold, is secondary.)

Perturbation families (each a different story for "small change"):
- P1 *worst-case removal* of k comparisons (adversarial or unlucky data loss/noise).
  Primary method: influence-function approximation (Koh & Liang; Broderick et al.) to
  pick candidates, then exact refit to verify. Report the smallest verified k as an
  **upper bound** on the true minimal k (a found perturbation, not a proven minimum); add
  the approximation-vs-refit error. On small instances, check against exact search
  (brute force / ILP) so we know how loose the bound is.
- P2 *worst-case outcome flips* of k comparisons (label noise / vote manipulation, no
  change in design counts).
- P3 *worst-case addition* of k comparisons involving a target (vote-rigging style; adding
  votes between existing participants only).
- B1 *random removal / random flips* of the same size: baseline for "unlucky" vs "worst".
- B2 *resampling noise*: bootstrap (and subsample) rank distribution = the baseline
  uncertainty a leaderboard already reports. The question is how far the worst-case size k*
  sits from what sampling noise already moves.

## 2. Data (core first, then optional)
Core (must be done):
| id | design | data |
| A | crowd votes | Arena human preference 55k (HF `lmarena-ai/arena-human-preference-55k`, pinned commit in `data.md`), ~60+ models |
| M-h | expert annotation | MT-Bench human judgments (6 models) |
| M-g | model judge | MT-Bench GPT-4 pairwise judgments, same question/model pairs as M-h |
| N | sports | NBA historical games (538 `nbaallelo.csv`), per season and pooled eras |

M-h vs M-g is a *matched* comparison (same items, different judge type). It is the cleanest
design contrast we have; use it.

Optional, in this order, only after the core results are in and checked:
1. (ranked above 140k by the feasibility review) LLM-judge labels on Arena battles (`potsawee/chatbot-arena-llm-judges`): matched to A.
   License undeclared: confirm terms and say so in the paper; drop if unclear.
2. Arena 140k (columns needed only; different period than 55k).
Not planned: WebDev Arena (dataset agreement), synthetic data (only allowed as clearly
labelled illustration; not needed).

Data live in `data/` of the working directory, outside the repository. Record source,
commit, sha256 of each file used.

## 3. Defining the "size" of a change and comparing datasets
A single number cannot compare 6 participants/3k comparisons with 100 teams/60k games.
Report each result on all of these scales, and treat disagreement between scales as a finding:
- (s1) fraction of all comparisons, k*/N, and absolute count k*;
- (s2) fraction of comparisons *involving the two participants concerned* (local scale);
- (s3) in units of sampling noise: primary unit is the claim's gap in bootstrap SE
  (z = (theta_i - theta_j)/se); B1 is reported as flip probability on a short log-grid of k
  (no root-finding to 0.5);
- (s4) matched-size control (replicated; for the 6-participant MT-Bench match the choice
  of which 6 models matters, so draw many 6-model subsets and report the spread): re-draw Arena subsets with N, participant count and
  comparisons-per-participant matched to MT-Bench and to an NBA season, to separate "design"
  from "size/sparsity".
Replication for uncertainty: the unit of replication differs, and must be stated.
Arena: bootstrap/subsample replicates of the battle set; NBA: seasons (many); MT-Bench:
resample questions (comparisons within a question are not independent; cluster it).
With 3-4 designs we cannot claim a population-level "design effect"; report as comparisons
under stated conditions, with the matched contrasts (M-h/M-g; A-subsampled vs M, N) as the
stronger evidence.

## 4. Analysis blocks (what experiment-repo delivers)
- E0 Data + BT fit. Loaders, cleaning rules (ties, both-bad, duplicate battles, `_iscopy`
  in NBA, position/home-advantage), BT/MLE fit with the leaderboard convention of the source
  (Arena: BT on logistic regression; ties as half win each, say so), sanity check of the
  recovered ranking against the sources' published ones (Chiang et al.; Zheng et al.) or
  the Elo column in NBA. Ties and home/position effects are modelling choices: treat as
  sensitivity (E5).
- E1 Baseline uncertainty: bootstrap rank/score CIs per dataset (B2) and the claims'
  C1-C4 status in the unperturbed fit (which claims are already statistically weak).
- E2 Worst-case removal (P1) for C1-C4 on all datasets, with verified k*, approximation
  error, and the exact-search check on small instances.
- E3 Flips (P2), additions (P3), random baselines (B1) at the same sizes.
- E4 Cross-design comparison on scales s1-s4, with the matched contrasts, plus a
  descriptive analysis of what predicts k* (score gap, z-gap, comparisons per pair, tie
  rate, participants, strength spread; s4 matching does not match spread or tie rate, so
  they enter as covariates). Prefer a simple, transparent model (e.g. k*/N against z on log
  scales) over a causal story.
- E5 Sensitivity: ties handling, home/position covariate, BT vs online Elo as the ranker on
  NBA/Arena, order of arrival, perturbation method (greedy vs one-shot influence ranking).
  Non-stationarity (claim 5) gets its own E5 item: NBA early vs late eras (seasons
  grouped), and an Arena time split only if the data carry a usable order (otherwise stated
  as not possible, text only).
- E6 (optional data, see 2).
NBA leaderboard definition: primary unit = one regular season, participants = teams (`team_id`) within that season, BT with a home-court term, `_iscopy` rows dropped; playoffs, era-pooled and franchise-level fits are sensitivity/secondary; the 538 Elo column is a sanity check only.
Alignment/NBA rules (fixed and documented): M-h vs M-g uses an explicit (question, model
pair, turn) alignment, question-clustered bootstrap, dropped counts recorded; NBA handles
`_iscopy`, playoffs vs regular season and home court explicitly. Keep the "3-4 designs"
conditionality in the abstract's scope. Freeze claim list, metric names and the `results/`
schema early (experiment-repo with figtab-repo) so figures and paper can draft.
All stochastic steps get a recorded seed; report CI/replicates for every headline number.
Primary metrics are the ones named above; anything added after seeing results is labelled
exploratory.

## 5. Evidence the paper needs (claims to be supported or not)
Do not assume the direction. The study must be able to support each of the following, or
its opposite, or "depends":
1. Which claims in each leaderboard are fragile and which are not, and by how much
   (C1-C4, k* and k*/N with intervals).
2. Worst-case size vs random removal vs bootstrap noise (does adversarial sensitivity
   exceed what sampling noise already implies, and by how much?).
3. Differences across designs, on every scale in section 3, including the matched
   contrasts, and which differences survive the size control.
4. What predicts fragility; where the method (approximation, upper bound) is loose.
5. Conditions of validity and limitations: BT model misspecification, ties, non-stationarity
   (NBA over time, Arena over time), what "small change" means to a manipulator vs noise,
   few designs, upper-bound nature of k*.

## 6. Division of the work (see `.forgejo/CODEOWNERS` in `paper-repo`)
| position | owns |
| idea-repo | `Brief`; related-work and conventions (BT inference, influence/AMIP, rank uncertainty, Elo, vote manipulation items 2,3,6,7); data facts and checksums; guard on excluded material |
| idea-review-repo | feasibility judgement of this plan |
| experiment-repo | `code/` (data loaders, fits, perturbation analyses, tests, reproduction document `code/README.md`), `results/` (numeric outputs the figures/tables are made from) |
| figtab-repo | `figures/` (figure and table sources, generating scripts, rendered outputs) |
| venue-repo | `venue/` (choice among ICML/ICLR/NeurIPS with reasons, latest official template, page limits, checklist requirements) |
| paper-repo | `paper/` (LaTeX, bib, PDF), root `README.md`, the filled checklist text with venue's format |
| story-repo | this plan; `.forgejo/CODEOWNERS` |
| internal/external review | read and judge; no path |

Order. Everything in E0 can start now. E1-E3 follow E0. figtab can draft layouts against
the claim list in section 5 before numbers exist, and fill them from `results/` as it
lands. venue-repo's choice is needed before paper-repo fixes the template. Optional data
(section 2) only after core E0-E4 are in `results/`.
Early checks: after E0, one small pilot of P1 on MT-Bench-h (6 participants) and one NBA
season to confirm the pipeline and the exact-search comparison before the large runs.

## 7. Plan risks (tracked, revise this file when they change)
- Model-time budget is small: if the budget gets tight, drop optional data and E5 pieces
  in this order (feasibility review): Kendall/C3, order-of-arrival and Elo ranker, Arena 140k,
  Arena LLM-judges. Ties/home sensitivity stays in E5 core. Never drop the
  M-h/M-g and A-vs-N core comparison or the uncertainty on headline numbers.
- NBA is non-stationary and has home advantage: per-season fits are the primary unit; the
  pooled fit is secondary and labelled.
- Greedy influence-based search can overstate k*; the exact-search check and the random
  baseline are what keep the claim honest.

## 8. Fixed delivered names (for `venue-artifacts.json`)
- `paper/main.pdf` (built from source), `paper/main.tex`, `paper/neurips_2026.sty`, `paper/checklist.tex`, `paper/refs.bib`: paper-repo.
- `code/README.md` reproduction document (environment/versions, data sources+versions+sha256, seeds, commands, runtimes, figure/table -> script map, excluded-material encounters section; idea-repo and figtab-repo feed it): experiment-repo. `code/` analysis scripts live in paper-repo's tree, delivered by pull request. Raw data stay in `data/`, never in the repository.
- `results/` numeric outputs: experiment-repo. `figures/` figures, table sources and their scripts: figtab-repo. `venue/` template and rules material: venue-repo.

## 9. Updates from idea-repo's data facts (wiki `Data-facts`, `Prior-work`)
- P1 primary method is the recursive greedy loop (influence score, refit, repeat) with exact refits; one-shot influence is a candidate generator and a comparison only (masking can hide fragility).
- Arena 55k has no timestamp/user column: an Arena time split is not possible; non-stationarity is shown on NBA eras only, and the paper says so. `winner_tie` merges "tie" and "tie (both bad)". 64 models; sampling probabilities unknown, so Arena's inverse-probability weighting is not reproduced (limitation).
- C4 is defined as the pairwise 95% interval for theta_i - theta_j excluding 0, not a simultaneous rank confidence set; Arena's published non-overlap rule is a secondary reading, and the paper states which is used.
- MT-Bench human: several judges per (question, turn, unordered pair): the unit of the human side (per vote vs per key) must be stated by experiment-repo, with the question-clustered bootstrap. The GPT-4 file cannot quantify position bias (swap built in); do not claim it.
- NBA: `_iscopy==0` only; ABA games are mixed in (sensitivity: drop them); per-pair samples are thin (median 2-4.5 games per pair per season), which is why NBA adjacent claims are expected to be unresolved already; treat as a result, not a defect.
