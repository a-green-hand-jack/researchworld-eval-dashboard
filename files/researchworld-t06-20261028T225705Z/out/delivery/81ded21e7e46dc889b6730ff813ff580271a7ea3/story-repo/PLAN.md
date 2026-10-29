# Study plan: stability of pairwise-comparison leaderboards

Status: v2 (revised after idea-review-repo feasibility verdict, story-repo#4; split in world/paper-repo PR #3). Objective: story-repo issue #1.
Budget reality: the world has 7200 model-seconds and 96 turns in total, one week of wall clock, CPU only.
The plan is tiered so the core finishes first; tier-2 work is added only after tier 1 is reported.

## Operational research questions
- **RQ1 (how fragile?)** For a fitted Bradley-Terry (BT) leaderboard, what is the smallest perturbation of the comparison
  data that changes a *decision* readers take from it: (a) the identity of rank 1, (b) the top-k set (k=3,5,10),
  (c) the order of a chosen adjacent pair, (d) rank correlation (Kendall tau) falling below 0.95 / 0.9?
- **RQ2 (noise vs. intent)** How does the budget needed by a *worst-case* (adversarial) perturbation compare with what
  *benign* noise does (bootstrap/resampling of comparisons, random deletion, random label flips)?
- **RQ3 (across designs)** Does fragility differ across evaluation designs, after scale is put on a common footing?
  Designs (real data, >= 2 required): crowd votes (Arena 55k), expert human + model judge on the same questions
  (MT-Bench human vs GPT-4 pair judgements), sports (NBA Elo file). Tier 2: LLM-judge verdicts on Arena battles
  (potsawee), Arena 140k, WebDev Arena.
- **RQ4 (what explains it)** Which measurable properties (adjacent-score gap in standard errors, comparisons per participant,
  tie rate, graph density, number of participants) predict the budget? Check with a clearly-labelled **synthetic** BT
  simulation where the truth is known (synthetic data used only for calibration, never as a headline result).

## Perturbation models (define scale carefully; justify in the paper)
1. Removal of m comparisons (the "small data change" / noise-or-deletion case).
2. Label flip of m comparisons (win<->loss; tie handling stated).
3. Injection of m new comparisons (vote-rigging-like; relates to starter lit 6 and 7), restricted to the realistic
   case of votes involving the target participant.
Budget is reported three ways: absolute m, fraction m/N, and **normalised** m / (benign-noise scale), where the benign scale
is the number of random removals/flips (or bootstrap resample size) that produces the same typical change in the same decision.
Cross-dataset comparison uses the normalised and fractional budgets, plus a common-N subsampling control (subsample each
dataset to the same N and, where possible, the same number of participants) to separate "size" from "design".

## Methods
- Model: BT MLE as logistic regression (ties as half-win, as in the Arena notebook; ties-as-separate-outcome and
  Davidson tie model as sensitivity). Light L2 for identifiability; fixed anchor/centering.
- Adversarial search: (i) influence-function / first-order approximation (Koh & Liang; Broderick et al. AMIP) to
  rank candidate comparisons; (ii) greedy with **exact refit** verification after each batch / by bisection on m;
  (iii) a direct pair-targeted heuristic (comparisons between the two participants) as a baseline.
  Reported budgets are *upper bounds on the minimum* (a found attack proves fragility; failure to find one does not prove
  robustness) -- the paper must say so. If a cheap certificate lower bound is possible (e.g. linearised bound), include it.
- Baselines: random removal/flip of the same size (Monte-Carlo, >= 100 draws, CI), bootstrap rank intervals,
  online Elo (as an alternative ranking method; natural for NBA).
- Uncertainty: bootstrap/resampling over comparisons for every headline number; seeds fixed; target pairs chosen by a rule
  fixed in advance (adjacent pairs; top-1 vs. rank-2) not by looking at results.
- Checks: approximation vs exact refit agreement; sensitivity to ties, regularisation, duplicates, model-name merging in Arena;
  NBA: home-court advantage handling stated (BT with home term vs without), `_iscopy` dedup.

## Division of work (see CODEOWNERS in paper-repo)
| Position | Delivers |
| --- | --- |
| idea-repo | context: prior work, conventions for BT leaderboards; Brief page. Must stay within the allowed starter literature and the objective's "do not access" rules (starter item 8 is not to be read, cited or searched for -- it closely matches the barred paper; follow idea-repo's Brief §3 and its search discipline; any accidental contact is logged in REPRODUCE.md). |
| idea-review-repo | feasibility verdict on this plan (tiers, budget) before experiments run |
| experiment-repo | `code/`, `results/`, `REPRODUCE.md`: data fetch with checksums, fits, perturbation experiments, uncertainty, sensitivity checks |
| figtab-repo | `figures/`, `tables/` for the claims C1-C5 below (main text: C1-C3, C4 if it fits in 9 pages) |
| venue-repo | `venue/`: chosen conference (latest edition, ICML/ICLR/NeurIPS), template, page limits, checklist requirements |
| paper-repo | `paper/` PDF + LaTeX incl. checklist, related work, limitations |
| story-repo | this plan, CODEOWNERS, claim list, consistency checks between analysis and paper |

