# ICLR 2027 submission items and our answers

ICLR 2027 has no NeurIPS-style paper checklist; these are the items it asks of authors (venue-repo `templates/checklist_iclr2027.md`). Section numbers refer to `paper/main.tex`; the answers are re-checked against the PDF before each version is proposed.

| Item | Mandatory | Where / answer |
|---|---|---|
| Main text <= 9 pages (submission) | yes | See `paper/main.pdf`; checked with `venue-repo/tools/check_venue.py` before each version. |
| Anonymous: no authors, affiliations, identifying links; `\iclrfinalcopy` commented out | yes | Author block reads "Anonymous authors"; `\iclrfinalcopy` is commented out in `main.tex`. |
| Official style files unmodified | yes | `paper/iclr2027_conference.sty`, `.bst`, `natbib.sty`, `fancyhdr.sty`, `math_commands.tex` are copies of the venue's files (hash-checked by the venue checker). |
| AI use statement section (<= 1 page, truthful) | yes | Section "AI use statement" (`paper/ai_use.tex`, same text in `paper/ai_use.md`). States that the study was done by LLM agents. |
| AI use disclosure in the submission form (form) | yes | Not part of the PDF; no submission is made by this study. |
| Acknowledge ICLR Code of Ethics (form) | yes | Not part of the PDF; no submission is made. Data are public leaderboard scores, no human subjects (Ethics statement). |
| Reproducibility statement (one paragraph, pointers only) | recommended | Section "Reproducibility statement"; details in `REPRODUCE.md`. |
| Ethics statement (<= 1 page) | recommended | Section "Ethics statement". |
| Code / supplementary material anonymised | encouraged | Repository contents contain no author names. |
| Claims in abstract and introduction match the evidence and scope | review standard | Scope (three leaderboards; MTEB are embedding models, not generative LLMs) is stated in abstract and Section 7. |
| Uncertainty reported for every comparison | review standard | Cluster-bootstrap CIs over test models and paired differences; what is resampled is stated in Section 4. |
| Limitations and failure cases discussed | review standard | Section "Discussion and limitations". |
