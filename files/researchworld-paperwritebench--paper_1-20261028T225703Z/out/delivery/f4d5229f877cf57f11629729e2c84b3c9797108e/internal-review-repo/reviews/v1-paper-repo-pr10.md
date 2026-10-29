# Review record: paper-repo PR #10 (Version 1), head 46de00d188c7b79056ba48385f9ae3d3a231690d

Inspected at that commit: template.tex, references.bib (identical to supplied), tables/*.tex, figures/* (all 7 opened and viewed;
foret_ablation.pdf is a regeneration of the supplied jpg), compiled with a stand-in neurips_2025.sty (not supplied; local stubs for
inconsolata/listofitems/ulem which this sandbox lacks), and code/ (openrlhf) for method fidelity. Conclusion: REQUEST CHANGES.

## Verified OK
- All numbers in tables match the supplied tables; text numbers (deltas to base, margins, ablation differences, 32B gains) recomputed and correct.
- Tables' Delta rows were recomputed against the stated strongest-baseline underline (supplied tables had inconsistent deltas, e.g. 72B MathVision +6.8, MMMU -1.4; 7B MathVista +4.7, MathVerse +6.3); the new values (+6.5, -1.5, +1.9, +3.9) are correct against the data.
- Figures exist, are legible and match their captions (teaser, vanishing_adv, adv_histogram, ssr_eval_curve, foret_ablation values 2.5/8.5/13.2 etc. agree with the supplied jpg).
- All 42 cited keys exist in references.bib; compile has no undefined citations/references after reruns. (references.bib has stray `,` lines at 35/252/264/276... that make bibtex report 34 errors; entries still resolve.)
- Negative result (MMMU val -1.5 vs QvQ, below Llama4-Scout) and single-run caveats are reported.

## Findings (all open, for paper-repo)
1. Forced Rethinking description contradicts code. experience_maker.py ~2018-2025 drops every rethought trajectory with res<0.5 ("only need to show correct rethinking"), keeps at most 2 per query (q2cnt<2), and ~2060-2075 *replaces* the original response in the group with the correct rethought one. Paper says rethought trajectories are added to the batch (Alg. 1), are scored by the same reward so wrong ones get negative credit, and that a model second-guessing correct answers is "penalised by the reward". None of that is what the code does. Correct Sec. 3.2, Alg. 1 and the conclusion/intro wording.
2. Advantage definition (Eq. 1) is not what the code computes. Code ("group"/"group_sft") subtracts the group mean only (experience_maker.py ~459-460) and does not divide by per-group std; the supplied adv_histogram/overview histograms have range [-1,1], impossible with std-normalised binary rewards. State the mean-only baseline (and what batch-level normalisation applies) or label Eq. 1 as standard GRPO and give the used one.
3. Rethinking fraction q is never given. Code: eligible complete responses are skipped with prob 0.35 (`np.random.uniform()<0.35: continue`), and incorrect responses in groups with mean >0.7 are also skipped. State q (or that about 65% of eligible responses are selected) in Sec. 3.2/4.
4. "Bound" in Fig. foret / Sec. 4.4: code (force_append_wait_all, `add_this = res>0.5  # this is upper bound`) shows it is an oracle: forced rethinking on all responses, counting a response only when rethinking yields a correct answer. Say so explicitly instead of "as we read the figure legend"; and say it is not attainable by a deployed model. Also the "forced" test-time variant uses the minimal "Wait" trigger in the code (selected=0 at eval).
5. Data-mix wording: "Removing the Text subset (13K queries)" / "Science and Text subsets (11K queries)" reads as if the removed subset is 13K/11K; in Table 3 these are the remaining sizes (16K -> 13K -> 11K).
6. Unsupported motivation: abstract/intro state that RL alone does not reliably produce reflective behaviour. No supplied experiment measures this (no rethinking ratio of the SSR-only model; the reward even gives +1.1 for native "Wait"). Hedge it as a hypothesis motivating the design, or support it.
7. Fig. 7 (rethinking) caption says the continuation "identifies the error and corrects it", while the text states the example ends without the requested answer; make the caption consistent. Rethinking ratios in Fig. 6b (36/24/78/18) are read off the supplied plot (marked ~); say "approximately" in the text.
8. Length: with a stand-in 5.5in x 9in single-column geometry, main text ends on p.12 (conclusion spills), references p.13-15; paper-repo reports p.11. The real neurips_2025.sty is not supplied, so I cannot confirm 11 pages; re-check after tightening if the style is available. (Informational.)

## Posture
Version 1 is close; items 1-2 are factual and must be fixed, 3-7 are accuracy/wording fixes. No findings for figtab-repo: figures and tables are accepted.

---
# Re-review at head 8e9f7f5067f0 (draft-4, PR #14 merged)

Resolved from the first round (checked in template.tex against code/): findings 1 (rethinking keeps only correct trajectories, at most 2 per query, replacing originals), 2 (mean-only advantage, Eq. 1 now matches the code), 3 (q ~ 0.65 and the group-accuracy skip rule), 4 (bound defined as oracle), 5 (13K/11K wording), 6 (motivation reworded, no unsupported claim), and the caption/ratio wording in 7. Numbers unchanged and still correct; 38.9K vs 16K subset relation is honestly flagged as unspecified. Related-work benchmark/data paragraph was removed (benchmark citations remain in Sec. 4.1); conclusion no longer overclaims selectivity ("OpenAI-o1 stronger on five of seven" is correct per Table 1).

New/remaining finding:
- Fig. 7 (rethinking.jpg) is now included at 0.45\linewidth (~2.5 in for a 1330 px image): the example response text and most of the word cloud render at about 3-4 pt and are unreadable in the compiled PDF. The figure exists to show the trajectory; it must be legible (e.g. width >= ~0.75\linewidth, or crop to the example panel and keep the quoted text in the prose), paying for the space elsewhere.
- Informational: with my stand-in geometry (5.5in x 9in, single column) main text still runs ~8 lines onto p.12 and the references begin there (14 pages total); paper-repo reports 11 pages with its stand-in. Real neurips_2025.sty not available; re-check page count after enlarging Fig. 7.

---
# Final review at head d5734c0f24c4 (draft-5, PR #15 merged): APPROVED

Inspected at that commit: diff 8e9f7f5..d5734c0 (template.tex only: Fig. 7 now cropped into example panel at 0.85 linewidth plus word cloud panel; text tightened; removed sentences were non-factual or redundant, no numbers or claims changed), recompiled with the stand-in style: no undefined references/citations, Fig. 7 example text legible in the PDF, all 7 figures and 3 tables present and referenced, all numbers still match the supplied tables, method text matches code/ (mean-only advantage, correct-only replacing rethought trajectories, q~0.65, oracle bound).
Page count: my stand-in (article 10pt/12pt leading, 5.5x9in) is looser than the real NeurIPS 10/11pt leading and ends the conclusion ~9 lines onto p.12; the real style is more compact, so 11 pages of main text is plausible; I cannot verify without neurips_2025.sty (not supplied). Not treated as a defect.
Known residual, not blocking: references.bib is the supplied file unchanged (stray commas make bibtex report errors on a few entries but every cited key resolves); the 16K-subset vs 38.9K relation is honestly stated as unspecified; results are single runs, stated.
