# Review of the final version (paper-repo PR #17, main 05011da4a8ca into final)

Document read: `document` branch `main/document.pdf`, built-from 05011da4a8ca2c0254fb8c7962203b27cfd20f06 (= PR head). 23 pages: 9 main, references, appendix A-E, checklist. Diff against the released v1 (40d9e36): wording only (R3 direction aggregation in §5, noise-margin sentence in §6.5, two table captions in Appendix C). Findings of `version1-pr13-rereview.md` otherwise unchanged and answered.

## Against the whole objective
- Question answered with a defined price (breadth, depth, feasibility), six rule families, three public boards, tests fixed in advance and reported with the verdicts as they came, conditions of validity and failure stated. Intended paper sections present; NeurIPS 2026 template, 9 main pages, checklist, anonymous. Numbers trace to released results; uncertainty is cluster-bootstrap. Reproduction notes give versions, data SHAs, seeds, commands, compute, script-per-table.
- **Gap against the objective's "not to access" clause:** `deliverable.md` requires that anything accidentally met of the withheld paper or pages discussing it be recorded in the reproduction notes (what, where, how much). Neither `code/REPRODUCE.md` nor `README.md` says anything on it, so a reader cannot tell whether nothing was met or the record is missing.

## Findings
**F1 (must). Reproduction notes lack the contact statement.** Add a short section to `code/REPRODUCE.md` stating either that no forbidden material was met, or what was, where and how much was read. The statement must come from the roles that searched the literature (idea-repo, which holds the record of what was read); it must not be written from assumption.

**F2 (must). R3 verdict contradicts its own criterion.** §5 (and the Brief) refute R3 if the held-out R2 is at least 0.9; the minimum reaches 0.93 (median 0.89) in its best direction (§6.4, Table 6). §5 now says the worst and best of six directions are reported, but the verdict is "borne out" / "supported" on the worst direction only. State the rule that decides the verdict (e.g. "refuted for a rule if its R2 reaches 0.9 in any direction") and apply it: either supported for six of seven rules with the minimum as the exception, or supported on the worst-direction reading, said as such in §6.4, Table 3 and the abstract/intro wording. One-sentence change; numbers unchanged.

## May (do not hold)
m1-m6, m8 of the first record, carried.

## Conclusion
Not approved at 05011da4a8ca: request changes for F1, F2. Everything else meets the objective and the venue's requirements as read.
