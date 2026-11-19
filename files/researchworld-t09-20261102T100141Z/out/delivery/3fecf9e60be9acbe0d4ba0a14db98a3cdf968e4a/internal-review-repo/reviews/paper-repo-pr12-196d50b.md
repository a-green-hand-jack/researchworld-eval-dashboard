# Review record: paper-repo PR #12, head 196d50b4ca0a (third round)

Verdict: **request changes** (remaining items wait on experiment-repo and figtab-repo).

Inspected: `make_numbers.py` regenerates `numbers.tex` identically; diff 540804e..196d50b touches only `experiments.tex` and `paper.pdf`.
Resolved: D paper side (Sec. 4.2 no longer ranks the real graphs; 0.34/0.46/0.55 are macros; family count flagged as single-draw). Together with B, C, G.
Open (unchanged since the previous record, all waiting on other owners): A (paper-numbered figure/table map, figtab-repo#6); E (config.json/experiments.py seed mismatch), F (run times, dangling "EXPERIMENT TABLE", MAINML listing) (experiment-repo#7); D experiment side (baseline-draw reruns on real graphs) is now optional for approval provided the single-draw wording stays, since the claims no longer depend on it.