## Claims the evidence must be able to support (drives figures/tables)
- C1: fragility curve per dataset: decision-flip probability / min budget vs. gap (figure) and a summary table with CIs.
- C2: adversarial vs benign budget ratio per dataset and decision type (table).
- C3: design comparison under common-N control (figure).
- C4: predictors of fragility (figure/table; synthetic calibration in appendix, labelled synthetic).
- C5: robustness to modelling choices (appendix table).
Any of C1-C5 may come out null ("sensitivity small" or "depends"); report as measured.

## Order and tiers
Tier 1 (must): Arena 55k, MT-Bench human + GPT-4, NBA; RQ1-RQ3; exact-refit verified attacks; baselines.
Tier 2: RQ4 synthetic calibration, sensitivity table, potsawee judges on Arena, Arena 140k (needed columns only).
Tier 3: WebDev Arena (licence agreement applies; skip if unclear).
Run heavy loops on `local-compute`; keep model-time use low (few long scripts, not many turns).

## Delivered paths and page budget (settled with venue-repo, story-repo#3)
Venue: NeurIPS 2026 main track, <= 9 content pages including figures/tables; refs, appendix, checklist excluded; appendix carries no main claim.
Main text therefore holds C1-C3 (+ C4 if it fits); C5 and synthetic calibration go to the appendix.
Paths: `paper/main.pdf`, `paper/*.tex` (checklist inside the tex), `REPRODUCE.md` (repro README), `code/` (all analysis code),
`figures/` + `figures/scripts/` (figure scripts), `tables/` + `tables/scripts/` (table scripts), `results/` (tidy CSVs the tables/figures read), `venue/`.

## v2 revisions (adopting idea-review-repo's verdict, story-repo#4; all six items accepted)
1. **Normalised budget, single definition.** Cross-dataset scale = (a) the target gap in bootstrap-SE units, and (b) b50 =
   the bootstrap/subsample size (fraction of N) at which the decision flips with probability 0.5 (always exists by taking
   small enough subsamples). Adversarial budget is reported as m, m/N, and m relative to the number of comparisons that
   carry the targeted participant(s) (m_i). The "equal random-removal effect" ratio in v1 is dropped. Random-removal/flip
   at the adversarial budget is a baseline reported as flip probability (often 0), not used as a denominator.
2. **Common-N controls fixed before running:** (i) Arena subsampled to N of MT-Bench-human/GPT-4 over all 64 models; (ii) Arena
   restricted to the top-6 models with all available comparisons (and its subsample to N). NBA analysed per season (~69
   replicates; dedupe `_iscopy`; BT with home term; sensitivity without) -> a distribution of fragility. MT-Bench GPT-4:
   state a rule for the position-bias/"tie (inconsistent)" rows (primary: inconsistent -> tie; alt: drop). No causal
   "experts vs crowds" claim: each design has one dataset except NBA seasons.
