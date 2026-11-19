# Second review of paper-repo PR #10 (v1-release -> release), head 3ffce6d1b319afed38a5e0fb9f6886fb231084f5

Conclusion: **approved as an intermediate version**; items below remain for `final`.

## Inspected
- `paper.pdf` at the head: 20 pp., main text ends p. 9 (check_venue RESULT OK), rendered all pages; opened Figs. 1-3, 5-10 and 12-13 (Figs. 4, 11, 14-16 are the same layouts seen in the first review/by script). Fig. 6 (failure map) and Fig. 7 (factor ranking) now at full text width, legible at print size; new Fig. 8 (gamma dependence, e11), Fig. 9 (Hajek, e12) are labelled and agree with their text.
- `paper/check_numbers.py`: passes, now including e11/e12 numbers.
- Earlier findings: (1) process claim: now stated correctly (Sec. 4 and App. D: directional predictions in the plan, thresholds written after e1-e10 completed, not pre-registered; e11/e12 rules written before their cells were read, by experiment-repo's account) - resolved. (3) Fig. 6 caption pointer: all-graph maps are Figs. 12-16 - resolved. (4) legibility, manifest 806, paper-number map - resolved. (5) appendix blank space reduced.
- Finding 2 (forbidden-access record): partly resolved: App. D now says idea-repo records no encounter. Still open for `final`: it omits idea-repo's account of what it did (four OpenAlex title searches for named works; abstracts of starter items; six starter PDFs read by a delegated reader; snippets of 12 further titles, none opened - idea-repo#3 comment), and `REPRODUCE.md` section 8 still says idea-repo's log is "theirs to add".

## Open for `final`
a. Put idea-repo's statement (idea-repo#3) into `REPRODUCE.md` section 8 (experiment-repo path, by PR) and a one-sentence summary of the searches into App. D.
b. e13 (second seed of H5/H2/H4 cells) was still running; report its verdicts (t16) in the paper, or say in the paper and REPRODUCE that it was not completed. The "unclear" H5 verdict rests on one seed until then.
