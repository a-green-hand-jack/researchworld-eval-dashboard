# Literature candidates (idea-repo)

`references_candidates.bib` — 40 entries, all verified to exist (arXiv API / Crossref / DOI BibTeX, 2026-10-28), all published ≤ 2024-10 (cutoff 2024-11). It compiles cleanly with `bibtex` (plain style). The paper's `references.bib` should contain only the entries actually cited; the supplied `references.bib` holds template placeholders (Authors14, Alpher02…) only and should be replaced. Titles/authors come from arXiv metadata; venue fields come from my own knowledge of where each was published and, for TIFS and TNNLS, from Crossref. Entries with only "arXiv preprint" had no verified venue.

## Use by topic (suggested)
- Problem / motivation, exact unlearning: `cao2015towards`, `bourtoule2021machine`, `ginart2019making`; survey `nguyen2022survey`.
- Newton / influence-style approximate unlearning (the family this method is in): `guo2020certified` (certified removal, Newton step, L2-regularised convex losses), `koh2017understanding` (influence functions), `sekhari2021remember`, `izzo2021approximate`, `neel2021descent`, `gupta2021adaptive`, `warnecke2023machine`, `golatkar2020eternal` (Fisher forgetting), `qiao2024hessian` (Hessian-free certified unlearning, arXiv).
- Linearised / mixed-linear networks: `golatkar2021mixed` (mixed-privacy forgetting), `golatkar2020forgetting`, `lee2019wide`, `jacot2018neural`.
- Zero-shot / source-free unlearning (closest related): `chundawat2023zero` (zero-shot MU, error-minimising noise + gradient-based impair/repair), `foster2024information` (**the "JiT" baseline of the log** — "Just-in-Time"; log describes it as Lipschitz-regularisation; arXiv 2402.01401, the title of the paper is "An Information Theoretic Approach to Machine Unlearning" — the arXiv abstract describes a zero-shot method minimising the gradient of the function around the forget point), `chang2024zero` (zero-shot class unlearning, arXiv Oct 2024), `kurmanji2023towards` (SCRUB; uses retain data), `chundawat2023bad` (needs retain data subset), `tarun2024fast`.
- Baselines in the log: NegGrad ≈ gradient ascent on the forget set (no dedicated citation in the log; `golatkar2020eternal`, `thudi2022unrolling`, `kurmanji2023towards` use/discuss it); Random Labels ≈ `graves2021amnesiac` (amnesiac ML) / relabel-and-finetune used in `golatkar2020eternal`-style comparisons; "Adversarial" = instance-wise unlearning with adversarial examples + weight importance → `cha2024learning` (this matching is my reading of the log's one-line description; confirm it is stated as "we follow the description in the log" rather than as fact about their exact code); JiT = `foster2024information`. Other fine-tuning/pruning methods: `foster2024fast`, `jia2023model`, `fan2024salun`, `chen2023boundary`, `chien2024certified`.
- Evaluation: `shokri2017membership` (membership inference), `goel2022towards`, `thudi2022unrolling`.
- Convex / SDP tools: `vandenberghe1996semidefinite`, `boyd2004convex`.
- Setup: `he2016deep` (ResNet-18), `deng2009imagenet` (ImageNet pretraining), `krizhevsky2009learning` (CIFAR-10/100), `khosla2011novel` (Stanford Dogs), `griffin2007caltech` (Caltech-256).

## Deliberately excluded
- "Towards Source-Free Machine Unlearning" (arXiv 2508.15127, Aug 2025) and any other work after 2024-11: violates the date cutoff (and the knowledge-isolation rule).
- Any claim that other papers share this paper's SDP/Hessian-estimation idea: I could not verify that and the paper must not assert it.

## Cautions for the writers
- Describe each cited method only as far as its abstract/title supports; do not attribute results to them that are not in the log. Do not state that the cited baselines were "run with the original code/hyper-parameters" — the log does not say.
- Cite own-work-type phrasing in third person (double blind).
- `thudi2022unrolling` venue (EuroS&P 2022) and `golatkar2021mixed` (CVPR 2021) are from memory — not checked against a venue page; if the report lists them with venue, a reviewer should recheck, or fall back to the arXiv form.

## Added
- `gdpr2016`: the GDPR (Art. 17, right to erasure) for the privacy-regulation motivation.

## Evaluation convention (as used in the supplied log, and in the works above)
Retrained-from-scratch on the retain set is the reference; report test / retain ("remaining") / forget accuracy plus a membership-inference score where ≈50% means the forget samples cannot be told from unseen data; and the gap to Retrained. A good unlearner has small gaps on all four — not just a forget accuracy drop (see the log's baselines: Random Labels forget acc 21%, MIA 47%, but test acc 20.6%).
