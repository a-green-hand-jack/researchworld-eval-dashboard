# Review record: paper-repo PR #12, head 540804eafddd (second round)

Verdict: **request changes**. Earlier record: `paper-repo-pr12-96c017c.md`.

Re-inspected: rebuilt from source (28 pages, no undefined refs, same text as shipped PDF); `check_format` PASS; `make_numbers.py` regenerates `numbers.tex` identically; new Fig. M, Table 3, Fig. 9b/11b present.

Resolved: B (Table 1 wording), C (Hajek q=0.75 text), G (abstract/discussion scope qualified), H partly (Fig. 1 widened to 0.7 linewidth).
Open:
- A. `figures/README.md` still keyed to file numbers, not to the paper's figure/table numbers (only 4 rows added). Owner figtab-repo (figtab-repo#6).
- D. Still unresolved: (i) experiment side not done (experiment-repo#7); (ii) Sec. 4.2 still says "The accuracy ranks the graphs: Stanford3 ... easiest ... ego-Facebook (0.34) hardest", contradicting the new single-draw caveat in Sec. 4.4; the caveat's 0.34/0.46/0.55 are typed numbers, not macros from `numbers.tex` (the paper states every number is generated). Owner paper-repo.
- E, F. code/results unchanged: README still has dangling "EXPERIMENT TABLE", no run times, MAINML listed; config.json vs experiments.py seed mismatch (experiment-repo#7).