3. **Bootstrap-of-attack capped.** Random baselines and bootstrap rank intervals: >=100-200 resamples. Adversarial budgets:
   pre-declared targets only (top-1 vs rank 2; adjacent pairs at ranks 1-2, 5-6 or similar fixed ex ante; Kendall threshold),
   all NBA seasons; at most 50 attack-resamples on one dataset, only after benchmarking one verified attack (experiment-repo
   to report seconds per attack; plan is adjusted from that number).
4. **Tiers:** tier 1 unchanged. Tier 2 reduced to RQ4 synthetic calibration (labelled synthetic) and the C5 sensitivity table
   (ties handling, L2, home term). potsawee judges, Arena 140k, WebDev Arena deferred: only if tier 1 is reported with budget
   to spare. Tier 3 dropped.
5. **Decisions:** top-1 (a), adjacent-pair order (c), Kendall tau (d) required; top-k set (b) optional (single k=3 only if time).
6. **Budget gates (world model-seconds, 7200):** tier-1 results reported by ~45% (3200 s); paper writing begins by ~55%;
   >=20% reserved for review/fix rounds. story-repo checks `ht-role status` at each gate; if behind, drop sensitivity (C5) and
   synthetic (C4) before any tier-1 baseline.

Mandatory scope statements in the paper: attacks are upper bounds on the minimal flip size (no robustness proof); results
concern BT fits to these snapshots (Arena-55k is 2023-24), not live leaderboards; Arena rows lack user/prompt ids so
bootstrap CIs are optimistic (rows not independent); static NBA BT is misspecified over long windows (hence per season).

## v3 additions (from idea-repo context digest, story-repo#5)
- **Tie rule per dataset (fixed before running).** Arena 55k: tie and both-bad merged into tie (31% of battles), primary = half-win to each side; sensitivity = ties dropped. MT-Bench human: tie = half-win; GPT-4: "inconsistent" -> tie (alt: drop). NBA: no ties. Chiang et al. do not state their tie handling, so we do not claim to reproduce "the Arena" fit exactly; we state our rule.
- **Arena-convention decision (e):** besides top-1, adjacent-pair order and Kendall tau, report the *published-style* rank = 1 + #models whose CI lower bound exceeds the model's CI upper bound (sandwich CIs), and whether it changes under perturbation (so the claim speaks to what readers see on a leaderboard). Optional/cheap; computed on the refit that verifies each attack.
- **Design vs size claims.** Only two contrasts are clean: MT-Bench expert vs GPT-4 on the 1,232 items present in both (design contrast, same models/questions), and within-dataset size/structure variation (subsampling, NBA seasons). Cross-dataset differences (Arena vs MT-Bench vs NBA) are confounded with N, #participants, tie rate and structure and are reported as such, never as a causal "design" effect; RQ3 is answered at that level, RQ4 quantifies the structural drivers.
- Reading requests to idea-repo: tie-extended BT (Davidson / half-win) and BT MLE existence on sparse or perfectly-separated graphs (NBA seasons, MT-Bench pairs), AMIP formulas as used for the ranking event.

## v4 amendments (idea-repo checks, story-repo#6)
- NBA: fit per season **and per `lg_id`** (1968-76 ABA/NBA are disconnected components in the same file; the MLE does not exist otherwise). Seasons or subsamples whose comparison graph is not connected are flagged and excluded or ridge-guarded (stated per case).
- Every attack step checks graph connectivity; a "flip" achieved by disconnecting the graph is not counted as a result. Common-N subsamples of Arena that disconnect 64 models need the ridge/guard fixed first (ridge value stated).
- No certified lower bound exists (AMIP is only an upper bound on the minimal budget): the paper reports "smallest budget found", never a minimum; v1's optional certificate is removed.
- Benign unit = bootstrap/sampling scale (CI width of the targeted gap; b_q subsample scale with censoring flags, as experiment-repo implements). Random-removal-equivalence ratio stays dropped.
- Budgets are defined on rank events, not score units (tie model changes score scale but not ordering: Kendall 0.98-1.0 across half-win/ties-dropped/Davidson/Rao-Kupper).
- Exact refit by bisection along the influence order is mandatory (first-order magnitude errors up to ~40%); report approximation error as a result.
