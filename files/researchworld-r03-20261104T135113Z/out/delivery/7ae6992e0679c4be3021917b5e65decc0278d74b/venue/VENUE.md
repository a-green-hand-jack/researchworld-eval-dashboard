# Venue decision and format requirements

Established 2026-11-04. Sources were read on that date; each requirement is marked **(verified)** (read on the official ICLR page or in the official template) or **(not established)**.

## Decision: ICLR 2027 (main conference)

- **Edition.** ICLR 2027 is the newest edition of the three allowed venues as of 2026-11-04. Its call for papers and style files are published (template commit `46ed6f4` of `github.com/ICLR/Master-Template`, dated 2026-09-01; zip from `https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip`, sha256 `0d940dfa9398ae99a18f24a85a8a683f367204b6af6d17d2899e60a67102529e`). The newest NeurIPS edition is 2026 (deadline May 2026; the NeurIPS 2027 call page returns 404). The ICML 2027 call page is a stub ("will be posted here soon"; checked 2026-11-04), so ICML 2026 is its latest edition with a template. Only ICLR was published later than the others.
- **Fit.** The paper is an evaluation-methodology / empirical-ML paper (benchmark selection and score inference). ICLR's main track accepts that, and it has no required checklist, so no checklist form is filled; the ICLR substitutes below are required instead.
- **Trade-off, stated plainly.** `deliverable.md` asks for the chosen venue's checklist "(for example NeurIPS's paper checklist)". ICLR 2027 does not require one (verified: the Author Guidelines page names none; the template has none). Instead it requires the AI-use statement. We therefore (a) fill the required AI-use statement, (b) include the recommended Reproducibility and Ethics statements, and (c) ask `paper-repo` for a *voluntary*, clearly labelled self-audit checklist in the appendix (not an ICLR requirement; see `checklist_selfaudit.md`). If the user prefers NeurIPS 2026 and its mandatory checklist, the venue is changeable, but would cost a re-format of `paper/`; I have not been asked to.

## Format requirements (ICLR 2027)

| Item | Requirement | Status |
|---|---|---|
| Template | `venue/template/` (unmodified official files; hashes in `venue/template.sha256`). `\usepackage{iclr2027_conference,times}`; bibliography style `iclr2027_conference.bst`; natbib. "Tweaking the style files may be grounds for rejection": do not edit `.sty`/`.bst`. | verified; test build of the official shell compiles (7 pages) |
| Main-text limit | **9 pages** for the submission version ("strictly enforced"; over the limit = desk rejection). 10 pages for rebuttal / camera-ready. | verified |
| What does not count | References; appendix (any length, placed after the bibliography; reviewers need not read it); AI-use statement; reproducibility statement; ethics statement; acknowledgements / ethics statements in camera-ready. | verified |
| What counts | All main text, figures, tables, and any theory placed in the main body, up to the end of the conclusion/discussion. | verified |
| Mode | **Anonymous submission build**: `\iclrfinalcopy` stays commented out; no author names, affiliations, acknowledgements or identifying URLs in the text, supplement or repo links (identity revealed = desk rejection). The shell's line-number ruler stays on. Camera-ready (`\iclrfinalcopy`) is not applicable to this delivery. | verified |
| Text block | 5.5 in x 9 in (single column), left margin 1.5 in, 10 pt type / 11 pt leading, Times, paragraphs separated by 1/2 line, title 17 pt small caps. | verified (template) |
| Figure width | Single column. Full width = `\linewidth` = 5.5 in (13.97 cm, 397.5 pt); use `\includegraphics[width=\linewidth]` or a fraction (e.g. two panels side by side at 0.48 `\linewidth`, each about 2.64 in). There is no two-column float. Use vector PDF; text in figures at least about 7 pt at final size. | verified (template); font-size floor is my recommendation, not a venue rule |
| Required statement | **AI-use statement** (mandatory section in the paper, at most 1 page, not counted in the page limit; also asked in the submission form). Must say: which tasks used generative AI (disclosure *required* for e.g. generating synthetic datasets, developing theoretical models, proofs, hypotheses, methodology, implementation, data cleaning, interpreting results; *recommended* for figures, code editing, drafting, literature search, polishing), which required-disclosure tasks did not use it, that all AI-assisted work was reviewed (and how), and that the authors take responsibility for the final content. Substantial LLM-produced falsehood is an ethics violation and can lead to desk rejection. | verified; the actual content must be written truthfully by `paper-repo` from what this organization did (see below) |
| Recommended | Reproducibility statement (one paragraph, before references, pointing at the paper/appendix/code that reproduces the results; not counted). Ethics statement (at most 1 page; the Code of Ethics acknowledgement is made in the submission form). | verified |
| Optional | Author-contributions section. | verified |
| Checklist | None required by ICLR 2027. | verified |
| Submission mechanics | OpenReview; every author needs a profile; at least one author a registered reviewer; quotas. Not applicable to an in-world delivery. | verified, not actionable here |
| Supplement | Anonymous code may be submitted as supplementary material; the reproducibility statement should reference it. Format/size limits of the supplement: not established. | not established |
| Reference style | natbib author-year per `iclr2027_conference.bst`; the exact layout is the template's. | verified |

## What the organization must disclose in the AI-use statement

This is a pointer for `paper-repo`, not the statement itself. In this world, essentially all of the work (ideas, planning, implementation, experiments, analysis, figures and drafting) was produced by LLM agents, and the statement has to say so truthfully, at the level of the required-disclosure task categories above, and say how the outputs were checked (for example, by independent review positions and by regenerating numbers from the shipped scripts). I cannot establish from here who counts as the "authors" taking responsibility; that sentence is `paper-repo`'s to word, and it should not claim human verification that did not happen.

## Items I could not establish

- ICLR 2027 supplementary-material size/format limits.
- Whether the ICLR 2027 style file differs in a content-relevant way from the 2026 one (I did not diff them; only the 2027 files are used).
- The deadlines on the call page are 2026 dates that have already passed (paper deadline 2026-09-25); this delivery is a research deliverable in the 2027 template, not a real submission.
